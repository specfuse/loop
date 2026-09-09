#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Criteria-per-gate WARN (#3269).

Nothing bounded how many acceptance criteria a gate carried. In one consumer
a single gate ran six close attempts against 46 criteria (three of them
re-closes at $8–13 each, every one re-deriving the lot), and closes were
close to half of loop spend. `check_criteria_per_gate` counts the acceptance
criteria bullets of a gate's substantive work units and prints one WARN when
the total exceeds `MAX_CRITERIA_PER_GATE_WARN`. WARN, never ERROR: an ERROR
would break every existing large gate on the next scaffold upgrade, and the
number is a starting point for the operator, not a verdict.

Covers:
  - WARN when a gate's substantive criteria exceed the threshold
  - silent at the threshold
  - ceremony WUs (close, plan-next, ...) are not counted
  - a `passed` gate and a sealed feature are skipped
  - never appends to the errors list (exit code 0)
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

_PLAN_FM = (
    "feature_id: FEAT-2026-9997\n"
    "title: Criteria cap lint test\n"
    "branch: feat/criteria-cap-lint-test\n"
    "roadmap_goal: Verify the criteria-per-gate WARN.\n"
    "status: active\n"
)


def _graph(n_units: int) -> list:
    units = [{"id": f"FEAT-2026-9997/T{i:02d}", "file": f"WU-{i:02d}.md", "depends_on": []}
             for i in range(1, n_units + 1)]
    units.append({"id": "FEAT-2026-9997/G1-CLOSE", "file": "WU-90-close.md",
                  "depends_on": [u["id"] for u in units]})
    return [{"gate": 1, "file": "GATE-01.md", "work_units": units}]


def _write_wu(feature: Path, wu_file: str, wu_id: str, wu_type: str,
              n_criteria: int, status: str = "pending") -> None:
    bullets = "".join(f"- criterion {i} — `check_{i}` exits 0\n" for i in range(n_criteria))
    (feature / wu_file).write_text(
        "---\n"
        f"id: {wu_id}\ntype: {wu_type}\nstatus: {status}\nattempts: 0\n"
        "---\n\n# WU\n\n**Context.** test\n\n"
        f"**Acceptance criteria.**\n\n{bullets}\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )


def _make_feature(tmpdir: str, per_unit: list, *, gate_status: str = "open",
                  plan_status: str = "active") -> tuple[Path, dict, list]:
    feature = Path(tmpdir) / "feature"
    feature.mkdir(exist_ok=True)
    fm = _PLAN_FM.replace("status: active", f"status: {plan_status}")
    gates = _graph(len(per_unit))
    rows = "".join(
        f"      - id: {u['id']}\n        file: {u['file']}\n"
        f"        depends_on: [{', '.join(u['depends_on'])}]\n"
        for u in gates[0]["work_units"]
    )
    graph = (
        "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n{rows}```\n"
    )
    (feature / "PLAN.md").write_text(f"---\n{fm}---\n\n# Plan\n\n{graph}")
    (feature / "GATE-01.md").write_text(f"---\ngate: 1\nstatus: {gate_status}\n---\n\n# Gate 1\n")
    for i, n in enumerate(per_unit, start=1):
        _write_wu(feature, f"WU-{i:02d}.md", f"FEAT-2026-9997/T{i:02d}", "implementation", n)
    # The closing unit carries its own (many) criteria; they must not count.
    _write_wu(feature, "WU-90-close.md", "FEAT-2026-9997/G1-CLOSE", "close", 30)
    plan_fm = {"feature_id": "FEAT-2026-9997", "status": plan_status}
    return feature, plan_fm, gates


def _run(feature: Path, plan_fm: dict, gates: list) -> tuple[str, list]:
    errs: list = []
    buf = io.StringIO()
    with redirect_stdout(buf):
        lint_plan.check_criteria_per_gate(feature, plan_fm, gates, errs)
    return buf.getvalue(), errs


class TestCriteriaPerGateWarn(unittest.TestCase):
    def test_threshold_is_a_positive_int(self):
        self.assertIsInstance(lint_plan.MAX_CRITERIA_PER_GATE_WARN, int)
        self.assertGreater(lint_plan.MAX_CRITERIA_PER_GATE_WARN, 0)

    def test_over_threshold_warns_once_naming_count_and_threshold(self):
        cap = lint_plan.MAX_CRITERIA_PER_GATE_WARN
        with tempfile.TemporaryDirectory() as tmp:
            feature, plan_fm, gates = _make_feature(tmp, [cap, 1])
            out, errs = _run(feature, plan_fm, gates)
        self.assertEqual(out.count("WARN:"), 1, out)
        self.assertIn("gate 1", out)
        self.assertIn(f"{cap + 1} acceptance criteria", out)
        self.assertIn(f"above {cap}", out)
        self.assertIn("two gates", out)
        self.assertEqual(errs, [], "WARN-only: never an error")

    def test_at_threshold_is_silent(self):
        cap = lint_plan.MAX_CRITERIA_PER_GATE_WARN
        with tempfile.TemporaryDirectory() as tmp:
            feature, plan_fm, gates = _make_feature(tmp, [cap - 3, 3])
            out, errs = _run(feature, plan_fm, gates)
        self.assertEqual(out, "")
        self.assertEqual(errs, [])

    def test_ceremony_units_are_not_counted(self):
        """The close WU in the fixture carries 30 bullets of its own; only the
        substantive units' criteria are the gate's definition of done."""
        with tempfile.TemporaryDirectory() as tmp:
            feature, plan_fm, gates = _make_feature(tmp, [2, 2])
            out, _ = _run(feature, plan_fm, gates)
        self.assertEqual(out, "")

    def test_passed_gate_and_sealed_feature_are_skipped(self):
        cap = lint_plan.MAX_CRITERIA_PER_GATE_WARN
        with tempfile.TemporaryDirectory() as tmp:
            feature, plan_fm, gates = _make_feature(tmp, [cap + 5], gate_status="passed")
            out, _ = _run(feature, plan_fm, gates)
            self.assertEqual(out, "", "a passed gate is history, not a plan to fix")
        with tempfile.TemporaryDirectory() as tmp:
            feature, plan_fm, gates = _make_feature(tmp, [cap + 5], plan_status="done")
            out, _ = _run(feature, plan_fm, gates)
            self.assertEqual(out, "")

    def test_lint_feature_entry_point_emits_the_warn_and_exits_zero(self):
        """The WARN reaches `specfuse lint`'s output through the normal
        aggregation path and does not turn the exit code red."""
        cap = lint_plan.MAX_CRITERIA_PER_GATE_WARN
        with tempfile.TemporaryDirectory() as tmp:
            feature, _, _ = _make_feature(tmp, [cap + 1])
            buf = io.StringIO()
            with redirect_stdout(buf):
                errs = lint_plan._lint_impl(feature)
        out = buf.getvalue()
        self.assertIn("acceptance criteria", out)
        self.assertFalse(
            any("acceptance criteria" in e and "above" in e for e in errs),
            "the cap must be a WARN, never an ERROR",
        )


if __name__ == "__main__":
    unittest.main()
