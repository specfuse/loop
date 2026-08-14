# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The conductor understands the driver's restart halt (#2321).

`_halt_for_driver_restart` exits 3 and deliberately flips no gate and no WU
status, so a fresh process resumes exactly where the halted one stopped.
`classify_halt` branched only on returncodes 2 and 1, so 3 fell through to
the `returncode == 0` block and — with no gate flipped — came out of the
final fallthrough as `HALT_AWAITING_REVIEW, None`. Observed 2026-08-14:
FEAT-2026-0079 halted for restart, the conductor escalated it as
`awaiting_review: None`, filed issue #2316, and then spent its next item
triaging that issue as a question, while the gate's remaining unit stayed
pending.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.agent import driver_invoke
from specfuse.agent.driver_invoke import (
    HALT_ADVANCED,
    HALT_DRIVER_ERROR,
    HALT_DRIVER_RESTART,
    FeatureState,
    classify_halt,
)
from specfuse.agent.providers.feature import FeatureProvider
from specfuse.agent.queue_read import DISPOSITION_WORKABLE
from specfuse.agent.run import STATUS_COMPLETED, STATUS_ESCALATED

_FEATURE = "FEAT-2026-0079"


def _state(plan_status="active", gates=None, event_count=0, feature_dir=None):
    return FeatureState(
        feature_dir=feature_dir,
        plan_status=plan_status,
        gates=gates if gates is not None else {1: "open"},
        event_count=event_count,
    )


def _staleness_event(halted=True):
    return {
        "event_type": "driver_staleness_detected",
        "correlation_id": f"{_FEATURE}/T01",
        "payload": {
            "gate": 1,
            "wu_id": f"{_FEATURE}/T01",
            "driver_paths": ["specfuse/loop/arm_eval.py"],
            "halted": halted,
            "reason": "driver_restart_required",
            "remaining_wu_ids": [f"{_FEATURE}/T02"],
            "resume_command": f"specfuse run --feature {_FEATURE}",
        },
    }


class ClassifyRestartTests(unittest.TestCase):
    def test_exit_three_is_a_restart_not_a_review_boundary(self):
        halt_class, detail = classify_halt(
            3, _state(), _state(), [_staleness_event()]
        )
        self.assertEqual(halt_class, HALT_DRIVER_RESTART)
        self.assertEqual(detail["wu_id"], f"{_FEATURE}/T01")
        self.assertEqual(detail["remaining_wu_ids"], [f"{_FEATURE}/T02"])
        self.assertEqual(detail["driver_paths"], ["specfuse/loop/arm_eval.py"])

    def test_exit_three_without_the_event_still_classifies(self):
        """The exit code is the contract; the event only enriches it. A run
        whose events.jsonl could not be re-read must not silently become a
        clean `awaiting_review` again."""
        halt_class, _ = classify_halt(3, _state(), _state(), [])
        self.assertEqual(halt_class, HALT_DRIVER_RESTART)

    def test_an_unrecognised_exit_code_is_an_error_not_a_success(self):
        """The bug's general shape: every unhandled non-zero code fell into
        the `returncode == 0` block."""
        halt_class, _ = classify_halt(7, _state(), _state(), [], "boom")
        self.assertEqual(halt_class, HALT_DRIVER_ERROR)

    def test_exit_zero_still_advances(self):
        before = _state(gates={1: "open", 2: "open"})
        after = _state(gates={1: "passed", 2: "open"})
        halt_class, _ = classify_halt(0, before, after, [])
        self.assertEqual(halt_class, HALT_ADVANCED)


class _ScriptedDriver:
    """Stands in for `driver_invoke.advance_feature`, replaying one halt per
    call and recording how many fresh dispatches it received."""

    def __init__(self, halts):
        self._halts = list(halts)
        self.calls = 0

    def __call__(self, runner, feature_id, *, features_root, **kwargs):
        self.calls += 1
        halt = self._halts[min(self.calls - 1, len(self._halts) - 1)]
        return driver_invoke.HaltResult(
            halt_class=halt[0], detail=halt[1], argv=["specfuse", "run"]
        )


def _restart_halt():
    return (HALT_DRIVER_RESTART, _staleness_event()["payload"])


class ProviderRestartTests(unittest.TestCase):
    """A restart is the driver asking for a fresh process, which is exactly
    what the next `advance_feature` is. Re-dispatching is the fix; escalating
    to a human is the fallback once the restarts stop being progress."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._real_advance = driver_invoke.advance_feature

    def tearDown(self):
        driver_invoke.advance_feature = self._real_advance
        self._tmp.cleanup()

    def _provider(self):
        provider = FeatureProvider(
            repo="acme-widget/example", features_root=Path(self._tmp.name)
        )
        item_id = f"feature-{_FEATURE}-g1"
        provider._rows = {
            item_id: {"disposition": DISPOSITION_WORKABLE, "feature_id": _FEATURE}
        }
        from specfuse.agent.run import ActionItem, KIND_FEATURE

        return provider, ActionItem(
            item_id=item_id, kind=KIND_FEATURE, summary=f"advance {_FEATURE}"
        )

    def test_a_restart_halt_re_dispatches_a_fresh_driver(self):
        driver = _ScriptedDriver(
            [_restart_halt(), (HALT_ADVANCED, {"gate": 1})]
        )
        driver_invoke.advance_feature = driver
        provider, item = self._provider()

        outcome = provider.execute(item)

        self.assertEqual(driver.calls, 2)
        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)

    def test_restarts_are_bounded_and_then_escalate(self):
        driver = _ScriptedDriver([_restart_halt()])
        driver_invoke.advance_feature = driver
        provider, item = self._provider()

        outcome = provider.execute(item)

        # One initial dispatch plus the cap's worth of restarts, and no more:
        # a unit that edits the driver on every attempt must not spin.
        self.assertEqual(driver.calls, 1 + FeatureProvider.MAX_DRIVER_RESTARTS)
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIsNotNone(outcome.escalation)
        self.assertIn("restart", outcome.detail)

    def test_the_escalation_names_the_unit_and_the_remaining_work(self):
        driver = _ScriptedDriver([_restart_halt()])
        driver_invoke.advance_feature = driver
        provider, item = self._provider()

        escalation = provider.execute(item).escalation

        blob = " ".join(
            [escalation.done_so_far, escalation.issue_summary, escalation.why_not_auto]
        )
        self.assertIn(f"{_FEATURE}/T01", blob)
        self.assertIn(f"{_FEATURE}/T02", blob)
        self.assertEqual(escalation.category, "blocked-wu")


if __name__ == "__main__":
    unittest.main()
