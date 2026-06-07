#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Per-gate cost budget brake — FEAT-2026-0007/T07.

Covers:
  (a) gate_budget_usd returns the parsed float when cost_budget_usd is set.
  (b) gate_budget_usd returns None when the field is absent.
  (c) gate_spent_usd sums cost_usd across done WU frontmatters and ignores
      non-done WUs.
  (d) _should_halt_for_budget returns True when spent >= budget, False below.
  (e) lint_plan accepts numeric cost_budget_usd and rejects non-numeric.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop, load_lint

loop = load_loop()
lint = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_PATH = REPO_ROOT / ".specfuse/scripts/lint_plan.py"


def _write_gate(path: Path, *, budget_line: str | None = None) -> None:
    lines = ["---", "gate: 1", "status: open"]
    if budget_line is not None:
        lines.append(budget_line)
    lines += ["---", "", "# Gate 1", ""]
    path.write_text("\n".join(lines))


def _write_wu(path: Path, *, wu_id: str, status: str,
              cost_usd: float | None = None) -> None:
    lines = [
        "---",
        f"id: {wu_id}",
        "type: implementation",
        "model: claude-sonnet-4-6",
        f"status: {status}",
        "attempts: 1",
    ]
    if cost_usd is not None:
        lines.append(f"cost_usd: {cost_usd}")
    lines += ["---", "", "# WU", ""]
    path.write_text("\n".join(lines))


def _write_plan_with_gate(feature: Path, *, with_close: bool = True) -> None:
    """Minimal PLAN.md with one gate referencing whatever WUs the test wrote.

    `with_close` is True for the lint integration cases that need the closing
    sequence to satisfy lint_plan's structural checks.
    """
    work_units = [
        "      - id: FEAT-2026-9701/T01",
        "        file: WU-T01.md",
        "        depends_on: []",
        "      - id: FEAT-2026-9701/T02",
        "        file: WU-T02.md",
        "        depends_on: [FEAT-2026-9701/T01]",
    ]
    if with_close:
        work_units += [
            "      - id: FEAT-2026-9701/G1-RETRO",
            "        file: WU-G1-RETRO.md",
            "        depends_on: [FEAT-2026-9701/T02]",
            "      - id: FEAT-2026-9701/G1-LESSONS",
            "        file: WU-G1-LESSONS.md",
            "        depends_on: [FEAT-2026-9701/G1-RETRO]",
            "      - id: FEAT-2026-9701/G1-DOCS",
            "        file: WU-G1-DOCS.md",
            "        depends_on: [FEAT-2026-9701/G1-LESSONS]",
            "      - id: FEAT-2026-9701/G1-PLAN",
            "        file: WU-G1-PLAN.md",
            "        depends_on: [FEAT-2026-9701/G1-DOCS]",
        ]
    plan = (
        "---\n"
        "feature_id: FEAT-2026-9701\n"
        "title: Budget brake fixture\n"
        "slug: budget-fixture\n"
        "branch: feat/budget-fixture\n"
        "roadmap_goal: exercise the per-gate budget brake under test\n"
        "status: active\n"
        "---\n\n"
        "# Plan\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        + "\n".join(work_units) + "\n"
        "```\n"
    )
    (feature / "PLAN.md").write_text(plan)


# --------------------------------------------------------------------------- #
# Helper unit tests                                                           #
# --------------------------------------------------------------------------- #


class TestGateBudgetUsd(unittest.TestCase):

    def test_returns_float_when_field_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_file = Path(tmp) / "GATE-01.md"
            _write_gate(gate_file, budget_line="cost_budget_usd: 2.5")
            self.assertEqual(loop.gate_budget_usd(gate_file), 2.5)

    def test_returns_none_when_field_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_file = Path(tmp) / "GATE-01.md"
            _write_gate(gate_file)
            self.assertIsNone(loop.gate_budget_usd(gate_file))

    def test_raises_on_non_numeric_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_file = Path(tmp) / "GATE-01.md"
            _write_gate(gate_file, budget_line='cost_budget_usd: "two-fifty"')
            with self.assertRaises(ValueError) as ctx:
                loop.gate_budget_usd(gate_file)
            self.assertIn("GATE-01.md", str(ctx.exception))


class TestGateSpentUsd(unittest.TestCase):

    def test_sums_done_wus_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            _write_wu(feature / "WU-T01.md", wu_id="FEAT-2026-9701/T01",
                      status="done", cost_usd=0.5)
            _write_wu(feature / "WU-T02.md", wu_id="FEAT-2026-9701/T02",
                      status="pending", cost_usd=1.25)
            _write_wu(feature / "WU-T03.md", wu_id="FEAT-2026-9701/T03",
                      status="done", cost_usd=0.75)
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-9701/T01", "file": "WU-T01.md"},
                    {"id": "FEAT-2026-9701/T02", "file": "WU-T02.md"},
                    {"id": "FEAT-2026-9701/T03", "file": "WU-T03.md"},
                ],
            }
            spent = loop.gate_spent_usd({}, gate, feature)
            self.assertAlmostEqual(spent, 1.25, places=6)

    def test_missing_cost_contributes_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            _write_wu(feature / "WU-T01.md", wu_id="FEAT-2026-9701/T01",
                      status="done", cost_usd=None)
            _write_wu(feature / "WU-T02.md", wu_id="FEAT-2026-9701/T02",
                      status="done", cost_usd=0.4)
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-9701/T01", "file": "WU-T01.md"},
                    {"id": "FEAT-2026-9701/T02", "file": "WU-T02.md"},
                ],
            }
            self.assertAlmostEqual(
                loop.gate_spent_usd({}, gate, feature), 0.4, places=6)


