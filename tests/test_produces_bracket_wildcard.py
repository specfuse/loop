#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A literal `[id]` segment beside a wildcard elsewhere — issue #1589.

#1181 fixed the case where a `produces:` entry's only metacharacters are a
literal bracket segment: `produces_is_glob` reads `*` and `?` only, so
`src/app/api/jobs/[id]/route.ts` is treated as the literal path it is.

An entry that mixes a literal bracket segment with a wildcard **elsewhere** was
still broken. The wildcard makes the whole entry a pattern, so `[id]` recovers
its character-class meaning — "one character, `i` or `d`" — and matches nothing:

    >>> glob.glob('src/app/[id]/*.ts', recursive=True)
    []
    >>> fnmatch.fnmatch('src/app/[id]/route.ts', 'src/app/[id]/*.ts')
    False

**Both halves of the unified contract failed here**, unlike #1181 where the
diff check's literal-equality branch rescued it: an entry carrying a wildcard is
never literally equal to a touched path, so it falls through to `fnmatch` and
fails for the same reason.

The fix escapes bracket segments that carry no wildcard *of their own*, so a
class written in the same segment as a wildcard (`src/[abc]*.ts`) keeps its
meaning — the escape hatch #1181 deliberately preserved.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_MIXED = "src/app/[id]/*.ts"


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


def _write_routes():
    p = Path("src/app/[id]")
    p.mkdir(parents=True, exist_ok=True)
    (p / "route.ts").write_text("export const GET = () => {}\n")
    (p / "page.ts").write_text("export default function Page() {}\n")
    return ["src/app/[id]/route.ts", "src/app/[id]/page.ts"]


class TestGlobPatternEscaping(unittest.TestCase):
    """The helper, in isolation — this is where the rule lives."""

    def test_bracket_segment_without_a_wildcard_is_escaped(self):
        self.assertEqual(
            loop.produces_glob_pattern("src/app/[id]/*.ts"), "src/app/[[]id]/*.ts",
        )

    def test_bracket_segment_with_its_own_wildcard_is_left_alone(self):
        """`[abc]*.ts` is an intentional class — the #1181 escape hatch."""
        self.assertEqual(
            loop.produces_glob_pattern("src/[abc]*.ts"), "src/[abc]*.ts",
        )

    def test_plain_and_wildcard_paths_are_untouched(self):
        for p in ("src/index.ts", "src/**/*.ts", "src/*/a.ts"):
            with self.subTest(p=p):
                self.assertEqual(loop.produces_glob_pattern(p), p)


class TestPresenceGateMatchesMixedEntry(_RestoresCwd):

    def test_mixed_entry_matches(self):
        """The bug: two real files, entry declared them, gate refused."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_routes()
            ok, summary = loop.assert_declared_deliverables(_make_wu([_MIXED]))
            self.assertTrue(ok, summary)

    def test_mixed_entry_still_refuses_when_nothing_matches(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src/app/[id]").mkdir(parents=True, exist_ok=True)
            ok, summary = loop.assert_declared_deliverables(_make_wu([_MIXED]))
            self.assertFalse(ok)
            self.assertIn("glob", summary)

    def test_intentional_character_class_still_matches_as_a_class(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir(exist_ok=True)
            Path("src/b-route.ts").write_text("x\n")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src/[abc]*.ts"]))
            self.assertTrue(ok, summary)


class TestBothGuardsAgreeOnMixedEntry(_RestoresCwd):
    """Unlike #1181, the diff half failed here too — pin them together."""

    def test_diff_cross_check_matches(self):
        ok, summary = loop.assert_produces_in_diff(
            _make_wu([_MIXED]), ["src/app/[id]/route.ts"],
        )
        self.assertTrue(ok, summary)

    def test_accepted_by_presence_gate_implies_accepted_by_diff_check(self):
        with integration_workspace() as root:
            os.chdir(root)
            touched = _write_routes()
            wu = _make_wu([_MIXED])
            presence_ok, presence_summary = loop.assert_declared_deliverables(wu)
            self.assertTrue(presence_ok, presence_summary)
            diff_ok, diff_summary = loop.assert_produces_in_diff(wu, touched)
            self.assertTrue(diff_ok, diff_summary)

    def test_diff_check_still_refuses_an_unmatched_entry(self):
        ok, _ = loop.assert_produces_in_diff(_make_wu([_MIXED]), ["src/other/a.ts"])
        self.assertFalse(ok)


class TestRefusalNoteResolvesMixedEntry(_RestoresCwd):

    def test_note_reports_a_matched_mixed_entry_as_present(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write_routes()
            note = loop.format_deliverable_missing_note(
                _make_wu([_MIXED, "MISSING.md"]),
                "declared deliverable absent: MISSING.md",
                [],
                attempt=1,
            )
            self.assertRegex(note, r"\[id\]/\*\.ts.*(?i:present)")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
