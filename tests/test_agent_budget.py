# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.agent.budget (FEAT-2026-0049/T03).

Covers: a cap is checked only at item boundaries and never mid-item, each
of the three caps independently stops the run, absent caps are unbounded,
`max_items=0` is distinguished from unset, and the PAUSE marker stops the
run with its own distinct, machine-readable reason.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.budget import (
    STOP_CAP,
    STOP_DRAINED,
    STOP_ERROR,
    STOP_PAUSE,
    RunBudget,
)


class _FakeClock:
    """A clock the test moves by hand — no sleeping, no wall-clock flake."""

    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class TestRunBudget(unittest.TestCase):

    def test_cap_is_not_checked_mid_item(self):
        """An item already in flight is never disturbed by a cap firing
        while it runs — the predicate is consulted only at boundaries."""
        clock = _FakeClock()
        budget = RunBudget(clock=clock, max_minutes=1)

        # Item starts while under budget.
        self.assertTrue(budget.may_start_next_item())
        budget.record_item_started()

        # Time passes *during* the item — well past the cap. The item in
        # flight has no way to be interrupted by this: there is no method
        # on RunBudget that aborts, cancels, or signals a running item.
        clock.advance(120)
        self.assertFalse(hasattr(budget, "abort_current_item"))
        self.assertFalse(hasattr(budget, "cancel"))

        # Only once the item finishes and the boundary is reached does the
        # cap become visible, blocking the *next* item.
        self.assertFalse(budget.may_start_next_item())
        # The item that already started was recorded, not rolled back.
        self.assertEqual(budget.items_started, 1)

    def test_max_minutes_stops_next_item(self):
        clock = _FakeClock()
        budget = RunBudget(clock=clock, max_minutes=5)

        budget.record_item_started()
        self.assertTrue(budget.may_start_next_item())

        clock.advance(5 * 60)
        self.assertFalse(budget.may_start_next_item())
        self.assertEqual(budget.items_started, 1)

    def test_max_tokens_stops_next_item(self):
        clock = _FakeClock()
        budget = RunBudget(clock=clock, max_tokens=1000)

        budget.record_item_started()
        budget.record_tokens(999)
        self.assertTrue(budget.may_start_next_item())

        budget.record_tokens(1)
        self.assertFalse(budget.may_start_next_item())
        self.assertEqual(budget.items_started, 1)

    def test_max_items_stops_next_item(self):
        clock = _FakeClock()
        budget = RunBudget(clock=clock, max_items=1)

        self.assertTrue(budget.may_start_next_item())
        budget.record_item_started()

        self.assertFalse(budget.may_start_next_item())
        self.assertEqual(budget.items_started, 1)

    def test_absent_caps_are_unbounded(self):
        clock = _FakeClock()
        budget = RunBudget(clock=clock)

        for _ in range(50):
            self.assertTrue(budget.may_start_next_item())
            budget.record_item_started()
        budget.record_tokens(10 ** 9)
        clock.advance(10 ** 9)

        self.assertTrue(budget.may_start_next_item())

    def test_max_items_zero_is_not_conflated_with_unset(self):
        clock = _FakeClock()

        unset = RunBudget(clock=clock)
        self.assertTrue(unset.may_start_next_item())

        zero = RunBudget(clock=clock, max_items=0)
        self.assertFalse(zero.may_start_next_item())

    def test_pause_marker_stops_at_next_boundary_with_distinct_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / ".agent.pause"
            clock = _FakeClock()
            budget = RunBudget(clock=clock, pause_marker=marker)

            self.assertFalse(budget.pause_requested())
            budget.record_item_started()

            marker.write_text("")
            self.assertTrue(budget.pause_requested())
            # A cap did not fire — the run stopped for a different, equally
            # distinct reason. Caller-side stop-reason selection uses these
            # two independent predicates to pick STOP_PAUSE over STOP_CAP.
            self.assertTrue(budget.may_start_next_item())

    def test_stop_reasons_are_distinct(self):
        reasons = {STOP_DRAINED, STOP_CAP, STOP_PAUSE, STOP_ERROR}
        self.assertEqual(len(reasons), 4)
        for reason in reasons:
            self.assertIsInstance(reason, str)


if __name__ == "__main__":
    unittest.main()
