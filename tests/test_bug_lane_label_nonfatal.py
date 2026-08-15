#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A failed guardrail-label write must not destroy the item — issue #1785.

`run_bug_lane` wrote its declining reason as a PR label with `check=True`, so a
label that is registered but not created on the repository raised
`CalledProcessError` out of the lane. On a live run that discarded 29.8 minutes
of correct work — a test-first fix and a mergeable PR — and replaced the
guardrail verdict with an exception repr, so the operator learned that a `gh`
command failed and never learned *why the lane declined to merge*.

Eight of `LABEL_REGISTRY`'s twenty-one labels were absent from the repository at
the time. The registry was complete; nothing had ever provisioned them.

`apply_triage` already treats the same condition as best-effort — it records
`label_written: False` and continues (`triage.py:184`). These tests hold the bug
lane to that same contract, so one registry cannot mean two opposite things.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop import bug_lane_run
from specfuse.loop.bug_lane import DECLINE_LABELS, REASON_CI_NOT_GREEN


def _ok(stdout=""):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def _fail(stderr="label not found"):
    return SimpleNamespace(returncode=1, stdout="", stderr=stderr)


class _LabelRunner:
    """Answers the lane's `gh` calls; `--add-label` fails per *fail_times*."""

    def __init__(self, fail_times: int = 99, provision_creates: bool = False):
        self.calls: list[list] = []
        self._fail_times = fail_times
        self._add_label_seen = 0
        self._provision_creates = provision_creates

    def __call__(self, args, check=False, cwd=None):
        self.calls.append(list(args))

        if "--add-label" in args:
            self._add_label_seen += 1
            if self._add_label_seen <= self._fail_times:
                if check:
                    import subprocess
                    raise subprocess.CalledProcessError(1, args)
                return _fail()
            return _ok()

        if args[:3] == ["gh", "label", "list"]:
            return _ok(json.dumps([]))
        if args[:3] == ["gh", "label", "create"]:
            return _ok() if self._provision_creates else _fail()
        return _ok()

    def add_label_calls(self):
        return [c for c in self.calls if "--add-label" in c]


class TestAddLabelIsBestEffort(unittest.TestCase):

    def test_a_failing_label_write_does_not_raise(self):
        """The bug: this raised CalledProcessError and killed the item."""
        runner = _LabelRunner(fail_times=99)
        ok = bug_lane_run.add_guardrail_label(
            runner, "acme/widget", 1784, DECLINE_LABELS[REASON_CI_NOT_GREEN],
        )
        self.assertFalse(ok)

    def test_it_retries_once_after_provisioning(self):
        """A missing label is created on demand, then the write retried."""
        runner = _LabelRunner(fail_times=1, provision_creates=True)
        ok = bug_lane_run.add_guardrail_label(
            runner, "acme/widget", 1784, DECLINE_LABELS[REASON_CI_NOT_GREEN],
        )
        self.assertTrue(ok)
        self.assertEqual(len(runner.add_label_calls()), 2, "did not retry")

    def test_a_succeeding_write_costs_one_call(self):
        runner = _LabelRunner(fail_times=0)
        ok = bug_lane_run.add_guardrail_label(
            runner, "acme/widget", 1784, DECLINE_LABELS[REASON_CI_NOT_GREEN],
        )
        self.assertTrue(ok)
        self.assertEqual(len(runner.add_label_calls()), 1, "retried unnecessarily")

    def test_a_raising_runner_is_survived(self):
        class _Boom:
            def __call__(self, args, check=False, cwd=None):
                raise OSError("gh exploded")

        self.assertFalse(
            bug_lane_run.add_guardrail_label(
                _Boom(), "acme/widget", 1, DECLINE_LABELS[REASON_CI_NOT_GREEN],
            )
        )

    def test_the_public_label_name_is_used_never_the_reason_constant(self):
        """Regression guard for #1420, which this fix must not undo."""
        runner = _LabelRunner(fail_times=0)
        bug_lane_run.add_guardrail_label(
            runner, "acme/widget", 1, DECLINE_LABELS[REASON_CI_NOT_GREEN],
        )
        argv = runner.add_label_calls()[0]
        self.assertIn("bug-lane:ci-not-green", argv)
        self.assertNotIn(REASON_CI_NOT_GREEN, argv)


class TestResultRecordsTheLabelOutcome(unittest.TestCase):
    """The guardrail verdict must survive even when the label does not."""

    def test_result_carries_label_written(self):
        result = bug_lane_run.BugLaneResult(
            outcome=bug_lane_run.OUTCOME_DECLINED,
            reason=REASON_CI_NOT_GREEN,
            pr_number=1784,
            label_written=False,
        )
        self.assertFalse(result.label_written)
        self.assertEqual(result.reason, REASON_CI_NOT_GREEN)

    def test_label_written_defaults_true_for_existing_callers(self):
        result = bug_lane_run.BugLaneResult(
            outcome=bug_lane_run.OUTCOME_MERGED, reason="eligible", pr_number=1,
        )
        self.assertTrue(result.label_written)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
