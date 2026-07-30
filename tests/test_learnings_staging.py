#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""LEARNINGS staging under autonomy_default=auto — FEAT-2026-0053/T09.

Covers `loop.assert_learnings_staged_under_auto` (registered in
`POST_PASS_INVARIANTS_BY_TYPE` for both `close` and `close-intermediate`):

  TestLearningsStaging:
    (a) test_auto_closing_wu_writing_learnings_does_not_pass
    (b) test_review_mode_identical_diff_passes
    (c) test_supervised_mode_identical_diff_passes
    (d) test_auto_closing_wu_writing_pending_file_passes
    (e) test_close_intermediate_type_also_gated

  TestVerifyPostPassInvariantsDispatch:
    registration-surface checks on POST_PASS_INVARIANTS_BY_TYPE.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@test.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign", "false"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "gc.auto", "0"], check=True)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _write_feature_scaffold(
    root: Path,
    feature_id: str = "FEAT-2026-7777",
    autonomy_default: str = "auto",
    wu_type: str = "close",
) -> Path:
    """Minimal PLAN.md + single-gate close WU, with autonomy_default set."""
    specfuse = root / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    feature_dir = specfuse / "features" / f"{feature_id}-test"
    feature_dir.mkdir(parents=True)

    wu_id = f"{feature_id}/G1-CLOSE" if wu_type == "close" else f"{feature_id}/G1-CLOSE-INTERMEDIATE"
    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nbranch: feat/test\n"
        f"roadmap_goal: test\nstatus: active\n"
        f"autonomy_default: {autonomy_default}\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n      - id: {wu_id}\n        file: WU-close.md\n"
        f"        depends_on: []\n```\n"
    )
    (feature_dir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: awaiting_review\n---\n\n# Gate 1\n"
    )
    (feature_dir / "WU-close.md").write_text(
        f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: opus\n"
        f"status: done\nattempts: 1\nverdict: met\n---\n\n# Close{_WU_BODY}"
    )
    return feature_dir


def _make_wu(feature_dir: Path, feature_id: str = "FEAT-2026-7777", wu_type: str = "close") -> "loop.WorkUnit":
    wu_id = f"{feature_id}/G1-CLOSE" if wu_type == "close" else f"{feature_id}/G1-CLOSE-INTERMEDIATE"
    return loop.WorkUnit(
        wu_id=wu_id,
        file=feature_dir / "WU-close.md",
        depends_on=[],
        type=wu_type,
        model="opus",
        status="done",
        attempts=1,
        title="Close",
        body=_WU_BODY,
        verdict="met",
    )


class TestLearningsStaging(unittest.TestCase):

    def test_auto_closing_wu_writing_learnings_does_not_pass(self):
        """Under auto, a close WU whose diff touches .specfuse/LEARNINGS.md
        is refused, and the reason names the staging file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            learnings = root / ".specfuse" / "LEARNINGS.md"
            learnings.write_text("# Learnings\n\n- a new rule landed straight.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "add learnings"], check=True)

            wu = _make_wu(feature_dir)
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_learnings_staged_under_auto(
                    wu, feature_dir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertFalse(ok)
            self.assertIn("learnings_not_staged", reason)
            self.assertIn("LEARNINGS-pending.md", reason)

    def test_review_mode_identical_diff_passes(self):
        """Identical diff, autonomy_default=review -> invariant is inert."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="review")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            learnings = root / ".specfuse" / "LEARNINGS.md"
            learnings.write_text("# Learnings\n\n- a new rule landed straight.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "add learnings"], check=True)

            wu = _make_wu(feature_dir)
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_learnings_staged_under_auto(
                    wu, feature_dir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_supervised_mode_identical_diff_passes(self):
        """Identical diff, autonomy_default=supervised -> invariant is inert."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="supervised")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            learnings = root / ".specfuse" / "LEARNINGS.md"
            learnings.write_text("# Learnings\n\n- a new rule landed straight.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "add learnings"], check=True)

            wu = _make_wu(feature_dir)
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_learnings_staged_under_auto(
                    wu, feature_dir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_auto_closing_wu_writing_pending_file_passes(self):
        """Under auto, a diff that touches only LEARNINGS-pending.md (and not
        .specfuse/LEARNINGS.md) passes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            pending = feature_dir / "LEARNINGS-pending.md"
            pending.write_text("# LEARNINGS-pending\n\n- staged lesson.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "stage lesson"], check=True)

            wu = _make_wu(feature_dir)
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_learnings_staged_under_auto(
                    wu, feature_dir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_close_intermediate_type_also_gated(self):
        """Same refusal fires for a close-intermediate WU under auto."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(
                root, autonomy_default="auto", wu_type="close-intermediate",
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            learnings = root / ".specfuse" / "LEARNINGS.md"
            learnings.write_text("# Learnings\n\n- a new rule landed straight.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "add learnings"], check=True)

            wu = _make_wu(feature_dir, wu_type="close-intermediate")
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_learnings_staged_under_auto(
                    wu, feature_dir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertFalse(ok)
            self.assertIn("learnings_not_staged", reason)


class TestVerifyPostPassInvariantsDispatch(unittest.TestCase):

    def test_registered_for_close(self):
        self.assertIn(
            loop.assert_learnings_staged_under_auto,
            loop.POST_PASS_INVARIANTS_BY_TYPE["close"],
        )

    def test_registered_for_close_intermediate(self):
        self.assertIn("close-intermediate", loop.POST_PASS_INVARIANTS_BY_TYPE)
        self.assertIn(
            loop.assert_learnings_staged_under_auto,
            loop.POST_PASS_INVARIANTS_BY_TYPE["close-intermediate"],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
