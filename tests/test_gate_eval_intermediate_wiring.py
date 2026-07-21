#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for FEAT-2026-0018/T05: intermediate gate auto-close wiring.

AC tests:
  test_auto_close_intermediate_fires_when_predicate_passes
    — predicate fires on a clean gate-1 of a two-gate feature; asserts
      (True, decision), RETROSPECTIVE stub, WU frontmatter, events.

  test_auto_close_intermediate_refuses_on_blocked_human
    — blocked_human event in chain causes predicate to refuse; asserts
      (False, decision) and that no files are mutated.

  test_plan_next_dispatched_after_auto_intermediate
    — full dispatch-loop scenario: close-intermediate is auto-skipped;
      plan-next's dispatch is called exactly once.

  test_idempotent_append_on_re_arm
    — calling append_stub_retrospective_intermediate twice produces
      exactly one Gate N section.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_scripts = str(REPO_ROOT / ".specfuse/scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

from tests._loop_loader import load_loop  # noqa: E402

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------


def _write_plan_md_two_gate(fdir: Path, feature_id: str) -> None:
    """Two-gate feature so gate 1 is intermediate (not terminal)."""
    (fdir / "PLAN.md").write_text(
        f"---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test\n"
        f"branch: feat/{feature_id.lower()}-test\n"
        f"roadmap_goal: test\n"
        f"status: active\n"
        f"---\n\n# Plan\n\n```yaml\n"
        f"gates:\n"
        f"  - gate: 1\n"
        f"    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {feature_id}/T01\n"
        f"        file: WU-01.md\n"
        f"        depends_on: []\n"
        f"      - id: {feature_id}/G1-CI\n"
        f"        file: WU-ci.md\n"
        f"        depends_on: [{feature_id}/T01]\n"
        f"      - id: {feature_id}/G1-PLAN\n"
        f"        file: WU-plan.md\n"
        f"        depends_on: [{feature_id}/G1-CI]\n"
        f"  - gate: 2\n"
        f"    file: GATE-02.md\n"
        f"    work_units:\n"
        f"      - id: {feature_id}/T02\n"
        f"        file: WU-02.md\n"
        f"        depends_on: []\n"
        f"```\n"
    )


def _write_wu_impl(fdir: Path, wu_id: str, filename: str,
                   cost: float = 0.5, planned: float = 0.5) -> None:
    (fdir / filename).write_text(
        f"---\nid: {wu_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: done\nattempts: 1\ncost_usd: {cost}\nplanned_cost_usd: {planned}\n"
        f"---\n\n# Impl{_WU_BODY}"
    )


def _write_wu_close_intermediate(fdir: Path, wu_id: str, filename: str) -> None:
    (fdir / filename).write_text(
        f"---\nid: {wu_id}\ntype: close-intermediate\nmodel: opus\n"
        f"status: pending\nattempts: 0\n"
        f"---\n\n# Close-intermediate{_WU_BODY}"
    )


def _write_wu_plan_next(fdir: Path, wu_id: str, filename: str) -> None:
    (fdir / filename).write_text(
        f"---\nid: {wu_id}\ntype: plan-next\nmodel: opus\n"
        f"status: pending\nattempts: 0\n"
        f"---\n\n# Plan-next{_WU_BODY}"
    )


def _write_gate_file(fdir: Path, gate_num: int) -> None:
    (fdir / f"GATE-{gate_num:02d}.md").write_text(
        f"---\ngate: {gate_num}\nstatus: awaiting_review\n---\n\n# Gate {gate_num}\n"
    )


def _write_task_completed_event(fdir: Path, wu_id: str) -> None:
    ev = json.dumps({
        "event_type": "task_completed",
        "correlation_id": wu_id,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "source": "driver",
        "source_version": "0.2.0",
        "payload": {},
    })
    with (fdir / "events.jsonl").open("a") as f:
        f.write(ev + "\n")


def _write_blocked_human_event(fdir: Path, wu_id: str) -> None:
    ev = json.dumps({
        "event_type": "human_escalation",
        "correlation_id": wu_id,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "source": "driver",
        "source_version": "0.2.0",
        "payload": {"reason": "spinning_detected"},
    })
    with (fdir / "events.jsonl").open("a") as f:
        f.write(ev + "\n")


def _make_gate_node(fdir: Path, feature_id: str, gate_num: int,
                    refs: list) -> "loop.GateNode":
    gate_file = fdir / f"GATE-{gate_num:02d}.md"
    fm, _ = loop.read_frontmatter(gate_file)
    return loop.GateNode(
        number=gate_num, file=gate_file, status=fm.get("status", "open"), refs=refs,
    )


def _make_ci_wu(fdir: Path, wu_id: str) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=fdir / "WU-ci.md",
        depends_on=[],
        type="close-intermediate",
        model="opus",
        effort="high",
        status="pending",
        attempts=0,
        title="Close-intermediate",
        body="",
    )


