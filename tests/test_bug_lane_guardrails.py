#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0048/T02: the bug-lane merge-eligibility predicate."""

from __future__ import annotations

import unittest

from specfuse.loop import arm_eval, bug_lane
from specfuse.loop.bug_lane import (
    MergeDecision,
    REASON_CI_NOT_GREEN,
    REASON_CI_PENDING,
    REASON_DAILY_CAP_REACHED,
    REASON_DIFF_TOO_LARGE,
    REASON_ELIGIBLE,
    REASON_JUDGE_PATH_TOUCHED,
    REASON_NO_TEST_EVIDENCE,
    REASON_UNREADABLE_INPUT,
    REASON_UNTRACEABLE,
    evaluate_merge_guardrails,
)


class _CapStateReader:
    def __init__(self, count: int = 0) -> None:
        self._count = count

    def merges_last_24h(self) -> int:
        return self._count


class _RaisingStateReader:
    def merges_last_24h(self) -> int:
        raise RuntimeError("boom")


def _base_kwargs(**overrides):
    kwargs = dict(
        changed_files=["tests/test_thing.py", "specfuse/other/thing.py"],
        ci_conclusion="success",
        diff_lines=10,
        max_diff_lines=500,
        provenance={"kind": "triaged_issue", "ref": "issue-123"},
        max_merges_per_day=5,
        state_reader=_CapStateReader(0),
    )
    kwargs.update(overrides)
    return kwargs


class TestEvaluateMergeGuardrails(unittest.TestCase):
    def test_all_guardrails_pass_is_eligible(self) -> None:
        decision = evaluate_merge_guardrails(**_base_kwargs())
        self.assertEqual(decision, MergeDecision(eligible=True, reason=REASON_ELIGIBLE))

    def test_purity_no_io(self) -> None:
        # In-memory args and a fake state reader only; no file, process, or
        # network access is reachable from this call.
        decision = evaluate_merge_guardrails(**_base_kwargs())
        self.assertTrue(decision.eligible)


class TestGuardrailTestEvidence(unittest.TestCase):
    def test_no_test_path_declines_alone(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(changed_files=["specfuse/loop/thing.py"])
        )
        self.assertEqual(decision, MergeDecision(False, REASON_NO_TEST_EVIDENCE))


class TestGuardrailCiGreen(unittest.TestCase):
    def test_ci_not_green_declines_alone(self) -> None:
        decision = evaluate_merge_guardrails(**_base_kwargs(ci_conclusion="failure"))
        self.assertEqual(decision, MergeDecision(False, REASON_CI_NOT_GREEN))

    def test_ci_conclusions_failure_empty_none_decline(self) -> None:
        for bad in ("failure", "", None):
            with self.subTest(bad=bad):
                decision = evaluate_merge_guardrails(**_base_kwargs(ci_conclusion=bad))
                self.assertFalse(decision.eligible)
                self.assertEqual(decision.reason, REASON_CI_NOT_GREEN)

    def test_ci_conclusion_pending_declines_ci_pending_not_ci_not_green(self) -> None:
        """Pending is "wait", not "red" (#3177, FEAT-2026-0108/T04): folding it
        into REASON_CI_NOT_GREEN produced seven escalations that said a build
        was red when it was only still queued."""
        decision = evaluate_merge_guardrails(**_base_kwargs(ci_conclusion="pending"))
        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason, REASON_CI_PENDING)

    def test_only_success_passes_ci_guardrail(self) -> None:
        decision = evaluate_merge_guardrails(**_base_kwargs(ci_conclusion="success"))
        self.assertNotEqual(decision.reason, REASON_CI_NOT_GREEN)


class TestGuardrailDiffSize(unittest.TestCase):
    def test_diff_too_large_declines_alone(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(diff_lines=501, max_diff_lines=500)
        )
        self.assertEqual(decision, MergeDecision(False, REASON_DIFF_TOO_LARGE))

    def test_diff_at_cap_passes(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(diff_lines=500, max_diff_lines=500)
        )
        self.assertNotEqual(decision.reason, REASON_DIFF_TOO_LARGE)


class TestGuardrailJudgePaths(unittest.TestCase):
    def test_judge_paths_imported_not_redefined(self) -> None:
        self.assertIs(bug_lane.JUDGE_PATHS, arm_eval.JUDGE_PATHS)

    def test_each_judge_path_entry_declines_alone(self) -> None:
        for judge_path in arm_eval.JUDGE_PATHS:
            with self.subTest(judge_path=judge_path):
                touched = (
                    judge_path + "extra.txt"
                    if judge_path.endswith("/")
                    else judge_path
                )
                decision = evaluate_merge_guardrails(
                    **_base_kwargs(
                        changed_files=["tests/test_thing.py", touched]
                    )
                )
                self.assertEqual(
                    decision, MergeDecision(False, REASON_JUDGE_PATH_TOUCHED)
                )


