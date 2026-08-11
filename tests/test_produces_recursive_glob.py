#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`produces:` entries containing `**` must match recursively — issue #1744.

`assert_declared_deliverables` called `glob.glob(path)` without
`recursive=True`. In Python that makes `**` behave as a single `*`: it matches
one path level, which for a directory tree yields directories, and the guard's
`Path(m).is_file()` filter then drops all of them. A work unit that produced
every declared deliverable was refused `deliverable_missing`, retried to the
cap, and escalated `spinning_detected` — **$32.74 across three byte-identical
refusals** in one downstream occurrence.

Observed directly:

    >>> glob.glob('src/test/expectations/typescript/**')
    ['src/test/expectations/typescript/Grp']            # a directory
    >>> glob.glob('src/test/expectations/typescript/**', recursive=True)
    [... 'src/test/expectations/typescript/Grp/src/comp/a.ts']

This is the third instance of the two halves of the unified literal/glob
contract disagreeing (after #1181 and #1589): `assert_produces_in_diff` uses
`fnmatch`, whose `*` already crosses `/`, so the diff cross-check accepted the
same entry the presence gate refused.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_TREE = "src/test/expectations/typescript/Grp/src/comp"
_STARSTAR = "src/test/expectations/typescript/**"


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
        title="deep tree",
        body="",
        produces=produces,
    )


def _write_tree() -> str:
    p = Path(_TREE)
    p.mkdir(parents=True, exist_ok=True)
    (p / "a.ts").write_text("export const a = 1\n")
    return str(p / "a.ts")


class TestRecursiveGlobSatisfiesPresenceGate(_RestoresCwd):

    def test_starstar_matches_a_file_several_levels_down(self):
        """The bug: every declared deliverable existed and the gate refused."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_tree()
            ok, summary = loop.assert_declared_deliverables(_make_wu([_STARSTAR]))
            self.assertTrue(ok, summary)

    def test_starstar_still_refuses_when_the_tree_has_no_file(self):
        """Not weakened: directories alone are not deliverables."""
        with integration_workspace() as root:
            os.chdir(root)
            Path(_TREE).mkdir(parents=True, exist_ok=True)
            ok, summary = loop.assert_declared_deliverables(_make_wu([_STARSTAR]))
            self.assertFalse(ok)
            self.assertIn("glob", summary)

    def test_starstar_ignores_empty_files(self):
        with integration_workspace() as root:
            os.chdir(root)
            p = Path(_TREE)
            p.mkdir(parents=True, exist_ok=True)
            (p / "a.ts").write_text("")
            ok, _ = loop.assert_declared_deliverables(_make_wu([_STARSTAR]))
            self.assertFalse(ok)

    def test_single_star_is_unchanged(self):
        """A single `*` must keep matching exactly one level."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("src/one").mkdir(parents=True, exist_ok=True)
            Path("src/one/a.ts").write_text("x\n")
            self.assertTrue(loop.assert_declared_deliverables(_make_wu(["src/*/a.ts"]))[0])
            # `src/*.ts` must NOT reach into src/one/
            ok, _ = loop.assert_declared_deliverables(_make_wu(["src/*.ts"]))
            self.assertFalse(ok)


class TestBothGuardsAgreeOnStarStar(_RestoresCwd):
    """The unified contract's property — the asymmetry this bug created."""

    def test_diff_cross_check_already_accepted_it(self):
        """`fnmatch`'s `*` crosses `/`, so the diff half always passed. Asserted
        so the pair cannot drift apart again."""
        ok, summary = loop.assert_produces_in_diff(
            _make_wu([_STARSTAR]), [f"{_TREE}/a.ts"],
        )
        self.assertTrue(ok, summary)

    def test_accepted_by_presence_gate_implies_accepted_by_diff_check(self):
        with integration_workspace() as root:
            os.chdir(root)
            touched = _write_tree()
            wu = _make_wu([_STARSTAR])
            presence_ok, presence_summary = loop.assert_declared_deliverables(wu)
            self.assertTrue(presence_ok, presence_summary)
            diff_ok, diff_summary = loop.assert_produces_in_diff(wu, [touched])
            self.assertTrue(diff_ok, diff_summary)


class TestRefusalNoteAlsoResolvesStarStar(_RestoresCwd):
    """#1412's note globs the same patterns; it must not report a satisfied
    `**` entry as ABSENT."""

    def test_note_reports_a_matched_starstar_as_present(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write_tree()
            note = loop.format_deliverable_missing_note(
                _make_wu([_STARSTAR, "MISSING.md"]),
                "declared deliverable absent: MISSING.md",
                [],
                attempt=1,
            )
            self.assertRegex(note, r"typescript/\*\*.*(?i:present)")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
