#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression tests for #74 — arm-gate edits wiped by the per-attempt reset.

arm-gate (and manual WU-body revisions at a gate boundary) writes UNCOMMITTED
working-tree changes: WU status flips (draft → pending), the completed gate's
flip (awaiting_review → passed), and edited acceptance criteria. If the loop
then runs and the first attempt fails, `git reset --hard head_before` discards
them — the gate silently reverts to drafts. The driver now refuses to start on
such uncommitted feature-folder edits (mirrors #71's pre-flight), so the human
checkpoint is durable once committed.
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


def _write_and_commit_feature(root: Path) -> Path:
    fdir = root / ".specfuse/features/FEAT-2026-9999-test"
    fdir.mkdir(parents=True)
    (fdir / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9999\ntitle: T\nbranch: feat/t\n"
        "roadmap_goal: t\nstatus: active\n---\n\n# Plan\n"
    )
    (fdir / "GATE-02.md").write_text("---\ngate: 2\nstatus: awaiting_review\n---\n\n# Gate 2\n")
    (fdir / "WU-05.md").write_text(
        "---\nid: FEAT-2026-9999/T05\ntype: implementation\n"
        "status: draft\nattempts: 0\n---\n\n# WU\n"
    )
    (fdir / "events.jsonl").write_text("{}\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "feat"], check=True)
    return fdir


class TestFeatureFolderTrackedModifications(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_arm_gate_wu_flip_is_detected(self):
        """A WU draft→pending flip (arm-gate) reads as a tracked modification."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_and_commit_feature(root)
            # Simulate arm-gate: flip WU status + gate status, uncommitted.
            (fdir / "WU-05.md").write_text(
                "---\nid: FEAT-2026-9999/T05\ntype: implementation\n"
                "status: pending\nattempts: 0\n---\n\n# WU (revised AC)\n"
            )
            os.chdir(root)
            rel = fdir.relative_to(root)
            mods = loop.feature_folder_tracked_modifications(rel)
            self.assertTrue(any("WU-05.md" in m for m in mods))
            with self.assertRaises(SystemExit):
                loop.require_feature_folder_unmodified(rel, {"branch": "feat/t"}, "FEAT-2026-9999")

    def test_clean_folder_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_and_commit_feature(root)
            os.chdir(root)
            rel = fdir.relative_to(root)
            self.assertEqual(loop.feature_folder_tracked_modifications(rel), [])
            loop.require_feature_folder_unmodified(rel, {"branch": "feat/t"}, "FEAT-2026-9999")  # must not raise

    def test_plan_md_flip_does_not_block(self):
        """pick-feature's PLAN.md status flip is expected, not an arm edit."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_and_commit_feature(root)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9999\ntitle: T\nbranch: feat/t\n"
                "roadmap_goal: t\nstatus: active\n---\n\n# Plan (touched)\n"
            )
            os.chdir(root)
            rel = fdir.relative_to(root)
            self.assertEqual(loop.feature_folder_tracked_modifications(rel), [])
            loop.require_feature_folder_unmodified(rel, {"branch": "feat/t"}, "FEAT-2026-9999")  # must not raise

    def test_events_jsonl_change_does_not_block(self):
        """events.jsonl is driver-managed (preserved across reset), not an arm edit."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            fdir = _write_and_commit_feature(root)
            (fdir / "events.jsonl").write_text('{"e": 1}\n')
            os.chdir(root)
            rel = fdir.relative_to(root)
            self.assertEqual(loop.feature_folder_tracked_modifications(rel), [])
            loop.require_feature_folder_unmodified(rel, {"branch": "feat/t"}, "FEAT-2026-9999")  # must not raise


class TestRunRefusesUncommittedArmEdits(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_run_exits_on_uncommitted_arm_edits(self):
        """End-to-end: run() hard-stops on uncommitted arm-gate edits."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_and_commit_feature_in_workspace(root)
            # Uncommitted arm flip after the folder was committed.
            (fdir / "WU-05.md").write_text(
                "---\nid: FEAT-2026-9999/T05\ntype: implementation\n"
                "status: pending\nattempts: 0\n---\n\n# WU revised\n"
            )
            with self.assertRaises(SystemExit):
                loop.run(None, dry_run=False)


def _write_and_commit_feature_in_workspace(root: Path) -> Path:
    """Same as _write_and_commit_feature but for the scaffolded integration repo."""
    fdir = root / ".specfuse/features/FEAT-2026-9999-test"
    fdir.mkdir(parents=True)
    (fdir / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9999\ntitle: T\nbranch: feat/t\n"
        "roadmap_goal: t\nstatus: active\n---\n\n# Plan\n"
    )
    (fdir / "GATE-02.md").write_text("---\ngate: 2\nstatus: awaiting_review\n---\n\n# Gate 2\n")
    (fdir / "WU-05.md").write_text(
        "---\nid: FEAT-2026-9999/T05\ntype: implementation\n"
        "status: draft\nattempts: 0\n---\n\n# WU\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "feat"], check=True)
    return fdir


if __name__ == "__main__":
    unittest.main()
