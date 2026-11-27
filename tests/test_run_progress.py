#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-LOOP-2026-0252 gate 1 oracle — a running unit's progress is visible.
One class per Definition-of-done clause in GATE-01.md. T01 implements clauses
1, 2 and 4, T02 clause 3, T03 clause 5, T04 clause 6.

Every run goes through `loop.run()` in a temporary repository, with a stubbed
agent session and two real stub gate commands. What must be on disk while the
attempt runs is read from inside the attempt, never compared afterwards.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import importlib.resources
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import notify, progress, validate_event
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


class _SessionBoom(Exception):
    pass


def _run_heartbeat_session(session_body):
    """`loop.run()` with a one-second heartbeat and *session_body* as the
    agent session. Returns what `run()` raised, or None."""
    with integration_workspace() as root, \
            tempfile.TemporaryDirectory() as snapshots:
        cwd = os.getcwd()
        os.chdir(root)
        try:
            fdir = _scaffold(root, Path(snapshots))
            with (root / ".specfuse/verification.yml").open("a") as fh:
                fh.write("defaults:\n  heartbeat_seconds: 1\n")
            subprocess.run(["git", "commit", "-q", "-am", "heartbeat"],
                           check=True)
            rel = fdir.relative_to(root)

            def session(wu, failure_note, cost_tracking=True):
                return session_body(wu, rel)

            with mock.patch.object(loop, "dispatch", session), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    loop.run(None, dry_run=False)
                except _SessionBoom as exc:
                    return exc
            return None
        finally:
            os.chdir(cwd)


class TestHeartbeat(unittest.TestCase):
    """Clause 3 — the status file is refreshed while an attempt runs."""

    def test_status_refreshes_during_the_session(self):
        before = set(threading.enumerate())
        samples = []

        def body(wu, rel):
            Path("notes").mkdir(exist_ok=True)
            Path("notes/a.txt").write_text("a\n")
            deadline = time.monotonic() + 3.4
            while time.monotonic() < deadline:
                samples.append(json.loads(
                    (rel / "work" / "STATUS.json").read_text()))
                time.sleep(0.05)
            self.during = set(threading.enumerate()) - before
            write_stub_deliverable(wu)
            return "```result\nstatus: complete\n```\n"

        _run_heartbeat_session(body)

        self.assertEqual({s["phase"] for s in samples}, {"agent"})
        updates = list(dict.fromkeys(s["updated_at"] for s in samples))
        self.assertGreaterEqual(len(updates) - 1, 2, updates)
        last = samples[-1]
        self.assertGreater(last["elapsed_seconds"],
                           samples[0]["elapsed_seconds"])
        self.assertIn("notes/a.txt", last["files_touched"])
        for name in ("events.jsonl", "WU-T01.md", "PROGRESS.md"):
            self.assertEqual(
                [p for p in last["files_touched"] if p.endswith(name)], [])
        self.assertTrue(self.during)
        self.assertEqual(set(threading.enumerate()) - before, set())

    def test_same_named_file_outside_the_feature_folder_is_listed(self):
        seen = {}

        def body(wu, rel):
            Path("docs").mkdir(exist_ok=True)
            Path("docs/PROGRESS.md").write_text("a\n")
            time.sleep(1.6)
            seen.update(json.loads((rel / "work" / "STATUS.json").read_text()))
            write_stub_deliverable(wu)
            return "```result\nstatus: complete\n```\n"

        _run_heartbeat_session(body)
        self.assertIn("docs/PROGRESS.md", seen["files_touched"])

    def test_no_thread_survives_a_raising_session(self):
        before = set(threading.enumerate())

        def body(wu, rel):
            self.during = set(threading.enumerate()) - before
            raise _SessionBoom()

        self.assertIsInstance(_run_heartbeat_session(body), _SessionBoom)
        self.assertTrue(self.during)
        self.assertEqual(set(threading.enumerate()) - before, set())

    def test_resolve_heartbeat_seconds(self):
        for cfg in ({}, {"defaults": {}}, None):
            self.assertEqual(loop.resolve_heartbeat_seconds(cfg), 30)
        for value, expected in (("x", 30), (0, 30), (-5, 30), (True, 30),
                                (1.5, 30), (7, 7)):
            with self.subTest(value=value):
                self.assertEqual(loop.resolve_heartbeat_seconds(
                    {"defaults": {"heartbeat_seconds": value}}), expected)


