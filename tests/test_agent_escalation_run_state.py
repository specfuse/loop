# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0108/T06: a stopped-outcome escalation reads what the
run actually left behind -- an open PR, a committed-but-unpushed fix branch,
or a `wip/<item_id>` ref (FEAT-2026-0108/T02) -- rather than asserting the
generic "never reached a guardrail or merge decision" sentence regardless.
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
from specfuse.agent.run import ActionItem, KIND_BUG, STATUS_ESCALATED
from specfuse.loop.bug_lane_run import BugLaneResult, OUTCOME_COULD_NOT_PROCEED


def _escalation_text(esc) -> str:
    return " ".join(
        [esc.done_so_far, esc.issue_summary, esc.decision_needed, esc.why_not_auto]
        + [opt[0] for opt in esc.options]
        + [esc.recommendation]
    )


def _runner_returning(branch_stdout: str, log_stdout: str):
    def runner(argv, check: bool = False):
        if argv[:3] == ["git", "branch", "--list"]:
            return SimpleNamespace(returncode=0, stdout=branch_stdout, stderr="")
        if argv[:2] == ["git", "log"]:
            return SimpleNamespace(returncode=0, stdout=log_stdout, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


class TestEscalationReadsRunState(unittest.TestCase):
    def test_stopped_item_with_open_pr_links_it(self):
        provider = BugsProvider(repo="o/r", runner=_runner_returning("", ""))
        item = ActionItem(item_id="bug-1481", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=OUTCOME_COULD_NOT_PROCEED, reason=None, pr_number=1532
            ),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        text = _escalation_text(outcome.escalation)
        self.assertIn("PR #1532", text)
        self.assertNotIn("never reached a guardrail", text)

    def test_wip_ref_is_named_with_commit_count(self):
        runner = _runner_returning(
            "wip/bug-99\n", "aaa\nbbb\nccc\n",
        )
        provider = BugsProvider(repo="o/r", runner=runner)
        item = ActionItem(item_id="bug-99", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=OUTCOME_COULD_NOT_PROCEED, reason=None, pr_number=None
            ),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        text = _escalation_text(outcome.escalation)
        self.assertIn("wip/bug-99", text)
        self.assertIn("3", text)
        self.assertNotIn("never reached a guardrail", text)

    def test_nothing_left_behind_keeps_generic_text(self):
        provider = BugsProvider(repo="o/r", runner=_runner_returning("", ""))
        item = ActionItem(item_id="bug-7", kind=KIND_BUG)

        with patch(
            "specfuse.agent.providers.bugs.run_bug_lane",
            return_value=BugLaneResult(
                outcome=OUTCOME_COULD_NOT_PROCEED, reason=None, pr_number=None
            ),
        ):
            outcome = provider.execute(item)

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        text = _escalation_text(outcome.escalation)
        self.assertIn("never reached a guardrail", text)


if __name__ == "__main__":
    unittest.main()
