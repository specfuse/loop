#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Post-dispatch gate-budget breach report — FEAT-2026-0062/T03.

The pre-dispatch brake (`_should_halt_for_budget`, checked before each WU
dispatch) cannot see an overrun incurred by a gate's own final work unit —
there is no subsequent dispatch to halt in front of. `_should_report_budget_breach`
is the sibling predicate evaluated after a WU's outcome resolves; the run loop
reports the breach as a `human_escalation` event (`reason:
gate_budget_exceeded_post_dispatch`) once every WU in the gate is done.

Covers:
  (a) unit: `_should_report_budget_breach` mirrors `_should_halt_for_budget`'s
      bool shape (over/under/no budget).
  (b) integration: a gate whose only WU breaches budget reports it after that
      WU completes — the case the pre-dispatch check structurally cannot reach.
  (c) integration: a gate that halts on the existing pre-dispatch check still
      halts there, unchanged, and does NOT also get a post-dispatch report for
      the same overrun (no double report).
  (d) integration: a gate that stays within budget, or declares no budget at
      all, reports nothing new.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, with_deliverable
from tests.test_driver_integration import _read_events

loop = load_loop()


# --------------------------------------------------------------------------- #
# Unit — the predicate itself                                                #
# --------------------------------------------------------------------------- #


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


class TestShouldReportBudgetBreach(unittest.TestCase):
    """Sibling of TestShouldHaltForBudget in test_loop_gate_budget.py — same
    shape, evaluated post-outcome rather than pre-dispatch."""

    def _setup(self, *, budget: float | None, t01_cost: float):
        tmp = tempfile.mkdtemp()
        feature = Path(tmp)
        gate_path = feature / "GATE-01.md"
        if budget is None:
            _write_gate(gate_path)
        else:
            _write_gate(gate_path, budget_line=f"cost_budget_usd: {budget}")
        _write_wu(feature / "WU-T01.md", wu_id="FEAT-2026-9701/T01",
                  status="done", cost_usd=t01_cost)
        gate = {
            "file": "GATE-01.md",
            "work_units": [
                {"id": "FEAT-2026-9701/T01", "file": "WU-T01.md"},
            ],
        }
        return feature, gate

    def test_over_budget_returns_true(self):
        feature, gate = self._setup(budget=1.0, t01_cost=1.5)
        self.assertTrue(loop._should_report_budget_breach({}, gate, feature))

    def test_under_budget_returns_false(self):
        feature, gate = self._setup(budget=2.0, t01_cost=0.5)
        self.assertFalse(loop._should_report_budget_breach({}, gate, feature))

    def test_no_budget_returns_false(self):
        feature, gate = self._setup(budget=None, t01_cost=10.0)
        self.assertFalse(loop._should_report_budget_breach({}, gate, feature))


# --------------------------------------------------------------------------- #
# Integration — the run loop                                                 #
# --------------------------------------------------------------------------- #


