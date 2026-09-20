# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`rules.bugs.required_checks` — the lane states what green it requires (#3373).

`automerge` merged a PR that left `main` red for an hour. All six guardrails
passed and `ci_conclusion` was `success`, because that repository's PR job is
deliberately a fast lane excluding the `regression` group — and both tests the
fix broke carry `@Tag("regression")`. The check the lane read **could not
fail** on that class of defect.

The nightly's own header states the assumption the split rests on: *"every
change had already passed it in the loop's `code` gate before its PR was
opened"*. True for driver work-unit PRs. **Not** true for bug-lane PRs, where a
headless session chooses which tests to run and reports the ones it chose.
"""

from __future__ import annotations

import json
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from specfuse.loop.agent_policy import resolve_required_checks
from specfuse.loop.bug_lane_run import pr_ci_conclusion

_BASE = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: medium
    automerge: "on"
{extra}  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 100000
  max_open_prs: 5
  max_items_per_day: 10
escalation:
  provider: none
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
  silence_hours: 24
"""


def _runner_for(rows):
    def runner(argv, check=False):
        if argv[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return runner


def _conclusion(rows, required=()):
    return pr_ci_conclusion(
        _runner_for(rows), "acme/widget", 7,
        sleep=lambda _s: None, clock=lambda: 0.0,
        deadline_seconds=0.0, poll_seconds=0.0,
        required_checks=required,
    )


class ResolvingTheKey(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write(self, extra: str = "") -> str:
        p = Path(self._tmp.name) / "agent-policy.yml"
        p.write_text(_BASE.format(extra=extra), encoding="utf-8")
        return str(p)

    def test_absent_key_requires_nothing(self):
        self.assertEqual(resolve_required_checks(self._write()), ())

    def test_a_declared_list_resolves(self):
        block = textwrap.indent("required_checks:\n  - full-suite\n  - nightly\n", "    ")
        self.assertEqual(resolve_required_checks(self._write(block)), ("full-suite", "nightly"))

    def test_a_string_is_the_single_check_case(self):
        block = textwrap.indent("required_checks: full-suite\n", "    ")
        self.assertEqual(resolve_required_checks(self._write(block)), ("full-suite",))

    def test_a_malformed_value_requires_nothing_rather_than_blocking_everything(self):
        block = textwrap.indent("required_checks: 7\n", "    ")
        self.assertEqual(resolve_required_checks(self._write(block)), ())

    def test_a_missing_file_requires_nothing(self):
        self.assertEqual(resolve_required_checks("/nonexistent/agent-policy.yml"), ())


class TheGreenTheLaneReads(unittest.TestCase):

    def test_without_required_checks_behaviour_is_unchanged(self):
        rows = [{"bucket": "pass", "name": "build", "state": "SUCCESS"}]
        self.assertEqual(_conclusion(rows), "success")

    def test_a_required_check_that_passed_is_success(self):
        rows = [
            {"bucket": "pass", "name": "build", "state": "SUCCESS"},
            {"bucket": "pass", "name": "full-suite", "state": "SUCCESS"},
        ]
        self.assertEqual(_conclusion(rows, ("full-suite",)), "success")

    def test_a_required_check_that_never_ran_is_not_success(self):
        # THE MEASURED CASE: the PR job is green and the check that would have
        # caught the defect is not in the list at all.
        rows = [{"bucket": "pass", "name": "build", "state": "SUCCESS"}]
        got = _conclusion(rows, ("full-suite",))
        self.assertNotEqual(got, "success")
        self.assertIn("full-suite", got)

    def test_a_required_check_that_failed_is_not_success(self):
        rows = [
            {"bucket": "pass", "name": "build", "state": "SUCCESS"},
            {"bucket": "fail", "name": "full-suite", "state": "FAILURE"},
        ]
        self.assertNotEqual(_conclusion(rows, ("full-suite",)), "success")

    def test_a_required_check_that_was_skipped_is_not_success(self):
        # Skipping is not a failure in general, which is why _BUCKETS_OK
        # tolerates it — but a check an operator NAMED as required and that did
        # not run cannot establish what it was required to establish.
        rows = [
            {"bucket": "pass", "name": "build", "state": "SUCCESS"},
            {"bucket": "skipping", "name": "full-suite", "state": "SKIPPED"},
        ]
        got = _conclusion(rows, ("full-suite",))
        self.assertNotEqual(got, "success")
        self.assertIn("full-suite", got)


class TheDeclineIsStillADecline(unittest.TestCase):

    def test_a_non_success_conclusion_declines_the_merge(self):
        from specfuse.loop.bug_lane import REASON_CI_NOT_GREEN, evaluate_merge_guardrails

        decision = evaluate_merge_guardrails(
            changed_files=["src/a.py", "tests/test_a.py"],
            ci_conclusion="required check never ran: full-suite",
            diff_lines=10, max_diff_lines=400,
            provenance="issue", max_merges_per_day=3,
            state_reader=lambda: 0,
        )
        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason, REASON_CI_NOT_GREEN)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
