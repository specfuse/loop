#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for planned_cost_usd lint WARNs (FEAT-2026-0015/T08).

Covers check_planned_cost():
  - WARN on active/draft WU missing planned_cost_usd
  - Sealed WU (wu done AND plan done) skipped silently
  - WARN on PLAN.md missing planned_cost_usd
  - WARN when PLAN.md cost differs from WU sum by > 10%
  - Silent when PLAN.md cost is within 10% of WU sum
  - WARN when PLAN has field but active WUs don't
  - Exit code 0 (empty errs list) for all warn scenarios
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

_VALID_PLAN_FM = (
    "feature_id: FEAT-2026-9998\n"
    "title: Planned cost lint test\n"
    "branch: feat/planned-cost-lint-test\n"
    "roadmap_goal: Verify planned_cost_usd lint.\n"
    "status: active\n"
)

_VALID_GRAPH = (
    "```yaml\n"
    "gates:\n"
    "  - gate: 1\n"
    "    work_units:\n"
    "      - id: FEAT-2026-9998/T01\n"
    "        file: WU-01-impl.md\n"
    "        depends_on: []\n"
    "      - id: FEAT-2026-9998/G1-CLOSE\n"
    "        file: WU-90-close.md\n"
    "        depends_on: [FEAT-2026-9998/T01]\n"
    "```\n"
)


