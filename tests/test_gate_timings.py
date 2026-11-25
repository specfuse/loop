#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-LOOP-2026-0250 gate 1 oracle — per-gate timings recorded as
`gate_result` events. One class per Definition-of-done clause in GATE-01.md.
T01 implements clause 1 and the schema half of clause 5; the rest are skipped
naming their owning unit.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

SCHEMA = (Path(__file__).resolve().parent.parent
          / "specfuse" / "loop" / "data" / "schemas" / "driver-event.schema.json")

_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
SLEEP = 0.3


class TestAttemptGateEvents(unittest.TestCase):
    """Clause 1 — attempt phase."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_dir = self.root / "feat"
        self.feature_dir.mkdir()
        self.wu_file = self.feature_dir / "WU-01.md"
        self.wu_file.write_text(
            "---\nid: FEAT-LOOP-2026-9999/T01\ntype: implementation\n"
            f"model: sonnet\nstatus: pending\nattempts: 0\n---\n\n# T{_BODY}")
        self.gate_file = self.feature_dir / "GATE-01.md"
        self.gate_file.write_text(
            "---\ngate: 1\nstatus: open\n"
            f'feature_oracle: "sleep {SLEEP} && exit 0"\n---\n\n# Gate 1\n')
        self.wu = loop.WorkUnit(
            wu_id="FEAT-LOOP-2026-9999/T01", file=self.wu_file, depends_on=[],
            type="implementation", model="sonnet", effort="medium",
            status="pending", attempts=1, title="T", body="**Objective.** x")
        self.cfg = {"code": [
            {"name": "slow-pass", "command": f"sleep {SLEEP} && exit 0"},
            {"name": "bad", "command": "exit 1"},
            {"name": "dependent", "command": "exit 0", "needs": ["bad"]},
        ]}

    def tearDown(self):
        self._tmp.cleanup()

    def _attempt(self):
        def dispatch_fn(wu, note):
            return "RESULT\nstatus: complete\n"

        def verify_fn(wu, fd, gate_file=None):
            return loop.verify(wu, fd, cfg=self.cfg, gate_file=gate_file)

        loop_outcome = loop.execute_unit_attempt(
            self.wu, self.feature_dir, None, dispatch_fn=dispatch_fn,
            verify_fn=verify_fn, cost_tracking=False, prerun_cfg=self.cfg,
            gate_file=self.gate_file)
        return loop_outcome, loop.build_attempt_gate_events(self.wu, 1)

    def test_one_gate_result_per_gate_with_payload(self):
        (outcome, _p, _u), events = self._attempt()
        self.assertEqual(outcome, "failed")
        self.assertTrue(all(e["event_type"] == "gate_result" for e in events))
        self.assertTrue(all(e["correlation_id"] == self.wu.wu_id for e in events))
        by_gate = {e["payload"]["gate"]: e["payload"] for e in events}
        self.assertEqual(
            sorted(by_gate), ["bad", "dependent", "feature_oracle", "slow-pass"])
        self.assertEqual(len(events), 4)
        for payload in by_gate.values():
            self.assertEqual(
                set(payload),
                {"attempt", "gate", "ok", "skipped", "duration_seconds", "phase"})
            self.assertEqual(payload["attempt"], 1)
            self.assertEqual(payload["phase"], "attempt")

    def test_durations_and_skip_semantics(self):
        _, events = self._attempt()
        by_gate = {e["payload"]["gate"]: e["payload"] for e in events}
        for name in ("slow-pass", "feature_oracle"):
            self.assertTrue(by_gate[name]["ok"])
            self.assertFalse(by_gate[name]["skipped"])
            self.assertGreaterEqual(by_gate[name]["duration_seconds"], SLEEP)
        self.assertFalse(by_gate["bad"]["ok"])
        self.assertFalse(by_gate["bad"]["skipped"])
        self.assertGreater(by_gate["bad"]["duration_seconds"], 0)
        dep = by_gate["dependent"]
        self.assertFalse(dep["ok"])
        self.assertTrue(dep["skipped"])
        self.assertEqual(dep["duration_seconds"], 0)

    def test_stub_verify_without_gate_results_emits_none(self):
        self.wu.last_gate_results = []
        self.assertEqual(loop.build_attempt_gate_events(self.wu, 1), [])


class TestAttemptSplit(unittest.TestCase):
    """Clause 2 — agent_seconds / verify_seconds on attempt_outcome."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_dir = self.root / "feat"
        self.feature_dir.mkdir()
        wu_file = self.feature_dir / "WU-01.md"
        wu_file.write_text(
            "---\nid: FEAT-LOOP-2026-9999/T01\ntype: implementation\n"
            f"model: sonnet\nstatus: pending\nattempts: 0\n---\n\n# T{_BODY}")
        self.gate_file = self.feature_dir / "GATE-01.md"
        self.gate_file.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        self.wu = loop.WorkUnit(
            wu_id="FEAT-LOOP-2026-9999/T01", file=wu_file, depends_on=[],
            type="implementation", model="sonnet", effort="medium",
            status="pending", attempts=1, title="T", body="**Objective.** x")
        self.cfg = {"code": [
            {"name": "slow-pass", "command": f"sleep {SLEEP} && exit 0"}]}

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, stdout):
        def dispatch_fn(wu, note):
            time.sleep(SLEEP)
            return stdout

        def verify_fn(wu, fd, gate_file=None):
            return loop.verify(wu, fd, cfg=self.cfg, gate_file=gate_file)

        t0 = time.monotonic()
        outcome, _p, usage = loop.execute_unit_attempt(
            self.wu, self.feature_dir, None, dispatch_fn=dispatch_fn,
            verify_fn=verify_fn, cost_tracking=False, prerun_cfg=self.cfg,
            gate_file=self.gate_file)
        duration = time.monotonic() - t0
        usage = dict(usage)
        usage["duration_seconds"] = duration
        event = loop.emit_attempt_outcome(self.wu, 1, outcome, usage)
        return outcome, event["payload"]

    def test_split(self):
        _, payload = self._run("RESULT\nstatus: complete\n")
        self.assertGreaterEqual(payload["agent_seconds"], SLEEP)
        self.assertGreaterEqual(payload["verify_seconds"], SLEEP)
        self.assertLessEqual(
            payload["agent_seconds"] + payload["verify_seconds"],
            payload["duration_seconds"])

    def test_blocked_records_zero_verify(self):
        outcome, payload = self._run(
            "```result\nstatus: blocked\nblocked_reason: nope\n```\n")
        self.assertEqual(outcome, "blocked")
        self.assertEqual(payload["verify_seconds"], 0)
        self.assertGreaterEqual(payload["agent_seconds"], SLEEP)

    def test_defaults_when_usage_lacks_keys(self):
        payload = loop.emit_attempt_outcome(self.wu, 1, "failed", {})["payload"]
        self.assertEqual(payload["agent_seconds"], 0.0)
        self.assertEqual(payload["verify_seconds"], 0.0)