def _status(age_seconds=0.0, **changes) -> dict:
    updated = dt.datetime.now(dt.timezone.utc) - dt.timedelta(
        seconds=age_seconds)
    status = {
        "feature": FEATURE_ID, "wu_id": WU_ID, "attempt": 1,
        "max_attempts": 3, "phase": "agent", "gate": None,
        "started_at": updated.isoformat(), "updated_at": updated.isoformat(),
        "elapsed_seconds": 12.4, "files_touched": [], "stop_reason": None,
    }
    status.update(changes)
    return status


class _Tty(io.StringIO):
    def isatty(self):
        return True


class TestWatch(unittest.TestCase):
    """Clause 5 — `specfuse-loop --watch`."""

    def _watch(self, statuses, *, out=None, argv=("--watch",), heartbeat=None):
        """`main()` over a status file that is rewritten with the next of
        *statuses* each time the watcher waits."""
        out = io.StringIO() if out is None else out
        err = io.StringIO()
        with integration_workspace() as root, \
                tempfile.TemporaryDirectory() as snapshots:
            cwd = os.getcwd()
            os.chdir(root)
            try:
                fdir = _scaffold(root, Path(snapshots))
                if heartbeat is not None:
                    with (root / ".specfuse/verification.yml").open("a") as fh:
                        fh.write(
                            f"defaults:\n  heartbeat_seconds: {heartbeat}\n")
                path = fdir / "work" / "STATUS.json"
                pending = list(statuses)

                def rewrite():
                    path.parent.mkdir(exist_ok=True)
                    path.write_text(json.dumps(pending.pop(0)))

                if pending:
                    rewrite()

                def sleep(_seconds):
                    if not pending:
                        raise AssertionError(
                            "watch kept waiting: " + out.getvalue())
                    rewrite()

                def tree():
                    return {p: p.read_bytes() for p in root.rglob("*")
                            if p.is_file() and ".git" not in p.parts
                            and p.name != "STATUS.json"}

                before = tree()
                with mock.patch.object(sys, "argv", ["specfuse-loop", *argv]), \
                        mock.patch.object(time, "sleep", sleep), \
                        mock.patch.object(loop, "acquire_tree_lock") as lock, \
                        mock.patch.object(loop, "auto_sync") as sync, \
                        mock.patch.object(loop, "run") as run, \
                        contextlib.redirect_stdout(out), \
                        contextlib.redirect_stderr(err):
                    rc = loop.main()
                for untouched in (lock, sync, run):
                    untouched.assert_not_called()
                self.assertEqual(tree(), before)
            finally:
                os.chdir(cwd)
        return rc, out.getvalue(), err.getvalue()

    def test_line_names_unit_attempt_phase_elapsed_and_gate(self):
        rc, out, _ = self._watch([
            _status(phase="gate", gate="alpha"),
            _status(phase="stopped"),
        ])
        self.assertEqual(rc, 0)
        first = out.splitlines()[0]
        for part in (WU_ID, "attempt 1/3", "phase gate", "gate alpha",
                     "elapsed 12s"):
            self.assertIn(part, first)
        self.assertNotIn("no update", out)
        self.assertNotIn("\r", out)
        self.assertNotIn("\x1b", out)

    def test_prints_only_on_unit_attempt_phase_or_gate_change(self):
        rc, out, _ = self._watch([
            _status(),
            _status(elapsed_seconds=42.0, files_touched=["a.txt"]),
            _status(phase="gate", gate="alpha"),
            _status(phase="gate", gate="beta"),
            _status(attempt=2),
            _status(attempt=2, wu_id=f"{FEATURE_ID}/T02"),
            _status(phase="stopped"),
        ])
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), 6, out)
        self.assertIn("phase agent", lines[0])
        self.assertIn("gate alpha", lines[1])
        self.assertIn("gate beta", lines[2])
        self.assertIn("attempt 2/3", lines[3])
        self.assertIn("/T02", lines[4])
        self.assertIn("phase stopped", lines[5])

    def test_stale_status_says_no_update_once(self):
        rc, out, _ = self._watch([
            _status(age_seconds=100),
            _status(age_seconds=101),
            _status(phase="stopped"),
        ])
        self.assertEqual(rc, 0)
        stale = [ln for ln in out.splitlines() if "no update for" in ln]
        self.assertEqual(len(stale), 1, out)
        self.assertRegex(stale[0], r"no update for 10\ds")

    def test_staleness_is_three_configured_heartbeat_intervals(self):
        for age, expected in ((20, False), (40, True)):
            with self.subTest(age=age):
                _, out, _ = self._watch(
                    [_status(age_seconds=age), _status(phase="stopped")],
                    heartbeat=10)
                self.assertEqual("no update for" in out, expected, out)

    def test_old_stopped_status_is_not_stale(self):
        rc, out, _ = self._watch([_status(age_seconds=500, phase="stopped")])
        self.assertEqual(rc, 0)
        self.assertNotIn("no update", out)

    def test_terminal_redraws_one_line_in_place(self):
        rc, out, _ = self._watch([
            _status(),
            _status(elapsed_seconds=42.0),
            _status(phase="stopped"),
        ], out=_Tty())
        self.assertEqual(rc, 0)
        self.assertEqual(out.count("\n"), 1, repr(out))
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(out.count("\r"), 3, repr(out))
        self.assertIn("elapsed 42s", out)

    def test_feature_argument_resolves_a_bare_id(self):
        rc, out, _ = self._watch(
            [_status(phase="stopped")],
            argv=("--watch", "--feature", FEATURE_ID))
        self.assertEqual(rc, 0)
        self.assertIn(WU_ID, out)

    def test_no_status_file_names_the_expected_path(self):
        rc, _, err = self._watch([])
        self.assertEqual(rc, 1)
        self.assertIn(
            f".specfuse/features/{FEATURE_ID}-{SLUG}/work/STATUS.json", err)


