#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""wu_lifetime_cost_usd — events-first, frontmatter-fallback lifetime cost.

FEAT-2026-0062/T01. See specfuse/loop/cost.py's module docstring and
FEAT-2026-0062/PLAN.md for the two re-arm shapes and the double-count trap
this suite exists to hold down as a test rather than a claim.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.cost import wu_lifetime_cost_usd


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _write_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


def _attempt_outcome(correlation_id: str, cost_usd) -> dict:
    return {
        "correlation_id": correlation_id,
        "event_type": "attempt_outcome",
        "payload": {"cost_usd": cost_usd},
    }


class TestLifetimeCost(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.wu_path = self.root / "WU-07-x.md"
        self.events_path = self.root / "events.jsonl"

    # -- criterion 1/2: fold-never-ran shape reads full lifetime from events --

    def test_fold_never_ran_wu_reads_full_lifetime(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0053/WU-07
type: implementation
status: done
re_arm_history:
  -
    timestamp: 2026-07-31T02:15:35+00:00
    prior_cost_usd: 5.01
cost_usd: 4.281823
---
body
""",
        )
        _write_events(
            self.events_path,
            [
                _attempt_outcome("FEAT-2026-0053/WU-07", 1.0),
                _attempt_outcome("FEAT-2026-0053/WU-07", 2.0),
                _attempt_outcome("FEAT-2026-0053/WU-07", 1.5),
                _attempt_outcome("FEAT-2026-0053/WU-07", 2.5),
                _attempt_outcome("FEAT-2026-0053/WU-07", 2.29),
            ],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 9.29, delta=0.01)

    # -- criterion 3: fold-ran shape must not double-count --

    def test_fold_ran_wu_does_not_double_count(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0020/WU-02
type: implementation
status: done
cost_usd: 0.539
cumulative_cost_usd: 0.473
re_arm_history:
  -
    timestamp: 2026-07-30T00:00:00+00:00
    prior_cost_usd: 0.473
---
body
""",
        )
        _write_events(
            self.events_path,
            [
                _attempt_outcome("FEAT-2026-0020/WU-02", 0.473),
                _attempt_outcome("FEAT-2026-0020/WU-02", 0.539),
            ],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 1.012, delta=0.01)

    # -- criterion 4: no attempt_outcome events -> frontmatter fallback --

    def test_no_events_falls_back_to_frontmatter_sum(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-01
cost_usd: 1.5
cumulative_cost_usd: 2.5
---
body
""",
        )
        _write_events(self.events_path, [])
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 4.0, delta=0.01)

    def test_fallback_does_not_return_false_zero(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-02
cost_usd: 1.5
cumulative_cost_usd: 2.5
---
body
""",
        )
        _write_events(self.events_path, [])
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertNotEqual(result, 0.0)

    # -- criterion 5: missing events.jsonl takes fallback, does not raise --

    def test_missing_events_file_takes_fallback(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-03
cost_usd: 3.0
---
body
""",
        )
        missing_events = self.root / "does-not-exist.jsonl"
        result = wu_lifetime_cost_usd(self.wu_path, missing_events)
        self.assertAlmostEqual(result, 3.0, delta=0.01)

    # -- criterion 6: never-re-armed WU returns exactly cost_usd --

    def test_never_rearmed_wu_returns_exactly_cost_usd(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-04
cost_usd: 2.718
---
body
""",
        )
        _write_events(self.events_path, [])
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 2.718, delta=0.0001)

    # -- criterion 7: malformed input contributes 0.0, never raises --

    def test_unparseable_jsonl_line_contributes_zero(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-05
cost_usd: 1.0
---
body
""",
        )
        _write(self.events_path, "{not valid json\n")
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        # No attempt_outcome seen for this WU (line was unparseable) -> fallback.
        self.assertAlmostEqual(result, 1.0, delta=0.01)

    def test_attempt_outcome_with_no_cost_usd_contributes_zero(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-06
cost_usd: 1.0
---
body
""",
        )
        _write_events(
            self.events_path,
            [
                {
                    "correlation_id": "FEAT-2026-0099/WU-06",
                    "event_type": "attempt_outcome",
                    "payload": {},
                }
            ],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        # An attempt_outcome WAS seen, so this takes the events path (sum 0.0),
        # not the frontmatter fallback.
        self.assertAlmostEqual(result, 0.0, delta=0.0001)

    # -- extra malformed-input coverage --

    def test_missing_wu_file_contributes_zero(self):
        missing_wu = self.root / "does-not-exist.md"
        result = wu_lifetime_cost_usd(missing_wu, self.events_path)
        self.assertAlmostEqual(result, 0.0, delta=0.0001)

    def test_wu_file_without_frontmatter_marker_contributes_zero(self):
        _write(self.wu_path, "no frontmatter here\n")
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 0.0, delta=0.0001)

    def test_non_dict_event_line_is_skipped(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-08
cost_usd: 1.0
---
body
""",
        )
        _write_events(self.events_path, [])
        with self.events_path.open("a") as fh:
            fh.write(json.dumps([1, 2, 3]) + "\n")
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 1.0, delta=0.01)

    def test_other_wu_events_are_not_summed(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-09
cost_usd: 1.0
---
body
""",
        )
        _write_events(
            self.events_path,
            [_attempt_outcome("FEAT-2026-0099/WU-OTHER", 99.0)],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        # No event for THIS WU -> fallback to frontmatter cost_usd.
        self.assertAlmostEqual(result, 1.0, delta=0.01)

    def test_non_dict_payload_contributes_zero(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-10
cost_usd: 1.0
---
body
""",
        )
        _write_events(
            self.events_path,
            [
                {
                    "correlation_id": "FEAT-2026-0099/WU-10",
                    "event_type": "attempt_outcome",
                    "payload": "not-a-dict",
                }
            ],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 0.0, delta=0.0001)

    def test_bool_cost_usd_contributes_zero(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-07
cost_usd: 1.0
---
body
""",
        )
        _write_events(
            self.events_path,
            [_attempt_outcome("FEAT-2026-0099/WU-07", True)],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 0.0, delta=0.0001)


if __name__ == "__main__":
    unittest.main()
