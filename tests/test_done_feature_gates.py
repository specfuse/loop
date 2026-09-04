#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0072/T03: a `status: done` feature must have every gate `passed`."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURES_DIR = REPO_ROOT / ".specfuse/features"

_GRAPH = (
    "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
    "      - id: FEAT-2026-0099/T01\n        file: WU-01.md\n"
    "        depends_on: []\n```\n"
)


def _plan_fm(status: str) -> str:
    return (
        "---\n"
        "feature_id: FEAT-2026-0099\n"
        "title: Test Feature\n"
        "branch: feat/test\n"
        "roadmap_goal: Test goal\n"
        f"status: {status}\n"
        "---\n"
    )


def _wu_fm(wid: str) -> str:
    return f"---\nid: {wid}\ntype: implementation\nstatus: done\n---\n"


def _build_feature(tmp_path: Path, plan_status: str, gate_status: str) -> Path:
    feat = tmp_path / "feat"
    feat.mkdir()
    (feat / "PLAN.md").write_text(_plan_fm(plan_status) + "\n" + _GRAPH)
    (feat / "WU-01.md").write_text(_wu_fm("FEAT-2026-0099/T01"))
    (feat / "GATE-01.md").write_text(f"---\nstatus: {gate_status}\n---\n\n# Gate 1\n")
    return feat


class TestDoneFeatureGates(unittest.TestCase):

    def test_done_feature_with_unpassed_gate_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "done", "awaiting_review")
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("done" in e and "GATE-01.md" in e for e in errs),
            f"expected done/unpassed-gate error; errs={errs}",
        )

    def test_done_feature_with_passed_gate_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "done", "passed")
            errs = lint_plan.lint(feat)
        self.assertFalse(
            any("GATE-01.md" in e and "status: done" in e for e in errs),
            f"passed gate should not trigger check; errs={errs}",
        )

    def test_non_done_feature_with_open_gate_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "active", "open")
            errs = lint_plan.lint(feat)
        self.assertFalse(
            any("GATE-01.md" in e and "not 'passed'" in e for e in errs),
            f"non-done feature should not trigger check; errs={errs}",
        )

    def test_review_artifact_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "done", "passed")
            (feat / "GATE-01-REVIEW.md").write_text("Some review notes, no frontmatter.\n")
            errs = lint_plan.lint(feat)
        self.assertFalse(
            any("GATE-01-REVIEW.md" in e for e in errs),
            f"REVIEW artifact should never be treated as a gate file; errs={errs}",
        )

    def test_criteria_artifact_is_ignored(self):
        """FEAT-2026-0056's GATE-NN-CRITERIA.md is not a gate file.

        It matches the `GATE-*.md` glob and carries no `status` frontmatter, so
        before this skip every feature reaching `status: done` with a criteria
        artifact on disk failed the lint. FEAT-2026-0056 was the first, and it
        failed on its own artifact the moment its terminal flips fired.
        """
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "done", "passed")
            (feat / "GATE-01-CRITERIA.md").write_text(
                "### T01#1\n\n- **criterion:** does the thing\n"
                "- **state:** `unverified`\n"
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            any("GATE-01-CRITERIA.md" in e for e in errs),
            f"CRITERIA artifact should never be treated as a gate file; errs={errs}",
        )

    def test_work_unit_deliverable_named_gate_something_is_not_a_gate(self):
        """#2907: a unit's own deliverable, `GATE-03-CONSUMER-VALIDATION.md`,
        matched the `GATE-*.md` glob, carried no frontmatter, and failed the
        lint the moment the feature went `done`. Gate files are the ones the
        PLAN graph names, not everything that starts with `GATE-`."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "done", "passed")
            (feat / "GATE-03-CONSUMER-VALIDATION.md").write_text(
                "# Consumer validation evidence\n\nProbed 3 consumers; all green.\n"
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            any("GATE-03-CONSUMER-VALIDATION.md" in e for e in errs),
            f"a deliverable is not a gate file; errs={errs}",
        )

    def test_gate_named_in_plan_but_missing_status_is_still_reported(self):
        # The allowlist must not weaken the check: a real gate that the PLAN
        # names and that is not `passed` is still an error on a done feature.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), "done", "open")
            errs = lint_plan.lint(feat)
        self.assertTrue(any("GATE-01.md" in e and "not 'passed'" in e for e in errs), errs)

    def test_excluded_feature_is_not_reported(self):
        errs = lint_plan.check_done_feature_gates(
            FEATURES_DIR / "FEAT-2026-0001-health-endpoint", {"status": "done"}
        )
        self.assertEqual(errs, [])

    def test_exclusions_have_non_empty_reasons(self):
        for feature_id, reason in lint_plan.DONE_FEATURE_GATE_EXCLUSIONS.items():
            self.assertTrue(
                isinstance(reason, str) and reason.strip(),
                f"{feature_id}: exclusion reason must be a non-empty string",
            )

    def test_exclusions_point_at_existing_directories(self):
        for feature_id in lint_plan.DONE_FEATURE_GATE_EXCLUSIONS:
            self.assertTrue(
                (FEATURES_DIR / feature_id).is_dir(),
                f"{feature_id}: exclusion names a feature directory that does not exist",
            )

    def test_tree_wide_sweep_has_zero_findings(self):
        for feature_dir in sorted(p for p in FEATURES_DIR.iterdir() if p.is_dir()):
            plan = feature_dir / "PLAN.md"
            if not plan.exists():
                continue
            fm, _ = lint_plan.read_frontmatter(plan)
            errs = lint_plan.check_done_feature_gates(feature_dir, fm)
            self.assertEqual(
                errs, [], f"{feature_dir.name}: unexpected done-gate findings: {errs}"
            )


if __name__ == "__main__":
    unittest.main()
