# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A bug-lane PR whose issue another PR already closed is superseded (#3447).

`run_bug_lane` read the issue once, for provenance, and never asked whether it
was still open. On clabonte/generator (2026-10-08) an interactive session fixed
the same issues in parallel: the lane opened #2355, the other session merged
#2357 ten minutes later and closed the issue, and the lane's escalation --
written after a CI wait -- still asked the operator to "review and merge PR
#2355 by hand", a duplicate of a closed fix that by then conflicted.

The lane now re-reads the issue when it has found its PR and again after the
CI wait, before it merges or escalates. A closed issue means the work is done
elsewhere: the lane closes its own PR, naming the PR that closed the issue,
and reports `superseded` -- never an escalation, never a merge.
"""

from __future__ import annotations

import json
import tempfile
import unittest

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import KIND_BUG, STATUS_COMPLETED, ActionItem
from specfuse.loop.bug_lane_run import OUTCOME_SUPERSEDED, run_bug_lane

_REPO = "acme-widget/example"
_ISSUE = 2350
_OWN_PR = 2355
_OTHER_PR = 2357

_POLICY = """
version: 1
queue: []
rules:
  bugs:
    preempt: false
    min_severity: low
    automerge: "{automerge}"
  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 1
  max_open_prs: 1
  max_items_per_day: 1
escalation:
  webhook_env: x
  assignee: x
  quiet_hours: x
  sla_hours: 1
"""

_SESSION = f"```result\nstatus: completed\npr_number: {_OWN_PR}\n```\n"


def _policy(automerge: str) -> str:
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    handle.write(_POLICY.format(automerge=automerge))
    handle.close()
    return handle.name


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _Runner:
    """Fake `gh`/`claude`. *states* is the issue state each successive state
    read returns, so a test can close the issue partway through the item."""

    def __init__(self, states, closed_by=(_OTHER_PR,)):
        self.calls: list[list[str]] = []
        self._states = list(states)
        self._closed_by = list(closed_by)

    def __call__(self, args, check=False, **_kwargs):
        self.calls.append(list(args))
        if args[:3] == ["gh", "issue", "view"]:
            fields = args[args.index("--json") + 1]
            if "state" in fields:
                state = self._states.pop(0) if len(self._states) > 1 else self._states[0]
                refs = [{"number": n} for n in self._closed_by] if state == "CLOSED" else []
                return _Result(stdout=json.dumps(
                    {"state": state, "closedByPullRequestsReferences": refs}
                ))
            return _Result(stdout=json.dumps(
                {"body": "<!-- specfuse:triage category=bug confidence=high -->"}
            ))
        if args[:3] == ["gh", "pr", "view"]:
            return _Result(stdout=json.dumps(
                {"files": [{"path": "tests/test_x.py", "additions": 5, "deletions": 0}]}
            ))
        if args[:3] == ["gh", "pr", "checks"]:
            return _Result(stdout=json.dumps([{"bucket": "pass", "name": "ci"}]))
        if args[:3] in (["gh", "pr", "merge"], ["gh", "pr", "edit"], ["gh", "pr", "close"]):
            return _Result()
        if args[:3] == ["gh", "pr", "list"]:
            return _Result(stdout="[]")
        if args[:3] == ["gh", "api", "graphql"] or args[:2] == ["gh", "search"]:
            return _Result(stdout="[]")
        if args[:2] == ["claude", "-p"]:
            return _Result(stdout=_SESSION)
        return _Result(stdout="[]")

    def matching(self, prefix):
        return [c for c in self.calls if c[: len(prefix)] == prefix]


def _run(runner, automerge="on"):
    return run_bug_lane(
        runner, _REPO, _ISSUE, ci_deadline_seconds=0, policy_path=_policy(automerge),
    )


class TestSupersededWhileTheItemRan(unittest.TestCase):
    def test_issue_closed_during_ci_wait_is_superseded_not_escalated(self):
        # Open when the PR is found, closed by the time CI has concluded.
        runner = _Runner(states=["OPEN", "CLOSED"])

        result = _run(runner, automerge="off")

        self.assertEqual(result.outcome, OUTCOME_SUPERSEDED)
        self.assertEqual(result.pr_number, _OWN_PR)

    def test_issue_closed_during_ci_wait_is_never_merged(self):
        runner = _Runner(states=["OPEN", "CLOSED"])

        _run(runner, automerge="on")

        self.assertEqual(runner.matching(["gh", "pr", "merge"]), [])

    def test_own_pr_is_closed_naming_the_pr_that_closed_the_issue(self):
        runner = _Runner(states=["CLOSED"])

        _run(runner)

        closes = runner.matching(["gh", "pr", "close", str(_OWN_PR)])
        self.assertEqual(len(closes), 1)
        self.assertIn(f"#{_OTHER_PR}", " ".join(closes[0]))

    def test_issue_already_closed_when_pr_is_found_skips_the_ci_wait(self):
        runner = _Runner(states=["CLOSED"])

        result = _run(runner)

        self.assertEqual(result.outcome, OUTCOME_SUPERSEDED)
        self.assertEqual(runner.matching(["gh", "pr", "checks"]), [])

    def test_issue_closed_by_hand_is_still_superseded(self):
        runner = _Runner(states=["CLOSED"], closed_by=())

        result = _run(runner)

        self.assertEqual(result.outcome, OUTCOME_SUPERSEDED)
        self.assertEqual(len(runner.matching(["gh", "pr", "close"])), 1)

    def test_issue_closed_by_the_lanes_own_pr_is_not_superseded(self):
        runner = _Runner(states=["CLOSED"], closed_by=(_OWN_PR,))

        result = _run(runner)

        self.assertNotEqual(result.outcome, OUTCOME_SUPERSEDED)
        self.assertEqual(runner.matching(["gh", "pr", "close"]), [])

    def test_open_issue_merges_as_before(self):
        runner = _Runner(states=["OPEN"])

        result = _run(runner)

        self.assertNotEqual(result.outcome, OUTCOME_SUPERSEDED)
        self.assertEqual(len(runner.matching(["gh", "pr", "merge"])), 1)


class TestUnreadableIssueStateFailsOpen(unittest.TestCase):
    def test_state_read_failure_keeps_the_existing_flow(self):
        runner = _Runner(states=["OPEN"])
        original = runner.__call__

        def failing(args, check=False, **kwargs):
            if args[:3] == ["gh", "issue", "view"] and "state" in args[args.index("--json") + 1]:
                runner.calls.append(list(args))
                return _Result(returncode=1, stderr="HTTP 502\n")
            return original(args, check=check, **kwargs)

        result = run_bug_lane(
            failing, _REPO, _ISSUE, ci_deadline_seconds=0, policy_path=_policy("on"),
        )

        self.assertNotEqual(result.outcome, OUTCOME_SUPERSEDED)
        self.assertEqual(len(runner.matching(["gh", "pr", "merge"])), 1)


class TestProviderReportsSupersededAsDone(unittest.TestCase):
    def test_superseded_item_completes_without_an_escalation(self):
        provider = BugsProvider(
            repo=_REPO, runner=_Runner(states=["CLOSED"]), policy_path=_policy("off"),
        )

        outcome = provider.execute(ActionItem(item_id=f"bug-{_ISSUE}", kind=KIND_BUG))

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)
        self.assertIn(f"#{_OTHER_PR}", outcome.detail)


if __name__ == "__main__":
    unittest.main()
