# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A pending CI run declines as `ci_pending`, never `ci_not_green` (#3177,
FEAT-2026-0108/T04).

Seven escalations in the 2026-09-02 run said `ci_not_green` about a PR whose
build was still queued; all seven went green minutes later and were merged
by hand. `pr_ci_conclusion` used to fold "still pending at the deadline"
into the same `_CI_UNKNOWN` spelling as "genuinely unreadable", so
`evaluate_merge_guardrails` could not tell the two apart and declined both as
`ci_not_green`. It now returns the public string `"pending"` at the
deadline, and the guardrail gives that its own reason and label.
"""

from __future__ import annotations

import json
import tempfile
import unittest

from specfuse.loop.agent_policy import bug_lane_ci_wait_seconds
from specfuse.loop.bug_lane import DECLINE_LABELS, REASON_CI_NOT_GREEN, REASON_CI_PENDING
from specfuse.loop.bug_lane_run import OUTCOME_DECLINED, run_bug_lane

_REPO = "acme-widget/example"
_ISSUE_NUMBER = 7
_PR_NUMBER = 21


def _policy_yaml(automerge: str = "on", ci_wait_minutes: int | None = None) -> str:
    extra = f"\n  ci_wait_minutes: {ci_wait_minutes}" if ci_wait_minutes is not None else ""
    return f"""
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
  max_items_per_day: 1{extra}
escalation:
  webhook_env: x
  assignee: x
  quiet_hours: x
  sla_hours: 1
"""


def _dump(policy_yaml: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8")
    handle.write(policy_yaml)
    handle.close()
    return handle.name


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _StubRunner:
    """Minimal fake `gh`/`claude` runner -- fixes this issue, opens a PR whose
    checks are given by *checks*."""

    def __init__(self, *, checks):
        self.calls: list[list[str]] = []
        self._checks = checks
        self._pr_body = f"Fixes it.\n\ncloses #{_ISSUE_NUMBER}\n"
        self._pr_files = [{"path": "tests/test_thing.py", "additions": 10, "deletions": 0}]
        self._issue_body = "<!-- specfuse:triage category=bug confidence=high -->\nRepro steps."

    def __call__(self, args, check=True):
        self.calls.append(list(args))
        if args[:3] == ["gh", "issue", "view"]:
            return _Result(stdout=json.dumps({"body": self._issue_body}))
        if args[:3] == ["gh", "pr", "list"]:
            return _Result(stdout=json.dumps([{"number": _PR_NUMBER, "body": self._pr_body}]))
        if args[:3] == ["gh", "pr", "view"]:
            return _Result(stdout=json.dumps({"files": self._pr_files}))
        if args[:3] == ["gh", "pr", "checks"]:
            return _Result(stdout=json.dumps(self._checks))
        if args[:3] == ["gh", "pr", "edit"]:
            return _Result(stdout="")
        if args[:2] == ["claude", "-p"]:
            return _Result(stdout="completed")
        raise AssertionError(f"unexpected call: {args}")

    def calls_matching(self, prefix):
        return [c for c in self.calls if c[: len(prefix)] == prefix]


class TestPendingCiDeclinesAsCiPending(unittest.TestCase):
    def test_pending_at_deadline_declines_ci_pending(self):
        runner = _StubRunner(checks=[{"bucket": "pending"}])
        result = run_bug_lane(
            runner, _REPO, _ISSUE_NUMBER,
            ci_deadline_seconds=0, policy_path=_dump(_policy_yaml("on")),
        )

        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertEqual(result.reason, REASON_CI_PENDING)
        self.assertEqual(REASON_CI_PENDING, "ci_pending")

        label_calls = runner.calls_matching(["gh", "pr", "edit"])
        self.assertTrue(label_calls, "expected the PR to be labelled")
        self.assertIn(DECLINE_LABELS[REASON_CI_PENDING], label_calls[0])
        self.assertIn("bug-lane:ci-pending", label_calls[0])

    def test_red_run_still_declines_ci_not_green(self):
        runner = _StubRunner(checks=[{"bucket": "fail"}])
        result = run_bug_lane(
            runner, _REPO, _ISSUE_NUMBER,
            ci_deadline_seconds=0, policy_path=_dump(_policy_yaml("on")),
        )

        self.assertEqual(result.outcome, OUTCOME_DECLINED)
        self.assertEqual(result.reason, REASON_CI_NOT_GREEN)

        label_calls = runner.calls_matching(["gh", "pr", "edit"])
        self.assertTrue(label_calls)
        self.assertIn(DECLINE_LABELS[REASON_CI_NOT_GREEN], label_calls[0])


class TestCiWaitFromPolicy(unittest.TestCase):
    def test_ci_wait_comes_from_policy(self):
        path = _dump(_policy_yaml("on", ci_wait_minutes=12))
        self.assertEqual(bug_lane_ci_wait_seconds(path), 720)

    def test_default_ci_wait_when_key_absent(self):
        path = _dump(_policy_yaml("on"))
        self.assertEqual(bug_lane_ci_wait_seconds(path), 600)

    def test_missing_policy_file_falls_back_to_default(self):
        self.assertEqual(bug_lane_ci_wait_seconds("/nonexistent/agent-policy.yml"), 600)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
