#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A literal `[...]` segment in a `produces:` path is not a glob — issue #1181.

`assert_declared_deliverables` classified an entry as a glob whenever it
contained any of `* ? [`. For a file-based routing convention that spells a
dynamic segment with brackets (Next.js App Router, Remix, SvelteKit), `[id]`
is a *literal directory name* on disk — but to `glob`/`fnmatch` it is a
character class meaning "one character, `i` or `d`". `glob.glob` therefore
returned `[]` no matter what the session wrote, so the presence gate refused
the WU every attempt with a byte-identical error and spun it to
`spinning_detected`.

Note the asymmetry this closed: `assert_produces_in_diff` tests literal
equality *before* falling back to `fnmatch`, so the same bracketed path
already passed the diff cross-check. The two guards' shared literal/glob
contract was true only for paths without brackets.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

#: A route path in the shape every bracket-routing framework produces.
BRACKET_PATH = "src/app/api/jobs/[id]/approve/route.ts"


class _RestoresCwd(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)


def _make_wu(produces: list) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=Path("WU-T01.md"),
        depends_on=[],
        type="implementation",
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title="bracket route",
        body="",
        produces=produces,
    )


def _write(rel: str, text: str = "export const GET = () => {}\n") -> None:
    p = Path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


# --------------------------------------------------------------------------- #
# The glob predicate — one rule, read by every surface that classifies a path #
# --------------------------------------------------------------------------- #


class TestProducesIsGlob(unittest.TestCase):

    def test_wildcards_are_globs(self):
        self.assertTrue(loop.produces_is_glob("src/**/*.ts"))
        self.assertTrue(loop.produces_is_glob("docs/adr-?.md"))

    def test_bare_bracket_segment_is_not_a_glob(self):
        self.assertFalse(loop.produces_is_glob(BRACKET_PATH))

    def test_plain_path_is_not_a_glob(self):
        self.assertFalse(loop.produces_is_glob("src/index.ts"))

    def test_bracket_with_a_wildcard_is_still_a_glob(self):
        """A wildcard anywhere means the author meant a pattern, so the
        brackets keep their character-class meaning."""
        self.assertTrue(loop.produces_is_glob("src/[abc]*.ts"))


# --------------------------------------------------------------------------- #
# assert_declared_deliverables — the gate that refused the file it was given  #
# --------------------------------------------------------------------------- #


class TestBracketPathPresenceGate(_RestoresCwd):

    def test_existing_bracket_path_passes(self):
        """The bug: the file is on disk at exactly the declared path."""
        with integration_workspace() as root:
            os.chdir(root)
            _write(BRACKET_PATH)
            ok, summary = loop.assert_declared_deliverables(_make_wu([BRACKET_PATH]))
            self.assertTrue(ok, summary)

    def test_absent_bracket_path_refused_as_absent_not_as_a_glob(self):
        """A missing bracket path is still refused — and the message names it
        as absent, which is actionable, rather than blaming a glob the author
        never wrote."""
        with integration_workspace() as root:
            os.chdir(root)
            ok, summary = loop.assert_declared_deliverables(_make_wu([BRACKET_PATH]))
            self.assertFalse(ok)
            self.assertIn("absent", summary)
            self.assertNotIn("glob", summary)

    def test_empty_bracket_path_refused_as_empty(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write(BRACKET_PATH, "")
            ok, summary = loop.assert_declared_deliverables(_make_wu([BRACKET_PATH]))
            self.assertFalse(ok)
            self.assertIn("empty", summary)

    def test_bracket_directory_still_refused_by_shape(self):
        """Directories were never valid produces: entries, bracketed or not."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("src/app/api/jobs/[id]").mkdir(parents=True)
            ok, summary = loop.assert_declared_deliverables(
                _make_wu(["src/app/api/jobs/[id]"]),
            )
            self.assertFalse(ok)
            self.assertIn("directory", summary)


class TestGlobBehaviourUnchanged(_RestoresCwd):
    """Guard not weakened: `*`/`?` entries keep every glob semantic."""

    def test_wildcard_glob_with_match_passes(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write("src/routes/a.ts")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src/routes/*.ts"]))
            self.assertTrue(ok, summary)

    def test_wildcard_glob_without_match_refused_as_a_glob(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src/routes").mkdir(parents=True)
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src/routes/*.ts"]))
            self.assertFalse(ok)
            self.assertIn("glob", summary)

    def test_wildcard_glob_ignores_empty_matches(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write("src/routes/a.ts", "")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src/routes/*.ts"]))
            self.assertFalse(ok)
            self.assertIn("glob", summary)

    def test_character_class_with_wildcard_still_matches_as_a_class(self):
        """`[abc]*.ts` carries a wildcard, so the class keeps its meaning and
        matches `b-route.ts` — an author who wants a class can still have one."""
        with integration_workspace() as root:
            os.chdir(root)
            _write("src/b-route.ts")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src/[abc]*.ts"]))
            self.assertTrue(ok, summary)


# --------------------------------------------------------------------------- #
# Cross-guard consistency — the property the shared contract claims           #
# --------------------------------------------------------------------------- #


class TestBothGuardsAgreeOnBracketPaths(_RestoresCwd):

    def test_diff_cross_check_accepts_the_bracket_path(self):
        """Already true on HEAD via the literal-equality branch; asserted here
        so the pair cannot drift back apart."""
        ok, summary = loop.assert_produces_in_diff(
            _make_wu([BRACKET_PATH]), [BRACKET_PATH],
        )
        self.assertTrue(ok, summary)

    def test_accepted_by_presence_gate_implies_accepted_by_diff_check(self):
        """The unified contract's property, over a bracketed path."""
        with integration_workspace() as root:
            os.chdir(root)
            _write(BRACKET_PATH)
            wu = _make_wu([BRACKET_PATH])
            presence_ok, presence_summary = loop.assert_declared_deliverables(wu)
            self.assertTrue(presence_ok, presence_summary)
            diff_ok, diff_summary = loop.assert_produces_in_diff(wu, [BRACKET_PATH])
            self.assertTrue(diff_ok, diff_summary)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