_STUB_COMMAND = (
    "import json, os, sys\n"
    "seen = {k: v for k, v in os.environ.items() "
    "if k.startswith('SPECFUSE_')}\n"
    "open(sys.argv[1], 'a').write("
    "json.dumps({'argv': sys.argv[1:], 'env': seen}) + '\\n')\n"
)
_NOTIFY_VARS = (
    "SPECFUSE_STOP_REASON", "SPECFUSE_FEATURE", "SPECFUSE_WORK_UNIT",
    "SPECFUSE_MESSAGE",
)


def _passing_session(wu, failure_note, cost_tracking=True):
    write_stub_deliverable(wu)
    return "```result\nstatus: complete\n```\n"


def _blocked_session(wu, failure_note, cost_tracking=True):
    return ("```result\nstatus: blocked\n"
            "blocked_reason: needs a human\n```\n")


def _raising_session(wu, failure_note, cost_tracking=True):
    raise _SessionBoom()


class _Notified:
    """One `loop.main()` over the real `run()`, with a counting webhook poster
    and a stub notify command that records each call outside the tree."""

    def __init__(self, session=_passing_session, *, command="stub",
                 webhook=True, argv=(), prepare=None):
        self.posts = []
        self.rc = self.raised = self.status = None
        with integration_workspace() as root, \
                tempfile.TemporaryDirectory() as outside:
            cwd = os.getcwd()
            os.chdir(root)
            try:
                self._run(root, Path(outside), session, command, webhook,
                          argv, prepare)
            finally:
                os.chdir(cwd)

    def _run(self, root, outside, session, command, webhook, argv, prepare):
        fdir = _scaffold(root, outside)
        stub = outside / "stub.py"
        stub.write_text(_STUB_COMMAND)
        calls = outside / "calls.jsonl"
        if command == "stub":
            command = shlex.join([sys.executable, str(stub), str(calls)])
        lines = ["escalation:",
                 f"  webhook_env: {'FIXTURE_HOOK' if webhook else chr(34) * 2}",
                 f"  provider: {'slack' if webhook else 'none'}"]
        if command is not None:
            lines.append(f"  notify_command: {json.dumps(command)}")
        (root / ".specfuse/agent-policy.yml").write_text(
            "\n".join(lines) + "\n")
        if prepare is not None:
            prepare(fdir)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-q", "-m", "policy"], check=True)

        def poster(url, payload):
            self.posts.append((url, payload))
            return 200

        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["specfuse-loop", *argv]), \
                mock.patch.dict(os.environ,
                                {"FIXTURE_HOOK": "https://example.com/hook"}), \
                mock.patch.object(notify, "_default_poster", poster), \
                mock.patch.object(loop, "_reexec_pinned", lambda _a: None), \
                mock.patch.object(loop, "auto_sync"), \
                mock.patch.object(loop, "dispatch", session), \
                contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(out):
            try:
                self.rc = loop.main()
            except (_SessionBoom, SystemExit) as exc:
                self.raised = exc
        self.output = out.getvalue()
        self.commands = [json.loads(ln) for ln in
                         calls.read_text().splitlines()] \
            if calls.exists() else []
        status = fdir / "work" / "STATUS.json"
        if status.is_file():
            self.status = json.loads(status.read_text())
        self.pwned = list(root.rglob("pwned"))


