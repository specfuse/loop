# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A PR with no check runs is pending, never `ci_not_green` (#3445).

`_read_ci_conclusion_once` already promised that "no check registered yet"
reads as pending -- but only for an empty JSON list, which `gh` never prints.
On a PR with no check runs, `gh pr checks --json` writes nothing to stdout,
prints `no checks reported on the '<branch>' branch` to stderr and exits 1.
Empty stdout fell through to `_CI_UNKNOWN`, which the guardrail declines as
`ci_not_green`: six bug-lane PRs on 2026-10-08 were reported red with zero
check runs (they conflicted with `main`, so GitHub never ran CI on them).
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.bug_lane import REASON_CI_NOT_GREEN, evaluate_merge_guardrails
from specfuse.loop.bug_lane_run import pr_ci_conclusion

_NO_CHECKS = SimpleNamespace(
    returncode=1,
    stdout="",
    stderr="no checks reported on the 'fix/issue-2354-dart-enum' branch\n",
)


def _runner(*responses):
    queue = list(responses)

    def run(argv, check=False):
        return queue.pop(0) if len(queue) > 1 else queue[0]

    return run


def _clock(step: float):
    now = [0.0]

    def tick():
        now[0] += step
        return now[0]

    return tick


class TestNoChecksIsPending(unittest.TestCase):
    def test_no_checks_until_deadline_is_pending_not_unknown(self):
        conclusion = pr_ci_conclusion(
            _runner(_NO_CHECKS), "o/r", 2354,
            sleep=lambda _s: None, clock=_clock(60.0), deadline_seconds=120.0,
        )

        self.assertEqual(conclusion, "pending")

    def test_no_checks_then_green_is_success(self):
        green = SimpleNamespace(
            returncode=0,
            stdout=json.dumps([{"bucket": "pass", "name": "ci", "state": "SUCCESS"}]),
            stderr="",
        )
        conclusion = pr_ci_conclusion(
            _runner(_NO_CHECKS, green), "o/r", 2354,
            sleep=lambda _s: None, clock=_clock(1.0), deadline_seconds=600.0,
        )

        self.assertEqual(conclusion, "success")

    def test_no_checks_is_not_declined_as_ci_not_green(self):
        conclusion = pr_ci_conclusion(
            _runner(_NO_CHECKS), "o/r", 2354,
            sleep=lambda _s: None, clock=_clock(60.0), deadline_seconds=120.0,
        )
        decision = evaluate_merge_guardrails(
            changed_files=["tests/test_thing.py", "specfuse/other/thing.py"],
            ci_conclusion=conclusion,
            diff_lines=10,
            max_diff_lines=500,
            provenance={"kind": "triaged_issue", "ref": "issue-123"},
            max_merges_per_day=5,
            state_reader=SimpleNamespace(merges_last_24h=lambda: 0),
        )

        self.assertNotEqual(decision.reason, REASON_CI_NOT_GREEN)

    def test_other_empty_stdout_failure_still_fails_closed(self):
        broken = SimpleNamespace(returncode=1, stdout="", stderr="HTTP 502: Bad Gateway\n")
        conclusion = pr_ci_conclusion(
            _runner(broken), "o/r", 2354,
            sleep=lambda _s: None, clock=_clock(60.0), deadline_seconds=120.0,
        )

        self.assertNotIn(conclusion, ("success", "pending"))


if __name__ == "__main__":
    unittest.main()
