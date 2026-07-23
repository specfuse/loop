#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for FEAT-2026-0018/T04: terminal gate auto-close wiring.

AC5: maybe_auto_close_terminal returns (True, decision) on a clean gate,
     close-WU frontmatter gains auto_close=true + verdict=met + status=done,
     RETROSPECTIVE.md has the Gate N section, events.jsonl gains one
     auto_close_decision event with predicate_version="v1".

AC6: maybe_auto_close_terminal returns (False, decision) when the gate has a
     blocked_human event in chain, leaves all files unchanged, and writes no
     event.
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


def _write_plan_md(fdir: Path, feature_id: str, gate_num: int = 1) -> None:
    (fdir / "PLAN.md").write_text(
        f"---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test\n"
        f"branch: feat/{feature_id.lower()}-test\n"
        f"roadmap_goal: test\n"
        f"status: active\n"
        f"---\n\n# Plan\n\n```yaml\n"
        f"gates:\n"
        f"  - gate: {gate_num}\n"
        f"    file: GATE-{gate_num:02d}.md\n"
        f"    work_units:\n"
        f"      - id: {feature_id}/T01\n"
        f"        file: WU-01.md\n"
        f"        depends_on: []\n"
        f"      - id: {feature_id}/G{gate_num}-CLOSE\n"
        f"        file: WU-close.md\n"
        f"        depends_on: [{feature_id}/T01]\n"
        f"```\n"
    )


def _write_wu_impl(fdir: Path, wu_id: str, cost: float = 0.5, planned: float = 0.5) -> None:
    (fdir / "WU-01.md").write_text(
        f"---\nid: {wu_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: done\nattempts: 1\ncost_usd: {cost}\nplanned_cost_usd: {planned}\n"
        f"---\n\n# T01{_WU_BODY}"
    )


def _write_wu_close(fdir: Path, wu_id: str) -> None:
    (fdir / "WU-close.md").write_text(
        f"---\nid: {wu_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n"
        f"---\n\n# Close{_WU_BODY}"
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
        "payload": {"reason": "spinning", "summary": "test blocked"},
    })
    with (fdir / "events.jsonl").open("a") as f:
        f.write(ev + "\n")


def _make_gate_node(fdir: Path, feature_id: str, gate_num: int = 1) -> "loop.GateNode":
    gate_file = fdir / f"GATE-{gate_num:02d}.md"
    fm, _ = loop.read_frontmatter(gate_file)
    refs = [
        {"id": f"{feature_id}/T01", "file": "WU-01.md", "depends_on": []},
        {"id": f"{feature_id}/G{gate_num}-CLOSE", "file": "WU-close.md",
         "depends_on": [f"{feature_id}/T01"]},
    ]
    return loop.GateNode(
        number=gate_num, file=gate_file, status=fm.get("status", "open"), refs=refs,
    )


def _make_close_wu(fdir: Path, wu_id: str) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=fdir / "WU-close.md",
        depends_on=[],
        type="close",
        model="opus",
        effort="high",
        status="pending",
        attempts=0,
        title="Close",
        body="",
    )


def _load_events(events_path: Path) -> list[dict]:
    events = []
    with events_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


# ---------------------------------------------------------------------------
# AC5: auto=True path
# ---------------------------------------------------------------------------


