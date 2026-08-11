# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the bugs provider (FEAT-2026-0049/T06).

Covers: selection (one `kind="bug"` item per open, bug-triaged issue, none
for untriaged or otherwise-triaged issues), outcome mapping (`merged` ->
completed, `declined` / `refused` / `could_not_proceed` -> escalated naming
`BugLaneResult.reason`), no second escalation for the two outcomes the lane
already files itself, registration in `default_providers()`, and that the
provider never issues a `git` command of its own.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import (
    KIND_BUG,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    ActionItem,
    default_providers,
)
from specfuse.agent.state import AgentSnapshot, IssueSummary
from specfuse.loop.bug_lane_run import (
    BugLaneResult,
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_DECLINED,
    OUTCOME_MERGED,
    OUTCOME_REFUSED,
)


def _recording_runner(calls: list):
    def runner(argv, check: bool = False):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


def _issue(number: int, category) -> IssueSummary:
    return IssueSummary(
        number=number,
        title=f"issue {number}",
        labels=(),
        triage_category=category,
        triage_confidence="high" if category is not None else None,
    )


def _snapshot(issues: tuple) -> AgentSnapshot:
    return AgentSnapshot(
        queue=(),
        triage_auto=False,
        bug_automerge=False,
        bug_lane_limits={},
        issues=issues,
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


class TestBugsProviderAdvertise(unittest.TestCase):
    def test_advertise_returns_bug_item_for_triaged_bug(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        snapshot = _snapshot((_issue(7, "bug"),))

        items = provider.advertise(snapshot)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, KIND_BUG)
        self.assertEqual(items[0].item_id, "bug-7")

    def test_advertise_skips_untriaged_issue(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        snapshot = _snapshot((_issue(8, None),))

        self.assertEqual(provider.advertise(snapshot), [])

    def test_advertise_skips_non_bug_category(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        snapshot = _snapshot((_issue(9, "feature"),))

        self.assertEqual(provider.advertise(snapshot), [])


class TestBugsProviderExecute(unittest.TestCase):
    def test_execute_maps_merged_to_completed(self):
        calls = []
        provider = BugsProvider(repo="o/r", runner=_recording_runner(calls))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(outcome=OUTCOME_MERGED, reason="eligible", pr_number=5),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertEqual(calls, [])

    def test_execute_maps_declined_to_escalated_with_reason(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=OUTCOME_DECLINED, reason="diff_too_large", pr_number=5
            ),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn("diff_too_large", outcome.detail)

    def test_execute_maps_refused_to_escalated_with_detail(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(outcome=OUTCOME_REFUSED, reason=None, pr_number=None),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn(OUTCOME_REFUSED, outcome.detail)

    def test_execute_maps_could_not_proceed_to_escalated_with_detail(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=OUTCOME_COULD_NOT_PROCEED, reason=None, pr_number=None
            ),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn(OUTCOME_COULD_NOT_PROCEED, outcome.detail)


class TestBugsProvider(unittest.TestCase):
    def test_declined_outcome_escalates_without_second_issue(self):
        calls = []
        provider = BugsProvider(repo="o/r", runner=_recording_runner(calls))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=OUTCOME_DECLINED, reason="diff_too_large", pr_number=5
            ),
        ):
            outcome = provider.execute(item)
            provider.reconcile(item, outcome)

        # Escalated with a payload so the loop's own `emit_escalation` call
        # files exactly one issue -- but this module issues no `gh` call of
        # its own, so there is never a second.
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIsNotNone(outcome.escalation)
        self.assertEqual(calls, [])
        self.assertFalse(any("issue" in call and "create" in call for call in calls))

    def test_lane_filed_outcomes_carry_no_escalation_payload(self):
        provider = BugsProvider(repo="o/r", runner=_recording_runner([]))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        for lane_outcome in (OUTCOME_REFUSED, OUTCOME_COULD_NOT_PROCEED):
            with patch(
                "specfuse.agent.providers.bugs.run_bug_lane",
                return_value=BugLaneResult(outcome=lane_outcome, reason=None, pr_number=None),
            ):
                outcome = provider.execute(item)
            self.assertIsNone(outcome.escalation)

    def test_reconcile_issues_no_gh_call(self):
        calls = []
        provider = BugsProvider(repo="o/r", runner=_recording_runner(calls))
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(outcome=OUTCOME_MERGED, reason="eligible", pr_number=5),
        ):
            outcome = provider.execute(item)
        provider.reconcile(item, outcome)

        self.assertEqual(calls, [])

    def test_default_providers_registers_bugs_provider(self):
        providers = default_providers(repo="o/r")

        self.assertEqual([type(p).__name__ for p in providers], ["BugsProvider"])

    def test_execute_passes_injected_runner_through_without_git_mutation(self):
        calls = []
        runner = _recording_runner(calls)
        provider = BugsProvider(repo="o/r", runner=runner)
        item = ActionItem(item_id="bug-3", kind=KIND_BUG)

        captured = {}

        def fake_run_bug_lane(passed_runner, repo, issue_number, **kwargs):
            captured["runner"] = passed_runner
            return BugLaneResult(outcome=OUTCOME_MERGED, reason="eligible", pr_number=5)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane", side_effect=fake_run_bug_lane
        ):
            provider.execute(item)

        self.assertIs(captured["runner"], runner)
        self.assertFalse(any(call[:1] == ["git"] for call in calls))


if __name__ == "__main__":
    unittest.main()
