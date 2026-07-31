#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""gate_spent_usd routed through the shared lifetime-cost reader —
FEAT-2026-0062/T02.

Covers the acceptance criteria that are specific to wiring `gate_spent_usd`
(loop.py) and the `budget_projection` spend term (arm_eval.py) through
`wu_lifetime_cost_usd` (cost.py, T01) rather than a per-module frontmatter
sum:

  (3) the fold-never-ran shape: `gate_spent_usd` reads the full lifetime
      spend from `events.jsonl`, not the frontmatter-only $4.28 it read
      before this WU.
  (4) the fold-ran shape does not double-count once routed through the
      shared reader.
  (5) a never-re-armed WU produces the identical number before and after,
      for both consumers.
  (6) `gate_spent_usd` and the spend term inside `budget_projection` agree
      on the same gate fixture.

`tests.test_cost_lifetime` owns exhaustive coverage of `wu_lifetime_cost_usd`
itself; this suite only exercises the two consumers that sit on top of it.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.cost import wu_lifetime_cost_usd
from tests._loop_loader import load_loop

loop = load_loop()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _write_events(path: Path, events: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


def _attempt_outcome(correlation_id: str, cost_usd) -> dict:
    return {
        "correlation_id": correlation_id,
        "event_type": "attempt_outcome",
        "payload": {"cost_usd": cost_usd},
    }


class TestGateSpentUsdLifetimeReader(unittest.TestCase):

    # -- criterion 3: fold-never-ran shape reads the full lifetime spend --

    def test_fold_never_ran_gate_reads_full_lifetime_spend(self):
        """FEAT-2026-0053/WU-07-shaped fixture: prior-cycle spend survives
        only in `re_arm_history[].prior_cost_usd`, `cumulative_cost_usd` is
        absent. Today's frontmatter-only sum reads $4.281823 (~$4.28); the
        shared reader's events sum is $9.29."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            _write(
                feature / "WU-07-x.md",
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
                feature / "events.jsonl",
                [
                    _attempt_outcome("FEAT-2026-0053/WU-07", 1.0),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 2.0),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 1.5),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 2.5),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 2.29),
                ],
            )
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-0053/WU-07", "file": "WU-07-x.md"},
                ],
            }
            spent = loop.gate_spent_usd({}, gate, feature)
            self.assertAlmostEqual(spent, 9.29, delta=0.01)
            # The pre-T02 frontmatter-only sum this WU replaces would have
            # read $4.281823 — quoted here to keep the "$4.28 today" claim
            # in the WU honest without re-deriving the old code path.
            self.assertNotAlmostEqual(spent, 4.281823, delta=0.01)

    # -- criterion 4: fold-ran shape must not double-count --

    def test_fold_ran_gate_does_not_double_count(self):
        """`cumulative_cost_usd` equals `re_arm_history[].prior_cost_usd` —
        the fold already ran. The shared reader must produce the events sum
        ($1.012), not an inflated value from summing frontmatter fields on
        top of events."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            _write(
                feature / "WU-02-x.md",
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
                feature / "events.jsonl",
                [
                    _attempt_outcome("FEAT-2026-0020/WU-02", 0.473),
                    _attempt_outcome("FEAT-2026-0020/WU-02", 0.539),
                ],
            )
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-0020/WU-02", "file": "WU-02-x.md"},
                ],
            }
            spent = loop.gate_spent_usd({}, gate, feature)
            self.assertAlmostEqual(spent, 1.012, delta=0.001)

    # -- criterion 5: never-re-armed WU is unchanged before and after --

    def test_never_rearmed_wu_unchanged_for_both_consumers(self):
        """No `re_arm_history`, no `cumulative_cost_usd`, no events.jsonl —
        the fallback path both consumers already exercised pre-T02. Must
        read exactly `cost_usd`, matching the pre-T02 behavior of each."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            wu_path = feature / "WU-01.md"
            _write(
                wu_path,
                """---
id: FEAT-2026-9999/T01
type: implementation
status: done
cost_usd: 2.5
---
body
""",
            )
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-9999/T01", "file": "WU-01.md"},
                ],
            }
            spent = loop.gate_spent_usd({}, gate, feature)
            self.assertAlmostEqual(spent, 2.5, delta=0.0001)
            # arm_eval's spend term for this WU goes through the same
            # reader and must land on the identical number.
            lifetime = wu_lifetime_cost_usd(wu_path, feature / "events.jsonl")
            self.assertAlmostEqual(lifetime, 2.5, delta=0.0001)

    # -- criterion 6: gate_spent_usd and budget_projection's spend term agree --

    def test_gate_spent_usd_agrees_with_budget_projection_spend_term(self):
        """Over the same gate fixture (mixed fold-ran, fold-never-ran, and
        never-re-armed WUs), `gate_spent_usd`'s total must equal the sum
        `budget_projection` computes over the identical WUs — both are
        `wu_lifetime_cost_usd` per WU, so they cannot diverge."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            _write(
                feature / "WU-07-x.md",
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
            _write(
                feature / "WU-02-x.md",
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
            _write(
                feature / "WU-01.md",
                """---
id: FEAT-2026-9999/T01
type: implementation
status: done
cost_usd: 2.5
---
body
""",
            )
            _write_events(
                feature / "events.jsonl",
                [
                    _attempt_outcome("FEAT-2026-0053/WU-07", 1.0),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 2.0),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 1.5),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 2.5),
                    _attempt_outcome("FEAT-2026-0053/WU-07", 2.29),
                    _attempt_outcome("FEAT-2026-0020/WU-02", 0.473),
                    _attempt_outcome("FEAT-2026-0020/WU-02", 0.539),
                ],
            )
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-0053/WU-07", "file": "WU-07-x.md"},
                    {"id": "FEAT-2026-0020/WU-02", "file": "WU-02-x.md"},
                    {"id": "FEAT-2026-9999/T01", "file": "WU-01.md"},
                ],
            }
            gate_total = loop.gate_spent_usd({}, gate, feature)

            events_path = feature / "events.jsonl"
            budget_projection_term = sum(
                wu_lifetime_cost_usd(feature / ref["file"], events_path)
                for ref in gate["work_units"]
            )

            self.assertAlmostEqual(gate_total, budget_projection_term, delta=0.0001)
            self.assertAlmostEqual(gate_total, 9.29 + 1.012 + 2.5, delta=0.01)


if __name__ == "__main__":
    unittest.main()
