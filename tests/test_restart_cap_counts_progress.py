# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The driver-restart cap must count progress, not restarts (#2617).

`FeatureProvider._advance` states the rule in its own docstring -- "restart
me" is only progress if something changed -- and then increments its counter
on every restart halt without checking whether anything changed. A gate whose
work units each legitimately edit a driver module (complete, halt for a
reload, hand off to the next unit) is therefore escalated as a spin once the
third unit finishes, however much progress it made.

Observed on FEAT-2026-0058 (#2616). The `driver_staleness_detected` payloads
from that run -- the same detail the guard already receives -- recorded
progress at every step:

    wu=T01  remaining=[T02, T03]
    wu=T02  remaining=[T03]
    wu=T03  remaining=[G1-CLOSE]

Three different units, each completing, `remaining_wu_ids` shrinking
monotonically. The gate stalled one unit from its close and a human was asked
to choose between three options all premised on a spin that never happened.

The genuine spin -- one unit re-editing the driver on every attempt, halt
detail identical each time -- must still escalate, which is what
`test_restarts_are_bounded_and_then_escalate` in test_agent_driver_restart.py
pins and what the no-progress cases below re-pin from this angle.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.agent import driver_invoke
from specfuse.agent.driver_invoke import HALT_ADVANCED, HALT_DRIVER_RESTART
from specfuse.agent.providers.feature import FeatureProvider
from specfuse.agent.queue_read import DISPOSITION_WORKABLE
from specfuse.agent.run import STATUS_COMPLETED, STATUS_ESCALATED

_FEATURE = "FEAT-2026-0079"


def _restart(wu: str, remaining: list[str]) -> tuple:
    """A restart halt whose detail reports *wu* done and *remaining* left."""
    return (
        HALT_DRIVER_RESTART,
        {
            "gate": 1,
            "wu_id": f"{_FEATURE}/{wu}",
            "driver_paths": ["specfuse/loop/lint_plan.py"],
            "halted": True,
            "reason": "driver_restart_required",
            "remaining_wu_ids": [f"{_FEATURE}/{r}" for r in remaining],
            "resume_command": f"specfuse run --feature {_FEATURE}",
        },
    )


class _ScriptedDriver:
    """Replays one halt per call; repeats the last once the script runs out."""

    def __init__(self, halts):
        self._halts = list(halts)
        self.calls = 0

    def __call__(self, runner, feature_id, *, features_root, **kwargs):
        self.calls += 1
        halt = self._halts[min(self.calls - 1, len(self._halts) - 1)]
        return driver_invoke.HaltResult(
            halt_class=halt[0], detail=halt[1], argv=["specfuse", "run"]
        )


class _ProviderCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._real_advance = driver_invoke.advance_feature

    def tearDown(self):
        driver_invoke.advance_feature = self._real_advance
        self._tmp.cleanup()

    def _run(self, halts):
        driver_invoke.advance_feature = _ScriptedDriver(halts)
        provider = FeatureProvider(
            repo="acme-widget/example", features_root=Path(self._tmp.name)
        )
        item_id = f"feature-{_FEATURE}-g1"
        provider._rows = {
            item_id: {"disposition": DISPOSITION_WORKABLE, "feature_id": _FEATURE}
        }
        from specfuse.agent.run import ActionItem, KIND_FEATURE

        item = ActionItem(
            item_id=item_id, kind=KIND_FEATURE, summary=f"advance {_FEATURE}"
        )
        return provider.execute(item), driver_invoke.advance_feature


class TestProgressResetsTheCap(_ProviderCase):
    def test_the_real_feat_0058_sequence_does_not_escalate(self):
        # The regression itself, replayed from #2616's recorded payloads.
        outcome, _ = self._run([
            _restart("T01", ["T02", "T03"]),
            _restart("T02", ["T03"]),
            _restart("T03", ["G1-CLOSE"]),
            (HALT_ADVANCED, {"gate": 1}),
        ])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)

    def test_more_restarts_than_the_cap_are_fine_while_work_completes(self):
        # Five units, each editing the driver once -- well past a cap of 2.
        outcome, driver = self._run([
            _restart("T01", ["T02", "T03", "T04", "T05"]),
            _restart("T02", ["T03", "T04", "T05"]),
            _restart("T03", ["T04", "T05"]),
            _restart("T04", ["T05"]),
            _restart("T05", ["G1-CLOSE"]),
            (HALT_ADVANCED, {"gate": 1}),
        ])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertEqual(driver.calls, 6)

    def test_a_shrinking_remaining_list_counts_as_progress(self):
        # Same unit id twice but the gate advanced -- the list is the signal.
        outcome, _ = self._run([
            _restart("T01", ["T02", "T03"]),
            _restart("T01", ["T03"]),
            _restart("T01", ["G1-CLOSE"]),
            (HALT_ADVANCED, {"gate": 1}),
        ])

        self.assertEqual(outcome.status, STATUS_COMPLETED)


class TestAGenuineSpinStillEscalates(_ProviderCase):
    def test_an_identical_halt_repeating_escalates(self):
        # One unit re-editing the driver every attempt: nothing changes, so
        # the cap must still fire. This is the case the guard exists for.
        outcome, driver = self._run([_restart("T01", ["T02", "T03"])])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(driver.calls, 1 + FeatureProvider.MAX_DRIVER_RESTARTS)

    def test_progress_then_a_spin_still_escalates(self):
        # The reset must not buy unlimited credit: once work stops advancing,
        # the cap applies again from there.
        outcome, driver = self._run([
            _restart("T01", ["T02", "T03"]),
            _restart("T02", ["T03"]),
        ])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        # The second dispatch progressed, so the counter reset there; the cap
        # then needs its own worth of stalled dispatches from that point.
        self.assertEqual(driver.calls, 2 + FeatureProvider.MAX_DRIVER_RESTARTS)

    def test_an_empty_detail_still_counts_toward_the_cap(self):
        # `_find_restart_detail` returns {} when the halting event cannot be
        # re-read, and driver_invoke is explicit that such a run is still a
        # restart. With no evidence of progress the cap must keep applying,
        # or it becomes unreachable exactly when the driver is least legible.
        outcome, driver = self._run([(HALT_DRIVER_RESTART, {})])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(driver.calls, 1 + FeatureProvider.MAX_DRIVER_RESTARTS)

    def test_a_detail_with_no_remaining_list_still_counts(self):
        outcome, driver = self._run([
            (HALT_DRIVER_RESTART, {"wu_id": f"{_FEATURE}/T01", "halted": True}),
        ])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(driver.calls, 1 + FeatureProvider.MAX_DRIVER_RESTARTS)


if __name__ == "__main__":
    unittest.main()
