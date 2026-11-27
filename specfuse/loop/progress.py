#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Live progress of a running driver (FEAT-LOOP-2026-0252).

One function per phase change. Each appends its event to `events.jsonl` at
once (never through a unit's buffered `wu_events`), rewrites the status file
`<feature>/work/STATUS.json`, and prints one plain line: no carriage return,
no ANSI.

Every function is a no-op unless `begin_run` was called, so a caller that runs
a gate set or an attempt outside `run()` writes nothing.

`build_event` and `flush_events` are passed in by the driver: it imports this
module, so this module does not import it.

Reports only; no merge, arm or close verdict reads anything written here.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
    started_at: str = ""
    started_clock: float = 0.0
    agent_clock: float = 0.0


_run: "_Run | None" = None


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
    write_status(run.feature_dir, {
        "feature": run.feature,
        "wu_id": run.wu_id,
        "attempt": run.attempt,
        "max_attempts": run.max_attempts,
        "phase": run.phase,
        "gate": run.gate,
        "started_at": run.started_at,
        "updated_at": _now(),
        "elapsed_seconds": round(time.monotonic() - run.started_clock, 3),
        "files_touched": [],
        "stop_reason": stop_reason,
    })


def _append_event(event_type: str, payload: dict) -> None:
    run = _run
    run.flush_events(run.events_path, [run.build_event(
        event_type, run.wu_id or run.feature, payload)])


def _say(text: str) -> None:
    plain = "".join(c if c.isprintable() else " " for c in text)
    print(f"   [{time.strftime('%H:%M:%S')}] {plain}", flush=True)


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
    _run.phase = PHASE_STOPPED
    _run.gate = None
    _rewrite_status(stop_reason)
    _run = None


def begin_attempt(wu_id: str, attempt: int, max_attempts: int) -> None:
    if _run is None:
        return
    _run.wu_id = wu_id
    _run.attempt = attempt
    _run.max_attempts = max_attempts
    _run.phase = PHASE_BETWEEN
    _run.gate = None
    _restart_clock(_run)
    _rewrite_status()


def clear_unit() -> None:
    """No unit is running: gates run from here belong to the feature."""
    if _run is None or _run.wu_id is None:
        return
    _run.wu_id = _run.attempt = _run.max_attempts = None
    _run.phase = PHASE_BETWEEN
    _run.gate = None
    _restart_clock(_run)
    _rewrite_status()


def agent_session_started() -> None:
    if _run is None:
        return
    _run.phase = PHASE_AGENT
    _run.gate = None
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
    _run.phase = PHASE_GATE
    _run.gate = name
    _rewrite_status()
    _append_event("gate_started", {"attempt": _run.attempt, "gate": name})
    _say(f"gate {name} started")


def gate_finished(name: str, ok: bool, duration_seconds: float) -> None:
    if _run is None:
        return
    _run.phase = PHASE_BETWEEN
    _run.gate = None
    _rewrite_status()
    _append_event("gate_finished", {
        "attempt": _run.attempt, "gate": name, "ok": bool(ok),
        "duration_seconds": duration_seconds})
    _say(f"gate {name} {'PASS' if ok else 'FAIL'} ({duration_seconds:.1f}s)")
