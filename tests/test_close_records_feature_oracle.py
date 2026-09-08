#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The close records the gate's `feature_oracle` verdict — FEAT-2026-0101/T02.

`specfuse lint --closing` fails a close whose gate declares a `feature_oracle`
but whose `## Measurements` section records no verdict for it, and is inert
for a gate that declares no oracle at all (T03 owns whether an absent
declaration is itself a finding).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

load_lint()

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


def _write_wu(path: Path, wu_id: str, status: str, extra_fm: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {wu_id}\ntype: close\nstatus: {status}\nattempts: 0\n{extra_fm}---\n\n"
        "# close WU\n\n"
        "**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )


def _write_gate(path: Path, oracle: "str | None") -> None:
    body = "---\ngate: 1\nstatus: open\n"
    if oracle is not None:
        body += f'feature_oracle: "{oracle}"\n'
    body += "---\n\n# Gate 1\n"
    path.write_text(body)


def _make_feature(root: Path, oracle: "str | None") -> Path:
    fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
    fdir.mkdir(parents=True)
    _write_plan(fdir, (
        "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        "      - id: FEAT-9999/G1-CLOSE\n        file: WU-close.md\n"
        "        depends_on: []\n"
    ))
    _write_gate(fdir / "GATE-01.md", oracle)
    _write_wu(fdir / "WU-close.md", "FEAT-9999/G1-CLOSE", "pending", extra_fm="verdict: met\n")
    (root / ".specfuse" / "LEARNINGS.md").write_text(
        "# Learnings\n\n- new lesson learned\n"
    )
    return fdir


class TestClosingLintFailsWhenOracleVerdictAbsent(unittest.TestCase):

    def test_closing_lint_fails_when_oracle_verdict_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = _make_feature(root, "python3 -m unittest tests.test_oracle -q")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n\n"
                "## Measurements\n\nSuite green.\n"
            )
            findings, notes = lc.lint_closing(fdir)
            self.assertTrue(
                any("feature_oracle" in f for f in findings),
                f"expected a feature_oracle finding, got: {findings}",
            )


class TestClosingLintPassesWhenVerdictRecorded(unittest.TestCase):

    def test_closing_lint_passes_when_verdict_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = _make_feature(root, "python3 -m unittest tests.test_oracle -q")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n\n"
                "## Measurements\n\nSuite green.\n\n"
                "### feature_oracle: PASS\n"
            )
            findings, notes = lc.lint_closing(fdir)
            self.assertEqual(
                [f for f in findings if "feature_oracle" in f], [],
                f"expected no feature_oracle finding, got: {findings}",
            )


class TestGateWithoutOracleImposesNoRequirement(unittest.TestCase):

    def test_gate_without_oracle_imposes_no_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            fdir = _make_feature(root, None)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n\n"
                "## Measurements\n\nSuite green.\n"
            )
            findings, notes = lc.lint_closing(fdir)
            self.assertEqual(
                [f for f in findings if "feature_oracle" in f], [],
                f"gate declares no feature_oracle, expected no finding, got: {findings}",
            )


if __name__ == "__main__":
    unittest.main()
