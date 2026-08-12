# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""One broken provider loses itself, not the whole run.

`execute()` has always been wrapped — a provider failing there parks its item
and the run continues. The other two protocol calls were not. `advertise()`
runs every loop pass against every provider, so one raising ended the run and
took five healthy providers' work with it; `reconcile()` ran after the outcome
was already decided, so raising there discarded real work including any
escalation the outcome carried.

Not hypothetical. #1746 was exactly this: `FeatureProvider.advertise` raised
`AttributeError` on the default invocation, and every shipped behaviour of the
command became reachable only by passing `--features-root` explicitly. That
fix normalised the one cause and its own changelog entry recorded the gap as
still open. Six providers ship now.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import (
    KIND_BUG,
    STATUS_COMPLETED,
    ActionItem,
    ActionOutcome,
    run_agent,
)


def _runner(argv, check=False):
    return SimpleNamespace(returncode=0, stdout="[]", stderr="")


class _Healthy:
    """Serves one item, then drains."""

    def __init__(self, item_id="bug-1"):
        self._item = ActionItem(item_id=item_id, kind=KIND_BUG, summary="real work")
        self.executed = 0
        self._served = False

    def advertise(self, snapshot):
        return () if self._served else (self._item,)

    def execute(self, item):
        self._served = True
        self.executed += 1
        return ActionOutcome(status=STATUS_COMPLETED, detail="did the work")

    def reconcile(self, item, outcome):
        return None


class _RaisesInAdvertise:
    def __init__(self):
        self.advertise_calls = 0

    def advertise(self, snapshot):
        self.advertise_calls += 1
        raise AttributeError("'str' object has no attribute 'is_dir'")

    def execute(self, item):  # pragma: no cover - never reached
        raise AssertionError("execute must not be called")

    def reconcile(self, item, outcome):  # pragma: no cover
        raise AssertionError("reconcile must not be called")


class _RaisesInReconcile(_Healthy):
    def reconcile(self, item, outcome):
        raise RuntimeError("bookkeeping blew up")


def _run(providers, lines):
    with tempfile.TemporaryDirectory() as tmp:
        return run_agent(
            specfuse_dir=Path(tmp),
            repo="o/r",
            runner=_runner,
            providers=providers,
            features_root=Path(tmp) / "features",
            reporter=lines.append,
        )


class TestAdvertiseFailureIsContained(unittest.TestCase):
    def test_a_healthy_provider_still_does_its_work(self):
        broken, healthy = _RaisesInAdvertise(), _Healthy()
        lines = []

        summary = _run((broken, healthy), lines)

        self.assertEqual(healthy.executed, 1, "the healthy provider was starved")
        self.assertEqual(summary.items_completed, 1)

    def test_the_failure_is_reported_not_swallowed(self):
        broken, healthy = _RaisesInAdvertise(), _Healthy()
        lines = []

        summary = _run((broken, healthy), lines)

        self.assertTrue(
            any("_RaisesInAdvertise failed to advertise" in ln for ln in lines),
            lines,
        )
        entries = [e for e in summary.escalations if "_RaisesInAdvertise" in e.item_id]
        self.assertEqual(len(entries), 1)
        self.assertIn("AttributeError", entries[0].reason)

    def test_the_broken_provider_is_not_retried_every_iteration(self):
        """A permanently-broken provider must not fill the log with itself."""
        broken, healthy = _RaisesInAdvertise(), _Healthy()
        lines = []

        summary = _run((broken, healthy), lines)

        self.assertEqual(broken.advertise_calls, 1)
        reports = [ln for ln in lines if "failed to advertise" in ln]
        self.assertEqual(len(reports), 1)
        self.assertEqual(
            len([e for e in summary.escalations if e.item_id.startswith("provider:")]), 1
        )

    def test_the_run_still_drains_rather_than_ending_early(self):
        broken, healthy = _RaisesInAdvertise(), _Healthy()
        lines = []

        summary = _run((broken, healthy), lines)

        self.assertEqual(summary.stop_reason, "drained")

    def test_every_provider_raising_still_drains_cleanly(self):
        lines = []

        summary = _run((_RaisesInAdvertise(), _RaisesInAdvertise()), lines)

        self.assertEqual(summary.stop_reason, "drained")
        self.assertEqual(summary.items_completed, 0)
        self.assertEqual(len(summary.escalations), 2)


class TestReconcileFailureDoesNotDiscardTheOutcome(unittest.TestCase):
    def test_the_item_still_counts_as_completed(self):
        """The work happened. Losing it because bookkeeping raised would
        discard a real outcome — and any escalation it carried."""
        lines = []

        summary = _run((_RaisesInReconcile(),), lines)

        self.assertEqual(summary.items_completed, 1)
        self.assertEqual(summary.stop_reason, "drained")

    def test_the_reconcile_failure_is_reported(self):
        lines = []

        _run((_RaisesInReconcile(),), lines)

        self.assertTrue(
            any("reconcile raised" in ln and "RuntimeError" in ln for ln in lines), lines
        )

    def test_the_outcome_is_still_reported_as_its_own_line(self):
        lines = []

        _run((_RaisesInReconcile(),), lines)

        self.assertTrue(any("bug-1 completed" in ln for ln in lines), lines)


if __name__ == "__main__":
    unittest.main()
