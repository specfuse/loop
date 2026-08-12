#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for arm_eval.py (FEAT-2026-0053/T03).

One class per stop-class criterion (v1: seven classes), plus the
no-baseline short circuit and one combined clean-feature scenario. Each
fixture is a self-contained temp feature directory — PLAN.md, GATE-NN.md,
WU files, PLAN.baseline.json, and (where relevant) a GATE-NN-REVIEW.md.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.arm_eval import ArmDecision, evaluate_arm_predicate


FEATURE_ID = "FEAT-2026-8801"


def _write(path: Path, text: str) -> None:
    path.write_text(text)


def _plan_md(feature: Path, gate2_wus: list) -> None:
    fm = (
        f"feature_id: {FEATURE_ID}\n"
        "title: Arm predicate test feature\n"
        "branch: feat/arm-predicate-test\n"
        "roadmap_goal: test\n"
        "status: active\n"
    )
    gate2_block = (
        "    work_units:\n" + "".join(
            f"      - id: {wid}\n        file: {wfile}\n        depends_on: []\n"
            for wid, wfile in gate2_wus
        )
        if gate2_wus else "    work_units: []\n"
    )
    graph = (
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {FEATURE_ID}/T01\n"
        "        file: WU-01.md\n"
        "        depends_on: []\n"
        f"      - id: {FEATURE_ID}/G1-CLOSE\n"
        "        file: WU-90.md\n"
        "        depends_on: []\n"
        "  - gate: 2\n"
        "    file: GATE-02.md\n"
        f"{gate2_block}"
        "```\n"
    )
    _write(feature / "PLAN.md", f"---\n{fm}---\n\n# Plan\n\n{graph}")


def _wu(feature: Path, filename: str, title: str, fm_lines: list) -> None:
    fm = "\n".join(fm_lines)
    _write(feature / filename, f"---\n{fm}\n---\n\n# {title}\n\nbody\n")


def _gate(feature: Path, gate_num: int, status: str) -> None:
    _write(
        feature / f"GATE-{gate_num:02d}.md",
        f"---\nstatus: {status}\n---\n\n# Gate {gate_num}\n\nbody\n",
    )


def _review(feature: Path, gate_num: int, fm_lines: "list | None") -> None:
    if fm_lines is None:
        _write(
            feature / f"GATE-{gate_num:02d}-REVIEW.md",
            "---\nstatus: draft\n---\n\n# Review\n\nbody\n",
        )
        return
    fm = "\n".join(fm_lines)
    _write(
        feature / f"GATE-{gate_num:02d}-REVIEW.md",
        f"---\n{fm}\n---\n\n# Review\n\nbody\n",
    )


def _baseline(feature: Path) -> None:
    snapshot = {
        "gates": [
            {
                "gate": 1,
                "work_units": [
                    {
                        "id": f"{FEATURE_ID}/T01",
                        "type": "implementation",
                        "goal": "Do T01",
                        "planned_cost_usd": 2.0,
                    },
                    {
                        "id": f"{FEATURE_ID}/G1-CLOSE",
                        "type": "close-intermediate",
                        "goal": "Close gate 1",
                        "planned_cost_usd": 1.0,
                    },
                ],
            },
            {"gate": 2, "work_units": []},
        ],
    }
    _write(feature / "PLAN.baseline.json", json.dumps(snapshot))


def _base_feature(feature: Path, *, t05_fm_extra: "list | None" = None,
                   gate1_status: str = "passed",
                   review_fm: "list | None" = ("open_questions: []",),
                   t01_title: str = "Do T01") -> None:
    """A clean, would-arm fixture: gate 1 passed & unmutated, gate 2 has one
    added WU (T05) with provenance, clean produces, no human_only, and a
    review file with an explicit empty open_questions list."""
    feature.mkdir(exist_ok=True)
    gate2_wus = [(f"{FEATURE_ID}/T05", "WU-05.md")]
    _plan_md(feature, gate2_wus)
    _wu(feature, "WU-01.md", t01_title, [
        "type: implementation", "status: done",
        "cost_usd: 2.0", "planned_cost_usd: 2.0",
    ])
    _wu(feature, "WU-90.md", "Close gate 1", [
        "type: close-intermediate", "status: done",
        "cost_usd: 1.0", "planned_cost_usd: 1.0",
    ])
    t05_lines = [
        "type: implementation", "status: pending",
        "cost_usd: 0.0", "planned_cost_usd: 1.0",
        "produces: [some/new/file.py]",
        "provenance: RETRO-1",
    ]
    if t05_fm_extra:
        t05_lines += t05_fm_extra
    _wu(feature, "WU-05.md", "Do T05", t05_lines)
    _gate(feature, 1, gate1_status)
    _review(feature, 2, list(review_fm) if review_fm is not None else None)
    _baseline(feature)


