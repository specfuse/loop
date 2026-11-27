#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-LOOP-2026-0252 gate 1 oracle — a running unit's progress is visible.
One class per Definition-of-done clause in GATE-01.md. T01 implements clauses
1, 2 and 4; the rest are skipped naming their owning unit.

Every run goes through `loop.run()` in a temporary repository, with a stubbed
agent session and two real stub gate commands. What must be on disk while the
attempt runs is read from inside the attempt, never compared afterwards.
"""

from __future__ import annotations

import contextlib
import importlib.resources
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import validate_event
from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()

FEATURE_ID = "FEAT-LOOP-2026-9999"
WU_ID = f"{FEATURE_ID}/T01"
SLUG = "run-progress-fixture"
STATUS_FIELDS = {
    "feature", "wu_id", "attempt", "max_attempts", "phase", "gate",
    "started_at", "updated_at", "elapsed_seconds", "files_touched",
}
PHASE_TYPES = (
    "agent_session_started", "agent_session_finished",
    "gate_started", "gate_finished",
)

_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _read_events(path: Path) -> list:
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln]


def _scaffold(root: Path, snapshots: Path) -> Path:
    """One gate, one implementation unit, gates `alpha` and `beta`. Each gate
    copies the status file it sees to *snapshots*; `beta` also fails unless
    its own `gate_started` is already in the event log."""
    own_event = '"gate_started".*"gate": "beta"'
    gates = [
        ("alpha", f"cp {{feature_dir}}/work/STATUS.json {snapshots}/alpha.json"),
        ("beta", f"cp {{feature_dir}}/work/STATUS.json {snapshots}/beta.json "
                 f"&& grep -q '{own_event}' {{feature_dir}}/events.jsonl"),
    ]
    code = "".join(
        f"  - name: {name}\n    command: {json.dumps(cmd)}\n"
        for name, cmd in gates)
    (root / ".specfuse/verification.yml").write_text(
        f"code:\n{code}"
        "doc:\n  - name: noop\n    command: \"true\"\n"
        "plannext:\n  - name: noop\n    command: \"true\"\n")
    (root / ".gitignore").write_text(".specfuse/.loop.lock\n")

    fdir = root / ".specfuse" / "features" / f"{FEATURE_ID}-{SLUG}"
    fdir.mkdir(parents=True)
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {FEATURE_ID}\ntitle: Progress\nslug: {SLUG}\n"
        f"branch: feat/{SLUG}\nroadmap_goal: exercise run progress\n"
        "status: active\n---\n\n# Plan\n\n```yaml\ngates:\n"
        "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        f"      - id: {WU_ID}\n        file: WU-T01.md\n"
        "        depends_on: []\n```\n")
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {WU_ID}\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"max_attempts: 1\n---\n\n# T01{_BODY}")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "fixture"],
                   check=True)
    return fdir


class _Observed:
    """One `loop.run()` and everything seen during and after it."""

    def __init__(self):
        with integration_workspace() as root, \
                tempfile.TemporaryDirectory() as snapshots:
            cwd = os.getcwd()
            os.chdir(root)
            try:
                self._run(root, Path(snapshots))
            finally:
                os.chdir(cwd)

    def _run(self, root: Path, snapshots: Path) -> None:
        fdir = _scaffold(root, snapshots)
        rel = fdir.relative_to(root)

        def session(wu, failure_note, cost_tracking=True):
            self.events_in_session = _read_events(rel / "events.jsonl")
            self.status_in_session = json.loads(
                (rel / "work" / "STATUS.json").read_text())
            write_stub_deliverable(wu)
            return "```result\nstatus: complete\n```\n"

        out = io.StringIO()
        with mock.patch.object(loop, "dispatch", session), \
                contextlib.redirect_stdout(out):
            self.rc = loop.run(None, dry_run=False)
        self.output = out.getvalue()
        self.events = _read_events(rel / "events.jsonl")
        self.status_after = json.loads(
            (rel / "work" / "STATUS.json").read_text())
        self.gate_status = {
            name: json.loads((snapshots / f"{name}.json").read_text())
            for name in ("alpha", "beta")
        }
        self.tracked = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True,
            check=True).stdout.splitlines()


class _ObservedRun(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.run_seen = _Observed()


class TestPhaseEvents(_ObservedRun):
    """Clause 1 — phase events, written as they happen."""

    def _phase_events(self):
        return [e for e in self.run_seen.events
                if e["event_type"] in PHASE_TYPES]

    def test_attempt_passes(self):
        self.assertEqual(self.run_seen.rc, 0, self.run_seen.output)
        outcomes = [e["payload"]["outcome"] for e in self.run_seen.events
                    if e["event_type"] == "attempt_outcome"]
        self.assertEqual(outcomes, ["passed"], self.run_seen.output)

    def test_order_and_payloads(self):
        seen = [(e["event_type"], e["payload"].get("gate"))
                for e in self._phase_events()]
        self.assertEqual(seen, [
            ("agent_session_started", None),
            ("agent_session_finished", None),
            ("gate_started", "alpha"), ("gate_finished", "alpha"),
            ("gate_started", "beta"), ("gate_finished", "beta"),
        ])
        for event in self._phase_events():
            self.assertEqual(event["correlation_id"], WU_ID)
            self.assertEqual(event["payload"]["attempt"], 1)
            if event["event_type"] == "gate_finished":
                self.assertEqual(
                    set(event["payload"]),
                    {"attempt", "gate", "ok", "duration_seconds"})
                self.assertIs(event["payload"]["ok"], True)
                self.assertGreaterEqual(event["payload"]["duration_seconds"], 0)

    def test_events_validate_against_the_packaged_schemas(self):
        root = importlib.resources.files("specfuse.loop").joinpath(
            "data", "schemas")
        for name, value in (
            ("SCHEMA_ROOT", root),
            ("SCHEMA_PATH", root / "event.schema.json"),
            ("PER_TYPE_SCHEMA_DIR", root / "events"),
            ("DRIVER_SCHEMA_PATH", root / "driver-event.schema.json"),
        ):
            patcher = mock.patch.object(validate_event, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        def clear_caches():
            validate_event._PER_TYPE_CACHE.clear()
            validate_event._DRIVER_EVENT_TYPES_CACHE = None
            validate_event._DRIVER_CORRELATION_PATTERNS_CACHE = \
                validate_event._UNSET

        clear_caches()
        self.addCleanup(clear_caches)
        validator = validate_event.load_validator()
        events = self._phase_events()
        self.assertEqual({e["event_type"] for e in events}, set(PHASE_TYPES))
        for event in events:
            self.assertEqual(
                validate_event.validate_line(
                    validator, "events.jsonl", 1, json.dumps(event)), [])

    def test_session_start_is_on_disk_while_the_session_runs(self):
        types = [e["event_type"] for e in self.run_seen.events_in_session]
        self.assertIn("agent_session_started", types)
        self.assertNotIn("agent_session_finished", types)

    def test_gate_start_is_on_disk_while_the_gate_runs(self):
        # `beta` exits non-zero unless its own gate_started is in the log.
        results = {e["payload"]["gate"]: e["payload"]["ok"]
                   for e in self._phase_events()
                   if e["event_type"] == "gate_finished"}
        self.assertIs(results.get("beta"), True, self.run_seen.output)

    def test_captured_attempt_diff_leaves_out_the_driver_event_log(self):
        # A replayed best-attempt diff carrying the log's hunk would not apply
        # over the preserved log. An agent's own events.jsonl stays in.
        with integration_workspace() as root:
            cwd = os.getcwd()
            os.chdir(root)
            self.addCleanup(os.chdir, cwd)
            logs = [Path(".specfuse/features/F/events.jsonl"),
                    Path("docs/events.jsonl")]
            for log in logs:
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text("{}\n")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-q", "-m", "logs"], check=True)
            for log in logs:
                log.write_text("{}\n{}\n")
            diff = loop.capture_working_tree_diff("HEAD")
            os.chdir(cwd)
        self.assertIn("docs/events.jsonl", diff)
        self.assertNotIn(".specfuse/features/F/events.jsonl", diff)


class TestStatusFile(_ObservedRun):
    """Clause 2 — the status file."""

    def test_during_the_session(self):
        status = self.run_seen.status_in_session
        self.assertLessEqual(STATUS_FIELDS, set(status))
        self.assertEqual(status["feature"], FEATURE_ID)
        self.assertEqual(status["wu_id"], WU_ID)
        self.assertEqual(status["attempt"], 1)
        self.assertEqual(status["max_attempts"], 1)
        self.assertEqual(status["phase"], "agent")
        self.assertIsNone(status["gate"])
        self.assertTrue(status["started_at"])
        self.assertTrue(status["updated_at"])
        self.assertGreaterEqual(status["elapsed_seconds"], 0)
        self.assertIsInstance(status["files_touched"], list)

    def test_during_each_gate(self):
        for name, status in self.run_seen.gate_status.items():
            with self.subTest(gate=name):
                self.assertLessEqual(STATUS_FIELDS, set(status))
                self.assertEqual(status["phase"], "gate")
                self.assertEqual(status["gate"], name)
                self.assertEqual(status["wu_id"], WU_ID)

    def test_stopped_after_run_returns(self):
        status = self.run_seen.status_after
        self.assertEqual(status["phase"], "stopped")
        self.assertIsNone(status["gate"])
        self.assertIsNone(status["stop_reason"])

    def test_never_tracked(self):
        self.assertTrue(self.run_seen.tracked)
        self.assertEqual(
            [p for p in self.run_seen.tracked
             if "STATUS.json" in p or p.endswith("work/.gitignore")], [])


class TestDriverLines(_ObservedRun):
    """Clause 4 — one plain line per phase change."""

    def test_one_line_per_phase_change(self):
        lines = self.run_seen.output.splitlines()
        for pattern in (
            r"\] agent session started$",
            r"\] agent session finished \(\d+\.\ds\)$",
            r"\] gate alpha started$",
            r"\] gate alpha PASS \(\d+\.\ds\)$",
            r"\] gate beta started$",
            r"\] gate beta PASS \(\d+\.\ds\)$",
        ):
            with self.subTest(pattern=pattern):
                matching = [ln for ln in lines
                            if re.search(pattern, ln)]
                self.assertEqual(len(matching), 1, self.run_seen.output)

    def test_no_carriage_return_or_ansi(self):
        self.assertNotIn("\r", self.run_seen.output)
        self.assertNotIn("\x1b", self.run_seen.output)


@unittest.skip("FEAT-LOOP-2026-0252/T02")
class TestHeartbeat(unittest.TestCase):
    """Clause 3 — owned by T02."""

    def test_placeholder(self):
        self.fail("T02 replaces this class")


@unittest.skip("FEAT-LOOP-2026-0252/T03")
class TestWatch(unittest.TestCase):
    """Clause 5 — owned by T03."""

    def test_placeholder(self):
        self.fail("T03 replaces this class")


@unittest.skip("FEAT-LOOP-2026-0252/T04")
class TestStopNotification(unittest.TestCase):
    """Clause 6 — owned by T04."""

    def test_placeholder(self):
        self.fail("T04 replaces this class")


if __name__ == "__main__":
    unittest.main()
