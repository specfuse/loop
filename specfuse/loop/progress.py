#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Live progress of a running driver (FEAT-LOOP-2026-0252).

One function per phase change. Each appends its event to `events.jsonl` at
once (never through a unit's buffered `wu_events`), rewrites the status file
`<feature>/work/STATUS.json`, and prints one plain line: no carriage return,
no ANSI. While an attempt runs, a heartbeat thread also rewrites the status
file, so its elapsed time and touched files stay current.

Gates may run in parallel (FEAT-LOOP-2026-0253), so `gate_started` and
`gate_finished` arrive from worker threads. One lock serialises every write to
`events.jsonl` and the status file; it is held for a write, never for a gate.

Every function is a no-op unless `begin_run` was called, so a caller that runs
a gate set or an attempt outside `run()` writes nothing.

`build_event` and `flush_events` are passed in by the driver: it imports this
module, so this module does not import it.

`watch` is the `specfuse-loop --watch` reader, run from a second terminal. It
only reads the status file: it takes no run lock and writes nothing.

`notify_stop` runs once, after `run()` has ended: it works out why the run
stopped from the events that run appended, and tells the operator.

Reports only; no merge, arm or close verdict reads anything written here.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import agent_policy, notify

logger = logging.getLogger(__name__)

STATUS_FILENAME = "STATUS.json"

PHASE_AGENT = "agent"
PHASE_GATE = "gate"
PHASE_BETWEEN = "between"
PHASE_STOPPED = "stopped"

# `work/` is gitignored by the scaffold. This keeps the status file out of git
# in a project whose ignore rules do not cover it, and ignores nothing else.
_WORK_IGNORE = f"/.gitignore\n/{STATUS_FILENAME}*\n"


@dataclass
class _Run:
    feature: str
    feature_dir: Path
    events_path: Path
    build_event: Callable
    flush_events: Callable
    wu_id: "str | None" = None
    attempt: "int | None" = None
    max_attempts: "int | None" = None
    phase: str = PHASE_BETWEEN
    gate: "str | None" = None
    gates_running: "list[str]" = field(default_factory=list)  # start order
    started_at: str = ""
    started_clock: float = 0.0
    agent_clock: float = 0.0
    files_touched: "list[str]" = field(default_factory=list)


_run: "_Run | None" = None
_heartbeat: "tuple[threading.Thread, threading.Event] | None" = None
# The heartbeat, the driver and parallel gate threads rewrite the status file
# through the same temporary name, and gate threads append to `events.jsonl`.
# Reentrant: a gate change holds it across its own status and event writes.
_write_lock = threading.RLock()


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _restart_clock(run: _Run) -> None:
    run.started_at = _now()
    run.started_clock = time.monotonic()


def status_path(feature_dir: Path) -> Path:
    return Path(feature_dir) / "work" / STATUS_FILENAME


def write_status(feature_dir: Path, status: dict) -> None:
    """Replace the status file atomically. A write failure is swallowed:
    progress reporting never fails a run."""
    path = status_path(feature_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        ignore = path.parent / ".gitignore"
        if not ignore.exists():
            ignore.write_text(_WORK_IGNORE, encoding="utf-8")
        tmp = path.with_name(f"{STATUS_FILENAME}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(status) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def _rewrite_status(stop_reason: "str | None" = None) -> None:
    run = _run
    with _write_lock:
        write_status(run.feature_dir, {
            "feature": run.feature,
            "wu_id": run.wu_id,
            "attempt": run.attempt,
            "max_attempts": run.max_attempts,
            "phase": run.phase,
            "gate": run.gate,
            "gates_running": list(run.gates_running),
            "started_at": run.started_at,
            "updated_at": _now(),
            "elapsed_seconds": round(time.monotonic() - run.started_clock, 3),
            "files_touched": run.files_touched,
            "stop_reason": stop_reason,
        })


def _append_event(event_type: str, payload: dict) -> None:
    run = _run
    with _write_lock:
        run.flush_events(run.events_path, [run.build_event(
            event_type, run.wu_id or run.feature, payload)])


def _clear_gates(run: _Run) -> None:
    run.gate = None
    run.gates_running = []


def _plain(text: str) -> str:
    return "".join(c if c.isprintable() else " " for c in text)


def _say(text: str) -> None:
    print(f"   [{time.strftime('%H:%M:%S')}] {_plain(text)}", flush=True)


def begin_run(
    feature: str, feature_dir: Path, events_path: Path, *,
    build_event: Callable, flush_events: Callable,
) -> None:
    global _run
    _run = _Run(feature, Path(feature_dir), Path(events_path),
                build_event, flush_events)
    _restart_clock(_run)


def end_run(stop_reason: "str | None" = None) -> None:
    """Mark the run stopped. A run that never reached a unit writes the status
    file too, so a reader never sees an earlier run's live phase."""
    global _run
    if _run is None:
        return
    stop_heartbeat()
    _run.phase = PHASE_STOPPED
    _clear_gates(_run)
    _rewrite_status(stop_reason)
    _run = None


def begin_attempt(wu_id: str, attempt: int, max_attempts: int) -> None:
    if _run is None:
        return
    _run.wu_id = wu_id
    _run.attempt = attempt
    _run.max_attempts = max_attempts
    _run.phase = PHASE_BETWEEN
    _clear_gates(_run)
    _run.files_touched = []
    _restart_clock(_run)
    _rewrite_status()


def start_heartbeat(
    interval_seconds: float,
    files_touched: "Callable[[], list[str] | None]",
) -> None:
    """Rewrite the status file every *interval_seconds* until
    `stop_heartbeat`. *files_touched* returning None, or raising, keeps the
    last list: a failed reading never stops the beat or the run."""
    global _heartbeat
    if _run is None:
        return
    stop_heartbeat()
    run = _run
    stop = threading.Event()

    def beat() -> None:
        while not stop.wait(interval_seconds):
            try:
                touched = files_touched()
            except Exception:  # noqa: BLE001 — reporting never fails a run
                touched = None
            if touched is not None:
                run.files_touched = touched
            _rewrite_status()

    thread = threading.Thread(
        target=beat, name="specfuse-heartbeat", daemon=True)
    thread.start()
    _heartbeat = (thread, stop)


def stop_heartbeat() -> None:
    """Stop the heartbeat and wait for its thread to end."""
    global _heartbeat
    if _heartbeat is None:
        return
    thread, stop = _heartbeat
    stop.set()
    thread.join()
    _heartbeat = None


def clear_unit() -> None:
    """No unit is running: gates run from here belong to the feature."""
    if _run is None or _run.wu_id is None:
        return
    _run.wu_id = _run.attempt = _run.max_attempts = None
    _run.files_touched = []
    _run.phase = PHASE_BETWEEN
    _clear_gates(_run)
    _restart_clock(_run)
    _rewrite_status()


def agent_session_started() -> None:
    if _run is None:
        return
    _run.phase = PHASE_AGENT
    _clear_gates(_run)
    _run.agent_clock = time.monotonic()
    _rewrite_status()
    _append_event("agent_session_started", {"attempt": _run.attempt})
    _say("agent session started")


def agent_session_finished() -> None:
    if _run is None:
        return
    seconds = time.monotonic() - _run.agent_clock
    _run.phase = PHASE_BETWEEN
    _rewrite_status()
    _append_event("agent_session_finished", {"attempt": _run.attempt})
    _say(f"agent session finished ({seconds:.1f}s)")


def gate_started(name: str) -> None:
    if _run is None:
        return
    with _write_lock:
        _run.phase = PHASE_GATE
        _run.gates_running.append(name)
        _run.gate = name
        _rewrite_status()
        _append_event("gate_started", {"attempt": _run.attempt, "gate": name})
        _say(f"gate {name} started")


def gate_finished(name: str, ok: bool, duration_seconds: float) -> None:
    if _run is None:
        return
    with _write_lock:
        if name in _run.gates_running:
            _run.gates_running.remove(name)
        running = _run.gates_running
        _run.phase = PHASE_GATE if running else PHASE_BETWEEN
        _run.gate = running[-1] if running else None
        _rewrite_status()
        _append_event("gate_finished", {
            "attempt": _run.attempt, "gate": name, "ok": bool(ok),
            "duration_seconds": duration_seconds})
        _say(f"gate {name} {'PASS' if ok else 'FAIL'} "
             f"({duration_seconds:.1f}s)")


_NOTIFY_TIMEOUT_SECONDS = 30


@dataclass
class _Stop:
    """What `notify_stop` needs once `run()` has ended."""

    feature: str
    feature_dir: Path
    events_path: Path
    started_at: "dt.datetime"
    load_graph: Callable
    owns_status: bool = True


_stop: "_Stop | None" = None


def remember_run(
    feature: str, feature_dir: Path, events_path: Path, *,
    load_graph: Callable,
) -> None:
    """Call as the run starts, before it appends any event.

    The run's events are later told apart by timestamp, not by a byte offset:
    `run()` may check out the feature branch, whose `events.jsonl` can be
    longer or shorter than the one the run started on (#3626).
    """
    global _stop
    _stop = _Stop(feature, Path(feature_dir), Path(events_path),
                  dt.datetime.now(dt.timezone.utc), load_graph)


def disown_status() -> None:
    """Another driver holds the tree: its status file is not ours to write."""
    if _stop is not None:
        _stop.owns_status = False


def forget_run() -> None:
    global _stop
    _stop = None


def _event_time(event: dict) -> "dt.datetime | None":
    try:
        when = dt.datetime.fromisoformat(str(event.get("timestamp", "")))
    except ValueError:
        return None
    return when if when.tzinfo is not None else None


def _events_since(path: Path, started_at: "dt.datetime") -> "list[dict]":
    """Events in *path* stamped at or after *started_at*. An event with no
    readable timezone-aware timestamp was not written by this run."""
    try:
        lines = path.read_bytes().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return []
    events = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        when = _event_time(event)
        if when is not None and when >= started_at:
            events.append(event)
    return events


def _stop_reason(
    stop: "_Stop | None", events: "list[dict]", raised: bool,
) -> str:
    fallback = "error" if raised else "stopped"
    if stop is None:
        return fallback
    if any(e.get("event_type") == "human_escalation" for e in events):
        return "halted"
    try:
        plan, gates = stop.load_graph(stop.feature_dir)
    except (Exception, SystemExit):  # noqa: BLE001 — an unreadable plan
        return fallback
    reached = {(e.get("payload") or {}).get("gate") for e in events
               if e.get("event_type") == "gate_reached"}
    if any(g.number in reached and g.status == "awaiting_review"
           for g in gates):
        return "awaiting_review"
    if plan.get("status") == "done":
        return "complete"
    return fallback


def _stop_work_unit(events: "list[dict]") -> str:
    """The unit of the last escalation, else the last unit the run wrote
    about. A feature-level escalation may name the unit it halted before."""
    escalations = [e for e in events
                   if e.get("event_type") == "human_escalation"]
    if escalations:
        last = escalations[-1]
        unit = str(last.get("correlation_id", ""))
        if "/" in unit:
            return unit
        return str((last.get("payload") or {}).get("next_wu_id") or "")
    for event in reversed(events):
        unit = str(event.get("correlation_id", ""))
        if "/" in unit:
            return unit
    return ""


def _run_notify_command(env: "dict[str, str]") -> None:
    """Run `escalation.notify_command`, when set, as an argument list."""
    try:
        policy = agent_policy.load_policy(None)
    except FileNotFoundError:
        return
    escalation = policy.get("escalation") if isinstance(policy, dict) else None
    command = (escalation.get("notify_command")
               if isinstance(escalation, dict) else None)
    if not isinstance(command, str) or not command.strip():
        return
    try:
        done = subprocess.run(
            shlex.split(command), env={**os.environ, **env},
            timeout=_NOTIFY_TIMEOUT_SECONDS, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        # The exception's text repeats the command, which may hold a token.
        logger.warning("notify_command failed: %s", type(exc).__name__)
        return
    if done.returncode != 0:
        logger.warning("notify_command exited %s", done.returncode)


def notify_stop(*, raised: bool, feature_arg: "str | None" = None) -> None:
    """Record why the run stopped and send it once to each configured channel.

    Never raises: reporting does not change how a run ends. A run that failed
    before it found its feature is reported under *feature_arg*.
    """
    global _stop
    stop, _stop = _stop, None
    try:
        events = ([] if stop is None
                  else _events_since(stop.events_path, stop.started_at))
        reason = _stop_reason(stop, events, raised)
        feature = stop.feature if stop else (feature_arg or "")
        unit = _stop_work_unit(events)
        if stop is not None and stop.owns_status:
            _write_stop_reason(stop, reason)
        message = f"specfuse-loop {reason}: {feature or 'unknown feature'}"
        if unit:
            message += f" (last unit {unit})"
    except Exception as exc:  # noqa: BLE001
        logger.warning("stop notification not built: %s", type(exc).__name__)
        return
    try:
        notify.post_notification(message)
    except Exception as exc:  # noqa: BLE001
        logger.warning("stop webhook failed: %s", type(exc).__name__)
    try:
        _run_notify_command({
            "SPECFUSE_STOP_REASON": reason,
            "SPECFUSE_FEATURE": feature,
            "SPECFUSE_WORK_UNIT": unit,
            "SPECFUSE_MESSAGE": message,
        })
    except Exception as exc:  # noqa: BLE001
        logger.warning("notify_command failed: %s", type(exc).__name__)


def _write_stop_reason(stop: _Stop, reason: str) -> None:
    """Set `stop_reason` on the status file. A run that ended before
    `begin_run` replaces whatever an earlier run left there."""
    now = _now()
    status = _read_status(status_path(stop.feature_dir)) or {
        "feature": stop.feature, "wu_id": None, "attempt": None,
        "max_attempts": None, "started_at": now, "elapsed_seconds": 0.0,
        "files_touched": [],
    }
    status.update(phase=PHASE_STOPPED, gate=None, gates_running=[],
                  updated_at=now, stop_reason=reason)
    write_status(stop.feature_dir, status)


# A watcher is stale after this many heartbeat intervals without a rewrite.
_STALE_INTERVALS = 3
_WATCH_POLL_SECONDS = 1.0


def _read_status(path: Path) -> "dict | None":
    try:
        status = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return status if isinstance(status, dict) else None


def _age_seconds(status: dict) -> "float | None":
    try:
        updated = dt.datetime.fromisoformat(status["updated_at"])
        return (dt.datetime.now(dt.timezone.utc) - updated).total_seconds()
    except (KeyError, TypeError, ValueError):
        return None


def _watch_line(status: dict, stale_age: "float | None") -> str:
    attempt = "-"
    if status.get("attempt") is not None:
        attempt = f"{status['attempt']}/{status.get('max_attempts')}"
    elapsed = status.get("elapsed_seconds")
    elapsed = f"{int(elapsed)}s" if isinstance(elapsed, (int, float)) else "-"
    line = (f"{status.get('wu_id') or status.get('feature')}  "
            f"attempt {attempt}  phase {status.get('phase')}  "
            f"gate {status.get('gate') or '-'}  elapsed {elapsed}")
    if stale_age is not None:
        # First, so cutting the line to the terminal width keeps it.
        line = f"no update for {int(stale_age)}s  {line}"
    return _plain(line)


def watch(feature_dir: Path, heartbeat_seconds: float) -> int:
    """Follow the status file of *feature_dir* until its phase is `stopped`.

    On a terminal one line is redrawn in place. Otherwise a line is printed
    when the unit, attempt, phase or gate changes, and once each time the file
    goes stale. Returns 0 when the run stopped, 1 when there is no status file,
    130 on Ctrl-C.
    """
    path = status_path(feature_dir)
    out = sys.stdout
    tty = out.isatty()
    shown = None
    drawn = 0
    try:
        while True:
            status = _read_status(path)
            if status is None:
                if not path.is_file():
                    if drawn:
                        out.write("\n")
                    print(f"No status file at {path}. `specfuse-loop` writes "
                          f"it while it runs this feature.", file=sys.stderr)
                    return 1
                time.sleep(_WATCH_POLL_SECONDS)
                continue
            stopped = status.get("phase") == PHASE_STOPPED
            age = _age_seconds(status)
            stale = (not stopped and age is not None
                     and age > _STALE_INTERVALS * heartbeat_seconds)
            line = _watch_line(status, age if stale else None)
            if tty:
                width = max(shutil.get_terminal_size().columns - 1, 1)
                text = line[:width]
                # Padding covers a longer previous line without ANSI codes.
                out.write("\r" + text.ljust(min(drawn, width)))
                out.flush()
                drawn = len(text)
            else:
                key = tuple(status.get(k) for k in (
                    "wu_id", "attempt", "phase", "gate")) + (stale,)
                # Leaving the stale state alone is not a change to report.
                if key != shown and not (
                        shown and shown[-1] and not stale
                        and key[:-1] == shown[:-1]):
                    print(line, file=out, flush=True)
                shown = key
            if stopped:
                if tty:
                    out.write("\n")
                return 0
            time.sleep(_WATCH_POLL_SECONDS)
    except KeyboardInterrupt:
        if drawn:
            out.write("\n")
        return 130
