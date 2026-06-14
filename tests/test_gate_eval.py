#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/gate_eval.py — FEAT-2026-0018/T02.

One class per predicate criterion (v1), plus graceful-degrade, override,
combined-scenario, and closing-WU-exclusion tests.
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

from gate_eval import AutoCloseDecision, evaluate_auto_close  # noqa: E402

FIXTURES = REPO_ROOT / "tests/fixtures/gate_eval"


# ---------------------------------------------------------------------------
# Criterion 1: No blocked_human in attempt chain
# ---------------------------------------------------------------------------


class TestBlockedHumanInChain(unittest.TestCase):

    def test_human_escalation_event_disables_auto(self):
        decision = evaluate_auto_close(FIXTURES / "blocked_in_chain", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any(r.startswith("blocked_human_in_chain") for r in decision.reasons),
            f"Expected blocked_human_in_chain reason; got {decision.reasons!r}",
        )

    def test_rearm_count_in_wu_frontmatter_triggers_blocked_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9920", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9920/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9920/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9920/T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0, extra_fm="rearm_count: 1\n")
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9920/G1-CLOSE", "close")
            _write_event(fdir, "FEAT-2026-9920/T01", "task_completed")
            decision = evaluate_auto_close(fdir, 1)
            self.assertFalse(decision.auto)
            self.assertTrue(
                any("blocked_human_in_chain" in r for r in decision.reasons),
                f"rearm_count=1 must trigger blocked_human_in_chain; got {decision.reasons!r}",
            )

    def test_no_blocked_events_allows_auto(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertFalse(
            any("blocked_human_in_chain" in r for r in decision.reasons)
        )


# ---------------------------------------------------------------------------
# Criterion 2: No replan events
# ---------------------------------------------------------------------------


class TestReplanEvent(unittest.TestCase):

    def test_replan_event_disables_auto(self):
        decision = evaluate_auto_close(FIXTURES / "replan_event", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any(r.startswith("replan_event") for r in decision.reasons),
            f"Expected replan_event reason; got {decision.reasons!r}",
        )

    def test_replan_followed_by_task_completed_still_disables(self):
        # replan_event fixture has task_completed after replan — check 2 still fires
        decision = evaluate_auto_close(FIXTURES / "replan_event", 1)
        self.assertTrue(
            any(r.startswith("replan_event") for r in decision.reasons)
        )

    def test_no_replan_does_not_add_replan_reason(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertFalse(
            any("replan_event" in r for r in decision.reasons)
        )


# ---------------------------------------------------------------------------
# Criterion 3: Per-WU cost ≤ 1.5× planned
# ---------------------------------------------------------------------------


class TestPerWuCostOverrun15x(unittest.TestCase):

    def test_1_6x_overrun_disables_auto(self):
        decision = evaluate_auto_close(FIXTURES / "cost_overrun_15x", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any(r.startswith("per_wu_cost_overrun") for r in decision.reasons),
            f"Expected per_wu_cost_overrun; got {decision.reasons!r}",
        )

    def test_exact_1_5x_is_at_ceiling_not_over(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_single_impl_close_fixture(fdir, "FEAT-2026-9921",
                                             cost=1.5, planned=1.0)
            _write_event(fdir, "FEAT-2026-9921/T01", "task_completed")
            decision = evaluate_auto_close(fdir, 1)
            self.assertFalse(
                any("per_wu_cost_overrun" in r for r in decision.reasons),
                "ratio exactly 1.5 must NOT fire per_wu_cost_overrun (ceiling is exclusive >)",
            )

    def test_close_wu_cost_is_excluded_from_ratio_check(self):
        # closing_high_cost fixture has close-intermediate at 5x — must be ignored
        decision = evaluate_auto_close(FIXTURES / "closing_high_cost", 1)
        self.assertFalse(
            any("per_wu_cost_overrun" in r for r in decision.reasons),
            "close-intermediate 5x cost must not trigger per_wu_cost_overrun",
        )


# ---------------------------------------------------------------------------
# Criterion 4: No WU > 2× planned (hard ceiling)
# ---------------------------------------------------------------------------


class TestPerWuCostHardOverrun2x(unittest.TestCase):

    def test_2_5x_overrun_adds_hard_overrun_reason(self):
        decision = evaluate_auto_close(FIXTURES / "cost_overrun_2x", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any("per_wu_hard_overrun" in r for r in decision.reasons),
            f"Expected per_wu_hard_overrun reason; got {decision.reasons!r}",
        )

    def test_2_5x_also_adds_soft_overrun_reason(self):
        # >2x implies >1.5x, so both checks fire
        decision = evaluate_auto_close(FIXTURES / "cost_overrun_2x", 1)
        self.assertTrue(
            any("per_wu_cost_overrun" in r for r in decision.reasons),
            "2.5x overrun must also fire per_wu_cost_overrun (>1.5x)",
        )

    def test_1_6x_does_not_fire_hard_overrun(self):
        decision = evaluate_auto_close(FIXTURES / "cost_overrun_15x", 1)
        self.assertFalse(
            any("per_wu_hard_overrun" in r for r in decision.reasons),
            "1.6x (below 2x hard ceiling) must not fire per_wu_hard_overrun",
        )


# ---------------------------------------------------------------------------
# Criterion 5: Plan-next ≤ 1.5× planned
# ---------------------------------------------------------------------------


class TestPlanNextOverrun(unittest.TestCase):

    def test_2x_plan_next_cost_disables_auto(self):
        decision = evaluate_auto_close(FIXTURES / "plan_next_overrun", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any(r.startswith("plan_next_overrun") for r in decision.reasons),
            f"Expected plan_next_overrun reason; got {decision.reasons!r}",
        )

    def test_plan_next_overrun_is_separate_from_per_wu_overrun(self):
        # plan-next WUs are skipped by checks 3/4; check 5 is the dedicated check
        decision = evaluate_auto_close(FIXTURES / "plan_next_overrun", 1)
        # T01 has no overrun — only plan_next_overrun should fire from cost checks
        cost_reasons = [r for r in decision.reasons if "per_wu_cost_overrun" in r
                        or "per_wu_hard_overrun" in r]
        self.assertEqual(cost_reasons, [],
                         "T01 cost=1.0x must not add per_wu cost reasons")


# ---------------------------------------------------------------------------
# Criterion 6: Gate total ≤ cost_budget_usd
# ---------------------------------------------------------------------------


class TestGateBudgetBust(unittest.TestCase):

    def test_gate_total_exceeds_budget_disables_auto(self):
        decision = evaluate_auto_close(FIXTURES / "budget_bust", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any(r.startswith("gate_budget_exceeded") for r in decision.reasons),
            f"Expected gate_budget_exceeded reason; got {decision.reasons!r}",
        )

    def test_gate_total_reported_in_metrics(self):
        decision = evaluate_auto_close(FIXTURES / "budget_bust", 1)
        self.assertAlmostEqual(
            decision.metrics["gate_total_cost"], 6.5, places=4,
            msg="gate_total_cost must be sum of all WU cost_usd (3.0 + 3.5 + 0.0)",
        )
        self.assertAlmostEqual(
            decision.metrics["gate_budget"], 5.0, places=4,
        )


# ---------------------------------------------------------------------------
# Criterion 7: Final outcome must be passed
# ---------------------------------------------------------------------------


class TestFinalOutcomeFailure(unittest.TestCase):

    def test_no_terminal_event_triggers_final_attempt_not_passed(self):
        decision = evaluate_auto_close(FIXTURES / "final_failure", 1)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any("final_attempt_not_passed" in r for r in decision.reasons),
            f"Expected final_attempt_not_passed reason; got {decision.reasons!r}",
        )

    def test_outcome_no_events_is_named_in_reason(self):
        decision = evaluate_auto_close(FIXTURES / "final_failure", 1)
        matching = [r for r in decision.reasons if "final_attempt_not_passed" in r]
        self.assertTrue(matching)
        self.assertIn("no_events", matching[0],
                      "Outcome 'no_events' must be named in the reason string")

    def test_close_wu_outcome_not_checked(self):
        # close WU in _NON_SUBSTANTIVE_TYPES — check 7 must not fire for it
        # blocked_in_chain has human_escalation on its close WU but check 7 is skipped
        decision = evaluate_auto_close(FIXTURES / "blocked_in_chain", 1)
        no_pass_for_close = [r for r in decision.reasons
                             if "final_attempt_not_passed" in r and "G1-CLOSE" in r]
        self.assertEqual(no_pass_for_close, [],
                         "close WU must not appear in final_attempt_not_passed reasons")


# ---------------------------------------------------------------------------
# Happy path: all criteria pass
# ---------------------------------------------------------------------------


class TestAutoCloseHappyPath(unittest.TestCase):

    def test_single_close_wu_no_events_returns_auto_true(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertTrue(decision.auto)
        self.assertEqual(decision.reasons, [])

    def test_decision_dataclass_fields_populated(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertIsInstance(decision, AutoCloseDecision)
        self.assertEqual(decision.gate_id, 1)
        self.assertEqual(decision.feature_id, "FEAT-2026-9901")
        self.assertEqual(decision.predicate_version, "v1")
        self.assertIsInstance(decision.metrics, dict)

    def test_auto_true_means_empty_reasons(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertEqual(len(decision.reasons), 0)


# ---------------------------------------------------------------------------
# Graceful degrade: missing planned_cost_usd
# ---------------------------------------------------------------------------


class TestMissingPlannedCostUsd(unittest.TestCase):

    def test_missing_planned_skips_ratio_check_and_warns(self):
        decision = evaluate_auto_close(FIXTURES / "missing_planned_cost", 1)
        self.assertTrue(decision.auto,
                        f"Missing planned_cost must not disable auto; reasons={decision.reasons!r}")
        warnings = decision.metrics.get("warnings", [])
        self.assertTrue(
            any("planned_cost_missing" in w for w in warnings),
            f"Expected planned_cost_missing in warnings; got {warnings!r}",
        )

    def test_warning_names_the_wu(self):
        decision = evaluate_auto_close(FIXTURES / "missing_planned_cost", 1)
        warnings = decision.metrics.get("warnings", [])
        matching = [w for w in warnings if "planned_cost_missing" in w]
        self.assertTrue(matching)
        self.assertIn("T01", matching[0],
                      "Warning must name the WU sub-id that is missing planned_cost_usd")


# ---------------------------------------------------------------------------
# Graceful degrade: missing gate cost_budget_usd
# ---------------------------------------------------------------------------


class TestMissingGateBudget(unittest.TestCase):

    def test_missing_gate_budget_skips_check6(self):
        decision = evaluate_auto_close(FIXTURES / "missing_budget", 1)
        self.assertTrue(decision.auto)
        self.assertFalse(
            any("gate_budget_exceeded" in r for r in decision.reasons),
            "No budget declared → gate_budget_exceeded must not fire",
        )

    def test_gate_budget_none_in_metrics(self):
        decision = evaluate_auto_close(FIXTURES / "missing_budget", 1)
        self.assertIsNone(
            decision.metrics.get("gate_budget"),
            "gate_budget metric must be None when GATE file has no cost_budget_usd",
        )


# ---------------------------------------------------------------------------
# Graceful degrade: missing events.jsonl
# ---------------------------------------------------------------------------


class TestMissingEventsJsonl(unittest.TestCase):

    def test_missing_events_file_warns_and_still_auto(self):
        decision = evaluate_auto_close(FIXTURES / "no_events", 1)
        self.assertTrue(decision.auto,
                        f"Missing events.jsonl must not disable auto; reasons={decision.reasons!r}")
        warnings = decision.metrics.get("warnings", [])
        self.assertIn(
            "events_jsonl_missing", warnings,
            f"Expected events_jsonl_missing in warnings; got {warnings!r}",
        )

    def test_malformed_json_lines_skipped_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9922", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9922/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9922/G1-CLOSE", "close")
            (fdir / "events.jsonl").write_text("not-valid-json\n{also bad\n")
            decision = evaluate_auto_close(fdir, 1)
            self.assertTrue(decision.auto,
                            "Malformed JSON lines must be skipped; predicate must not crash")

    def test_events_with_non_matching_correlation_id_filtered(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9923", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9923/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9923/G1-CLOSE", "close")
            # Write event for a DIFFERENT feature — must be filtered out
            (fdir / "events.jsonl").write_text(
                json.dumps({
                    "event_type": "human_escalation",
                    "correlation_id": "FEAT-2026-9999/T01",  # not in this gate
                    "timestamp": "2026-01-01T00:00:00Z",
                }) + "\n"
            )
            decision = evaluate_auto_close(fdir, 1)
            self.assertTrue(decision.auto,
                            "Events for other features must be filtered; auto must remain True")


# ---------------------------------------------------------------------------
# Graceful degrade: missing WU file
# ---------------------------------------------------------------------------


class TestMissingWuFile(unittest.TestCase):

    def test_missing_wu_file_returns_wu_file_missing_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9912", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9912/T01", "file": "WU-missing.md", "depends_on": []},
                    {"id": "FEAT-2026-9912/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9912/G1-CLOSE", "close")
            # Deliberately omit WU-missing.md

            decision = evaluate_auto_close(fdir, 1)
            self.assertFalse(decision.auto)
            self.assertTrue(
                any(r.startswith("wu_file_missing") for r in decision.reasons),
                f"Expected wu_file_missing reason; got {decision.reasons!r}",
            )

    def test_wu_file_missing_names_the_sub_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9912", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9912/T01", "file": "WU-missing.md", "depends_on": []},
                    {"id": "FEAT-2026-9912/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9912/G1-CLOSE", "close")

            decision = evaluate_auto_close(fdir, 1)
            matching = [r for r in decision.reasons if "wu_file_missing" in r]
            self.assertTrue(matching)
            self.assertIn("T01", matching[0],
                          "wu_file_missing reason must name the missing WU's sub-id")


# ---------------------------------------------------------------------------
# Override: auto_close_disabled per PLAN.md
# ---------------------------------------------------------------------------


class TestAutoCloseDisabledPerPlan(unittest.TestCase):

    def test_auto_close_disabled_flag_prevents_auto(self):
        decision = evaluate_auto_close(FIXTURES / "disabled_per_plan", 1)
        self.assertFalse(decision.auto)
        self.assertIn(
            "auto_close_disabled_per_plan", decision.reasons,
            f"Expected auto_close_disabled_per_plan; got {decision.reasons!r}",
        )

    def test_override_is_the_only_reason(self):
        decision = evaluate_auto_close(FIXTURES / "disabled_per_plan", 1)
        self.assertEqual(
            decision.reasons, ["auto_close_disabled_per_plan"],
            "Override fires before WU inspection — must be the sole reason",
        )

    def test_override_wins_over_otherwise_passing_criteria(self):
        # disabled_per_plan has costs that match plan — would auto=True if not for override
        decision = evaluate_auto_close(FIXTURES / "disabled_per_plan", 1)
        self.assertEqual(len(decision.reasons), 1,
                         "Exactly one reason: the override, not downstream checks")


# ---------------------------------------------------------------------------
# Combined: multiple criteria fail simultaneously
# ---------------------------------------------------------------------------


class TestMultipleFailures(unittest.TestCase):

    def test_multiple_failures_all_collected(self):
        decision = evaluate_auto_close(FIXTURES / "multiple_failures", 1)
        self.assertFalse(decision.auto)
        self.assertGreaterEqual(
            len(decision.reasons), 3,
            f"Expected ≥3 reasons (no short-circuit); got {decision.reasons!r}",
        )

    def test_blocked_human_in_combined(self):
        decision = evaluate_auto_close(FIXTURES / "multiple_failures", 1)
        self.assertTrue(
            any("blocked_human_in_chain" in r for r in decision.reasons)
        )

    def test_cost_overrun_in_combined(self):
        decision = evaluate_auto_close(FIXTURES / "multiple_failures", 1)
        self.assertTrue(
            any("per_wu_cost_overrun" in r for r in decision.reasons)
        )

    def test_plan_next_overrun_in_combined(self):
        decision = evaluate_auto_close(FIXTURES / "multiple_failures", 1)
        self.assertTrue(
            any("plan_next_overrun" in r for r in decision.reasons)
        )

    def test_predicate_does_not_short_circuit(self):
        # All reasons must be collected even when multiple checks fail
        decision = evaluate_auto_close(FIXTURES / "multiple_failures", 1)
        blocked = any("blocked_human_in_chain" in r for r in decision.reasons)
        overrun = any("per_wu_cost_overrun" in r for r in decision.reasons)
        plan_next = any("plan_next_overrun" in r for r in decision.reasons)
        self.assertTrue(blocked and overrun and plan_next,
                        "All three failure types must appear in reasons (no short-circuit)")


# ---------------------------------------------------------------------------
# Closing-WU exclusion from cost checks (AC7 of T01)
# ---------------------------------------------------------------------------


class TestClosingWusSkippedInCostChecks(unittest.TestCase):

    def test_close_intermediate_5x_cost_does_not_disable_auto(self):
        decision = evaluate_auto_close(FIXTURES / "closing_high_cost", 1)
        self.assertTrue(
            decision.auto,
            f"close-intermediate 5x cost must be ignored; reasons={decision.reasons!r}",
        )
        self.assertEqual(decision.reasons, [])

    def test_close_wu_not_in_per_wu_cost_metrics(self):
        # Close WU is still counted in gate_total_cost but not ratio-checked
        decision = evaluate_auto_close(FIXTURES / "closing_high_cost", 1)
        self.assertFalse(
            any("per_wu_cost_overrun" in r for r in decision.reasons),
            "close-intermediate must not appear in cost-ratio failure reasons",
        )

    def test_gate_total_includes_close_wu_cost(self):
        # close-int cost IS summed into gate_total (used for budget check)
        decision = evaluate_auto_close(FIXTURES / "closing_high_cost", 1)
        # T01:1.0 + close-int:5.0 + plan-next:1.0 = 7.0
        self.assertAlmostEqual(decision.metrics["gate_total_cost"], 7.0, places=4)


# ---------------------------------------------------------------------------
# Edge cases: gate_not_found, predicate_version, feature_id fallback
# ---------------------------------------------------------------------------


class TestEdgeCases(unittest.TestCase):

    def test_gate_not_found_returns_auto_false(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 99)
        self.assertFalse(decision.auto)
        self.assertTrue(
            any("gate_not_found" in r for r in decision.reasons),
            f"Expected gate_not_found; got {decision.reasons!r}",
        )

    def test_predicate_version_is_v1(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertEqual(decision.predicate_version, "v1")

    def test_feature_id_read_from_frontmatter(self):
        decision = evaluate_auto_close(FIXTURES / "happy_1wu_terminal", 1)
        self.assertEqual(decision.feature_id, "FEAT-2026-9901")

    def test_feature_id_falls_back_to_dirname(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Use a subdirectory with identifiable name; omit feature_id from frontmatter
            fdir = Path(tmp) / "my-dir-name"
            fdir.mkdir()
            # Write PLAN.md without feature_id (lint would fail but predicate degrades)
            plan_text = (
                "---\ntitle: No feature_id\n---\n\n# Plan\n\n"
                "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n    work_units: []\n```\n"
            )
            (fdir / "PLAN.md").write_text(plan_text)
            decision = evaluate_auto_close(fdir, 1)
            # gate 1 exists but has no WUs → predicate runs with empty WU list → auto=True
            # feature_id must fall back to dir name when frontmatter lacks feature_id
            self.assertEqual(decision.feature_id, "my-dir-name")

    def test_empty_events_file_does_not_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9924", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9924/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9924/G1-CLOSE", "close")
            (fdir / "events.jsonl").write_text("")  # exists but empty
            decision = evaluate_auto_close(fdir, 1)
            warnings = decision.metrics.get("warnings", [])
            self.assertNotIn("events_jsonl_missing", warnings,
                             "Empty events.jsonl must not produce events_jsonl_missing warning")
            self.assertTrue(decision.auto)


# ---------------------------------------------------------------------------
# Helper functions for dynamic fixtures
# ---------------------------------------------------------------------------


def _write_plan_md(
    fdir: Path,
    feature_id: str,
    gates: list,
    extra_frontmatter: str = "",
) -> None:
    gate_yaml = _render_gate_yaml(gates)
    content = (
        f"---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test fixture {feature_id}\n"
        f"branch: feat/{feature_id.lower()}-test-fixture\n"
        f"roadmap_goal: Synthetic fixture for gate_eval predicate unit tests\n"
        f"status: active\n"
        f"{extra_frontmatter}"
        f"---\n\n"
        f"# Plan\n\n"
        f"```yaml\n"
        f"{gate_yaml}"
        f"```\n"
    )
    (fdir / "PLAN.md").write_text(content)


def _render_gate_yaml(gates: list) -> str:
    lines = ["gates:\n"]
    for g in gates:
        lines.append(f"  - gate: {g['gate']}\n")
        if g.get("file"):
            lines.append(f"    file: {g['file']}\n")
        wu_list = g.get("work_units") or []
        if wu_list:
            lines.append("    work_units:\n")
            for wu in wu_list:
                lines.append(f"      - id: {wu['id']}\n")
                lines.append(f"        file: {wu['file']}\n")
                deps = wu.get("depends_on") or []
                if deps:
                    dep_str = ", ".join(deps)
                    lines.append(f"        depends_on: [{dep_str}]\n")
                else:
                    lines.append("        depends_on: []\n")
        else:
            lines.append("    work_units: []\n")
    return "".join(lines)


def _write_wu_file(
    fdir: Path,
    filename: str,
    wu_id: str,
    wu_type: str,
    cost_usd: float | None = None,
    planned_cost_usd: float | None = None,
    extra_fm: str = "",
) -> None:
    lines = [
        f"id: {wu_id}",
        f"type: {wu_type}",
        "status: done",
        "attempts: 1",
    ]
    if cost_usd is not None:
        lines.append(f"cost_usd: {cost_usd}")
    if planned_cost_usd is not None:
        lines.append(f"planned_cost_usd: {planned_cost_usd}")
    fm_block = "\n".join(lines)
    if extra_fm:
        fm_block = fm_block + "\n" + extra_fm.rstrip()
    (fdir / filename).write_text(f"---\n{fm_block}\n---\n\nTest fixture WU.\n")


def _write_event(
    fdir: Path,
    correlation_id: str,
    event_type: str,
    timestamp: str = "2026-01-01T00:00:00Z",
) -> None:
    ev = json.dumps({
        "event_type": event_type,
        "correlation_id": correlation_id,
        "timestamp": timestamp,
    })
    with (fdir / "events.jsonl").open("a") as f:
        f.write(ev + "\n")


def _write_single_impl_close_fixture(
    fdir: Path,
    feature_id: str,
    cost: float,
    planned: float,
) -> None:
    _write_plan_md(fdir, feature_id, gates=[{
        "gate": 1, "file": "GATE-01.md", "work_units": [
            {"id": f"{feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{feature_id}/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
        ],
    }])
    _write_wu_file(fdir, "WU-01.md", f"{feature_id}/T01", "implementation",
                   cost_usd=cost, planned_cost_usd=planned)
    _write_wu_file(fdir, "WU-90.md", f"{feature_id}/G1-CLOSE", "close")


if __name__ == "__main__":
    unittest.main()
