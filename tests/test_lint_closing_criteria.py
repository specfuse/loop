#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`specfuse lint --closing`'s GATE-NN-CRITERIA.md well-formedness check —
FEAT-2026-0056/T03.

`close-l` / `close-intermediate-f` fire only when the gate's criteria
artifact exists (`applies_when="criteria_artifact_present"`), which is what
keeps the requirement satisfiable across the existing corpus: no feature
folder has a criteria artifact yet, so it fires on none of them.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

from specfuse.loop import lint_closing as lc  # noqa: E402
from specfuse.loop.lint_closing import check_criteria_state_well_formed  # noqa: E402,F401


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
    header = (
        "---\nfeature_id: FEAT-9999\ntitle: Test\nbranch: feat/test\n"
        "roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n"
    )
    (feature_dir / "PLAN.md").write_text(header + "```yaml\ngates:\n" + gates_yaml + "```\n")


def _write_wu(path: Path, wu_id: str, wu_type: str, status: str, extra_fm: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {wu_id}\ntype: {wu_type}\nstatus: {status}\nattempts: 1\n{extra_fm}---\n\n"
        f"# {wu_type} WU\n\n"
        "**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )


def _ready_close(fdir: Path) -> None:
    """Fill in every OTHER close requirement so only close-l can fail."""
    (fdir / "RETROSPECTIVE.md").write_text(
        "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n"
    )
    (fdir.parents[2] / ".specfuse" / "LEARNINGS.md").write_text(
        "# Learnings\n\n- new lesson learned\n"
    )
    docs = fdir.parents[2] / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "closing.md").write_text("doc\n")


def _close_feature(tmp: Path, extra_fm: str = "verdict: met\n") -> Path:
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
    _ready_close(fdir)
    return fdir


class TestArtifactAbsentOrMissingFieldsAreFindings(unittest.TestCase):

    def test_missing_kind_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **state:** `pass`\n"
                "- **attempt:** `1`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("close-l", joined)
            self.assertIn("T01#1", joined)
            self.assertIn("missing kind", joined)

    def test_unrecognized_kind_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **kind:** `wide`\n"
                "- **state:** `pass`\n"
                "- **attempt:** `1`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("close-l", joined)
            self.assertIn("T01#1", joined)
            self.assertIn("kind", joined)

    def test_missing_state_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **kind:** `narrow`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("close-l", joined)
            self.assertIn("T01#1", joined)

    def test_unrecognized_state_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **kind:** `narrow`\n"
                "- **state:** `passed`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("close-l", joined)
            self.assertIn("T01#1", joined)


class TestBroadPassAttemptCarryForward(unittest.TestCase):

    def test_broad_pass_wrong_attempt_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Full suite is green.\n"
                "- **kind:** `broad`\n"
                "- **state:** `pass`\n"
                "- **attempt:** `2`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("close-l", joined)
            self.assertIn("T01#1", joined)

    def test_narrow_pass_wrong_attempt_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** A scoped test passes.\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                "- **attempt:** `2`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("close-l", joined)

    def test_broad_pass_current_attempt_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Full suite is green.\n"
                "- **kind:** `broad`\n"
                "- **state:** `pass`\n"
                "- **attempt:** `1`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("close-l", joined)


class TestArtifactAbsenceAndCorpusSatisfiability(unittest.TestCase):

    def test_absent_artifact_yields_zero_close_l_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            # No GATE-01-CRITERIA.md written at all.

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("close-l", joined)

    def test_well_formed_artifact_yields_zero_close_l_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** A scoped test passes.\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                "- **attempt:** `2`\n"
                "\n"
                "### T01#2\n\n"
                "- **criterion:** Full suite is green.\n"
                "- **kind:** `broad`\n"
                "- **state:** `pass`\n"
                "- **attempt:** `1`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            self.assertEqual(findings, [])

    def test_close_intermediate_reports_close_intermediate_f(self):
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
            (fdir / "RETROSPECTIVE.md").write_text("# Retrospective\n\n## Gate 1\n\nDone.\n")
            (fdir.parents[2] / ".specfuse" / "LEARNINGS.md").write_text(
                "# Learnings\n\n- new lesson learned\n"
            )
            docs = fdir.parents[2] / "docs"
            docs.mkdir()
            (docs / "closing.md").write_text("doc\n")
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **state:** `pass`\n"
                "- **attempt:** `1`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("close-intermediate-f", joined)
            self.assertIn("T01#1", joined)


class TestCorpusSweepStaysClean(unittest.TestCase):
    """Every existing feature folder in this repo lacks a criteria artifact,
    so close-l / close-intermediate-f must never fire against the real
    corpus — the arming precondition GATE-01.md's probe requires."""

    def test_real_feature_corpus_has_no_close_l_or_close_intermediate_f_findings(self):
        repo_root = Path(__file__).resolve().parents[1]
        features_dir = repo_root / ".specfuse" / "features"
        if not features_dir.is_dir():
            self.skipTest("no .specfuse/features directory in this checkout")
        for feature_dir in sorted(p for p in features_dir.iterdir() if p.is_dir()):
            findings, _ = lc.lint_closing(feature_dir)
            joined = "\n".join(findings)
            self.assertNotIn(
                "close-l", joined, f"unexpected close-l finding in {feature_dir}",
            )
            self.assertNotIn(
                "close-intermediate-f", joined,
                f"unexpected close-intermediate-f finding in {feature_dir}",
            )


if __name__ == "__main__":
    unittest.main()