class TestMaybeAutoCloseTerminalAutoPath(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9980"
        self.gate_num = 1
        fdir = self.root
        self.fdir = fdir

        _write_plan_md(fdir, self.feature_id, self.gate_num)
        _write_wu_impl(fdir, f"{self.feature_id}/T01")
        _write_wu_close(fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        _write_gate_file(fdir, self.gate_num)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")

        self.gate = _make_gate_node(fdir, self.feature_id, self.gate_num)
        self.close_wu = _make_close_wu(fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_terminal(
            self.fdir, self.feature_id, self.gate, [self.gate],
            self.events_path, self.close_wu, repo_root=self.root,
        )

    def test_returns_true_and_decision(self):
        result, decision = self._call()
        self.assertTrue(result)
        self.assertTrue(decision.auto)
        self.assertEqual(decision.predicate_version, "v1")

    def test_close_wu_frontmatter_auto_close_true(self):
        self._call()
        fm, _ = loop.read_frontmatter(self.close_wu.file)
        self.assertIs(fm.get("auto_close"), True)

    def test_close_wu_frontmatter_verdict_met(self):
        self._call()
        fm, _ = loop.read_frontmatter(self.close_wu.file)
        self.assertEqual(fm.get("verdict"), "met")

    def test_close_wu_frontmatter_status_done(self):
        self._call()
        fm, _ = loop.read_frontmatter(self.close_wu.file)
        self.assertEqual(fm.get("status"), "done")

    def test_retrospective_exists_and_non_empty(self):
        self._call()
        retro = self.fdir / "RETROSPECTIVE.md"
        self.assertTrue(retro.exists())
        self.assertTrue(retro.read_text().strip())

    def test_retrospective_has_gate_section(self):
        self._call()
        retro = self.fdir / "RETROSPECTIVE.md"
        self.assertTrue(
            re.search(
                rf"^#{{1,3}} Gate {self.gate_num}\b",
                retro.read_text(),
                re.MULTILINE,
            ),
            f"RETROSPECTIVE.md must have ## Gate {self.gate_num} heading",
        )

    def test_events_has_auto_close_decision(self):
        self._call()
        events = _load_events(self.events_path)
        auto_close_events = [e for e in events if e.get("event_type") == "auto_close_decision"]
        self.assertEqual(len(auto_close_events), 1)

    def test_event_predicate_version_v1(self):
        self._call()
        events = _load_events(self.events_path)
        ev = next(e for e in events if e.get("event_type") == "auto_close_decision")
        self.assertEqual(ev["payload"]["predicate_version"], "v1")

    def test_event_auto_true(self):
        self._call()
        events = _load_events(self.events_path)
        ev = next(e for e in events if e.get("event_type") == "auto_close_decision")
        self.assertIs(ev["payload"]["auto"], True)

    def test_event_gate_number(self):
        self._call()
        events = _load_events(self.events_path)
        ev = next(e for e in events if e.get("event_type") == "auto_close_decision")
        self.assertEqual(ev["payload"]["gate"], self.gate_num)


# ---------------------------------------------------------------------------
# AC6: auto=False path — blocked_human event in chain
# ---------------------------------------------------------------------------


class TestMaybeAutoCloseTerminalPerWuOptOut(unittest.TestCase):
    """#189: a close WU marked auto_close_disabled must NOT be auto-closed,
    even on an otherwise clean/on-plan gate — it is dispatched instead."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9981"
        self.gate_num = 1
        fdir = self.root
        self.fdir = fdir
        _write_plan_md(fdir, self.feature_id, self.gate_num)
        _write_wu_impl(fdir, f"{self.feature_id}/T01")
        # Close WU carries the per-WU opt-out.
        (fdir / "WU-close.md").write_text(
            f"---\nid: {self.feature_id}/G{self.gate_num}-CLOSE\ntype: close\n"
            f"model: opus\nstatus: pending\nattempts: 0\n"
            f"auto_close_disabled: true\n---\n\n# Close\n"
        )
        _write_gate_file(fdir, self.gate_num)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")
        self.gate = _make_gate_node(fdir, self.feature_id, self.gate_num)
        self.close_wu = _make_close_wu(
            fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_refuses_and_names_reason(self):
        result, decision = loop.maybe_auto_close_terminal(
            self.fdir, self.feature_id, self.gate, [self.gate],
            self.events_path, self.close_wu, repo_root=self.root,
        )
        self.assertFalse(result)
        self.assertFalse(decision.auto)
        self.assertIn("auto_close_disabled_per_wu", decision.reasons)

    def test_close_wu_not_marked_auto_closed(self):
        loop.maybe_auto_close_terminal(
            self.fdir, self.feature_id, self.gate, [self.gate],
            self.events_path, self.close_wu, repo_root=self.root,
        )
        fm, _ = loop.read_frontmatter(self.close_wu.file)
        # Status untouched (still dispatchable); no auto_close output marker.
        self.assertEqual(fm.get("status"), "pending")
        self.assertNotEqual(fm.get("auto_close"), True)

    def test_helper_reads_the_flag(self):
        self.assertTrue(loop._close_wu_disables_auto_close(self.close_wu))


class TestMaybeAutoCloseTerminalDeliverableMissing(unittest.TestCase):
    """#190: auto-close must refuse when an implementation WU reports done but
    its declared `produces:` deliverable is absent — dispatch the close."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9982"
        self.gate_num = 1
        fdir = self.root
        self.fdir = fdir
        _write_plan_md(fdir, self.feature_id, self.gate_num)
        # Implementation WU claims done + a produces path that does NOT exist.
        missing = fdir / "src" / "never-created.py"
        (fdir / "WU-01.md").write_text(
            f"---\nid: {self.feature_id}/T01\ntype: implementation\n"
            f"model: sonnet\nstatus: done\nattempts: 1\ncost_usd: 0.5\n"
            f"planned_cost_usd: 0.5\nproduces: [{missing}]\n---\n\n# T01\n"
        )
        _write_wu_close(fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        _write_gate_file(fdir, self.gate_num)
        _write_task_completed_event(fdir, f"{self.feature_id}/T01")
        self.gate = _make_gate_node(fdir, self.feature_id, self.gate_num)
        self.close_wu = _make_close_wu(
            fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_terminal(
            self.fdir, self.feature_id, self.gate, [self.gate],
            self.events_path, self.close_wu, repo_root=self.root,
        )

    def test_refuses_on_missing_deliverable(self):
        result, decision = self._call()
        self.assertFalse(result)
        self.assertFalse(decision.auto)
        self.assertTrue(any("declared_deliverable_missing" in r
                            for r in decision.reasons),
                        f"reasons={decision.reasons}")

    def test_present_deliverable_still_auto_closes(self):
        # Create the declared deliverable → predicate proceeds to auto-close.
        missing = self.fdir / "src" / "never-created.py"
        missing.parent.mkdir(parents=True, exist_ok=True)
        missing.write_text("x = 1\n")
        result, decision = self._call()
        self.assertTrue(result)
        self.assertTrue(decision.auto)

    def test_helper_reports_the_offender(self):
        ok, reason = loop._gate_impl_deliverables_present(self.fdir, self.gate)
        self.assertFalse(ok)
        self.assertIn("never-created.py", reason)


class TestMaybeAutoCloseTerminalNonAutoPath(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9981"
        self.gate_num = 1
        fdir = self.root
        self.fdir = fdir

        _write_plan_md(fdir, self.feature_id, self.gate_num)
        _write_wu_impl(fdir, f"{self.feature_id}/T01")
        _write_wu_close(fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        _write_gate_file(fdir, self.gate_num)
        # blocked_human event on the impl WU prevents auto=True
        _write_blocked_human_event(fdir, f"{self.feature_id}/T01")

        self.gate = _make_gate_node(fdir, self.feature_id, self.gate_num)
        self.close_wu = _make_close_wu(fdir, f"{self.feature_id}/G{self.gate_num}-CLOSE")
        self.events_path = fdir / "events.jsonl"
        self._close_wu_content_before = self.close_wu.file.read_text()

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_terminal(
            self.fdir, self.feature_id, self.gate, [self.gate],
            self.events_path, self.close_wu, repo_root=self.root,
        )

    def test_returns_false(self):
        result, decision = self._call()
        self.assertFalse(result)
        self.assertFalse(decision.auto)

    def test_no_retrospective_created(self):
        self._call()
        self.assertFalse((self.fdir / "RETROSPECTIVE.md").exists())

    def test_close_wu_unchanged(self):
        self._call()
        self.assertEqual(self.close_wu.file.read_text(), self._close_wu_content_before)

    def test_no_auto_close_decision_event(self):
        self._call()
        events = _load_events(self.events_path)
        self.assertFalse(
            any(e.get("event_type") == "auto_close_decision" for e in events),
            "no auto_close_decision event must be written when auto=False",
        )


if __name__ == "__main__":
    unittest.main()
