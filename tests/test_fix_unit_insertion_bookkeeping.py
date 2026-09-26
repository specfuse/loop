#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for FEAT-2026-0115/T03 — an inserted fix unit is off-plan for
auto-close, and the escalation brief names why insertion did not happen.

Two things this file proves:

1. `gate_eval.evaluate_auto_close` disables auto-close on a `fix_unit_inserted`
   event the same way it already does for `replan`, and counts it in
   `metrics`.
2. `loop.format_spinout_escalation_brief`'s new `insertion_refused` keyword
   renders the drafted file, the refusing class/reason (or "review mode"),
   and the arming command in option 1 — and leaves the brief byte-identical
   to today's when it is not passed.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_scripts = str(REPO_ROOT / ".specfuse/scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

from gate_eval import evaluate_auto_close  # noqa: E402

from tests._loop_loader import load_loop  # noqa: E402

loop = load_loop()


# ---------------------------------------------------------------------------
# gate_eval: fix_unit_inserted disables auto-close
# ---------------------------------------------------------------------------


def _write_plan_md(fdir: Path, feature_id: str, gates: list) -> None:
    lines = ["gates:\n"]
    for g in gates:
        lines.append(f"  - gate: {g['gate']}\n")
        lines.append(f"    file: {g['file']}\n")
        lines.append("    work_units:\n")
        for wu in g["work_units"]:
            lines.append(f"      - id: {wu['id']}\n")
            lines.append(f"        file: {wu['file']}\n")
            lines.append("        depends_on: []\n")
    gate_yaml = "".join(lines)
    content = (
        "---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test fixture {feature_id}\n"
        f"branch: feat/{feature_id.lower()}-test-fixture\n"
        "roadmap_goal: Synthetic fixture for gate_eval predicate unit tests\n"
        "status: active\n"
        "---\n\n"
        "# Plan\n\n"
        "```yaml\n"
        f"{gate_yaml}"
        "```\n"
    )
    (fdir / "PLAN.md").write_text(content)


def _write_wu_file(fdir: Path, filename: str, wu_id: str, wu_type: str) -> None:
    fm = (
        f"id: {wu_id}\n"
        f"type: {wu_type}\n"
        "status: done\n"
        "attempts: 1\n"
        "cost_usd: 1.0\n"
        "planned_cost_usd: 1.0\n"
    )
    (fdir / filename).write_text(f"---\n{fm}---\n\nTest fixture WU.\n")


def _write_event(fdir: Path, correlation_id: str, event_type: str) -> None:
    ev = json.dumps({
        "event_type": event_type,
        "correlation_id": correlation_id,
        "timestamp": "2026-01-01T00:00:00Z",
    })
    with (fdir / "events.jsonl").open("a") as f:
        f.write(ev + "\n")


def _scaffold(fdir: Path, feature_id: str) -> None:
    _write_plan_md(fdir, feature_id, gates=[{
        "gate": 1, "file": "GATE-01.md", "work_units": [
            {"id": f"{feature_id}/T01", "file": "WU-01.md"},
            {"id": f"{feature_id}/G1-CLOSE", "file": "WU-90.md"},
        ],
    }])
    _write_wu_file(fdir, "WU-01.md", f"{feature_id}/T01", "implementation")
    _write_wu_file(fdir, "WU-90.md", f"{feature_id}/G1-CLOSE", "close")
    _write_event(fdir, f"{feature_id}/T01", "task_completed")
    _write_event(fdir, f"{feature_id}/G1-CLOSE", "task_completed")


class FixUnitInsertedDisablesAutoClose(unittest.TestCase):

    def test_fix_unit_inserted_event_disables_auto(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            feature_id = "FEAT-2026-9921"
            _scaffold(fdir, feature_id)
            _write_event(fdir, f"{feature_id}/T01", "fix_unit_inserted")

            decision = evaluate_auto_close(fdir, 1)
            self.assertFalse(decision.auto)
            self.assertTrue(
                any(r.startswith("fix_unit_inserted") for r in decision.reasons),
                f"Expected fix_unit_inserted reason; got {decision.reasons!r}",
            )
            self.assertEqual(decision.metrics["fix_unit_inserted_count"], 1)
            self.assertIn(
                f"{feature_id}/T01", decision.metrics["fix_unit_inserted_events"])

    def test_no_fix_unit_inserted_event_allows_auto(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            feature_id = "FEAT-2026-9922"
            _scaffold(fdir, feature_id)

            decision = evaluate_auto_close(fdir, 1)
            self.assertTrue(decision.auto, f"reasons={decision.reasons!r}")
            self.assertEqual(decision.metrics["fix_unit_inserted_count"], 0)
            self.assertEqual(decision.metrics["fix_unit_inserted_events"], [])


# ---------------------------------------------------------------------------
# escalation brief: names the draft, refusing class/reason, arming command
# ---------------------------------------------------------------------------


def _render(*, insertion_refused=None):
    wu = loop.WorkUnit.__new__(loop.WorkUnit)
    object.__setattr__(wu, "wu_id", "FEAT-2026-8889/T01")
    object.__setattr__(wu, "title", "Do the thing")
    return loop.format_spinout_escalation_brief(
        wu, 1, ["FEAT-2026-8889/T00"], ["FEAT-2026-8889/T02"],
        "agent_reported_blocked", 3, ["blocked"], False,
        "specfuse run --feature FEAT-2026-8889",
        insertion_refused=insertion_refused,
    )


class EscalationBriefNamesRefusedInsertion(unittest.TestCase):

    def test_refused_insertion_names_draft_class_and_arm_command(self):
        brief = _render(insertion_refused={
            "draft_file": "WU-04-fix-the-thing.md",
            "class": "judge_editing",
            "reason": "produces: names specfuse/loop/loop.py",
        })
        self.assertIn("WU-04-fix-the-thing.md", brief)
        self.assertIn("judge_editing", brief)
        self.assertIn("produces: names specfuse/loop/loop.py", brief)
        self.assertIn("/arm-gate", brief)
        self.assertIn("specfuse run --feature FEAT-2026-8889", brief)

    def test_review_mode_names_review_mode_not_a_class(self):
        brief = _render(insertion_refused={
            "draft_file": "WU-04-fix-the-thing.md",
            "class": None,
            "reason": "review mode",
        })
        self.assertIn("WU-04-fix-the-thing.md", brief)
        self.assertIn("review mode", brief)
        self.assertIn("/arm-gate", brief)

    def test_plain_block_brief_is_byte_identical_to_no_kwarg(self):
        with_default = _render()

        wu = loop.WorkUnit.__new__(loop.WorkUnit)
        object.__setattr__(wu, "wu_id", "FEAT-2026-8889/T01")
        object.__setattr__(wu, "title", "Do the thing")
        legacy_call = loop.format_spinout_escalation_brief(
            wu, 1, ["FEAT-2026-8889/T00"], ["FEAT-2026-8889/T02"],
            "agent_reported_blocked", 3, ["blocked"], False,
            "specfuse run --feature FEAT-2026-8889",
        )
        self.assertEqual(with_default, legacy_call)


if __name__ == "__main__":
    unittest.main()
