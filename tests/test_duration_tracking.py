#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Duration tracking — per-attempt and cumulative wall-clock recording.

Verifies acceptance criteria for FEAT-2026-0006/T01:
  1. A single passing attempt records duration_seconds in attempts_usage.
  2. Cumulative duration sums correctly across a failed-then-passed sequence.
  3. The cumulative value is written to WU frontmatter at outcome time.
  4. Duration is captured even when cost_tracking is False.

No real `claude -p` is spawned — dispatch and verify are stubbed, matching
the pattern in test_cost_tracking.py.
"""

from __future__ import annotations

import os
import unittest

from tests._loop_loader import load_loop
from tests._workspace import with_deliverable
from tests.test_driver_integration import (
    integration_workspace,
    write_minimal_feature,
    _read_frontmatter,
    _read_events,
)
from tests.test_cost_tracking import _write_verification_yml

loop = load_loop()


class TestDurationTracking(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        # Dispatch stubs must write a deliverable or the presence gate
        # (FEAT-2026-0022) rejects the WU as hollow. See #150 —
        # `.specfuse/.loop.lock` used to stand in as the deliverable.
        if name == "dispatch":
            replacement = with_deliverable(replacement)
        setattr(loop, name, replacement)

    # ------------------------------------------------------------------ #
    # AC#1 — single attempt records duration_seconds in attempts_usage     #
    # ------------------------------------------------------------------ #

    def test_single_attempt_records_duration_seconds(self):
        """A single passing attempt writes duration_seconds in attempts_usage."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=True)
            write_minimal_feature(root, "FEAT-2026-9301", "dur-single",
                                  "feat/dur-single", [
                                      ("FEAT-2026-9301/T01", "implementation", "pending"),
                                  ])

            self._patch("dispatch",
                        lambda wu, fn, cost_tracking=True: (
                            "(stub)\n",
                            {"cost_usd": 0.001, "input_tokens": 10,
                             "output_tokens": 5},
                        ))
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9301-dur-single"
            events = _read_events(fdir / "events.jsonl")
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == "FEAT-2026-9301/T01"]
            self.assertEqual(len(completed), 1)
            au = completed[0]["payload"]["attempts_usage"]
            self.assertEqual(len(au), 1)
            self.assertIn("duration_seconds", au[0])
            # duration must be a non-negative number
            self.assertGreaterEqual(au[0]["duration_seconds"], 0.0)

    # ------------------------------------------------------------------ #
    # AC#2 — cumulative duration sums across failed-then-passed            #
    # ------------------------------------------------------------------ #

    def test_cumulative_duration_sums_across_attempts(self):
        """Two failed attempts then a pass — cumulative duration_seconds equals
        the sum of all three per-attempt values."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=True)
            write_minimal_feature(root, "FEAT-2026-9302", "dur-cum",
                                  "feat/dur-cum", [
                                      ("FEAT-2026-9302/T01", "implementation", "pending"),
                                  ])

            def fake_dispatch(wu, fn, cost_tracking=True):
                return ("(stub)\n",
                        {"cost_usd": 0.001, "input_tokens": 10,
                         "output_tokens": 5})

            # Fail twice, pass on third attempt for T01; always pass for
            # the closing-sequence WUs that follow.
            t01_results = [False, False, True]
            t01_call = [0]

            def fake_verify(wu, fd, cfg=None):
                if wu.wu_id == "FEAT-2026-9302/T01":
                    result = t01_results[t01_call[0]]
                    t01_call[0] += 1
                    return result, "(stub)"
                return True, "(stub)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9302-dur-cum"
            events = _read_events(fdir / "events.jsonl")
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == "FEAT-2026-9302/T01"]
            self.assertEqual(len(completed), 1)
            au = completed[0]["payload"]["attempts_usage"]
            self.assertEqual(len(au), 3)
            for entry in au:
                self.assertIn("duration_seconds", entry)

            # Cumulative is the sum of per-attempt durations (up to float rounding).
            expected_sum = round(
                sum(entry["duration_seconds"] for entry in au), 3
            )
            # The frontmatter value must equal that sum.
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertIn("duration_seconds", t01_fm)
            actual = round(float(t01_fm["duration_seconds"]), 3)
            self.assertAlmostEqual(actual, expected_sum, places=2)

    # ------------------------------------------------------------------ #
    # AC#3 — cumulative value written to WU frontmatter                   #
    # ------------------------------------------------------------------ #

    def test_cumulative_duration_written_to_frontmatter(self):
        """duration_seconds is present in WU frontmatter after a passing run."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=True)
            write_minimal_feature(root, "FEAT-2026-9303", "dur-fm",
                                  "feat/dur-fm", [
                                      ("FEAT-2026-9303/T01", "implementation", "pending"),
                                  ])

            self._patch("dispatch",
                        lambda wu, fn, cost_tracking=True: ("(stub)\n", None))
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9303-dur-fm"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertIn("duration_seconds", t01_fm)
            self.assertGreaterEqual(float(t01_fm["duration_seconds"]), 0.0)

    # ------------------------------------------------------------------ #
    # AC#4 — duration captured even when cost_tracking is False            #
    # ------------------------------------------------------------------ #

    def test_duration_recorded_when_cost_tracking_disabled(self):
        """duration_seconds in both attempts_usage and frontmatter even when
        cost_tracking: false prevents any cost/token recording."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=False)
            write_minimal_feature(root, "FEAT-2026-9304", "dur-no-cost",
                                  "feat/dur-no-cost", [
                                      ("FEAT-2026-9304/T01", "implementation", "pending"),
                                  ])

            # Real dispatch returns (text, None) when cost_tracking is False.
            def fake_dispatch(wu, fn, cost_tracking=True):
                return "(stub)\n", None

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9304-dur-no-cost"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            # duration written even without cost tracking
            self.assertIn("duration_seconds", t01_fm)
            self.assertGreaterEqual(float(t01_fm["duration_seconds"]), 0.0)
            # cost fields must NOT be present
            self.assertNotIn("cost_usd", t01_fm)

            events = _read_events(fdir / "events.jsonl")
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == "FEAT-2026-9304/T01"]
            au = completed[0]["payload"]["attempts_usage"]
            self.assertEqual(len(au), 1)
            self.assertIn("duration_seconds", au[0])
            self.assertNotIn("cost_usd", au[0])


if __name__ == "__main__":
    unittest.main()