class TestNoBaseline(unittest.TestCase):
    def test_missing_baseline_short_circuits_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            gate2_wus = [(f"{FEATURE_ID}/T05", "WU-05.md")]
            _plan_md(feature, gate2_wus)
            _wu(feature, "WU-01.md", "Do T01", [
                "type: implementation", "status: done",
                "cost_usd: 2.0", "planned_cost_usd: 2.0",
            ])
            _wu(feature, "WU-90.md", "Close gate 1", [
                "type: close-intermediate", "status: done",
                "cost_usd: 1.0", "planned_cost_usd: 1.0",
            ])
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "provenance: RETRO-1",
            ])
            _gate(feature, 1, "passed")
            _review(feature, 2, ["open_questions: []"])
            # No PLAN.baseline.json written.

            decision = evaluate_arm_predicate(feature, 1)
            self.assertFalse(decision.would_arm)
            for name in decision.classes:
                self.assertEqual(decision.classes[name].status, "not_evaluable")
                self.assertEqual(decision.classes[name].reason, "no_baseline")


class TestArmPredicate(unittest.TestCase):
    def test_clean_on_plan_feature_would_arm(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertIsInstance(decision, ArmDecision)
            self.assertTrue(decision.would_arm, decision.classes)
            for name, verdict in decision.classes.items():
                self.assertEqual(verdict.status, "clean", f"{name}: {verdict.reason}")

    # --- Class 1: budget projection ---

    def test_budget_projection_fires_over_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            # Bump T05's planned cost far past 2x baseline planned total ($6.0).
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 100.0",
                "produces: [some/new/file.py]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["budget_projection"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_budget_projection_stays_clean_within_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["budget_projection"].status, "clean")

    def test_budget_projection_counts_rearmed_lifetime_spend(self):
        """FEAT-2026-0062/T02 criterion 1: a re-armed WU's prior-cycle spend
        sits in `cumulative_cost_usd`, not `cost_usd`. Baseline planned total
        is $3.00 (T01 $2.00 + G1-CLOSE $1.00), so the ceiling is $6.00.
        WU-01's `cost_usd` alone ($2.00) plus G1-CLOSE ($1.00) projects to
        $3.00 — clean on the pre-T02 per-cycle sum. Its actual lifetime spend
        (cost_usd + cumulative_cost_usd = $12.00) plus G1-CLOSE ($1.00)
        projects to $13.00, past the $6.00 ceiling — must fire. No
        events.jsonl exists in this fixture, so the shared reader takes the
        frontmatter fallback and sums both fields."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-01.md", "Do T01", [
                "type: implementation", "status: done",
                "cost_usd: 2.0", "cumulative_cost_usd: 10.0",
                "planned_cost_usd: 2.0",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["budget_projection"].status, "fired")
            self.assertFalse(decision.would_arm)

    # --- Class 2: judge-editing ---

    def test_judge_editing_fires_on_driver_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                # A named decision module, not any path under the package.
                # `JUDGE_PATHS` stopped covering `specfuse/loop/` wholesale
                # (#1938): a WU producing a module that decides nothing no
                # longer fires this class, and `some_module.py` -- which does
                # not exist -- would now be one of those.
                "produces: [specfuse/loop/gate_eval.py]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["judge_editing"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_judge_editing_stays_clean_on_ordinary_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["judge_editing"].status, "clean")

    # --- Class 3: decision-class paths ---

    def test_decision_class_paths_fires_on_dependency_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [requirements.txt]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["decision_class_paths"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_decision_class_paths_stays_clean_on_ordinary_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["decision_class_paths"].status, "clean")

    def test_decision_class_paths_fires_on_maven_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [pom.xml]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["decision_class_paths"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_decision_class_paths_fires_on_each_covered_exact_manifest(self):
        covered = (
            "pyproject.toml", "package.json", "pom.xml", "build.gradle",
            "build.gradle.kts", "Cargo.toml", "go.mod", "Gemfile",
            "composer.json",
        )
        for manifest in covered:
            with tempfile.TemporaryDirectory() as tmp:
                feature = Path(tmp) / "feature"
                _base_feature(feature)
                _wu(feature, "WU-05.md", "Do T05", [
                    "type: implementation", "status: pending",
                    "cost_usd: 0.0", "planned_cost_usd: 1.0",
                    f"produces: [{manifest}]",
                    "provenance: RETRO-1",
                ])
                decision = evaluate_arm_predicate(feature, 1)
                self.assertEqual(
                    decision.classes["decision_class_paths"].status, "fired", manifest
                )

    def test_decision_class_paths_fires_on_each_covered_pattern(self):
        cases = ("requirements.txt", "requirements-dev.txt", "App.csproj",
                 "sub/dir/App.csproj")
        for path in cases:
            with tempfile.TemporaryDirectory() as tmp:
                feature = Path(tmp) / "feature"
                _base_feature(feature)
                _wu(feature, "WU-05.md", "Do T05", [
                    "type: implementation", "status: pending",
                    "cost_usd: 0.0", "planned_cost_usd: 1.0",
                    f"produces: [{path}]",
                    "provenance: RETRO-1",
                ])
                decision = evaluate_arm_predicate(feature, 1)
                self.assertEqual(
                    decision.classes["decision_class_paths"].status, "fired", path
                )

    def test_decision_class_paths_not_evaluable_on_glob_or_directory(self):
        for path in ("src/**", "config/"):
            with tempfile.TemporaryDirectory() as tmp:
                feature = Path(tmp) / "feature"
                _base_feature(feature)
                _wu(feature, "WU-05.md", "Do T05", [
                    "type: implementation", "status: pending",
                    "cost_usd: 0.0", "planned_cost_usd: 1.0",
                    f"produces: [{path}]",
                    "provenance: RETRO-1",
                ])
                decision = evaluate_arm_predicate(feature, 1)
                self.assertEqual(
                    decision.classes["decision_class_paths"].status,
                    "not_evaluable",
                    path,
                )
                self.assertFalse(decision.would_arm)

    def test_decision_class_paths_covered_precedes_undecidable(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [pom.xml, src/**]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["decision_class_paths"].status, "fired")

    def test_decision_class_paths_clean_reason_names_coverage_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            verdict = decision.classes["decision_class_paths"]
            self.assertEqual(verdict.status, "clean")
            self.assertTrue(verdict.reason)
            self.assertIn("pom.xml", verdict.reason)

    def test_decision_class_paths_not_evaluable_reason_names_path_and_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [src/**]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            reason = decision.classes["decision_class_paths"].reason
            self.assertIn("src/**", reason)
            self.assertIn("trigger 2", reason)

    def test_decision_class_paths_named_uncovered_entries_have_reasons(self):
        from specfuse.loop.arm_eval import DEPENDENCY_MANIFEST_NAMED_UNCOVERED

        for pattern, reason in DEPENDENCY_MANIFEST_NAMED_UNCOVERED.items():
            self.assertTrue(reason, pattern)

    # --- Class 4: retroactive edits ---

    def test_retroactive_edits_fires_on_passed_gate_goal_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature, t01_title="Do T01")
            # Mutate T01's title after the baseline snapshot was taken.
            _wu(feature, "WU-01.md", "A totally different goal", [
                "type: implementation", "status: done",
                "cost_usd: 2.0", "planned_cost_usd: 2.0",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["retroactive_edits"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_retroactive_edits_stays_clean_when_gate_not_yet_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature, gate1_status="open")
            # Mutate T01's title too, but gate 1 is not "passed" yet, so this
            # is in-flight editing, not a retroactive edit.
            _wu(feature, "WU-01.md", "A totally different goal", [
                "type: implementation", "status: done",
                "cost_usd: 2.0", "planned_cost_usd: 2.0",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["retroactive_edits"].status, "clean")

    # --- Class 5: drift caps ---

    def test_drift_caps_fires_on_added_wu_count_over_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            gate2_wus = [
                (f"{FEATURE_ID}/T05", "WU-05.md"),
                (f"{FEATURE_ID}/T06", "WU-06.md"),
            ]
            _plan_md(feature, gate2_wus)
            _wu(feature, "WU-01.md", "Do T01", [
                "type: implementation", "status: done",
                "cost_usd: 2.0", "planned_cost_usd: 2.0",
            ])
            _wu(feature, "WU-90.md", "Close gate 1", [
                "type: close-intermediate", "status: done",
                "cost_usd: 1.0", "planned_cost_usd: 1.0",
            ])
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [some/new/file.py]",
                "provenance: RETRO-1",
            ])
            _wu(feature, "WU-06.md", "Do T06", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [some/other/file.py]",
                "provenance: RETRO-2",
            ])
            _gate(feature, 1, "passed")
            _review(feature, 2, ["open_questions: []"])
            _baseline(feature)  # baseline has 2 WUs total -> cap is 0.5*2=1.0

            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["drift_caps"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_drift_caps_stays_clean_within_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["drift_caps"].status, "clean")

    # --- Class 6: missing provenance (veto channel) ---

    def test_missing_provenance_fires_on_added_wu_without_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: pending",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [some/new/file.py]",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["missing_provenance"].status, "fired")
            self.assertFalse(decision.would_arm)

    def test_missing_provenance_stays_clean_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["missing_provenance"].status, "clean")

    # --- Class 7: open questions / human-only (veto channel) ---

    def test_open_questions_fires_when_field_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature, review_fm=["status: draft"])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(
                decision.classes["open_questions_human_only"].status, "fired"
            )
            self.assertFalse(decision.would_arm)

    def test_open_questions_fires_when_non_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature, review_fm=["open_questions: [needs a human]"])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(
                decision.classes["open_questions_human_only"].status, "fired"
            )
            self.assertFalse(decision.would_arm)

    def test_human_only_wu_fires(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature, t05_fm_extra=["human_only: true"])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(
                decision.classes["open_questions_human_only"].status, "fired"
            )
            self.assertFalse(decision.would_arm)

    def test_open_questions_stays_clean_when_present_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(
                decision.classes["open_questions_human_only"].status, "clean"
            )

    def test_review_missing_file_fires(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            (feature / "GATE-02-REVIEW.md").unlink()
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(
                decision.classes["open_questions_human_only"].status, "fired"
            )
            self.assertFalse(decision.would_arm)


if __name__ == "__main__":
    unittest.main()
