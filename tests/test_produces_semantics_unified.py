#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unified declared-deliverables / produces-in-diff contract (FEAT-2026-0055/T03).

Before this WU, `assert_declared_deliverables` (presence gate, FEAT-2026-0022/T02)
accepted only literal paths, while `assert_produces_in_diff` (#198) accepted
literal paths and fnmatch globs. A directory passed the presence gate (it
"exists") but always failed the diff cross-check, and a glob passed the diff
cross-check but never satisfied the literal-only presence gate — a WU author
had no single declaration form that satisfied both.

This module asserts the unified contract: literal paths and globs both
satisfy both gates; directories satisfy neither, with an explicit refusal
naming why (instead of the old silent presence-pass/diff-fail split); and the
property "accepted by declared-deliverables implies accepted by
produces-in-diff for the same form" holds across literal and glob fixtures.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


class _RestoresCwd(unittest.TestCase):
    """integration_workspace() removes its temp dir on exit; restore cwd so a
    later test's os.getcwd() does not hit a deleted directory."""

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)


def _make_wu(produces: list, wu_id: str = "FEAT-2026-0055/T03",
             wu_file: str = "WU-T03.md") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path(wu_file),
        depends_on=[],
        type="implementation",
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title=wu_id,
        body="",
        produces=produces,
    )


class TestUnifiedSemantics(_RestoresCwd):
    """Behavior table: literal / glob / directory, before vs after this WU."""

    def test_literal_present_nonempty_still_passes(self):
        """Literal path, unchanged: exists + non-empty -> pass."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("X.md").write_text("content\n")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["X.md"]))
            self.assertTrue(ok, summary)

    def test_literal_absent_still_fails(self):
        with integration_workspace() as root:
            os.chdir(root)
            ok, summary = loop.assert_declared_deliverables(_make_wu(["GONE.md"]))
            self.assertFalse(ok)
            self.assertIn("absent", summary)

    def test_glob_satisfies_declared_deliverables_when_match_exists(self):
        """AC: a glob with >=1 existing non-empty match now satisfies the
        presence gate too — fails on HEAD (literal-only presence gate)."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            Path("src/rule.py").write_text("SEVERITY = 'ERROR'\n")
            ok, summary = loop.assert_declared_deliverables(
                _make_wu(["src/*.py"]))
            self.assertTrue(ok, summary)

    def test_glob_with_no_existing_match_fails(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            ok, summary = loop.assert_declared_deliverables(
                _make_wu(["src/*.py"]))
            self.assertFalse(ok)
            self.assertIn("src/*.py", summary)

    def test_glob_matching_only_empty_files_fails(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            Path("src/rule.py").write_text("")
            ok, summary = loop.assert_declared_deliverables(
                _make_wu(["src/*.py"]))
            self.assertFalse(ok)
            self.assertIn("src/*.py", summary)

    def test_directory_refused_with_explicit_message(self):
        """AC: a directory path is refused with a message naming the unified
        contract, not a silent presence-pass."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            Path("src/rule.py").write_text("content\n")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src"]))
            self.assertFalse(ok)
            self.assertIn("directory", summary)
            self.assertIn("src", summary)

    def test_directory_trailing_slash_refused(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            ok, summary = loop.assert_declared_deliverables(_make_wu(["src/"]))
            self.assertFalse(ok)
            self.assertIn("directory", summary)


class TestProducesInDiffUnchanged(unittest.TestCase):
    """assert_produces_in_diff's own behavior must not shift."""

    def test_literal_match_passes(self):
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src/rule.py"]), ["src/rule.py"])
        self.assertTrue(ok, summary)

    def test_glob_match_passes(self):
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src/*.py"]), ["src/rule.py"])
        self.assertTrue(ok, summary)

    def test_directory_entry_never_matches_diff(self):
        """A directory entry was never a valid diff-match form either — the
        diff lists files, never a bare directory path."""
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src"]), ["src/rule.py"])
        self.assertFalse(ok)
        self.assertIn("src", summary)


class TestAcceptedImpliesAcceptedByDiff(_RestoresCwd):
    """Property: a produces: form accepted by the (unified) declared-
    deliverables presence gate is accepted by produces-in-diff matching for
    the same squash diff, across literal and glob fixtures."""

    def _assert_implication(self, produces, touched):
        wu = _make_wu(produces)
        presence_ok, _ = loop.assert_declared_deliverables(wu)
        if presence_ok:
            diff_ok, diff_summary = loop.assert_produces_in_diff(wu, touched)
            self.assertTrue(
                diff_ok,
                f"{produces} passed declared-deliverables but failed "
                f"produces-in-diff against touched={touched}: {diff_summary}",
            )

    def test_literal_fixture(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("X.md").write_text("content\n")
            self._assert_implication(["X.md"], ["X.md"])

    def test_glob_fixture(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            Path("src/rule.py").write_text("SEVERITY = 'ERROR'\n")
            self._assert_implication(["src/*.py"], ["src/rule.py"])

    def test_glob_fixture_multiple_matches(self):
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir()
            Path("src/rule.py").write_text("a\n")
            Path("src/flags.py").write_text("b\n")
            self._assert_implication(["src/*.py"], ["src/rule.py", "src/flags.py"])


if __name__ == "__main__":
    unittest.main()
