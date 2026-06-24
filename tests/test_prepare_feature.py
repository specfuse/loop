#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""--prepare and the branch-aware guard hints.

`draft-feature` writes the feature folder but neither creates the feature's
branch nor commits, so the loop refuses to start (#71/#74). The refusal must
tell you to create the branch first (when you're on the default branch), and
`--prepare` must do branch-create + commit for you.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_FEAT_ID = "FEAT-2026-9999"
_BRANCH = "feat/FEAT-2026-9999-thing"


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.com"],
                   check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign", "false"],
                   check=True)
    (root / "README.md").write_text("# fixture\n")
    specfuse = root / ".specfuse"
    specfuse.mkdir()
    (specfuse / "verification.yml").write_text(
        "code:\n  - name: noop\n    command: \"true\"\n"
        "doc:\n  - name: noop\n    command: \"true\"\n"
        "plannext:\n  - name: noop\n    command: \"true\"\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)


def _write_uncommitted_feature(root: Path) -> Path:
    """A freshly-drafted, UNcommitted feature folder on the current branch."""
    fdir = root / ".specfuse" / "features" / f"{_FEAT_ID}-thing"
    fdir.mkdir(parents=True)
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {_FEAT_ID}\ntitle: T\nbranch: {_BRANCH}\n"
        f"roadmap_goal: t\nstatus: active\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        f"      - id: {_FEAT_ID}/T01\n        file: WU-01.md\n"
        f"        depends_on: []\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-01.md").write_text(
        f"---\nid: {_FEAT_ID}/T01\ntype: implementation\n"
        "status: pending\nattempts: 0\n---\n\n# WU\n"
    )
    return fdir


def _feat_fm() -> dict:
    return {"feature_id": _FEAT_ID, "branch": _BRANCH}


class TestPrepareFeature(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_prepare_creates_branch_and_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_uncommitted_feature(root)
            os.chdir(root)
            rel = fdir.relative_to(root)
            loop.prepare_feature(_feat_fm(), rel, _FEAT_ID)
            # on the feature branch now
            self.assertEqual(loop._current_branch(), _BRANCH)
            # folder is tracked + tree clean (committed)
            self.assertEqual(loop.untracked_feature_files(rel), [])
            self.assertEqual(loop.feature_folder_tracked_modifications(rel), [])
            tracked = subprocess.run(["git", "ls-files", str(rel)],
                                     capture_output=True, text=True).stdout
            self.assertIn("PLAN.md", tracked)

    def test_prepare_only_prepares_then_stops(self):
        """--prepare-only branches + commits but does NOT dispatch (rc=0)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            _write_uncommitted_feature(root)
            os.chdir(root)

            called = {"dispatch": False}

            def _no_dispatch(*a, **k):
                called["dispatch"] = True
                raise AssertionError("must not dispatch under --prepare-only")

            orig = loop.dispatch
            loop.dispatch = _no_dispatch
            try:
                rc = loop.run(None, dry_run=False, prepare_only=True)
            finally:
                loop.dispatch = orig

            self.assertEqual(rc, 0)
            self.assertFalse(called["dispatch"])
            self.assertEqual(loop._current_branch(), _BRANCH)
            # folder committed (tree clean)
            rel = Path(".specfuse/features") / f"{_FEAT_ID}-thing"
            self.assertEqual(loop.untracked_feature_files(rel), [])

    def test_committed_guard_message_suggests_prepare_and_branch(self):
        """On the default branch, the untracked-folder refusal names --prepare
        AND the `git checkout -b <branch>` step."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_uncommitted_feature(root)
            os.chdir(root)
            rel = fdir.relative_to(root)
            err = io.StringIO()
            with self.assertRaises(SystemExit) as cm, redirect_stderr(err):
                loop.require_feature_folder_committed(rel, _feat_fm(), _FEAT_ID)
            msg = str(cm.exception)
            self.assertIn("specfuse-loop --prepare", msg)
            self.assertIn(f"git checkout -b {_BRANCH}", msg)

    def test_guard_message_omits_checkout_when_on_feature_branch(self):
        """When already on the feature branch, no checkout line — just commit."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_uncommitted_feature(root)
            os.chdir(root)
            subprocess.run(["git", "checkout", "-q", "-b", _BRANCH], check=True)
            rel = fdir.relative_to(root)
            with self.assertRaises(SystemExit) as cm:
                loop.require_feature_folder_committed(rel, _feat_fm(), _FEAT_ID)
            msg = str(cm.exception)
            self.assertIn("specfuse-loop --prepare", msg)
            self.assertNotIn("git checkout -b", msg)


if __name__ == "__main__":
    unittest.main()