def _make_plan_next_wu(fdir: Path, wu_id: str) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=fdir / "WU-plan.md",
        depends_on=[],
        type="plan-next",
        model="opus",
        effort="high",
        status="pending",
        attempts=0,
        title="Plan-next",
        body="",
    )


def _load_events(events_path: Path) -> list[dict]:
    events = []
    if not events_path.exists():
        return events
    with events_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


# ---------------------------------------------------------------------------
# AC test 1: predicate fires on a clean intermediate gate
# ---------------------------------------------------------------------------


class TestAutoCloseIntermediateFiresOnCleanGate(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9970"
        fdir = self.root
        self.fdir = fdir

        _write_plan_md_two_gate(fdir, self.feature_id)
        _write_wu_impl(fdir, f"{self.feature_id}/T01", "WU-01.md")
        _write_wu_close_intermediate(fdir, f"{self.feature_id}/G1-CI", "WU-ci.md")
        _write_wu_plan_next(fdir, f"{self.feature_id}/G1-PLAN", "WU-plan.md")
        (fdir / "WU-02.md").write_text(
            f"---\nid: {self.feature_id}/T02\ntype: implementation\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# T02{_WU_BODY}"
        )
        _write_gate_file(fdir, 1)
        _write_gate_file(fdir, 2)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")

        refs_g1 = [
            {"id": f"{self.feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{self.feature_id}/G1-CI", "file": "WU-ci.md",
             "depends_on": [f"{self.feature_id}/T01"]},
            {"id": f"{self.feature_id}/G1-PLAN", "file": "WU-plan.md",
             "depends_on": [f"{self.feature_id}/G1-CI"]},
        ]
        refs_g2 = [
            {"id": f"{self.feature_id}/T02", "file": "WU-02.md", "depends_on": []},
        ]
        self.gate1 = _make_gate_node(fdir, self.feature_id, 1, refs_g1)
        self.gate2 = _make_gate_node(fdir, self.feature_id, 2, refs_g2)
        self.gates = [self.gate1, self.gate2]
        self.ci_wu = _make_ci_wu(fdir, f"{self.feature_id}/G1-CI")
        self.plan_next_wu = _make_plan_next_wu(fdir, f"{self.feature_id}/G1-PLAN")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_intermediate(
            self.fdir, self.feature_id, self.gate1, self.gates,
            self.events_path, self.root, self.ci_wu, self.plan_next_wu,
        )

    def test_per_wu_opt_out_refuses(self):
        # #189: close-intermediate marked auto_close_disabled → not auto-closed.
        self.ci_wu.file.write_text(
            f"---\nid: {self.feature_id}/G1-CI\ntype: close-intermediate\n"
            f"model: opus\nstatus: pending\nattempts: 0\n"
            f"auto_close_disabled: true\n---\n\n# CI\n"
        )
        result, decision = self._call()
        self.assertFalse(result)
        self.assertIn("auto_close_disabled_per_wu", decision.reasons)

    def test_returns_true_and_decision(self):
        result, decision = self._call()
        self.assertTrue(result)
        self.assertTrue(decision.auto)
        self.assertEqual(decision.predicate_version, "v1")

    def test_retrospective_has_gate_section(self):
        self._call()
        retro = self.fdir / "RETROSPECTIVE.md"
        self.assertTrue(retro.exists())
        self.assertTrue(
            re.search(r"^## Gate 1\b", retro.read_text(), re.MULTILINE),
            "RETROSPECTIVE.md must have ## Gate 1 heading",
        )

    def test_close_wu_status_done(self):
        self._call()
        fm, _ = loop.read_frontmatter(self.ci_wu.file)
        self.assertEqual(fm.get("status"), "done")

    def test_close_wu_auto_close_true(self):
        self._call()
        fm, _ = loop.read_frontmatter(self.ci_wu.file)
        self.assertIs(fm.get("auto_close"), True)

    def test_close_wu_no_verdict_met(self):
        self._call()
        fm, _ = loop.read_frontmatter(self.ci_wu.file)
        self.assertIsNone(
            fm.get("verdict"),
            "close-intermediate WU must NOT have verdict: met set by auto-close",
        )

    def test_events_has_auto_close_decision(self):
        self._call()
        events = _load_events(self.events_path)
        auto_close_events = [
            e for e in events if e.get("event_type") == "auto_close_decision"
        ]
        self.assertEqual(len(auto_close_events), 1)

    def test_event_gate_type_intermediate(self):
        self._call()
        events = _load_events(self.events_path)
        ev = next(e for e in events if e.get("event_type") == "auto_close_decision")
        self.assertEqual(ev["payload"]["gate_type"], "intermediate")

    def test_event_plan_next_dispatched_true(self):
        self._call()
        events = _load_events(self.events_path)
        ev = next(e for e in events if e.get("event_type") == "auto_close_decision")
        self.assertIs(ev["payload"]["plan_next_dispatched"], True)

    def test_event_predicate_version_v1(self):
        self._call()
        events = _load_events(self.events_path)
        ev = next(e for e in events if e.get("event_type") == "auto_close_decision")
        self.assertEqual(ev["payload"]["predicate_version"], "v1")


# ---------------------------------------------------------------------------
# AC test 2: predicate refuses on blocked_human event
# ---------------------------------------------------------------------------


class TestAutoCloseIntermediateRefusesOnBlockedHuman(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9971"
        fdir = self.root
        self.fdir = fdir

        _write_plan_md_two_gate(fdir, self.feature_id)
        _write_wu_impl(fdir, f"{self.feature_id}/T01", "WU-01.md")
        _write_wu_close_intermediate(fdir, f"{self.feature_id}/G1-CI", "WU-ci.md")
        _write_wu_plan_next(fdir, f"{self.feature_id}/G1-PLAN", "WU-plan.md")
        (fdir / "WU-02.md").write_text(
            f"---\nid: {self.feature_id}/T02\ntype: implementation\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# T02{_WU_BODY}"
        )
        _write_gate_file(fdir, 1)
        _write_gate_file(fdir, 2)
        # blocked_human event prevents auto=True
        _write_blocked_human_event(fdir, f"{self.feature_id}/T01")

        refs_g1 = [
            {"id": f"{self.feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{self.feature_id}/G1-CI", "file": "WU-ci.md",
             "depends_on": [f"{self.feature_id}/T01"]},
            {"id": f"{self.feature_id}/G1-PLAN", "file": "WU-plan.md",
             "depends_on": [f"{self.feature_id}/G1-CI"]},
        ]
        refs_g2 = [
            {"id": f"{self.feature_id}/T02", "file": "WU-02.md", "depends_on": []},
        ]
        self.gate1 = _make_gate_node(fdir, self.feature_id, 1, refs_g1)
        self.gate2 = _make_gate_node(fdir, self.feature_id, 2, refs_g2)
        self.gates = [self.gate1, self.gate2]
        self.ci_wu = _make_ci_wu(fdir, f"{self.feature_id}/G1-CI")
        self.plan_next_wu = _make_plan_next_wu(fdir, f"{self.feature_id}/G1-PLAN")
        self.events_path = fdir / "events.jsonl"
        self._ci_wu_content_before = self.ci_wu.file.read_text()

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_intermediate(
            self.fdir, self.feature_id, self.gate1, self.gates,
            self.events_path, self.root, self.ci_wu, self.plan_next_wu,
        )

    def test_returns_false_and_decision(self):
        result, decision = self._call()
        self.assertFalse(result)
        self.assertFalse(decision.auto)

    def test_no_retrospective_created(self):
        self._call()
        self.assertFalse((self.fdir / "RETROSPECTIVE.md").exists())

    def test_close_wu_unchanged(self):
        self._call()
        self.assertEqual(self.ci_wu.file.read_text(), self._ci_wu_content_before)

    def test_no_auto_close_decision_event(self):
        self._call()
        events = _load_events(self.events_path)
        auto_events = [
            e for e in events if e.get("event_type") == "auto_close_decision"
        ]
        self.assertEqual(
            len(auto_events), 0,
            "no auto_close_decision event must be written when predicate refuses",
        )


# ---------------------------------------------------------------------------
# AC test 3: plan-next is dispatched after auto-intermediate skip
# ---------------------------------------------------------------------------


class TestPlanNextDispatchedAfterAutoIntermediate(unittest.TestCase):
    """Unit-level scenario: simulate the dispatch loop's ready() calls to verify
    that after auto-closing close-intermediate (adding it to done_ids), the
    plan-next WU becomes ready and would be dispatched on the next iteration.

    This test exercises the dependency-frontier contract without invoking the
    full driver loop (which requires a real git tree). The invariant under test
    is that ready(units, done_ids) returns the plan-next WU after the auto-close
    skip — which is exactly what the dispatch loop observes.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9972"
        fdir = self.root
        self.fdir = fdir

        _write_plan_md_two_gate(fdir, self.feature_id)
        _write_wu_impl(fdir, f"{self.feature_id}/T01", "WU-01.md")
        _write_wu_close_intermediate(fdir, f"{self.feature_id}/G1-CI", "WU-ci.md")
        _write_wu_plan_next(fdir, f"{self.feature_id}/G1-PLAN", "WU-plan.md")
        (fdir / "WU-02.md").write_text(
            f"---\nid: {self.feature_id}/T02\ntype: implementation\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# T02{_WU_BODY}"
        )
        _write_gate_file(fdir, 1)
        _write_gate_file(fdir, 2)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")

        self.t01_id = f"{self.feature_id}/T01"
        self.ci_id = f"{self.feature_id}/G1-CI"
        self.plan_id = f"{self.feature_id}/G1-PLAN"
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _make_units(self) -> list:
        """Build the gate-1 unit list as the driver's load step would."""
        refs = [
            {"id": self.t01_id, "file": "WU-01.md", "depends_on": []},
            {"id": self.ci_id, "file": "WU-ci.md",
             "depends_on": [self.t01_id]},
            {"id": self.plan_id, "file": "WU-plan.md",
             "depends_on": [self.ci_id]},
        ]
        return [loop.load_wu(self.fdir, r) for r in refs]

    def test_close_intermediate_never_dispatched(self):
        """close-intermediate WU is auto-closed; it must not appear in
        the ready set once done_ids carries its ID."""
        units = self._make_units()
        done_ids: set[str] = {self.t01_id}  # T01 pre-done

        # First ready set: only G1-CI is ready.
        first_pending = loop.ready(units, done_ids)
        ci_wus = [w for w in first_pending if w.type == "close-intermediate"]
        self.assertEqual(len(ci_wus), 1, "G1-CI must be the sole ready WU here")

        ci_wu = ci_wus[0]
        gate1 = _make_gate_node(
            self.fdir, self.feature_id, 1,
            [{"id": self.t01_id, "file": "WU-01.md", "depends_on": []},
             {"id": self.ci_id, "file": "WU-ci.md",
              "depends_on": [self.t01_id]},
             {"id": self.plan_id, "file": "WU-plan.md",
              "depends_on": [self.ci_id]}],
        )
        gate2 = _make_gate_node(
            self.fdir, self.feature_id, 2,
            [{"id": f"{self.feature_id}/T02", "file": "WU-02.md",
              "depends_on": []}],
        )

        auto_closed, _ = loop.maybe_auto_close_intermediate(
            self.fdir, self.feature_id, gate1, [gate1, gate2],
            self.events_path, self.root, ci_wu, None,
        )
        self.assertTrue(auto_closed)
        # Mirror what the dispatch loop does: flip in-memory status AND add to done_ids
        ci_wu.status = loop.DONE
        done_ids.add(ci_wu.wu_id)

        # After auto-close, G1-CI must NOT appear in the next ready set.
        second_pending = loop.ready(units, done_ids)
        ci_still_ready = [w for w in second_pending if w.type == "close-intermediate"]
        self.assertEqual(ci_still_ready, [],
                         "close-intermediate must not be ready again after auto-close skip")

    def test_plan_next_dispatched_exactly_once(self):
        """After auto-close adds G1-CI to done_ids, G1-PLAN becomes the sole
        ready WU on the next loop iteration — exactly as the driver would see."""
        units = self._make_units()
        done_ids: set[str] = {self.t01_id}

        # Simulate auto-close skip: auto-close fires, done_ids gains G1-CI.
        ci_wu = next(w for w in units if w.type == "close-intermediate")
        gate1 = _make_gate_node(
            self.fdir, self.feature_id, 1,
            [{"id": self.t01_id, "file": "WU-01.md", "depends_on": []},
             {"id": self.ci_id, "file": "WU-ci.md",
              "depends_on": [self.t01_id]},
             {"id": self.plan_id, "file": "WU-plan.md",
              "depends_on": [self.ci_id]}],
        )
        gate2 = _make_gate_node(
            self.fdir, self.feature_id, 2,
            [{"id": f"{self.feature_id}/T02", "file": "WU-02.md",
              "depends_on": []}],
        )
        loop.maybe_auto_close_intermediate(
            self.fdir, self.feature_id, gate1, [gate1, gate2],
            self.events_path, self.root, ci_wu, None,
        )
        done_ids.add(ci_wu.wu_id)

        next_pending = loop.ready(units, done_ids)
        plan_wus = [w for w in next_pending if w.type == "plan-next"]
        self.assertEqual(
            len(plan_wus), 1,
            f"plan-next must be the sole ready WU after auto-close; got "
            f"{[w.wu_id for w in next_pending]}",
        )


# ---------------------------------------------------------------------------
# AC test 4: idempotent append on re-arm
# ---------------------------------------------------------------------------


class TestIdempotentAppendOnReArm(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9973"
        fdir = self.root
        self.fdir = fdir

        _write_plan_md_two_gate(fdir, self.feature_id)
        _write_wu_impl(fdir, f"{self.feature_id}/T01", "WU-01.md")
        _write_wu_close_intermediate(fdir, f"{self.feature_id}/G1-CI", "WU-ci.md")
        _write_wu_plan_next(fdir, f"{self.feature_id}/G1-PLAN", "WU-plan.md")
        (fdir / "WU-02.md").write_text(
            f"---\nid: {self.feature_id}/T02\ntype: implementation\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# T02{_WU_BODY}"
        )
        _write_gate_file(fdir, 1)
        _write_gate_file(fdir, 2)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")

        refs_g1 = [
            {"id": f"{self.feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{self.feature_id}/G1-CI", "file": "WU-ci.md",
             "depends_on": [f"{self.feature_id}/T01"]},
            {"id": f"{self.feature_id}/G1-PLAN", "file": "WU-plan.md",
             "depends_on": [f"{self.feature_id}/G1-CI"]},
        ]
        refs_g2 = [
            {"id": f"{self.feature_id}/T02", "file": "WU-02.md", "depends_on": []},
        ]
        self.gate1 = _make_gate_node(fdir, self.feature_id, 1, refs_g1)
        self.gate2 = _make_gate_node(fdir, self.feature_id, 2, refs_g2)
        self.gates = [self.gate1, self.gate2]
        self.ci_wu = _make_ci_wu(fdir, f"{self.feature_id}/G1-CI")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_second_call_does_not_duplicate_section(self):
        from gate_eval import evaluate_auto_close
        decision = evaluate_auto_close(self.fdir, 1)
        self.assertTrue(decision.auto, "predicate must fire for this fixture")

        loop.append_stub_retrospective_intermediate(self.fdir, 1, decision)
        loop.append_stub_retrospective_intermediate(self.fdir, 1, decision)

        retro_text = (self.fdir / "RETROSPECTIVE.md").read_text()
        matches = re.findall(r"^## Gate 1\b", retro_text, re.MULTILINE)
        self.assertEqual(
            len(matches), 1,
            f"Expected exactly one ## Gate 1 section; found {len(matches)}",
        )


# ---------------------------------------------------------------------------
# Regression test for #23 — maybe_auto_close_intermediate idempotency
# ---------------------------------------------------------------------------


class TestMaybeAutoCloseIntermediateIdempotent(unittest.TestCase):
    """Regression for issue #23.

    Before the fix, the dispatch loop could re-enter with a stale in-memory
    `wu.status == "pending"` even though the auto-close path had already
    written `status: done` + `auto_close: true` to disk and added the WU id
    to `done_ids`. Calling `maybe_auto_close_intermediate` a second time then
    appended a duplicate `auto_close_decision` event and (in the caller) a
    duplicate bookkeeping commit.

    The fix is two layered guards:

    1. `maybe_auto_close_intermediate` short-circuits at the top if the
       WU's on-disk frontmatter already shows status=done AND auto_close
       truthy, returning (False, decision_with_auto=False) and emitting
       no event.
    2. The caller mirrors the disk status flip into the in-memory
       `wu.status = DONE`, so `ready()`'s `u.status in DISPATCHABLE`
       filter excludes the WU on the next while-loop pass.

    Guard 1 is what this test exercises. Guard 2 is exercised by
    TestPlanNextDispatchedAfterAutoIntermediate.test_close_intermediate_never_dispatched
    (which already mirrors the in-memory flip).
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9974"
        fdir = self.root
        self.fdir = fdir

        _write_plan_md_two_gate(fdir, self.feature_id)
        _write_wu_impl(fdir, f"{self.feature_id}/T01", "WU-01.md")
        _write_wu_close_intermediate(fdir, f"{self.feature_id}/G1-CI", "WU-ci.md")
        _write_wu_plan_next(fdir, f"{self.feature_id}/G1-PLAN", "WU-plan.md")
        (fdir / "WU-02.md").write_text(
            f"---\nid: {self.feature_id}/T02\ntype: implementation\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# T02{_WU_BODY}"
        )
        _write_gate_file(fdir, 1)
        _write_gate_file(fdir, 2)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")

        refs_g1 = [
            {"id": f"{self.feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{self.feature_id}/G1-CI", "file": "WU-ci.md",
             "depends_on": [f"{self.feature_id}/T01"]},
            {"id": f"{self.feature_id}/G1-PLAN", "file": "WU-plan.md",
             "depends_on": [f"{self.feature_id}/G1-CI"]},
        ]
        refs_g2 = [
            {"id": f"{self.feature_id}/T02", "file": "WU-02.md", "depends_on": []},
        ]
        self.gate1 = _make_gate_node(fdir, self.feature_id, 1, refs_g1)
        self.gate2 = _make_gate_node(fdir, self.feature_id, 2, refs_g2)
        self.gates = [self.gate1, self.gate2]
        self.ci_wu = _make_ci_wu(fdir, f"{self.feature_id}/G1-CI")
        self.plan_next_wu = _make_plan_next_wu(fdir, f"{self.feature_id}/G1-PLAN")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_intermediate(
            self.fdir, self.feature_id, self.gate1, self.gates,
            self.events_path, self.root, self.ci_wu, self.plan_next_wu,
        )

    def test_first_call_fires_second_call_short_circuits(self):
        first_ok, first_decision = self._call()
        self.assertTrue(first_ok)
        self.assertTrue(first_decision.auto)

        second_ok, second_decision = self._call()
        self.assertFalse(
            second_ok,
            "second call must report no-action when WU is already auto-closed",
        )
        self.assertFalse(
            second_decision.auto,
            "decision.auto must be False on the idempotent short-circuit",
        )
        self.assertIn(
            "already_auto_closed", second_decision.reasons,
            "decision.reasons must surface the short-circuit cause",
        )

    def test_exactly_one_auto_close_decision_event(self):
        self._call()
        self._call()
        events = _load_events(self.events_path)
        auto_events = [
            e for e in events if e.get("event_type") == "auto_close_decision"
        ]
        self.assertEqual(
            len(auto_events), 1,
            f"expected exactly 1 auto_close_decision event, got {len(auto_events)} "
            f"— second call must NOT re-emit (issue #23 double-fire regression)",
        )

    def test_retrospective_has_exactly_one_gate_section(self):
        self._call()
        self._call()
        retro_text = (self.fdir / "RETROSPECTIVE.md").read_text()
        matches = re.findall(r"^## Gate 1\b", retro_text, re.MULTILINE)
        self.assertEqual(
            len(matches), 1,
            "second auto-close call must not duplicate the Gate 1 section",
        )


class TestMaybeAutoCloseTerminalIdempotent(unittest.TestCase):
    """Regression for issue #23 — same idempotency contract on the terminal
    path. Setup mirrors the existing terminal-auto-close fixtures: single-gate
    feature with one impl WU and one close WU."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9975"
        fdir = self.root
        self.fdir = fdir

        (fdir / "PLAN.md").write_text(
            f"---\n"
            f"feature_id: {self.feature_id}\n"
            f"title: Test\n"
            f"branch: feat/{self.feature_id.lower()}-test\n"
            f"roadmap_goal: test\n"
            f"status: active\n"
            f"---\n\n# Plan\n\n```yaml\n"
            f"gates:\n"
            f"  - gate: 1\n"
            f"    file: GATE-01.md\n"
            f"    work_units:\n"
            f"      - id: {self.feature_id}/T01\n"
            f"        file: WU-01.md\n"
            f"        depends_on: []\n"
            f"      - id: {self.feature_id}/G1-CLOSE\n"
            f"        file: WU-close.md\n"
            f"        depends_on: [{self.feature_id}/T01]\n"
            f"```\n"
        )
        _write_wu_impl(fdir, f"{self.feature_id}/T01", "WU-01.md")
        (fdir / "WU-close.md").write_text(
            f"---\nid: {self.feature_id}/G1-CLOSE\ntype: close\nmodel: opus\n"
            f"status: pending\nattempts: 0\n---\n\n# Close{_WU_BODY}"
        )
        _write_gate_file(fdir, 1)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")

        refs_g1 = [
            {"id": f"{self.feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{self.feature_id}/G1-CLOSE", "file": "WU-close.md",
             "depends_on": [f"{self.feature_id}/T01"]},
        ]
        self.gate1 = _make_gate_node(fdir, self.feature_id, 1, refs_g1)
        self.gates = [self.gate1]
        self.close_wu = loop.WorkUnit(
            wu_id=f"{self.feature_id}/G1-CLOSE",
            file=fdir / "WU-close.md",
            depends_on=[f"{self.feature_id}/T01"],
            type="close",
            model="opus",
            effort="high",
            status="pending",
            attempts=0,
            title="Close",
            body="",
        )
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_terminal(
            self.fdir, self.feature_id, self.gate1, self.gates,
            self.events_path, self.close_wu, repo_root=self.root,
        )

    def test_second_call_short_circuits(self):
        first_ok, _ = self._call()
        self.assertTrue(first_ok)

        second_ok, second_decision = self._call()
        self.assertFalse(second_ok)
        self.assertFalse(second_decision.auto)
        self.assertIn("already_auto_closed", second_decision.reasons)

        events = _load_events(self.events_path)
        auto_events = [
            e for e in events if e.get("event_type") == "auto_close_decision"
        ]
        self.assertEqual(
            len(auto_events), 1,
            "terminal auto-close must not double-fire (issue #23 regression)",
        )


if __name__ == "__main__":
    unittest.main()