def _make_feature(tmpdir: str, *, plan_fm: str = _VALID_PLAN_FM,
                  extra_fm: str = "") -> Path:
    """Create a minimal valid feature dir with PLAN.md only (no WU files yet)."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir(exist_ok=True)
    content = f"---\n{plan_fm}{extra_fm}---\n\n# Plan\n\n{_VALID_GRAPH}"
    (feature / "PLAN.md").write_text(content)
    return feature


def _write_wu(feature: Path, *, wu_id: str, wu_file: str, wu_type: str,
              wu_status: str = "done",
              planned_cost: float | None = None) -> None:
    cost_line = f"planned_cost_usd: {planned_cost}\n" if planned_cost is not None else ""
    (feature / wu_file).write_text(
        "---\n"
        f"id: {wu_id}\n"
        f"type: {wu_type}\n"
        f"status: {wu_status}\n"
        "attempts: 1\n"
        f"{cost_line}"
        "---\n\n# Title\n"
    )


def _run_lint(feature: Path) -> tuple[list[str], str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        errs = lint_plan.lint(feature)
    return errs, buf.getvalue()


class TestPlannedCostLint(unittest.TestCase):

    def test_lint_warns_on_active_wu_missing_planned_cost(self):
        """Non-sealed WU without planned_cost_usd → WARN naming the file, exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # PLAN is active → WU done is NOT sealed (plan not done)
            feature = _make_feature(tmpdir)
            _write_wu(feature, wu_id="FEAT-2026-9998/T01", wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done", planned_cost=None)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE", wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=1.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            self.assertIn("WARN:", stdout)
            self.assertIn("planned_cost_usd", stdout)
            self.assertIn("WU-01-impl.md", stdout)

    def test_lint_skips_warn_on_sealed_wu_missing_planned_cost(self):
        """Sealed feature (plan done + wu done) → no per-WU WARN even if field absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sealed_fm = (
                "feature_id: FEAT-2026-9998\n"
                "title: Planned cost lint test\n"
                "branch: feat/planned-cost-lint-test\n"
                "roadmap_goal: Verify planned_cost_usd lint.\n"
                "status: done\n"
            )
            feature = _make_feature(tmpdir, plan_fm=sealed_fm,
                                    extra_fm="planned_cost_usd: 0.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01", wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done", planned_cost=None)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE", wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=None)
            errs, stdout = _run_lint(feature)
            wu_warns = [ln for ln in stdout.splitlines()
                        if "WARN:" in ln and "planned_cost_usd" in ln
                        and "PLAN.md:" not in ln]
            self.assertEqual(wu_warns, [],
                             f"sealed WUs must not warn; stdout={stdout!r}")

    def test_lint_warns_on_plan_missing_planned_cost(self):
        """PLAN.md without planned_cost_usd → WARN mentioning PLAN.md, exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir)  # no planned_cost_usd in PLAN.md
            _write_wu(feature, wu_id="FEAT-2026-9998/T01", wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done", planned_cost=1.0)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE", wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=1.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            plan_warns = [ln for ln in stdout.splitlines()
                          if "WARN:" in ln and "PLAN.md" in ln
                          and "planned_cost_usd" in ln]
            self.assertTrue(plan_warns,
                            f"must warn about PLAN.md missing field; stdout={stdout!r}")

    def test_lint_warns_on_plan_wu_sum_delta_over_10pct(self):
        """PLAN.md cost vs WU sum delta > 10% → delta WARN with delta named, exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # PLAN = 10.00, WU sum = 5.00 → delta 50% > 10%
            feature = _make_feature(tmpdir, extra_fm="planned_cost_usd: 10.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01", wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done", planned_cost=4.0)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE", wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=1.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            delta_warns = [ln for ln in stdout.splitlines()
                           if "WARN:" in ln and "differs from sum" in ln]
            self.assertTrue(delta_warns,
                            f"must warn about delta; stdout={stdout!r}")
            self.assertIn("50%", stdout)

    def test_lint_silent_when_plan_wu_sum_within_10pct(self):
        """PLAN.md cost within 10% of WU sum → no delta WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # PLAN = 10.00, WU sum = 9.50 → delta 5% ≤ 10%
            feature = _make_feature(tmpdir, extra_fm="planned_cost_usd: 10.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01", wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done", planned_cost=8.5)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE", wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=1.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            delta_warns = [ln for ln in stdout.splitlines()
                           if "WARN:" in ln and "differs from sum" in ln]
            self.assertEqual(delta_warns, [],
                             f"must NOT warn for ≤10% delta; stdout={stdout!r}")

    def test_lint_warns_when_plan_has_field_but_wus_dont(self):
        """PLAN.md has planned_cost_usd but non-sealed WUs are missing it → WARN per WU."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # PLAN active → WUs with status=done are NOT sealed
            feature = _make_feature(tmpdir, extra_fm="planned_cost_usd: 5.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01", wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done", planned_cost=None)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE", wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=None)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            wu_warns = [ln for ln in stdout.splitlines()
                        if "WARN:" in ln and "planned_cost_usd" in ln
                        and "PLAN.md:" not in ln]
            self.assertTrue(wu_warns,
                            f"must warn for WUs missing field; stdout={stdout!r}")

    def test_lint_warns_on_ceremony_wu_below_cost_floor(self):
        """close WU with planned_cost_usd below the ceremony floor → WARN
        naming the file and the floor (#201)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, extra_fm="planned_cost_usd: 12.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01",
                      wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done",
                      planned_cost=10.0)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE",
                      wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=2.5)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], "floor finding must be WARN-only")
            floor_warns = [ln for ln in stdout.splitlines()
                           if "WARN:" in ln and "floor" in ln]
            self.assertTrue(floor_warns, f"expected floor WARN; {stdout!r}")
            self.assertIn("WU-90-close.md", floor_warns[0])

    def test_lint_silent_on_ceremony_wu_at_or_above_floor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, extra_fm="planned_cost_usd: 15.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01",
                      wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done",
                      planned_cost=10.0)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE",
                      wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=5.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("floor", stdout)

    def test_lint_no_floor_warn_for_implementation_wu(self):
        """The floor applies to ceremony types only — a cheap implementation
        WU is a legitimate estimate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, extra_fm="planned_cost_usd: 7.50\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01",
                      wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done",
                      planned_cost=1.5)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE",
                      wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=6.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("floor", stdout)

    def test_lint_no_floor_warn_on_sealed_ceremony_wu(self):
        """Sealed feature: history is not re-estimated — no floor WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sealed_fm = (
                "feature_id: FEAT-2026-9998\n"
                "title: Planned cost lint test\n"
                "branch: feat/planned-cost-lint-test\n"
                "roadmap_goal: Verify planned_cost_usd lint.\n"
                "status: done\n"
            )
            feature = _make_feature(tmpdir, plan_fm=sealed_fm,
                                    extra_fm="planned_cost_usd: 12.00\n")
            _write_wu(feature, wu_id="FEAT-2026-9998/T01",
                      wu_file="WU-01-impl.md",
                      wu_type="implementation", wu_status="done",
                      planned_cost=10.0)
            _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE",
                      wu_file="WU-90-close.md",
                      wu_type="close", wu_status="done", planned_cost=2.0)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("floor", stdout)

    def test_lint_exit_code_zero_for_all_planned_cost_warns(self):
        """All planned_cost warn scenarios produce empty errs list (exit code 0)."""
        scenarios = [
            # (extra_fm for PLAN, wu1_cost, wu2_cost, label)
            ("", None, None, "PLAN missing, WUs missing"),
            ("planned_cost_usd: 10.00\n", None, None, "PLAN present, WUs missing"),
            ("planned_cost_usd: 10.00\n", 1.0, 1.0, "big delta >10%"),
            ("", 1.0, 1.0, "PLAN missing, WUs present"),
        ]
        for extra_fm, cost1, cost2, label in scenarios:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmpdir:
                    feature = _make_feature(tmpdir, extra_fm=extra_fm)
                    _write_wu(feature, wu_id="FEAT-2026-9998/T01",
                              wu_file="WU-01-impl.md",
                              wu_type="implementation", wu_status="done",
                              planned_cost=cost1)
                    _write_wu(feature, wu_id="FEAT-2026-9998/G1-CLOSE",
                              wu_file="WU-90-close.md",
                              wu_type="close", wu_status="done",
                              planned_cost=cost2)
                    errs, _ = _run_lint(feature)
                    self.assertEqual(errs, [],
                                     f"[{label}] planned_cost warns must never "
                                     f"produce errs; errs={errs}")


if __name__ == "__main__":
    unittest.main()