def _write_feature(root: Path, feature_id: str, slug: str, branch: str,
                    wus: list, *, budget: float | None = None) -> Path:
    """Minimal single-gate feature, no auto-added closing sequence.

    Unlike write_minimal_feature (test_driver_integration.py) this does not
    append the retro/lessons/docs/plan-next WUs — a plain gate of ordinary
    WUs is enough to exercise the budget brake / breach report, and keeping
    the gate to exactly the WUs under test means "all WUs in this gate are
    done" lines up with "the WU under test is the gate's last WU".
    """
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    plan_wu_rows = []
    for i, (wu_id, _wu_type, _wu_status) in enumerate(wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{wus[i - 1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Post-dispatch budget fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the post-dispatch budget breach report under test
status: active
---

# Plan: {slug}

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
{chr(10).join(plan_wu_rows)}
```
"""
    (fdir / "PLAN.md").write_text(plan)

    gate_lines = ["---", "gate: 1", "status: open"]
    if budget is not None:
        gate_lines.append(f"cost_budget_usd: {budget}")
    gate_lines += ["---", "", "# Gate 1", ""]
    (fdir / "GATE-01.md").write_text("\n".join(gate_lines))

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\n"
            f"model: claude-haiku-4-5-20251001\nstatus: {wu_status}\n"
            f"attempts: 0\n---\n\n# {tnn}{body}"
        )

    (root / ".gitignore").write_text(".specfuse/.loop.lock\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


def _cost_dispatch(cost_by_tnn: dict):
    """Dispatch stub returning (text, usage) with a per-WU cost_usd."""
    def fake_dispatch(wu, failure_note, cost_tracking=True):
        tnn = wu.wu_id.split("/")[-1]
        cost = cost_by_tnn.get(tnn, 0.0)
        return ("(simulated agent output)\n",
                {"cost_usd": cost, "input_tokens": 10, "output_tokens": 10})
    return fake_dispatch


def _passing_verify(wu, feature_dir, cfg=None):
    return True, "(stub)"


class _RunLoopCase(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        if name == "dispatch":
            replacement = with_deliverable(replacement)
        setattr(loop, name, replacement)

    def _breaches(self, events, reason="gate_budget_exceeded_post_dispatch"):
        return [e for e in events
                if e["event_type"] == "human_escalation"
                and e["payload"].get("reason") == reason]


class TestPostDispatchBreach(_RunLoopCase):

    def test_final_wu_overrun_is_reported(self):
        """A gate whose budget is breached only by its last WU currently
        produces no breach signal at all (fails on HEAD before this WU)."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_feature(
                root, "FEAT-2026-9101", "final-overrun",
                "feat/test-final-overrun",
                [("FEAT-2026-9101/T01", "implementation", "pending")],
                budget=1.0,
            )
            self._patch("dispatch", _cost_dispatch({"T01": 1.5}))
            self._patch("verify", _passing_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0, "single-WU gate should complete, not halt")

            fdir = root / ".specfuse/features/FEAT-2026-9101-final-overrun"
            events = _read_events(fdir / "events.jsonl")
            breaches = self._breaches(events)
            self.assertEqual(
                len(breaches), 1,
                f"expected exactly one post-dispatch breach; events={events}")
            payload = breaches[0]["payload"]
            self.assertEqual(payload["gate"], 1)
            self.assertEqual(payload["budget_usd"], 1.0)
            self.assertAlmostEqual(payload["spent_usd"], 1.5, places=6)
            self.assertEqual(payload["final_wu_id"], "FEAT-2026-9101/T01")

            # T01 itself still shows PASS/done — the report is additive, not
            # a refusal of already-completed work.
            t01_fm = loop.read_frontmatter(fdir / "WU-T01.md")[0]
            self.assertEqual(t01_fm.get("status"), "done")

    def test_within_budget_reports_nothing(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write_feature(
                root, "FEAT-2026-9102", "within-budget",
                "feat/test-within-budget",
                [("FEAT-2026-9102/T01", "implementation", "pending")],
                budget=5.0,
            )
            self._patch("dispatch", _cost_dispatch({"T01": 0.5}))
            self._patch("verify", _passing_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9102-within-budget"
            events = _read_events(fdir / "events.jsonl")
            self.assertEqual(self._breaches(events), [])

    def test_no_budget_declared_reports_nothing(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write_feature(
                root, "FEAT-2026-9103", "no-budget",
                "feat/test-no-budget",
                [("FEAT-2026-9103/T01", "implementation", "pending")],
                budget=None,
            )
            self._patch("dispatch", _cost_dispatch({"T01": 999.0}))
            self._patch("verify", _passing_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9103-no-budget"
            events = _read_events(fdir / "events.jsonl")
            self.assertEqual(self._breaches(events), [])

    def test_pre_dispatch_halt_unchanged_and_no_double_report(self):
        """A two-WU gate whose FIRST WU already breaches budget must still
        halt at the existing pre-dispatch check point, with its existing
        `gate_budget_exceeded` event unchanged — and must NOT also emit a
        post-dispatch breach for the same overrun (T02 never dispatches, so
        the gate's WUs are never all done)."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_feature(
                root, "FEAT-2026-9104", "pre-dispatch-halt",
                "feat/test-pre-dispatch-halt",
                [("FEAT-2026-9104/T01", "implementation", "pending"),
                 ("FEAT-2026-9104/T02", "implementation", "pending")],
                budget=1.0,
            )
            self._patch("dispatch", _cost_dispatch({"T01": 1.5, "T02": 0.0}))
            self._patch("verify", _passing_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "budget exceeded before T02 should halt")

            fdir = root / ".specfuse/features/FEAT-2026-9104-pre-dispatch-halt"
            events = _read_events(fdir / "events.jsonl")

            pre_dispatch = [e for e in events
                            if e["event_type"] == "human_escalation"
                            and e["payload"].get("reason") ==
                            "gate_budget_exceeded"]
            self.assertEqual(len(pre_dispatch), 1,
                              f"pre-dispatch halt event missing/changed; "
                              f"events={events}")
            self.assertEqual(pre_dispatch[0]["payload"]["next_wu_id"],
                              "FEAT-2026-9104/T02")

            self.assertEqual(
                self._breaches(events), [],
                "post-dispatch breach must not double-report the overrun "
                "the pre-dispatch check already halted on")

            t01_fm = loop.read_frontmatter(fdir / "WU-T01.md")[0]
            self.assertEqual(t01_fm.get("status"), "done")
            t02_fm = loop.read_frontmatter(fdir / "WU-T02.md")[0]
            self.assertNotEqual(t02_fm.get("status"), "done",
                                "T02 must never have dispatched")


if __name__ == "__main__":
    unittest.main()
