#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`specfuse lint --closing`'s pristine-entry skip — FEAT-2026-0056/T06.

A pristine entry — `state: unverified`, no `kind:`, no `oracle:`, byte for
byte what `_precreate_criteria_state_stub` seeds — must not be a finding.
Everything else `check_criteria_state_well_formed` already polices (T03)
must stay exactly as blocking. New file: T03's `tests/test_lint_closing_criteria.py`
is not touched by this unit.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

load_lint()

from specfuse.loop import lint_closing as lc  # noqa: E402


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


class TestPristineEntryIsNotAFinding(unittest.TestCase):

    def test_pristine_seeded_entry_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **state:** `unverified`\n"
                "\n"
                "### T01#2\n\n"
                "- **criterion:** Something else must hold.\n"
                "- **state:** `unverified`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("close-l", joined)
            self.assertEqual(findings, [])

    def test_annotated_pass_without_kind_is_still_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **state:** `pass`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            self.assertEqual(len(findings), 1)
            self.assertIn("T01#1", findings[0])

    def test_unverified_with_oracle_is_still_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _close_feature(tmp)
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n"
                "- **criterion:** Something must hold.\n"
                "- **oracle:** some test ran\n"
                "- **state:** `unverified`\n"
            )

            findings, _ = lc.lint_closing(fdir)
            self.assertEqual(len(findings), 1)
            self.assertIn("T01#1", findings[0])

    def test_broad_pass_wrong_attempt_still_a_finding(self):
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
            self.assertEqual(len(findings), 1)
            self.assertIn("T01#1", findings[0])


if __name__ == "__main__":
    unittest.main()