class TestGuardrailProvenance(unittest.TestCase):
    def test_untraceable_declines_alone(self) -> None:
        decision = evaluate_merge_guardrails(**_base_kwargs(provenance=None))
        self.assertEqual(decision, MergeDecision(False, REASON_UNTRACEABLE))

    def test_empty_ref_declines(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(provenance={"kind": "triaged_issue", "ref": ""})
        )
        self.assertEqual(decision, MergeDecision(False, REASON_UNTRACEABLE))

    def test_unknown_kind_declines(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(provenance={"kind": "vibes", "ref": "issue-1"})
        )
        self.assertEqual(decision, MergeDecision(False, REASON_UNTRACEABLE))

    def test_diagnosed_finding_kind_passes(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(
                provenance={"kind": "diagnosed_finding", "ref": "finding-1"}
            )
        )
        self.assertNotEqual(decision.reason, REASON_UNTRACEABLE)


class TestGuardrailDailyCap(unittest.TestCase):
    def test_daily_cap_reached_declines_alone(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(max_merges_per_day=5, state_reader=_CapStateReader(5))
        )
        self.assertEqual(decision, MergeDecision(False, REASON_DAILY_CAP_REACHED))

    def test_below_cap_passes(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(max_merges_per_day=5, state_reader=_CapStateReader(4))
        )
        self.assertNotEqual(decision.reason, REASON_DAILY_CAP_REACHED)

    def test_raising_state_reader_declines_not_raises(self) -> None:
        decision = evaluate_merge_guardrails(
            **_base_kwargs(state_reader=_RaisingStateReader())
        )
        self.assertEqual(decision, MergeDecision(False, REASON_UNREADABLE_INPUT))


class TestFailClosed(unittest.TestCase):
    def _assert_declines(self, **overrides) -> None:
        decision = evaluate_merge_guardrails(**_base_kwargs(**overrides))
        self.assertFalse(decision.eligible)

    def test_changed_files_none(self) -> None:
        self._assert_declines(changed_files=None)

    def test_changed_files_wrong_type(self) -> None:
        self._assert_declines(changed_files=42)

    def test_changed_files_wrong_element_type(self) -> None:
        self._assert_declines(changed_files=["tests/test_thing.py", 5])

    def test_ci_conclusion_none(self) -> None:
        self._assert_declines(ci_conclusion=None)

    def test_ci_conclusion_wrong_type(self) -> None:
        self._assert_declines(ci_conclusion=1)

    def test_diff_lines_none(self) -> None:
        self._assert_declines(diff_lines=None)

    def test_diff_lines_wrong_type(self) -> None:
        self._assert_declines(diff_lines="10")

    def test_diff_lines_negative(self) -> None:
        self._assert_declines(diff_lines=-1)

    def test_max_diff_lines_none(self) -> None:
        self._assert_declines(max_diff_lines=None)

    def test_max_diff_lines_wrong_type(self) -> None:
        self._assert_declines(max_diff_lines="500")

    def test_max_diff_lines_zero(self) -> None:
        self._assert_declines(max_diff_lines=0)

    def test_provenance_missing_kind(self) -> None:
        self._assert_declines(provenance={"ref": "issue-1"})

    def test_provenance_missing_ref(self) -> None:
        self._assert_declines(provenance={"kind": "triaged_issue"})

    def test_provenance_wrong_type(self) -> None:
        self._assert_declines(provenance="issue-1")

    def test_max_merges_per_day_none(self) -> None:
        self._assert_declines(max_merges_per_day=None)

    def test_max_merges_per_day_wrong_type(self) -> None:
        self._assert_declines(max_merges_per_day="5")

    def test_state_reader_returns_wrong_type(self) -> None:
        class _BadReader:
            def merges_last_24h(self):
                return "not-an-int"

        self._assert_declines(state_reader=_BadReader())

    def test_no_input_raises_exception(self) -> None:
        malformed_variants = [
            dict(changed_files=None),
            dict(changed_files=42),
            dict(ci_conclusion=None),
            dict(diff_lines=None),
            dict(max_diff_lines=None),
            dict(provenance=None),
            dict(max_merges_per_day=None),
            dict(state_reader=_RaisingStateReader()),
        ]
        for variant in malformed_variants:
            with self.subTest(variant=variant):
                try:
                    decision = evaluate_merge_guardrails(**_base_kwargs(**variant))
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"raised {exc!r} for {variant}")
                self.assertFalse(decision.eligible)


if __name__ == "__main__":
    unittest.main()
