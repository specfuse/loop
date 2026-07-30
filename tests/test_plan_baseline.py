#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for plan_baseline.py (FEAT-2026-0053/T01).

Covers:
  - write_baseline_if_absent() writes PLAN.baseline.json on first dispatch
    with per-gate WU ids, types, goal lines, and planned costs.
  - a second call against an existing baseline is a byte-identical no-op,
    even when the underlying plan has since mutated.
  - load_baseline() returns the parsed snapshot, or None when absent.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.plan_baseline import (
    load_baseline,
    load_plan_graph,
    write_baseline_if_absent,
)

_PLAN_FM = (
    "feature_id: FEAT-2026-9997\n"
    "title: Plan baseline test\n"
    "branch: feat/plan-baseline-test\n"
    "roadmap_goal: Verify plan baseline snapshot.\n"
    "status: active\n"
)

_GRAPH = (
    "```yaml\n"
    "gates:\n"
    "  - gate: 1\n"
    "    file: GATE-01.md\n"
    "    work_units:\n"
    "      - id: FEAT-2026-9997/T01\n"
    "        file: WU-01-impl.md\n"
    "        depends_on: []\n"
    "      - id: FEAT-2026-9997/G1-CLOSE\n"
    "        file: WU-90-close.md\n"
    "        depends_on: [FEAT-2026-9997/T01]\n"
    "```\n"
)


def _make_feature(tmpdir: str) -> Path:
    feature = Path(tmpdir) / "feature"
    feature.mkdir(exist_ok=True)
    (feature / "PLAN.md").write_text(f"---\n{_PLAN_FM}---\n\n# Plan\n\n{_GRAPH}")
    (feature / "WU-01-impl.md").write_text(
        "---\ntype: implementation\nplanned_cost_usd: 1.5\n---\n\n"
        "# Do the thing\n\nbody text\n"
    )
    (feature / "WU-90-close.md").write_text(
        "---\ntype: close\nplanned_cost_usd: 0.5\n---\n\n"
        "# Close the gate\n\nbody text\n"
    )
    return feature


class TestBaseline(unittest.TestCase):
    def test_first_dispatch_writes_baseline_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir)
            baseline_path = feature / "PLAN.baseline.json"
            self.assertFalse(baseline_path.exists())

            plan = load_plan_graph(feature)
            write_baseline_if_absent(feature, plan)

            self.assertTrue(baseline_path.exists())
            snapshot = json.loads(baseline_path.read_text())
            self.assertEqual(snapshot, {
                "gates": [
                    {
                        "gate": 1,
                        "work_units": [
                            {
                                "id": "FEAT-2026-9997/T01",
                                "type": "implementation",
                                "goal": "Do the thing",
                                "planned_cost_usd": 1.5,
                            },
                            {
                                "id": "FEAT-2026-9997/G1-CLOSE",
                                "type": "close",
                                "goal": "Close the gate",
                                "planned_cost_usd": 0.5,
                            },
                        ],
                    },
                ],
            })

    def test_second_call_is_a_byte_identical_noop_even_after_plan_mutates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir)
            baseline_path = feature / "PLAN.baseline.json"

            plan = load_plan_graph(feature)
            write_baseline_if_absent(feature, plan)
            before = baseline_path.read_bytes()

            # Mutate the plan after the baseline was written: new WU title,
            # new cost, and an entirely new gate/work-unit.
            (feature / "WU-01-impl.md").write_text(
                "---\ntype: implementation\nplanned_cost_usd: 99.0\n---\n\n"
                "# A totally different goal\n\nbody text\n"
            )
            mutated_plan = dict(plan)
            mutated_plan["gates"] = plan["gates"] + [
                {"gate": 2, "file": "GATE-02.md", "work_units": []}
            ]

            write_baseline_if_absent(feature, mutated_plan)
            after = baseline_path.read_bytes()

            self.assertEqual(before, after)

    def test_load_baseline_returns_none_when_absent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir)
            self.assertIsNone(load_baseline(feature))

    def test_load_baseline_returns_parsed_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir)
            plan = load_plan_graph(feature)
            write_baseline_if_absent(feature, plan)

            loaded = load_baseline(feature)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["gates"][0]["work_units"][0]["id"],
                              "FEAT-2026-9997/T01")


if __name__ == "__main__":
    unittest.main()
