#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The bug lane waits for a terminal CI conclusion — issue #1786.

FIXTURES CORRECTED under #1826: these originally emitted a `conclusion`
field that `gh pr checks` has never had, so they agreed with the code and
both disagreed with reality. They now emit gh's real `bucket` shape.

`pr_ci_conclusion` issued exactly one `gh pr checks` and was called moments
after `/fix-bug` opened the PR (`bug_lane_run.py:310` then `:315`). A PR seconds
old always has queued or in-progress checks, so the read was `unknown`, the
guardrails failed closed, and the lane declined. Two consequences on a live run:
`rules.bugs.automerge` could never fire, and PR #1784 — green and mergeable —
was labelled `bug-lane:ci-not-green`.

Each piece was individually right; the fail-closed contract is correct. The
timing was the defect: the one read happened at the one moment a pending
conclusion is guaranteed rather than exceptional.

`sleep` and `clock` are injected so these tests neither sleep nor depend on wall
time.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.bug_lane_run import pr_ci_conclusion


#: Maps this module's shorthand onto the REAL `gh pr checks` row shape.
#: These fixtures originally emitted `{"conclusion": ...}`, a field `gh pr
#: checks` does not have — the assumption that hid #1826 for the whole life of
#: the bug. `bucket` is what gh actually returns.
_BUCKET_FOR = {"": "pending", "SUCCESS": "pass", "FAILURE": "fail"}


def _rows(*conclusions):
    return SimpleNamespace(
        returncode=0,
        stdout=json.dumps([
            {"bucket": _BUCKET_FOR.get(c, c.lower()), "name": f"c{i}", "state": c or "PENDING"}
            for i, c in enumerate(conclusions)
        ]),
        stderr="",
    )


class _ScriptedRunner:
    """Replays a sequence of results, one per call, repeating the last."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = 0

    def __call__(self, args, check=False):
        self.calls += 1
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


class _FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _sleeper(clock):
    def _sleep(seconds):
        clock.now += seconds
    return _sleep


class TestWaitsForTerminalConclusion(unittest.TestCase):

    def test_pending_then_success_reads_success(self):
        """The bug: the first read is always pending on a fresh PR."""
        clock = _FakeClock()
        runner = _ScriptedRunner([
            _rows("", ""),                   # queued — what the lane used to see
            _rows("", "SUCCESS"),            # partially done
            _rows("SUCCESS", "SUCCESS"),     # terminal
        ])
        result = pr_ci_conclusion(
            runner, "acme/widget", 1784,
            sleep=_sleeper(clock), clock=clock,
        )
        self.assertEqual(result.lower(), "success")
        self.assertGreater(runner.calls, 1, "did not poll")

    def test_pending_then_failure_reads_failure(self):
        clock = _FakeClock()
        runner = _ScriptedRunner([
            _rows("", ""),
            _rows("FAILURE", "SUCCESS"),
        ])
        result = pr_ci_conclusion(
            runner, "acme/widget", 1, sleep=_sleeper(clock), clock=clock,
        )
        self.assertNotEqual(result.lower(), "success")

    def test_already_terminal_does_not_poll(self):
        """A settled PR costs exactly one call — no added latency."""
        clock = _FakeClock()
        runner = _ScriptedRunner([_rows("SUCCESS", "SUCCESS")])
        result = pr_ci_conclusion(
            runner, "acme/widget", 1, sleep=_sleeper(clock), clock=clock,
        )
        self.assertEqual(result.lower(), "success")
        self.assertEqual(runner.calls, 1)

    def test_never_pending_stops_at_the_deadline(self):
        """Bounded: checks that never settle must not hang the lane."""
        clock = _FakeClock()
        runner = _ScriptedRunner([_rows("", "")])
        result = pr_ci_conclusion(
            runner, "acme/widget", 1,
            sleep=_sleeper(clock), clock=clock, deadline_seconds=30,
        )
        self.assertEqual(result, "unknown")
        self.assertLessEqual(clock.now, 60, "waited well past the deadline")


class TestFailClosedContractPreserved(unittest.TestCase):
    """Not weakened: every existing unreadable case still yields `unknown`."""

    def _once(self, result):
        clock = _FakeClock()
        return pr_ci_conclusion(
            _ScriptedRunner([result]), "acme/widget", 1,
            sleep=_sleeper(clock), clock=clock, deadline_seconds=0,
        )

    def test_non_zero_exit_is_unknown(self):
        self.assertEqual(
            self._once(SimpleNamespace(returncode=1, stdout="", stderr="boom")),
            "unknown",
        )

    def test_unparseable_output_is_unknown(self):
        self.assertEqual(
            self._once(SimpleNamespace(returncode=0, stdout="not json", stderr="")),
            "unknown",
        )

    def test_empty_row_list_is_unknown(self):
        self.assertEqual(
            self._once(SimpleNamespace(returncode=0, stdout="[]", stderr="")),
            "unknown",
        )

    def test_mixed_terminal_conclusions_is_not_success(self):
        """Corrected with #1826: a pass alongside a fail is a legible FAILING
        verdict, not an unreadable one. It was only `unknown` while the
        conclusion field this asserted on did not exist."""
        self.assertNotEqual(self._once(_rows("SUCCESS", "FAILURE")), "success")

    def test_raising_runner_is_unknown(self):
        class _Boom:
            def __call__(self, args, check=False):
                raise OSError("gh exploded")

        clock = _FakeClock()
        self.assertEqual(
            pr_ci_conclusion(
                _Boom(), "acme/widget", 1,
                sleep=_sleeper(clock), clock=clock, deadline_seconds=0,
            ),
            "unknown",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
