#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A run that could not see the queue does not report `drained` (#3392).

When the snapshot's issue listing failed, `run_agent` reported the failure,
treated the listing as empty, found no candidates and stopped with `drained` —
exit 0, zero attempted, zero escalated.

Observed with nine dispatchable bugs in the queue, two of them deliberately
ranked first for that run:

    snapshot: 0 open issues, 0 open PRs, 115 features, queue=0
    snapshot: issues unreadable — gh issue list ... tls: failed to verify certificate
    run finished — drained after 0.00 minutes
    stop reason:      drained

`drained` means "worked through everything there was". Here it meant "could not
see anything". The two are opposite, and the summary — the part an operator
reads, and the only part automation parses — rendered them identically.

This is the shape this project keeps finding: **a failure reported in the
grammar of success.** An unattended runner is where it costs most; a scheduled
run reporting `drained` every night while its credentials are broken looks like
a quiet backlog.

Refusing rather than draining follows `STOP_DIRTY_TREE`'s precedent: nothing was
budgeted because nothing was dispatched, and every provider that matters reads
`snapshot.issues`, so a run without it can do nothing except mislead.
"""

from __future__ import annotations

import unittest

from specfuse.agent.run import (
    STOP_DRAINED,
    STOP_SNAPSHOT_UNREADABLE,
    _refuse_unreadable_snapshot,
    exit_code_for,
)


class _Snapshot:
    def __init__(self, issues_error=None, prs_error=None):
        self.issues_error = issues_error
        self.prs_error = prs_error


class TheRefusal(unittest.TestCase):

    def _refuse(self, reason="gh issue list exited 1: tls: failed to verify"):
        lines = []
        summary = _refuse_unreadable_snapshot(reason, report=lines.append)
        return summary, lines

    def test_it_does_not_report_drained(self):
        summary, _ = self._refuse()

        self.assertEqual(STOP_SNAPSHOT_UNREADABLE, summary.stop_reason)
        self.assertNotEqual(STOP_DRAINED, summary.stop_reason)

    def test_nothing_is_attempted_or_completed(self):
        summary, _ = self._refuse()

        self.assertEqual(0, summary.items_attempted)
        self.assertEqual(0, summary.items_completed)

    def test_it_escalates_so_the_summary_is_not_silent(self):
        summary, _ = self._refuse()

        self.assertEqual(1, summary.items_escalated)
        self.assertEqual(1, len(summary.escalations))

    def test_the_escalation_carries_which_listing_failed(self):
        summary, _ = self._refuse("gh issue list exited 1: tls: bad cert")

        self.assertIn("tls: bad cert", summary.escalations[0].reason)

    def test_it_says_so_on_the_way_out(self):
        _, lines = self._refuse()

        self.assertTrue(
            any("refused" in line for line in lines),
            f"the run must say it refused, not finish quietly: {lines}",
        )


class TheExitCode(unittest.TestCase):
    """A scheduled run's output must be self-describing without its log."""

    def test_a_blind_run_exits_non_zero(self):
        self.assertNotEqual(0, exit_code_for(STOP_SNAPSHOT_UNREADABLE))

    def test_a_genuinely_drained_run_still_exits_zero(self):
        self.assertEqual(0, exit_code_for(STOP_DRAINED))

    def test_an_unknown_reason_does_not_invent_a_failure(self):
        # Every other stop reason kept exit 0; this narrows to the one case
        # that is a refusal rather than an outcome.
        self.assertEqual(0, exit_code_for("some_future_reason"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
