#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for FEATURE-REVIEW.md accumulation on auto-arm (FEAT-2026-0053/T08)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.arm_txn import (
    FEATURE_REVIEW_FILENAME,
    append_feature_review_entry,
    apply_arm_transaction,
    plan_arm_transaction,
)

FEATURE_ID = "FEAT-2026-8901"

ARM_PAYLOAD = {
    "gate": 1,
    "would_arm": True,
    "predicate_version": "v1",
    "classes": {
        "budget_projection": {"status": "clean", "reason": "within cap"},
        "open_questions_human_only": {"status": "clean", "reason": "empty"},
    },
}

TIMESTAMP = "2026-07-30T00:00:00+00:00"


def _write(path: Path, text: str) -> None:
    path.write_text(text)


def _plan_md(feature: Path, gate2_wus: list) -> None:
    fm = (
        f"feature_id: {FEATURE_ID}\n"
        "title: Feature review accumulation test\n"
        "branch: feat/feature-review-test\n"
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


def _gate_review(feature: Path, next_gate: int, open_questions: list, doubt_body: str) -> None:
    oq_yaml = (
        "\n".join(f'  - "{q}"' for q in open_questions) if open_questions else ""
    )
    fm = f"gate: {next_gate}\nopen_questions:\n{oq_yaml}\n" if open_questions else (
        f"gate: {next_gate}\nopen_questions: []\n"
    )
    doubt_block = f"## Doubt\n\n{doubt_body}\n" if doubt_body is not None else ""
    _write(
        feature / f"GATE-{next_gate:02d}-REVIEW.md",
        f"---\n{fm}---\n\n# Gate {next_gate} review\n\n{doubt_block}",
    )


def _feature(tmp: str, gate2_wus: list, gate1_status="awaiting_review") -> Path:
    feature = Path(tmp) / "feature"
    feature.mkdir()
    _plan_md(feature, gate2_wus)
    _gate(feature, 1, gate1_status)
    _gate(feature, 2, "open")
    for _, fname in gate2_wus:
        _wu(feature, fname, "draft")
    return feature


class TestFeatureReviewAccumulation(unittest.TestCase):
    def test_auto_arm_appends_gate_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            _gate_review(
                feature, 2,
                open_questions=["is the cap right?"],
                doubt_body="1. **Biggest worry.** This is the doubt prose.",
            )

            txn = plan_arm_transaction(
                feature, just_closed_gate=1,
                arm_payload=ARM_PAYLOAD, timestamp=TIMESTAMP,
            )
            applied = apply_arm_transaction(txn)

            review_path = feature / FEATURE_REVIEW_FILENAME
            self.assertIn(review_path, applied)
            text = review_path.read_text()
            self.assertIn("Gate 1", text)
            self.assertIn("is the cap right?", text)
            self.assertIn("## Doubt", text)
            self.assertIn("Biggest worry", text)
            self.assertIn("would_arm: True", text)
            self.assertIn("budget_projection: clean", text)

    def test_path_appears_in_transaction_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            _gate_review(feature, 2, open_questions=[], doubt_body="doubt text")

            txn = plan_arm_transaction(
                feature, just_closed_gate=1,
                arm_payload=ARM_PAYLOAD, timestamp=TIMESTAMP,
            )

            self.assertIn(feature / FEATURE_REVIEW_FILENAME, txn.paths)

    def test_without_arm_payload_no_feature_review_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            _gate_review(feature, 2, open_questions=[], doubt_body="doubt text")

            txn = plan_arm_transaction(feature, just_closed_gate=1)

            self.assertIsNone(txn.feature_review_path)
            self.assertNotIn(feature / FEATURE_REVIEW_FILENAME, txn.paths)
            applied = apply_arm_transaction(txn)
            self.assertFalse((feature / FEATURE_REVIEW_FILENAME).exists())
            self.assertNotIn(feature / FEATURE_REVIEW_FILENAME, applied)

    def test_two_successive_arms_append_in_order_without_rewriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            _gate_review(feature, 2, open_questions=[], doubt_body="gate 1 doubt")

            txn1 = plan_arm_transaction(
                feature, just_closed_gate=1,
                arm_payload=ARM_PAYLOAD, timestamp=TIMESTAMP,
            )
            apply_arm_transaction(txn1)
            first_text = (feature / FEATURE_REVIEW_FILENAME).read_text()

            # Simulate gate 2 closing: gate 2 -> awaiting_review, gate 3 has a
            # drafted WU, and a GATE-03-REVIEW.md exists for the next arm.
            _gate(feature, 2, "awaiting_review")
            # Extend the plan graph with gate 3 directly.
            plan_text = (feature / "PLAN.md").read_text()
            plan_text = plan_text.replace(
                "  - gate: 2\n    file: GATE-02.md\n"
                "    work_units:\n"
                f"      - id: {FEATURE_ID}/T02\n        file: WU-02.md\n"
                "        depends_on: []\n",
                "  - gate: 2\n    file: GATE-02.md\n"
                "    work_units:\n"
                f"      - id: {FEATURE_ID}/T02\n        file: WU-02.md\n"
                "        depends_on: []\n"
                "  - gate: 3\n    file: GATE-03.md\n"
                "    work_units:\n"
                f"      - id: {FEATURE_ID}/T03\n        file: WU-03.md\n"
                "        depends_on: []\n",
            )
            _write(feature / "PLAN.md", plan_text)
            _wu(feature, "WU-03.md", "draft")
            _gate_review(
                feature, 3, open_questions=[], doubt_body="gate 2 doubt",
            )

            timestamp2 = "2026-07-30T01:00:00+00:00"
            txn2 = plan_arm_transaction(
                feature, just_closed_gate=2,
                arm_payload=ARM_PAYLOAD, timestamp=timestamp2,
            )
            apply_arm_transaction(txn2)

            final_text = (feature / FEATURE_REVIEW_FILENAME).read_text()
            self.assertTrue(final_text.startswith(first_text.rstrip("\n")[:20]))
            self.assertIn("Gate 1", final_text)
            self.assertIn("Gate 2", final_text)
            self.assertLess(
                final_text.index("Gate 1"), final_text.index("Gate 2"),
            )
            self.assertIn("gate 1 doubt", final_text)
            self.assertIn("gate 2 doubt", final_text)

    def test_malformed_review_file_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            _write(
                feature / "GATE-02-REVIEW.md",
                "---\ngate: 2\nopen_questions: [unterminated\n---\n\n# broken\n",
            )

            txn = plan_arm_transaction(
                feature, just_closed_gate=1,
                arm_payload=ARM_PAYLOAD, timestamp=TIMESTAMP,
            )
            applied = apply_arm_transaction(txn)

            review_path = feature / FEATURE_REVIEW_FILENAME
            self.assertIn(review_path, applied)
            text = review_path.read_text()
            self.assertIn("Gate 1", text)
            self.assertIn("(no `## Doubt` section found)", text)

    def test_missing_review_file_records_absence_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            # No GATE-02-REVIEW.md written at all.

            txn = plan_arm_transaction(
                feature, just_closed_gate=1,
                arm_payload=ARM_PAYLOAD, timestamp=TIMESTAMP,
            )
            applied = apply_arm_transaction(txn)

            text = (feature / FEATURE_REVIEW_FILENAME).read_text()
            self.assertIn("(none)", text)
            self.assertIn("(no `## Doubt` section found)", text)
            self.assertIn(feature / FEATURE_REVIEW_FILENAME, applied)

    def test_append_feature_review_entry_symbol_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _feature(tmp, [(f"{FEATURE_ID}/T02", "WU-02.md")])
            _gate_review(feature, 2, open_questions=[], doubt_body="direct call doubt")

            path = append_feature_review_entry(
                feature, just_closed_gate=1,
                arm_payload=ARM_PAYLOAD, timestamp=TIMESTAMP,
            )

            self.assertEqual(path, feature / FEATURE_REVIEW_FILENAME)
            self.assertIn("direct call doubt", path.read_text())


if __name__ == "__main__":
    unittest.main()
