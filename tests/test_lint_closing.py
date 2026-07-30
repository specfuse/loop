#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`specfuse-lint --closing` — FEAT-2026-0054/T02.

Fixtures cover: a fully-ready close (exit 0), each guard class from T01's
equivalence fixtures (exit 1, correct guard named), and a plan-next case
reproducing the #261 naming trap.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

from specfuse.loop import lint_closing as lc  # noqa: E402

PLAN_HEADER = (
    "---\nfeature_id: FEAT-9999\ntitle: Test\nbranch: feat/test\n"
    "roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n"
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                    capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / ".specfuse").mkdir(parents=True, exist_ok=True)
    (root / ".specfuse" / "LEARNINGS.md").write_text("# Learnings\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")


def _write_plan(feature_dir: Path, gates_yaml: str) -> None:
    (feature_dir / "PLAN.md").write_text(PLAN_HEADER + "```yaml\ngates:\n" + gates_yaml + "```\n")


def _write_wu(path: Path, wu_id: str, wu_type: str, status: str, extra_fm: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {wu_id}\ntype: {wu_type}\nstatus: {status}\nattempts: 0\n{extra_fm}---\n\n"
        f"# {wu_type} WU\n\n"
        "**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )


class TestFullyReadyClose(unittest.TestCase):

    def test_exit_zero_when_all_requirements_satisfied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
            fdir.mkdir(parents=True)
            _write_plan(fdir, (
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-CLOSE\n        file: WU-close.md\n"
                "        depends_on: []\n"
            ))
            _write_wu(fdir / "WU-close.md", "FEAT-9999/G1-CLOSE", "close", "pending",
                      extra_fm="verdict: met\n")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n"
            )
            (root / ".specfuse" / "LEARNINGS.md").write_text(
                "# Learnings\n\n- new lesson learned\n"
            )
            docs = root / "docs"
            docs.mkdir()
            (docs / "closing.md").write_text("doc\n")

            findings, notes = lc.lint_closing(fdir)
            self.assertEqual(findings, [])
            code = lc.main_closing(fdir)
            self.assertEqual(code, 0)


class TestGuardClasses(unittest.TestCase):
    """One case per T01 equivalence-fixture guard class."""

    def _close_feature(self, tmp: Path, extra_fm: str = "") -> Path:
        root = Path(tmp)
        _init_repo(root)
        fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
        fdir.mkdir(parents=True)
        _write_plan(fdir, (
            "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
            "      - id: FEAT-9999/G1-CLOSE\n        file: WU-close.md\n"
            "        depends_on: []\n"
        ))
        _write_wu(fdir / "WU-close.md", "FEAT-9999/G1-CLOSE", "close", "pending",
                  extra_fm=extra_fm)
        return fdir

    def test_reports_missing_retrospective_naming_postsquash_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._close_feature(tmp, extra_fm="verdict: met\n")
            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_retrospective_exists", joined)

    def test_reports_missing_verdict_naming_postsquash_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._close_feature(tmp)
            (fdir / "RETROSPECTIVE.md").write_text("# Retrospective\n\nBody.\n")
            (fdir.parents[2] / ".specfuse" / "LEARNINGS.md").write_text(
                "# Learnings\n\n- new lesson\n"
            )
            docs = fdir.parents[2] / "docs"
            docs.mkdir()
            (docs / "closing.md").write_text("doc\n")

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_verdict_well_formed", joined)
            self.assertIn("would fail assert_verdict_well_formed after squash", joined)

            code = lc.main_closing(fdir)
            self.assertEqual(code, 1)

    def test_reports_missing_cost_analysis_when_verdict_met(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._close_feature(tmp, extra_fm="verdict: met\n")
            (fdir / "RETROSPECTIVE.md").write_text("# Retrospective\n\nNo cost section.\n")
            (fdir.parents[2] / ".specfuse" / "LEARNINGS.md").write_text(
                "# Learnings\n\n- new lesson\n"
            )
            docs = fdir.parents[2] / "docs"
            docs.mkdir()
            (docs / "closing.md").write_text("doc\n")

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_cost_analysis_section_when_met", joined)

    def test_reports_missing_failure_class_breakdown_when_failures_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._close_feature(tmp, extra_fm="verdict: met\n")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n"
            )
            (fdir.parents[2] / ".specfuse" / "LEARNINGS.md").write_text(
                "# Learnings\n\n- new lesson\n"
            )
            docs = fdir.parents[2] / "docs"
            docs.mkdir()
            (docs / "closing.md").write_text("doc\n")
            (fdir / "events.jsonl").write_text(
                '{"event_type": "attempt_outcome", "correlation_id": '
                '"FEAT-9999/G1-T01", "payload": {"outcome": "failed", '
                '"failure_class": "verification", "failure_signature": "x"}}\n'
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn(
                "assert_failure_class_breakdown_when_failures_present", joined,
            )

    def test_reports_missing_gate_section_for_close_intermediate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
            fdir.mkdir(parents=True)
            _write_plan(fdir, (
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-CLOSE-INTERMEDIATE\n"
                "        file: WU-close-intermediate.md\n        depends_on: []\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: [FEAT-9999/G1-CLOSE-INTERMEDIATE]\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units: []\n"
            ))
            _write_wu(
                fdir / "WU-close-intermediate.md", "FEAT-9999/G1-CLOSE-INTERMEDIATE",
                "close-intermediate", "pending",
            )
            _write_wu(fdir / "WU-plan.md", "FEAT-9999/G1-PLAN", "plan-next", "draft")
            (fdir / "RETROSPECTIVE.md").write_text("# Retrospective\n\nNo gate section.\n")

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_retrospective_gate_section", joined)


class TestPlanNextGateReviewNamingTrap(unittest.TestCase):
    """Reproduces #261: review file named for the closed gate, not the armed one."""

    def test_names_assert_gate_review_exists_when_review_wrong_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
            fdir.mkdir(parents=True)
            _write_plan(fdir, (
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
                "      - id: FEAT-9999/T01\n        file: WU-T01.md\n"
                "        depends_on: []\n"
            ))
            _write_wu(fdir / "WU-plan.md", "FEAT-9999/G1-PLAN", "plan-next", "pending")
            # #261 trap: authored the review for the gate being CLOSED (01),
            # not the gate being ARMED (02).
            (fdir / "GATE-01-REVIEW.md").write_text("# Gate 1 review\n\nStuff.\n")

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_gate_review_exists", joined)
            self.assertIn("GATE-02-REVIEW.md", joined)

    def test_exit_zero_when_review_named_for_armed_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
            fdir.mkdir(parents=True)
            _write_plan(fdir, (
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
                "      - id: FEAT-9999/T01\n        file: WU-T01.md\n"
                "        depends_on: []\n"
            ))
            _write_wu(fdir / "WU-plan.md", "FEAT-9999/G1-PLAN", "plan-next", "pending")
            (fdir / "GATE-02-REVIEW.md").write_text("# Gate 2 review\n\nStuff.\n")

            findings, _ = lc.lint_closing(fdir)
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
