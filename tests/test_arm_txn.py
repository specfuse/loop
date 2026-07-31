#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for arm_txn.py (FEAT-2026-0053/T05).

Each fixture is a self-contained temp feature directory — PLAN.md,
GATE-NN.md, and WU files — built directly rather than through the driver.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.arm_txn import (
    apply_arm_transaction,
    arm_tag_name,
    plan_arm_transaction,
)

FEATURE_ID = "FEAT-2026-8802"


def _write(path: Path, text: str) -> None:
    path.write_text(text)


def _plan_md(feature: Path, gate2_wus: list) -> None:
    fm = (
        f"feature_id: {FEATURE_ID}\n"
        "title: Arm transaction test feature\n"
        "branch: feat/arm-transaction-test\n"
        "roadmap_goal: test\n"
        "status: active\n"
    )
    gate2_block = (
        "    work_units:\n" + "".join(
            f"      - id: {wid}\n        file: {wfile}\n        depends_on: []\n"
            for wid, wfile in gate2_wus
        )
        if gate2_wus else "    work_units: []\n"
    )
    graph = (
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {FEATURE_ID}/T01\n"
        "        file: WU-01.md\n"
        "        depends_on: []\n"
        "  - gate: 2\n"
        "    file: GATE-02.md\n"
        f"{gate2_block}"
        "```\n"
    )
    _write(feature / "PLAN.md", f"---\n{fm}---\n\n# Plan\n\n{graph}")


def _wu(feature: Path, filename: str, status: str) -> None:
    _write(
        feature / filename,
        f"---\nid: {FEATURE_ID}/x\nstatus: {status}\nattempts: 0\n---\n\n"
        f"# Work unit\n\nbody text stays put.\n",
    )


def _gate(feature: Path, gate_num: int, status: str) -> None:
    _write(
        feature / f"GATE-{gate_num:02d}.md",
        f"---\ngate: {gate_num}\nstatus: {status}\ncost_budget_usd: 10.0\n---\n\n"
        f"# Gate {gate_num}\n\nbody text stays put.\n",
    )


def _feature(tmp: str, gate2_wus: list, gate1_status="awaiting_review", wu_statuses=None) -> Path:
    feature = Path(tmp) / "feature"
    feature.mkdir()
    _plan_md(feature, gate2_wus)
    _gate(feature, 1, gate1_status)
    _gate(feature, 2, "open")
    statuses = wu_statuses if wu_statuses is not None else ["draft"] * len(gate2_wus)
    for (_, fname), status in zip(gate2_wus, statuses, strict=True):
        _wu(feature, fname, status)
    return feature


class TestPlanArmTransaction(unittest.TestCase):
    def test_plan_lists_draft_wus_and_gate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(
                tmp,
                [(f"{FEATURE_ID}/T02", "WU-02.md"), (f"{FEATURE_ID}/T03", "WU-03.md")],
            )
            txn = plan_arm_transaction(feature, just_closed_gate=1)

            self.assertEqual(
                {p.name for p in txn.draft_wu_paths}, {"WU-02.md", "WU-03.md"}
            )
            self.assertEqual(txn.gate_file_path.name, "GATE-01.md")
            self.assertEqual(
                set(txn.paths),
                {feature / "WU-02.md", feature / "WU-03.md", feature / "GATE-01.md"},
            )
            self.assertEqual(len(txn.paths), len(set(txn.paths)))


class TestArmTagName(unittest.TestCase):
    def test_literal_tag_name(self):
        self.assertEqual(
            arm_tag_name("FEAT-2026-0053", 1),
            "pre-arm/FEAT-2026-0053/gate-1",
        )


class TestApplyArmTransaction(unittest.TestCase):
    def test_flips_draft_wus_and_gate_status_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            txn = plan_arm_transaction(feature, just_closed_gate=1)

            applied = apply_arm_transaction(txn)

            self.assertEqual(set(applied), {feature / "WU-02.md", feature / "GATE-01.md"})
            wu_text = (feature / "WU-02.md").read_text()
            self.assertIn("status: pending", wu_text)
            self.assertIn("body text stays put.", wu_text)
            gate_text = (feature / "GATE-01.md").read_text()
            self.assertIn("status: passed", gate_text)
            self.assertIn("cost_budget_usd: 10.0", gate_text)
            self.assertIn("body text stays put.", gate_text)

    def test_no_other_frontmatter_field_or_body_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            wu_before = (feature / "WU-02.md").read_text()
            txn = plan_arm_transaction(feature, just_closed_gate=1)
            apply_arm_transaction(txn)
            wu_after = (feature / "WU-02.md").read_text()

            before_lines = [ln for ln in wu_before.splitlines() if not ln.startswith("status:")]
            after_lines = [ln for ln in wu_after.splitlines() if not ln.startswith("status:")]
            self.assertEqual(before_lines, after_lines)

    def test_idempotent_second_call_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            txn = plan_arm_transaction(feature, just_closed_gate=1)
            apply_arm_transaction(txn)

            wu_snapshot = (feature / "WU-02.md").read_text()
            gate_snapshot = (feature / "GATE-01.md").read_text()

            second_applied = apply_arm_transaction(txn)

            self.assertEqual(second_applied, [])
            self.assertEqual((feature / "WU-02.md").read_text(), wu_snapshot)
            self.assertEqual((feature / "GATE-01.md").read_text(), gate_snapshot)

    def test_replanning_after_apply_reports_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            txn1 = plan_arm_transaction(feature, just_closed_gate=1)
            apply_arm_transaction(txn1)

            txn2 = plan_arm_transaction(feature, just_closed_gate=1)
            applied2 = apply_arm_transaction(txn2)

            self.assertEqual(txn2.paths, ())
            self.assertEqual(applied2, [])


class TestEmptyArm(unittest.TestCase):
    def test_no_draft_wus_in_next_gate_reports_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")], wu_statuses=["pending"])
            txn = plan_arm_transaction(feature, just_closed_gate=1)

            self.assertEqual(txn.draft_wu_paths, ())
            applied = apply_arm_transaction(txn)
            self.assertEqual(applied, [])

    def test_no_such_gate_reports_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [])
            txn = plan_arm_transaction(feature, just_closed_gate=2)

            self.assertEqual(txn.draft_wu_paths, ())
            self.assertEqual(txn.paths, ())
            applied = apply_arm_transaction(txn)
            self.assertEqual(applied, [])

    def test_gate_not_awaiting_review_excludes_gate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(
                tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")], gate1_status="passed"
            )
            txn = plan_arm_transaction(feature, just_closed_gate=1)

            self.assertIsNone(txn.gate_file_path)
            self.assertEqual(set(txn.paths), {feature / "WU-02.md"})


class TestNoGitOperations(unittest.TestCase):
    def test_module_source_has_no_git_calls(self):
        import re

        src = Path("specfuse/loop/arm_txn.py").read_text()
        self.assertIsNone(re.search(r"subprocess|\bgit\(", src))


if __name__ == "__main__":
    unittest.main()
