#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`escalation.assignee` is read from policy and empty means omit — issue #1762.

`emit_escalation` defaulted `assignee` to the literal `"specfuse-operator"`, a
placeholder assignable on no repository, and no caller passed the
`escalation.assignee` value the operator had already declared in
`.specfuse/agent-policy.yml`. On the first live `specfuse-agent run` the whole
`gh issue create` exited 1 on that flag, the escalation was never filed, and the
run still reported `items escalated: 1` — success on the outside, empty inbox on
the inside.

The existing tests injected an assignee, which is how a username valid nowhere
survived to a live run. These assert the *unconfigured* path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import agent_policy
from specfuse.loop import escalation


_POLICY = """version: 1
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "off"
  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: ""
  provider: none
  assignee: {assignee}
  quiet_hours: ""
  sla_hours: 24
"""


def _policy_file(tmp: str, assignee: str) -> str:
    p = Path(tmp) / "agent-policy.yml"
    p.write_text(_POLICY.format(assignee=assignee))
    return str(p)


class _RecordingRunner:
    """Captures argv and reports success, so no `gh` process is spawned."""

    def __init__(self, stdout: str = ""):
        self.calls: list[list] = []
        self._stdout = stdout

    def __call__(self, args, check=True):
        self.calls.append(list(args))

        class _R:
            returncode = 0
            stdout = self._stdout

        return _R()

    def create_argv(self):
        for call in self.calls:
            if "issue" in call and "create" in call:
                return call
        return None


class TestResolveEscalationAssignee(unittest.TestCase):

    def test_reads_a_configured_assignee(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _policy_file(tmp, "clabonte")
            self.assertEqual(
                agent_policy.resolve_escalation_assignee(path), "clabonte",
            )

    def test_empty_stays_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _policy_file(tmp, '""')
            self.assertEqual(agent_policy.resolve_escalation_assignee(path), "")

    def test_absent_policy_file_is_empty_not_a_placeholder(self):
        self.assertEqual(
            agent_policy.resolve_escalation_assignee("/nope/agent-policy.yml"), "",
        )


class TestEmitEscalationOmitsEmptyAssignee(unittest.TestCase):
    """The defect: an unassignable placeholder failed the whole create."""

    def _emit(self, runner, **kw):
        return escalation.emit_escalation(
            "FEAT-2026-9999/T01",
            category="blocked-wu",
            repo="acme/widget",
            done_so_far="ran a thing",
            issue_summary="a thing needs a human",
            decision_needed="pick one",
            why_not_auto="the agent cannot decide this",
            options=[
                ("Do X", "fast", "risky"),
                ("Do Y", "safe", "slow"),
            ],
            recommendation="Do Y",
            runner=runner,
            **kw,
        )

    def test_empty_assignee_omits_the_flag(self):
        runner = _RecordingRunner(stdout="https://github.com/acme/widget/issues/7")
        self._emit(runner, assignee="")
        argv = runner.create_argv()
        self.assertIsNotNone(argv, "no `gh issue create` was issued")
        self.assertNotIn("--assignee", argv)

    def test_configured_assignee_is_passed_through(self):
        runner = _RecordingRunner(stdout="https://github.com/acme/widget/issues/7")
        self._emit(runner, assignee="clabonte")
        argv = runner.create_argv()
        self.assertIn("--assignee", argv)
        self.assertIn("clabonte", argv)

    def test_default_no_longer_injects_a_placeholder_username(self):
        """With no assignee argument at all, nothing is assigned — a default
        that is invalid on every repository is not a safe default."""
        runner = _RecordingRunner(stdout="https://github.com/acme/widget/issues/7")
        self._emit(runner)
        argv = runner.create_argv()
        self.assertNotIn("--assignee", argv)
        self.assertNotIn("specfuse-operator", argv)

    def test_whitespace_only_assignee_is_treated_as_empty(self):
        runner = _RecordingRunner(stdout="https://github.com/acme/widget/issues/7")
        self._emit(runner, assignee="   ")
        argv = runner.create_argv()
        self.assertNotIn("--assignee", argv)

    def test_labels_are_still_applied(self):
        """Not weakened: the needs-human label is what the inbox greps for."""
        runner = _RecordingRunner(stdout="https://github.com/acme/widget/issues/7")
        self._emit(runner, assignee="")
        argv = runner.create_argv()
        self.assertIn(escalation.NEEDS_HUMAN_LABEL, argv)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
