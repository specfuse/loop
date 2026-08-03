#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for arm_sweep.py (FEAT-2026-0063/T01).

Each fixture is a self-contained temp `features_root` holding one or more
feature folders — PLAN.md, PLAN.baseline.json, and (where a class needs it)
WU files — built directly rather than through the driver, mirroring
test_arm_eval.py's fixture style.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.arm_sweep import EXCLUDED_REASON_NO_BASELINE, sweep_arm_predicate


def _write(path: Path, text: str) -> None:
    path.write_text(text)


def _plan_md(feature_dir: Path, feature_id: str, gate_nums: list, wu_ids_by_gate: dict) -> None:
    gates_yaml = ""
    for g in gate_nums:
        wu_ids = wu_ids_by_gate.get(g, [])
        if wu_ids:
            wus = "".join(
                f"      - id: {wid}\n        file: {wfile}\n        depends_on: []\n"
                for wid, wfile in wu_ids
            )
            gates_yaml += f"  - gate: {g}\n    file: GATE-{g:02d}.md\n    work_units:\n{wus}"
        else:
            gates_yaml += f"  - gate: {g}\n    file: GATE-{g:02d}.md\n    work_units: []\n"
    fm = (
        f"feature_id: {feature_id}\n"
        "title: fixture feature\n"
        "branch: feat/fixture\n"
        "roadmap_goal: test\n"
        "status: active\n"
    )
    graph = f"```yaml\ngates:\n{gates_yaml}```\n"
    _write(feature_dir / "PLAN.md", f"---\n{fm}---\n\n# Plan\n\n{graph}")


def _baseline(feature_dir: Path, gate_nums_and_wus: dict) -> None:
    gates_out = []
    for g, wu_ids in gate_nums_and_wus.items():
        gates_out.append(
            {
                "gate": g,
                "work_units": [
                    {
                        "id": wid,
                        "type": "implementation",
                        "goal": wid,
                        "planned_cost_usd": 1.0,
                    }
                    for wid in wu_ids
                ],
            }
        )
    (feature_dir / "PLAN.baseline.json").write_text(
        json.dumps({"gates": gates_out}, indent=2, sort_keys=True) + "\n"
    )


def _wu(feature_dir: Path, filename: str, wu_id: str, provenance: "str | None") -> None:
    prov_line = f"provenance: {provenance}\n" if provenance else ""
    fm = f"id: {wu_id}\ntype: implementation\nstatus: pending\n{prov_line}"
    _write(feature_dir / filename, f"---\n{fm}---\n\n# {wu_id}\n\nbody\n")


class TestArmSweep(unittest.TestCase):
    def test_excluded_features_reported_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with_baseline = root / "FEAT-2026-9001-with-baseline"
            with_baseline.mkdir()
            _plan_md(with_baseline, "FEAT-2026-9001", [1], {})
            _baseline(with_baseline, {1: []})

            without_baseline = root / "FEAT-2026-9002-without-baseline"
            without_baseline.mkdir()
            _plan_md(without_baseline, "FEAT-2026-9002", [1], {})

            report = sweep_arm_predicate(root)

            self.assertEqual(report.evaluable_count, 1)
            self.assertEqual(report.excluded_count, 1)
            self.assertEqual(
                report.excluded,
                [
                    {
                        "feature": "FEAT-2026-9002-without-baseline",
                        "reason": EXCLUDED_REASON_NO_BASELINE,
                    }
                ],
            )
            self.assertIn("FEAT-2026-9001", report.evaluated)

    def test_unevaluable_feature_lands_in_ledger_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            broken = root / "FEAT-2026-9101-broken"
            broken.mkdir()
            (broken / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9101\n---\n\n# Plan\n\nno graph block here\n"
            )
            _baseline(broken, {1: []})

            report = sweep_arm_predicate(root)

            self.assertEqual(report.evaluable_count, 1)
            self.assertEqual(len(report.evaluated), 0)
            self.assertIn("FEAT-2026-9101-broken", report.could_not_evaluate)
            self.assertIn("ValueError", report.could_not_evaluate["FEAT-2026-9101-broken"])

    def test_never_observed_status_is_explicit_not_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            clean = root / "FEAT-2026-9201-clean"
            clean.mkdir()
            _plan_md(clean, "FEAT-2026-9201", [1], {})
            _baseline(clean, {1: []})

            report = sweep_arm_predicate(root)

            for obs in report.class_observations.values():
                self.assertIn("not_evaluable", obs.counts)
                self.assertEqual(obs.counts["not_evaluable"], 0)
                self.assertIsNone(obs.first_seen["not_evaluable"])

    def test_gates_swept_come_from_each_feature_own_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            three_gate = root / "FEAT-2026-9301-three-gate"
            three_gate.mkdir()
            _plan_md(three_gate, "FEAT-2026-9301", [1, 2, 3], {})
            _baseline(three_gate, {1: [], 2: [], 3: []})

            one_gate = root / "FEAT-2026-9302-one-gate"
            one_gate.mkdir()
            _plan_md(one_gate, "FEAT-2026-9302", [1], {})
            _baseline(one_gate, {1: []})

            report = sweep_arm_predicate(root)

            self.assertEqual(report.evaluated["FEAT-2026-9301"], [1, 2, 3])
            self.assertEqual(report.evaluated["FEAT-2026-9302"], [1])

    def test_first_observation_is_earliest_in_deterministic_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            # Both features have an added WU (relative to their own baseline)
            # missing provenance, firing missing_provenance at gate 1. "a"
            # sorts before "b" in the deterministic directory walk, so its
            # (feature_id, gate) must be the recorded first sighting even
            # though both fire on the same gate number.
            feat_a = root / "FEAT-2026-9401-a"
            feat_a.mkdir()
            _plan_md(
                feat_a,
                "FEAT-2026-9401",
                [1],
                {1: [("FEAT-2026-9401/T02", "WU-02.md")]},
            )
            _wu(feat_a, "WU-02.md", "FEAT-2026-9401/T02", provenance=None)
            _baseline(feat_a, {1: []})

            feat_b = root / "FEAT-2026-9402-b"
            feat_b.mkdir()
            _plan_md(
                feat_b,
                "FEAT-2026-9402",
                [1],
                {1: [("FEAT-2026-9402/T02", "WU-02.md")]},
            )
            _wu(feat_b, "WU-02.md", "FEAT-2026-9402/T02", provenance=None)
            _baseline(feat_b, {1: []})

            report = sweep_arm_predicate(root)

            obs = report.class_observations["missing_provenance"]
            self.assertEqual(obs.counts["fired"], 2)
            self.assertEqual(obs.first_seen["fired"], ("FEAT-2026-9401", 1))


if __name__ == "__main__":
    unittest.main()
