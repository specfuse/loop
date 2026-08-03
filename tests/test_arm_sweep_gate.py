#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/arm_sweep_gate.py (FEAT-2026-0063/T02).

Fixtures mirror test_arm_sweep.py's build-a-feature-folder-directly style:
PLAN.md and PLAN.baseline.json written straight to a temp `features_root`,
no driver involved.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from _loop_loader import load_module

arm_sweep_gate = load_module(".specfuse/scripts/arm_sweep_gate.py", "arm_sweep_gate")


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


def _wu(feature_dir: Path, filename: str, wu_id: str, produces: "list | None" = None) -> None:
    produces = produces or []
    produces_yaml = ""
    if produces:
        produces_yaml = "produces:\n" + "".join(f"  - {p}\n" for p in produces)
    fm = f"id: {wu_id}\ntype: implementation\nstatus: pending\n{produces_yaml}"
    _write(feature_dir / filename, f"---\n{fm}---\n\n# {wu_id}\n\nbody\n")


def _run_gate(root: Path):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = arm_sweep_gate.arm_sweep_gate_main(root)
    return code, out.getvalue(), err.getvalue()


class TestArmSweepGate(unittest.TestCase):
    def test_unevaluable_feature_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            broken = root / "FEAT-2026-9101-broken"
            broken.mkdir()
            (broken / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9101\n---\n\n# Plan\n\nno graph block here\n"
            )
            _baseline(broken, {1: []})

            code, out, err = _run_gate(root)

            self.assertEqual(code, 1)
            self.assertIn("FEAT-2026-9101-broken", err)

    def test_all_evaluable_features_clean_exits_zero_despite_never_fired_classes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            clean = root / "FEAT-2026-9201-clean"
            clean.mkdir()
            _plan_md(clean, "FEAT-2026-9201", [1], {})
            _baseline(clean, {1: []})

            code, out, err = _run_gate(root)

            self.assertEqual(code, 0)
            self.assertIn("NEVER fired", out)

    def test_not_evaluable_verdict_among_evaluable_features_fails_and_names_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            feat = root / "FEAT-2026-9301-undecidable"
            feat.mkdir()
            _plan_md(
                feat,
                "FEAT-2026-9301",
                [1, 2],
                {2: [("FEAT-2026-9301/T02", "WU-02.md")]},
            )
            _wu(feat, "WU-02.md", "FEAT-2026-9301/T02", produces=["src/generated/*.ts"])
            _baseline(feat, {1: []})

            code, out, err = _run_gate(root)

            self.assertEqual(code, 1)
            self.assertIn("decision_class_paths", err)
            self.assertIn("FEAT-2026-9301", err)

    def test_branch_observation_table_prints_on_both_exit_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = root / "FEAT-2026-9401-clean"
            clean.mkdir()
            _plan_md(clean, "FEAT-2026-9401", [1], {})
            _baseline(clean, {1: []})
            code_ok, out_ok, _ = _run_gate(root)
            self.assertEqual(code_ok, 0)
            self.assertIn("branch-observation table:", out_ok)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = root / "FEAT-2026-9402-broken"
            broken.mkdir()
            (broken / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9402\n---\n\n# Plan\n\nno graph block here\n"
            )
            _baseline(broken, {1: []})
            code_fail, out_fail, _ = _run_gate(root)
            self.assertEqual(code_fail, 1)
            self.assertIn("branch-observation table:", out_fail)

    def test_no_baselined_feature_anywhere_exits_zero_with_explicit_nothing_evaluable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_baseline = root / "FEAT-2026-9501-no-baseline"
            no_baseline.mkdir()
            _plan_md(no_baseline, "FEAT-2026-9501", [1], {})

            code, out, err = _run_gate(root)

            self.assertEqual(code, 0)
            self.assertIn("nothing evaluable", out)


if __name__ == "__main__":
    unittest.main()
