#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""close-b accepts staged lessons under `autonomy_default: auto` — issue #1419.

`close-b` (`assert_learnings_appended_or_noop`) was satisfied by exactly one
of two things: added lines in `.specfuse/LEARNINGS.md`, or the literal
`nothing generalizes` in `RETROSPECTIVE.md`. `close-i`
(`assert_learnings_staged_under_auto`) *forbids* the first under
`autonomy_default: auto`, requiring the lessons stage to the feature-local
`LEARNINGS-pending.md` instead. So an `auto` close whose lessons genuinely
generalized had to write a sentence asserting the opposite to pass.

Covers both enforcement surfaces — the post-squash driver guard in `loop.py`
and its pre-squash mirror `_check_learnings_appended_or_noop` in
`lint_closing.py` — plus the registry description both read from.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests.test_closing_deliverable_guard import _make_wu

loop = load_loop()

from specfuse.loop import closing_requirements as creq  # noqa: E402
from specfuse.loop import lint_closing as lc  # noqa: E402
from specfuse.loop.closing_requirements import CLOSING_REQUIREMENTS  # noqa: E402

_RETRO_NO_PHRASE = (
    "# Retrospective\n\n## Cost analysis\n\nCheap.\n\n"
    "## Lessons\n\nTwo entries staged for promotion at PR review.\n"
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


def _commit_all(root: Path, msg: str) -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", msg], check=True)


def _write_feature_scaffold(root: Path, autonomy_default: str) -> Path:
    """Minimal PLAN.md the guard can read `autonomy_default` from."""
    feature_dir = root / ".specfuse" / "features" / "FEAT-2026-7777-test"
    feature_dir.mkdir(parents=True)
    (feature_dir / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-7777\ntitle: Test\nbranch: feat/test\n"
        "roadmap_goal: test\nstatus: active\n"
        f"autonomy_default: {autonomy_default}\n---\n\n# Plan\n\n```yaml\n"
        "gates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units:\n      - id: FEAT-2026-7777/G1-CLOSE\n"
        "        file: WU-close.md\n        depends_on: []\n```\n"
    )
    (feature_dir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: awaiting_review\n---\n\n# Gate 1\n"
    )
    (feature_dir / "RETROSPECTIVE.md").write_text(_RETRO_NO_PHRASE)
    return feature_dir


def _run_driver_guard(root: Path, feature_dir: Path, head_before: str, wu_type: str = "close"):
    wu = _make_wu(
        file=feature_dir / "WU-close.md",
        wu_id="FEAT-2026-7777/G1-CLOSE",
        wu_type=wu_type,
    )
    old_cwd = os.getcwd()
    try:
        os.chdir(root)
        return loop.assert_learnings_appended_or_noop(wu, feature_dir, root, head_before)
    finally:
        os.chdir(old_cwd)


def _lint_ctx(feature_dir: Path, root: Path, autonomy_default: str, wu_type: str = "close"):
    return lc.ClosingContext(
        feature_dir=feature_dir,
        repo_root=root,
        plan_fm={"autonomy_default": autonomy_default},
        gates=[],
        wu_id="FEAT-2026-7777/G1-CLOSE",
        wu_type=wu_type,
        gate_num=1,
        wfm={"verdict": "met"},
        wbody="",
    )


def _requirement(wu_type: str, req_id: str) -> creq.Requirement:
    return next(r for r in CLOSING_REQUIREMENTS[wu_type] if r.id == req_id)


# --------------------------------------------------------------------------- #
# Post-squash driver guard (loop.assert_learnings_appended_or_noop)           #
# --------------------------------------------------------------------------- #


class TestDriverGuardAcceptsStagedLessons(unittest.TestCase):

    def test_auto_pending_additions_satisfy_close_b(self):
        """The bug: under `auto`, a close that staged real lessons in
        LEARNINGS-pending.md and did NOT claim 'nothing generalizes' passes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            _commit_all(root, "init")
            head_before = _git(root, "rev-parse", "HEAD")

            (feature_dir / creq.LEARNINGS_PENDING_FILENAME).write_text(
                "# LEARNINGS-pending\n\n- A durable rule worth promoting.\n"
            )
            _commit_all(root, "stage lessons")

            ok, reason = _run_driver_guard(root, feature_dir, head_before)
            self.assertTrue(ok, msg=f"unexpected refusal: {reason!r}")
            self.assertEqual(reason, "")

    def test_auto_pending_additions_satisfy_close_intermediate_b(self):
        """Same acceptance for a close-intermediate WU."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            _commit_all(root, "init")
            head_before = _git(root, "rev-parse", "HEAD")

            (feature_dir / creq.LEARNINGS_PENDING_FILENAME).write_text(
                "# LEARNINGS-pending\n\n- A durable rule worth promoting.\n"
            )
            _commit_all(root, "stage lessons")

            ok, reason = _run_driver_guard(
                root, feature_dir, head_before, wu_type="close-intermediate",
            )
            self.assertTrue(ok, msg=f"unexpected refusal: {reason!r}")

    def test_review_mode_pending_additions_do_not_satisfy_close_b(self):
        """Guard not weakened: outside `auto`, close-i is inert and
        .specfuse/LEARNINGS.md is the sanctioned home, so staging alone
        must still refuse."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="review")
            _commit_all(root, "init")
            head_before = _git(root, "rev-parse", "HEAD")

            (feature_dir / creq.LEARNINGS_PENDING_FILENAME).write_text(
                "# LEARNINGS-pending\n\n- A durable rule worth promoting.\n"
            )
            _commit_all(root, "stage lessons")

            ok, reason = _run_driver_guard(root, feature_dir, head_before)
            self.assertFalse(ok)
            self.assertIn("assert_learnings_appended_or_noop", reason)

    def test_auto_with_no_lessons_anywhere_still_refuses(self):
        """Under `auto`, an empty staging file and no no-op phrase still fails
        — the new route requires added content, not a touched path."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            _commit_all(root, "init")
            head_before = _git(root, "rev-parse", "HEAD")

            (feature_dir / "notes.md").write_text("unrelated\n")
            _commit_all(root, "unrelated change")

            ok, reason = _run_driver_guard(root, feature_dir, head_before)
            self.assertFalse(ok)
            self.assertIn("assert_learnings_appended_or_noop", reason)

    def test_auto_no_op_phrase_still_accepted(self):
        """The genuine no-op route survives for a session that truly found
        nothing generalizable."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            (feature_dir / creq.RETROSPECTIVE_FILENAME).write_text(
                "# Retrospective\n\nNothing generalizes from this gate.\n"
            )
            _commit_all(root, "init")
            head_before = _git(root, "rev-parse", "HEAD")

            ok, reason = _run_driver_guard(root, feature_dir, head_before)
            self.assertTrue(ok, msg=f"unexpected refusal: {reason!r}")

    def test_missing_plan_file_does_not_raise(self):
        """The guard reads PLAN.md defensively — a feature dir without one
        (the pre-existing unit-test shape) must fall through, not explode."""
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            (feature_dir / creq.RETROSPECTIVE_FILENAME).write_text(
                "# Retro\n\nNothing generalizes here.\n"
            )
            wu = _make_wu(wu_type="close")
            ok, reason = loop.assert_learnings_appended_or_noop(
                wu, feature_dir, feature_dir, "0" * 40,
            )
            self.assertTrue(ok, msg=f"unexpected refusal: {reason!r}")


# --------------------------------------------------------------------------- #
# Pre-squash lint mirror (lint_closing._check_learnings_appended_or_noop)     #
# --------------------------------------------------------------------------- #


class TestLintMirrorAcceptsStagedLessons(unittest.TestCase):

    def test_auto_pending_additions_satisfy_lint(self):
        """The mirror must agree with the driver, or `specfuse lint --closing`
        keeps telling an auto session to write the false phrase."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            _commit_all(root, "init")

            (feature_dir / creq.LEARNINGS_PENDING_FILENAME).write_text(
                "# LEARNINGS-pending\n\n- A durable rule worth promoting.\n"
            )

            req = _requirement("close", "close-b")
            ctx = _lint_ctx(feature_dir, root, autonomy_default="auto")
            ok, reason = lc._check_learnings_appended_or_noop(req, ctx)
            self.assertTrue(ok, msg=f"unexpected finding: {reason!r}")

    def test_review_mode_pending_additions_do_not_satisfy_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="review")
            _commit_all(root, "init")

            (feature_dir / creq.LEARNINGS_PENDING_FILENAME).write_text(
                "# LEARNINGS-pending\n\n- A durable rule worth promoting.\n"
            )

            req = _requirement("close", "close-b")
            ctx = _lint_ctx(feature_dir, root, autonomy_default="review")
            ok, reason = lc._check_learnings_appended_or_noop(req, ctx)
            self.assertFalse(ok)
            self.assertIn(creq.NOTHING_GENERALIZES_PHRASE, reason)

    def test_auto_with_no_lessons_anywhere_still_finds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            feature_dir = _write_feature_scaffold(root, autonomy_default="auto")
            _commit_all(root, "init")

            req = _requirement("close", "close-b")
            ctx = _lint_ctx(feature_dir, root, autonomy_default="auto")
            ok, reason = lc._check_learnings_appended_or_noop(req, ctx)
            self.assertFalse(ok)


# --------------------------------------------------------------------------- #
# Registry description — what lint prints when the requirement fails          #
# --------------------------------------------------------------------------- #


class TestRegistryDescribesStagingRoute(unittest.TestCase):

    def test_close_b_description_names_the_staging_file(self):
        req = _requirement("close", "close-b")
        self.assertIn(creq.LEARNINGS_PENDING_FILENAME, req.description)

    def test_close_intermediate_b_description_names_the_staging_file(self):
        req = _requirement("close-intermediate", "close-intermediate-b")
        self.assertIn(creq.LEARNINGS_PENDING_FILENAME, req.description)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