def _all_passed(fdir):
    for name, old, new in (("GATE-01.md", "open", "passed"),
                           ("PLAN.md", "active", "done")):
        path = fdir / name
        path.write_text(path.read_text().replace(
            f"status: {old}", f"status: {new}"))


def _draft_unit(fdir):
    path = fdir / "WU-T01.md"
    path.write_text(path.read_text().replace(
        "status: pending", "status: draft"))


class TestStopNotification(unittest.TestCase):
    """Clause 6 — one notification when the run stops."""

    def _assert_notified(self, seen, reason, unit):
        self.assertEqual(len(seen.posts), 1, seen.output)
        self.assertEqual(len(seen.commands), 1, seen.output)
        env = seen.commands[0]["env"]
        for name in _NOTIFY_VARS:
            self.assertIn(name, env)
        self.assertEqual(env["SPECFUSE_STOP_REASON"], reason, seen.output)
        self.assertEqual(env["SPECFUSE_FEATURE"], FEATURE_ID)
        self.assertEqual(env["SPECFUSE_WORK_UNIT"], unit, seen.output)
        self.assertIn(reason, env["SPECFUSE_MESSAGE"])
        self.assertEqual(seen.posts[0][1], {"text": env["SPECFUSE_MESSAGE"]})
        self.assertEqual(len(seen.commands[0]["argv"]), 1)
        self.assertEqual(seen.status["phase"], "stopped")
        self.assertEqual(seen.status["stop_reason"], reason)

    def test_halted(self):
        seen = _Notified(_blocked_session)
        self._assert_notified(seen, "halted", WU_ID)

    def test_awaiting_review(self):
        seen = _Notified()
        self.assertEqual(seen.rc, 0, seen.output)
        self._assert_notified(seen, "awaiting_review", WU_ID)

    def test_complete(self):
        seen = _Notified(prepare=_all_passed,
                         argv=("--feature", FEATURE_ID))
        self.assertEqual(seen.rc, 0, seen.output)
        self._assert_notified(seen, "complete", "")

    def test_error(self):
        seen = _Notified(_raising_session)
        self.assertIsInstance(seen.raised, _SessionBoom, seen.output)
        self._assert_notified(seen, "error", WU_ID)

    def test_stopped(self):
        seen = _Notified(prepare=_draft_unit)
        self.assertEqual(seen.rc, 2, seen.output)
        self._assert_notified(seen, "stopped", "")

    def test_events_of_an_earlier_run_are_not_read(self):
        def earlier(fdir):
            _draft_unit(fdir)
            (fdir / "events.jsonl").write_text(json.dumps({
                "event_type": "human_escalation",
                "correlation_id": WU_ID, "payload": {}}) + "\n")

        self._assert_notified(_Notified(prepare=earlier), "stopped", "")

    def test_a_held_lock_leaves_the_other_drivers_status_alone(self):
        live = _status()

        def other_driver(fdir):
            (fdir / "work").mkdir()
            (fdir / "work" / ".gitignore").write_text("*\n")
            (fdir / "work" / "STATUS.json").write_text(json.dumps(live))

        with mock.patch.object(loop, "acquire_tree_lock",
                               side_effect=BlockingIOError):
            seen = _Notified(prepare=other_driver)
        self.assertEqual(seen.rc, 1, seen.output)
        self.assertEqual(len(seen.commands), 1, seen.output)
        self.assertEqual(seen.status, live)

    def test_a_failing_command_leaves_the_exit_code_unchanged(self):
        python = shlex.quote(sys.executable)
        for label, command in (
            ("exit 1", f"{python} -c 'raise SystemExit(1)'"),
            ("timeout", f"{python} -c 'import time; time.sleep(20)'"),
            ("missing", "specfuse-no-such-program-fixture"),
            ("unbalanced quote", "echo 'x"),
        ):
            with self.subTest(label), \
                    mock.patch.object(progress, "_NOTIFY_TIMEOUT_SECONDS", 1), \
                    self.assertLogs(progress.logger, "WARNING"):
                started = time.monotonic()
                seen = _Notified(command=command)
                self.assertEqual(seen.rc, 0, seen.output)
                self.assertIsNone(seen.raised)
                self.assertEqual(len(seen.posts), 1)
                self.assertLess(time.monotonic() - started, 15)

    def test_the_command_timeout_is_thirty_seconds(self):
        self.assertEqual(progress._NOTIFY_TIMEOUT_SECONDS, 30)

    def test_nothing_configured_sends_nothing(self):
        with mock.patch.object(progress.subprocess, "run",
                               wraps=subprocess.run) as ran:
            seen = _Notified(command=None, webhook=False)
        self.assertEqual(seen.rc, 0, seen.output)
        self.assertEqual((seen.posts, seen.commands), ([], []))
        self.assertEqual(
            [c for c in ran.call_args_list
             if "SPECFUSE_MESSAGE" in (c.kwargs.get("env") or {})], [])

    def test_dry_run_sends_nothing(self):
        seen = _Notified(argv=("--dry-run",))
        self.assertEqual(seen.rc, 0, seen.output)
        self.assertEqual((seen.posts, seen.commands), ([], []))

    def test_message_never_reaches_a_shell(self):
        hostile = "FEAT-X; touch pwned"
        seen = _Notified(argv=("--feature", hostile))
        self.assertIsInstance(seen.raised, SystemExit, seen.output)
        self.assertEqual(len(seen.commands), 1, seen.output)
        env = seen.commands[0]["env"]
        self.assertIn("; touch pwned", env["SPECFUSE_MESSAGE"])
        self.assertEqual(env["SPECFUSE_STOP_REASON"], "error")
        self.assertEqual(len(seen.commands[0]["argv"]), 1)
        self.assertEqual(seen.pwned, [])


if __name__ == "__main__":
    unittest.main()