class TestBaselineAndBroadPhases(unittest.TestCase):
    """Clause 3 — baseline and broad phases."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.cfg = {"code": [
            {"name": "ok-gate", "command": "exit 0"},
            {"name": "bad", "command": "exit 1"},
        ]}

    def tearDown(self):
        self._tmp.cleanup()

    def _check(self, events, phase, cid):
        self.assertEqual(len(events), 2)
        for e in events:
            self.assertEqual(e["event_type"], "gate_result")
            self.assertEqual(e["correlation_id"], cid)
            self.assertEqual(
                set(e["payload"]),
                {"attempt", "gate", "ok", "skipped", "duration_seconds", "phase"})
            self.assertIsNone(e["payload"]["attempt"])
            self.assertEqual(e["payload"]["phase"], phase)
        self.assertEqual(
            sorted(e["payload"]["gate"] for e in events), ["bad", "ok-gate"])

    def test_broad_run_phase(self):
        ok, failing = loop.run_gate_broad_set(self.root, self.cfg)
        self.assertFalse(ok)
        self.assertEqual(set(failing[0]), {
            "gate", "failure_class", "failure_signature"})
        self._check(
            loop.build_phase_gate_events("broad", "FEAT-LOOP-2026-9999"),
            "broad", "FEAT-LOOP-2026-9999")
        self.assertEqual(loop.build_phase_gate_events("broad", "X"), [])

    def test_baseline_phase(self):
        failing = loop.probe_baseline(self.root, self.cfg)
        self.assertEqual(
            set(failing[0]), {"gate", "failure_class", "failure_signature"})
        self._check(
            loop.build_phase_gate_events("baseline", "FEAT-LOOP-2026-9999/T01"),
            "baseline", "FEAT-LOOP-2026-9999/T01")

    def test_unchanged_tree_broad_skip_emits_none(self):
        gate_file = self.root / "GATE-01.md"
        gate_file.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        green = {"code": [{"name": "ok-gate", "command": "exit 0"}]}
        orig = loop._current_tree_hash
        loop._current_tree_hash = lambda: "tree-abc"
        try:
            _, _, ran = loop.gate_broad_run_check(gate_file, self.root, green)
            self.assertTrue(ran)
            loop.build_phase_gate_events("broad", "F")
            _, _, ran = loop.gate_broad_run_check(gate_file, self.root, green)
            self.assertFalse(ran)
            self.assertEqual(loop.build_phase_gate_events("broad", "F"), [])
        finally:
            loop._current_tree_hash = orig


class TestStatsReport(unittest.TestCase):
    """Clause 4 — owned by T04."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, events):
        d = self.root / ".specfuse" / "features" / name
        d.mkdir(parents=True)
        (d / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n")

    @staticmethod
    def _attempt(ts, n, **extra):
        payload = {"attempt": n, "outcome": "passed", "cost_usd": 1.0,
                   "duration_seconds": 10.0}
        payload.update(extra)
        return {"timestamp": ts, "correlation_id": "FEAT-LOOP-2026-9999/T01",
                "event_type": "attempt_outcome", "payload": payload}

    @staticmethod
    def _gate(ts, gate, secs, phase="attempt", attempt=1):
        return {"timestamp": ts, "correlation_id": "FEAT-LOOP-2026-9999/T01",
                "event_type": "gate_result",
                "payload": {"attempt": attempt, "gate": gate, "ok": True,
                            "skipped": False, "duration_seconds": secs,
                            "phase": phase}}

    def test_new_corpus_reports_split_and_gates(self):
        from specfuse.loop import events_stats
        self._write("FEAT-LOOP-2026-9999-x", [
            self._attempt("t1", 1, agent_seconds=6.0, verify_seconds=2.0),
            self._attempt("t2", 2, agent_seconds=2.0, verify_seconds=2.0),
            self._gate("t1", "tests", 4.0), self._gate("t1", "lint", 1.0),
            self._gate("t2", "tests", 2.0, attempt=2),
            self._gate("t3", "tests", 9.0, phase="broad"),
        ])
        stats = events_stats.collect([self.root])
        split = next(iter(stats["time_split"].values()))
        self.assertEqual(split["agent_seconds"], 8.0)
        self.assertEqual(split["verify_seconds"], 4.0)
        self.assertAlmostEqual(split["agent_share"], 0.6667, places=4)
        rows = {(r["phase"], r["gate"]): r for r in stats["gate_timings"]}
        t = rows[("attempt", "tests")]
        self.assertEqual((t["runs"], t["total_seconds"], t["median_seconds"],
                          t["max_seconds"]), (2, 6.0, 3.0, 4.0))
        self.assertEqual(rows[("broad", "tests")]["total_seconds"], 9.0)
        # ordered by total seconds, descending
        totals = [r["total_seconds"] for r in stats["gate_timings"]]
        self.assertEqual(totals, sorted(totals, reverse=True))
        text = events_stats.render(stats)
        self.assertNotIn("not recorded", text)
        self.assertIn("slowest gates", text)
        json.dumps(stats)

    def test_old_corpus_reads_not_recorded(self):
        from specfuse.loop import events_stats
        self._write("FEAT-LOOP-2026-8888-old", [self._attempt("t1", 1)])
        stats = events_stats.collect([self.root])
        self.assertEqual(stats["time_split"], {})
        self.assertEqual(stats["gate_timings"], [])
        text = events_stats.render(stats)
        self.assertEqual(text.count("not recorded"), 2)


class TestNothingExistingChanges(unittest.TestCase):
    """Clause 5 — T01 owns the schema half; T02-T04 own the rest."""

    def test_gate_result_in_schema_event_types(self):
        schema = json.loads(SCHEMA.read_text())
        self.assertIn("gate_result", schema["event_types"])

    def test_emitted_events_validate(self):
        from specfuse.loop import validate_event
        validator = validate_event.load_validator()
        wu = loop.WorkUnit(
            wu_id="FEAT-LOOP-2026-9999/T01", file=Path("WU-01.md"),
            depends_on=[], type="implementation", model="sonnet",
            effort="medium", status="pending", attempts=1, title="T",
            body="x")
        wu.last_gate_results = [
            {"name": "g", "ok": True, "skipped": False, "duration_seconds": 0.5},
            {"name": "h", "ok": False, "skipped": True, "duration_seconds": 0}]
        events = loop.build_attempt_gate_events(wu, 1)
        events.append(loop.emit_attempt_outcome(
            wu, 1, "passed", {"agent_seconds": 1.0, "verify_seconds": 0.5,
                              "duration_seconds": 2.0}))
        loop._PHASE_GATE_RESULTS["broad"] = list(wu.last_gate_results)
        events += loop.build_phase_gate_events("broad", "FEAT-LOOP-2026-9999")
        for e in events:
            self.assertEqual(
                validate_event.validate_line(
                    validator, "t", 0, json.dumps(e)), [], e["event_type"])


if __name__ == "__main__":
    unittest.main()
