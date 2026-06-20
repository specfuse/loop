#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression tests for #71 — untracked feature folder deleted by per-attempt reset.

A freshly drafted feature folder (all files untracked — draft-feature does not
commit) passed the tracked-only dirty check, got swept into the first WU's
squash, and was then DELETED by the next failed attempt's `git reset --hard`,
crashing the driver with an unhandled FileNotFoundError on the next frontmatter
write.

Two guards:
  1. Pre-flight `require_feature_folder_committed` hard-stops on an untracked
     feature folder before any dispatch.
  2. Crash-hardening: `write_frontmatter_field` raises a clear
     WorkUnitFileMissingError (not a bare FileNotFoundError) if its target file
     has vanished.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.com"],
                   check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign", "false"],
                   check=True)
    (root / "README.md").write_text("# fixture\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)


def _write_feature_folder(root: Path) -> Path:
    fdir = root / ".specfuse/features/FEAT-2026-9999-test"
    fdir.mkdir(parents=True)
    (fdir / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9999\ntitle: T\nbranch: feat/t\n"
        "roadmap_goal: t\nstatus: active\n---\n\n# Plan\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-01.md").write_text(
        "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
        "status: pending\nattempts: 0\n---\n\n# WU\n"
    )
    return fdir


class TestRequireFeatureFolderCommitted(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_untracked_folder_hard_stops(self):
        """An untracked feature folder must exit the driver, not slip through."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_feature_folder(root)  # NOT committed
            os.chdir(root)
            rel = fdir.relative_to(root)
            files = loop.untracked_feature_files(rel)
            self.assertTrue(files, "the freshly written folder must read as untracked")
            with self.assertRaises(SystemExit):
                loop.require_feature_folder_committed(rel)

    def test_committed_folder_passes(self):
        """A committed feature folder is a no-op (no exit)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_feature_folder(root)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "feat"],
                           check=True)
            os.chdir(root)
            rel = fdir.relative_to(root)
            self.assertEqual(loop.untracked_feature_files(rel), [])
            loop.require_feature_folder_committed(rel)  # must not raise

    def test_gitignored_work_dir_does_not_block(self):
        """Driver-managed gitignored paths (work/) must not count as untracked."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            (root / ".gitignore").write_text(".specfuse/**/work/\n")
            fdir = _write_feature_folder(root)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "feat"],
                           check=True)
            # Now create a gitignored work/ artifact under the committed folder.
            (fdir / "work" / "FEAT_T01").mkdir(parents=True)
            (fdir / "work" / "FEAT_T01" / "attempt-1.md").write_text("note\n")
            os.chdir(root)
            rel = fdir.relative_to(root)
            self.assertEqual(loop.untracked_feature_files(rel), [],
                             "gitignored work/ must not be flagged")
            loop.require_feature_folder_committed(rel)  # must not raise


class TestWriteFrontmatterFieldHardening(unittest.TestCase):

    def test_missing_file_raises_clear_error(self):
        """A vanished frontmatter file raises WorkUnitFileMissingError, not a
        bare FileNotFoundError (the #71 crash)."""
        with tempfile.TemporaryDirectory() as tmp:
            gone = Path(tmp) / "WU-gone.md"
            with self.assertRaises(loop.WorkUnitFileMissingError):
                loop.write_frontmatter_field(gone, "status", "done")

    def test_present_file_still_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            wu = Path(tmp) / "WU-01.md"
            wu.write_text("---\nstatus: pending\n---\n\n# WU\n")
            loop.write_frontmatter_field(wu, "status", "done")
            self.assertIn("status: done", wu.read_text())


class TestRunRefusesUntrackedFeatureFolder(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_run_exits_before_dispatch_on_untracked_folder(self):
        """End-to-end: run() hard-stops on an untracked feature folder."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_feature_folder(root)  # untracked under the scaffolded repo
            with self.assertRaises(SystemExit):
                loop.run(None, dry_run=False)


if __name__ == "__main__":
    unittest.main()
