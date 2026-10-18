# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The bug lane reports what its `/fix-bug` session spent (#3419).

`run_bug_lane` launched the session with a plain `claude -p` call, so its
usage envelope was never asked for, and `BugsProvider` hard-coded `spend=0`
on every outcome. `tokens spent` in the run summary counted triage alone
(805 over a run with five 15-18 minute `/fix-bug` sessions), and
`max_tokens` -- the operator's cost ceiling -- never bounded the lane that
spends.

The session now runs with `--output-format json`; its text is the envelope's
`result`, read exactly as before, and its usage reaches `ActionOutcome.spend`
through the same `usage_spend` the triage provider uses.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import KIND_BUG, STATUS_COMPLETED, STATUS_ESCALATED, ActionItem

_REPO = "o/r"
_ISSUE = 2115
_PR = 2120

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


def _policy(automerge):
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8")
    handle.write(_POLICY.format(automerge=automerge))
    handle.close()
    return handle.name


def _envelope(text, input_tokens=1200, output_tokens=300, cache_read=50000):
    return json.dumps({
        "type": "result",
        "result": text,
        "total_cost_usd": 0.42,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
        },
    })


class _Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _Runner:
    def __init__(self, session_text, *, raise_timeout=False):
        self.calls = []
        self._text = session_text
        self._raise_timeout = raise_timeout

    def __call__(self, argv, check=False, **_kwargs):
        self.calls.append(list(argv))
        if argv[:1] == ["claude"]:
            if self._raise_timeout:
                raise subprocess.TimeoutExpired(argv, 1)
            if "--output-format" in argv:
                return _Result(stdout=_envelope(self._text))
            return _Result(stdout=self._text)
        if argv[:3] == ["gh", "issue", "view"]:
            fields = argv[argv.index("--json") + 1]
            if "state" in fields:
                return _Result(stdout=json.dumps({"state": "OPEN"}))
            return _Result(stdout=json.dumps(
                {"body": "<!-- specfuse:triage category=bug confidence=high -->"}))
        if argv[:3] == ["gh", "pr", "view"]:
            return _Result(stdout=json.dumps(
                {"files": [{"path": "tests/test_x.py", "additions": 5, "deletions": 0}]}))
        if argv[:3] == ["gh", "pr", "checks"]:
            return _Result(stdout=json.dumps([{"bucket": "pass", "name": "ci"}]))
        return _Result(stdout="[]")


def _execute(runner, automerge="off"):
    provider = BugsProvider(repo=_REPO, runner=runner, policy_path=_policy(automerge))
    return provider.execute(ActionItem(item_id=f"bug-{_ISSUE}", kind=KIND_BUG))


_COMPLETED = f"```result\nstatus: completed\npr_number: {_PR}\n```\n"
_REFUSED = "```result\nstatus: refused\nreason: feature-scoped, 4 files\n```\n"


class TestBugLaneSpendIsReported(unittest.TestCase):
    def test_session_is_asked_for_its_usage_envelope(self):
        runner = _Runner(_COMPLETED)

        _execute(runner)

        claude = [c for c in runner.calls if c[:1] == ["claude"]]
        self.assertEqual(len(claude), 1)
        self.assertIn("--output-format", claude[0])
        self.assertEqual(claude[0][claude[0].index("--output-format") + 1], "json")

    def test_merged_item_reports_all_usage_tokens(self):
        outcome = _execute(_Runner(_COMPLETED), automerge="on")

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertEqual(outcome.spend, 51500)  # cache reads count too (#3522)

    def test_escalated_item_reports_its_spend_too(self):
        outcome = _execute(_Runner(_REFUSED))

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.spend, 51500)

    def test_envelope_text_is_read_as_the_session_output(self):
        # The outcome and PR number come from the envelope's `result`.
        outcome = _execute(_Runner(_COMPLETED), automerge="off")

        self.assertIn(f"PR #{_PR}", outcome.escalation.decision_needed
                      + outcome.escalation.recommendation
                      + outcome.escalation.done_so_far)

    def test_timeout_still_escalates_as_timed_out(self):
        outcome = _execute(_Runner(_COMPLETED, raise_timeout=True))

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn("timed out", outcome.detail)


if __name__ == "__main__":
    unittest.main()