class TestShouldHaltForBudget(unittest.TestCase):
    """The test-extracted run-loop predicate: budget set + spent >= budget
    returns True; below budget or no budget returns False."""

    def _setup(self, *, budget: float | None, t01_cost: float,
               t01_status: str = "done"):
        tmp = tempfile.mkdtemp()
        feature = Path(tmp)
        gate_path = feature / "GATE-01.md"
        if budget is None:
            _write_gate(gate_path)
        else:
            _write_gate(gate_path, budget_line=f"cost_budget_usd: {budget}")
        _write_wu(feature / "WU-T01.md", wu_id="FEAT-2026-9701/T01",
                  status=t01_status, cost_usd=t01_cost)
        gate = {
            "file": "GATE-01.md",
            "work_units": [
                {"id": "FEAT-2026-9701/T01", "file": "WU-T01.md"},
            ],
        }
        return feature, gate

    def test_over_budget_returns_true(self):
        feature, gate = self._setup(budget=1.0, t01_cost=1.5)
        self.assertTrue(loop._should_halt_for_budget({}, gate, feature))

    def test_under_budget_returns_false(self):
        feature, gate = self._setup(budget=2.0, t01_cost=0.5)
        self.assertFalse(loop._should_halt_for_budget({}, gate, feature))

    def test_no_budget_returns_false(self):
        feature, gate = self._setup(budget=None, t01_cost=10.0)
        self.assertFalse(loop._should_halt_for_budget({}, gate, feature))


# --------------------------------------------------------------------------- #
# lint_plan integration                                                       #
# --------------------------------------------------------------------------- #


def _write_full_lint_fixture(feature: Path, *, budget_line: str | None) -> None:
    """Write a PLAN + GATE + WU set that satisfies every other lint check, so
    the only variable is the GATE.md cost_budget_usd line under test."""
    _write_plan_with_gate(feature)
    gate_path = feature / "GATE-01.md"
    if budget_line is None:
        _write_gate(gate_path)
    else:
        _write_gate(gate_path, budget_line=budget_line)

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    wus = [
        ("WU-T01.md", "FEAT-2026-9701/T01", "implementation", "done"),
        ("WU-T02.md", "FEAT-2026-9701/T02", "implementation", "done"),
        ("WU-G1-RETRO.md", "FEAT-2026-9701/G1-RETRO", "retrospective", "done"),
        ("WU-G1-LESSONS.md", "FEAT-2026-9701/G1-LESSONS", "lessons", "done"),
        ("WU-G1-DOCS.md", "FEAT-2026-9701/G1-DOCS", "docs", "done"),
        ("WU-G1-PLAN.md", "FEAT-2026-9701/G1-PLAN", "plan-next", "done"),
    ]
    for fname, wu_id, wu_type, status in wus:
        (feature / fname).write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\n"
            f"model: claude-sonnet-4-6\nstatus: {status}\nattempts: 1\n---\n"
            f"\n# {fname}{body}"
        )


class TestLintCostBudget(unittest.TestCase):
    """lint_plan accepts numeric cost_budget_usd; rejects non-numeric."""

    def test_lint_accepts_numeric_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            _write_full_lint_fixture(feature, budget_line="cost_budget_usd: 2.5")
            errs = lint.lint(feature)
            self.assertEqual(errs, [],
                             f"numeric cost_budget_usd must lint clean; errs={errs}")

    def test_lint_rejects_non_numeric_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            _write_full_lint_fixture(
                feature, budget_line='cost_budget_usd: "two-fifty"')
            errs = lint.lint(feature)
            self.assertTrue(errs, "non-numeric cost_budget_usd must produce errors")
            self.assertTrue(
                any("cost_budget_usd" in e and "numeric" in e for e in errs),
                f"error must name cost_budget_usd and numeric; errs={errs}",
            )

    def test_lint_cli_exit_codes(self):
        """End-to-end via subprocess: the linter CLI exits 0 on a numeric
        budget and non-zero on the non-numeric one (matches AC 7(e))."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            _write_full_lint_fixture(feature, budget_line="cost_budget_usd: 2.5")
            rc_ok = subprocess.run(
                [sys.executable, str(LINT_PATH), str(feature)],
                capture_output=True, text=True,
            ).returncode
            self.assertEqual(rc_ok, 0)

            _write_full_lint_fixture(
                feature, budget_line='cost_budget_usd: "two-fifty"')
            rc_bad = subprocess.run(
                [sys.executable, str(LINT_PATH), str(feature)],
                capture_output=True, text=True,
            ).returncode
            self.assertNotEqual(rc_bad, 0)


if __name__ == "__main__":
    unittest.main()
