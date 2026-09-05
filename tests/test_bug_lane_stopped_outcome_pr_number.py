# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0108/T05H: `run_bug_lane`'s escalating branch
(`refused` / `could_not_proceed`) carries the PR number `/fix-bug`'s own
RESULT block reported, instead of returning a literal `pr_number=None` and
throwing away what `extract_pr_number` (T05) already reads from the same
session output.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import ActionItem, KIND_BUG, STATUS_ESCALATED
from specfuse.loop.bug_lane_run import (
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_REFUSED,
    run_bug_lane,
)

_REPO = "acme-widget/example"
_ISSUE_NUMBER = 7
_PR_NUMBER = 1532


def _stub_runner(session_output: str):
    """Fake `gh`/`git`/`claude` runner. `run_bug_lane`'s escalating branch
    also reads `git branch --list` / `git log` for unpushed work -- both
    return nothing here, so `unpushed_work` stays `None` and the PR number
    is the only signal in play.
    """

    def runner(argv, check: bool = False, **_kwargs):
        if argv[:2] == ["claude", "-p"]:
            return SimpleNamespace(returncode=0, stdout=session_output, stderr="")
        if argv[:2] == ["git", "branch"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:2] == ["git", "log"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


class TestStoppedOutcomeCarriesPrNumber(unittest.TestCase):
    def test_could_not_proceed_carries_pr_number(self):
        session_output = (
            "```result\n"
            "status: could_not_proceed\n"
            f"pr_number: {_PR_NUMBER}\n"
            "```\n"
        )
        result = run_bug_lane(_stub_runner(session_output), _REPO, _ISSUE_NUMBER)

        self.assertEqual(result.outcome, OUTCOME_COULD_NOT_PROCEED)
        self.assertEqual(result.pr_number, _PR_NUMBER)

    def test_refused_carries_pr_number_when_present(self):
        session_output = (
            "```result\n"
            "status: refused\n"
            f"pr_number: {_PR_NUMBER}\n"
            "```\n"
        )
        result = run_bug_lane(_stub_runner(session_output), _REPO, _ISSUE_NUMBER)

        self.assertEqual(result.outcome, OUTCOME_REFUSED)
        self.assertEqual(result.pr_number, _PR_NUMBER)

    def test_stopped_without_pr_number_stays_none(self):
        session_output = "```result\nstatus: could_not_proceed\n```\n"
        result = run_bug_lane(_stub_runner(session_output), _REPO, _ISSUE_NUMBER)

        self.assertEqual(result.outcome, OUTCOME_COULD_NOT_PROCEED)
        self.assertIsNone(result.pr_number)


class TestProviderEscalationEndToEnd(unittest.TestCase):
    def test_provider_escalation_names_the_open_pr_end_to_end(self):
        session_output = (
            "```result\n"
            "status: could_not_proceed\n"
            f"pr_number: {_PR_NUMBER}\n"
            "```\n"
        )
        provider = BugsProvider(repo=_REPO, runner=_stub_runner(session_output))
        item = ActionItem(item_id="bug-1481", kind=KIND_BUG)

        outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        esc = outcome.escalation
        text = " ".join(
            [esc.done_so_far, esc.issue_summary, esc.decision_needed, esc.why_not_auto]
            + [opt[0] for opt in esc.options]
            + [esc.recommendation]
        )
        self.assertIn(f"PR #{_PR_NUMBER}", text)
        self.assertNotIn("never reached a guardrail", text)


if __name__ == "__main__":
    unittest.main()
