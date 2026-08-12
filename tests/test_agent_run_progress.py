# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""An unattended run reports what it is doing while it is doing it.

The first live run printed nothing for 85 minutes and then a summary. An
operator watching it had no way to tell a working item from a hung one, no
per-item cost, and no record of which items the snapshot even offered. The
loop now emits the same timestamped shape `specfuse run` does.
"""

from __future__ import annotations

import re
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
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    _default_reporter,
    run_agent,
)


def _runner(argv, check=False):
    return SimpleNamespace(returncode=0, stdout="[]", stderr="")


class _Clock:
    def __init__(self):
        self._now = 0.0

    def __call__(self):
        self._now += 30.0
        return self._now


class _Provider:
    def __init__(self, outcome, *, raises=False):
        self._item = ActionItem(
            item_id="bug-240", kind=KIND_BUG, summary="header overstates its evidence"
        )
        self._outcome = outcome
        self._raises = raises
        self._served = False

    def advertise(self, snapshot):
        if self._served:
            return ()
        return (self._item,)

    def execute(self, item):
        self._served = True
        if self._raises:
            raise RuntimeError("boom")
        return self._outcome

    def reconcile(self, item, outcome):
        return None


def _run(provider, lines):
    with tempfile.TemporaryDirectory() as tmp:
        return run_agent(
            specfuse_dir=Path(tmp),
            repo="o/r",
            runner=_runner,
            providers=(provider,),
            features_root=Path(tmp) / "features",
            clock=_Clock(),
            reporter=lines.append,
        )


class TestProgressReporting(unittest.TestCase):
    def test_run_start_and_snapshot_are_announced(self):
        lines = []
        _run(_Provider(ActionOutcome(status=STATUS_COMPLETED, detail="merged")), lines)

        self.assertTrue(any("run started" in ln and "o/r" in ln for ln in lines))
        self.assertTrue(any(ln.startswith("snapshot:") for ln in lines))

    def test_each_item_is_announced_before_it_runs(self):
        lines = []
        _run(_Provider(ActionOutcome(status=STATUS_COMPLETED, detail="merged")), lines)

        starts = [ln for ln in lines if ln.startswith("item 1:")]
        self.assertEqual(len(starts), 1)
        self.assertIn("bug-240", starts[0])
        self.assertIn(KIND_BUG, starts[0])
        self.assertIn("header overstates its evidence", starts[0])
        # ...and before its result line, not after it.
        self.assertLess(
            lines.index(starts[0]),
            next(i for i, ln in enumerate(lines) if "completed" in ln),
        )

    def test_completed_item_reports_its_wall_clock_cost(self):
        lines = []
        _run(_Provider(ActionOutcome(status=STATUS_COMPLETED, detail="merged")), lines)

        done = [ln for ln in lines if "bug-240 completed" in ln]
        self.assertEqual(len(done), 1)
        self.assertRegex(done[0], r"in \d+(\.\d+)?[sm] ")

    def test_escalated_item_reports_reason_and_cost(self):
        lines = []
        outcome = ActionOutcome(
            status=STATUS_ESCALATED, detail="judge_path_touched", escalation=None
        )
        _run(_Provider(outcome), lines)

        escalated = [ln for ln in lines if "bug-240 escalated" in ln]
        self.assertEqual(len(escalated), 1)
        self.assertIn("judge_path_touched", escalated[0])

    def test_a_raising_provider_is_reported_not_silent(self):
        lines = []
        _run(_Provider(None, raises=True), lines)

        self.assertTrue(any("bug-240 failed" in ln and "boom" in ln for ln in lines))

    def test_run_end_reports_stop_reason_and_elapsed(self):
        lines = []
        summary = _run(
            _Provider(ActionOutcome(status=STATUS_COMPLETED, detail="merged")), lines
        )

        end = [ln for ln in lines if ln.startswith("run finished")]
        self.assertEqual(len(end), 1)
        self.assertIn(summary.stop_reason, end[0])

    def test_reporter_silences_stdout_when_supplied(self):
        import contextlib
        import io

        buffer = io.StringIO()
        lines = []
        with contextlib.redirect_stdout(buffer):
            _run(
                _Provider(ActionOutcome(status=STATUS_COMPLETED, detail="merged")),
                lines,
            )

        self.assertEqual(buffer.getvalue(), "")
        self.assertTrue(lines)


class TestDefaultReporterShape(unittest.TestCase):
    def test_line_carries_an_hh_mm_ss_timestamp(self):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            _default_reporter("bug-240 completed")

        self.assertRegex(buffer.getvalue(), r"^\[\d{2}:\d{2}:\d{2}\] bug-240 completed\n$")

    def test_shape_matches_the_driver_log(self):
        """`specfuse run` prints `[HH:MM:SS] -- ...` per work unit; an
        operator should not have to learn a second format for the agent."""
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            _default_reporter("x")

        self.assertIsNotNone(re.match(r"^\[\d{2}:\d{2}:\d{2}\] ", buffer.getvalue()))


if __name__ == "__main__":
    unittest.main()
