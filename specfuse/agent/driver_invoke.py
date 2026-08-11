# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Invoke `specfuse run` as a subprocess and classify what came back
(FEAT-2026-0049/T13).

`GATE-04.md` names the two live defects that make in-process invocation of
the driver's entrypoint wrong here — #757 (a work unit that edits the
driver cannot take effect for anything the same process dispatches
afterwards) and #1040 (console scripts resolving the loop package from
site-packages rather than the working tree). This module never imports the
driver's package and never calls its entrypoint function directly — every
invocation goes through an injected `runner(argv, check=False)` callable,
the same subprocess-injection shape `specfuse/agent/state.py` already uses
for `gh`.

The driver's exit code alone is ambiguous (`0` covers both "a gate
advanced" and "the feature is complete"; `1` covers both "a work unit
blocked" and "another driver holds the lock"). `classify_halt` resolves
every ambiguity against state the driver already writes — `PLAN.md` and
`GATE-NN.md` frontmatter before and after the run, and the `events.jsonl`
rows the run appended — never against a driver change. See `WU-13`'s table
for the exit-code-to-evidence mapping this module encodes.

`read_frontmatter` and `load_plan_graph` come from `specfuse.loop.lint_plan`
and `specfuse.loop.plan_baseline` — plain parsers, not the driver — the same
modules `specfuse/agent/state.py` already reads through for the same
reason. This module issues no `git` command, no `gh` command, and writes no
file.
"""

from __future__ import annotations

import json
from collections import namedtuple
from pathlib import Path
from typing import Callable, Optional

from specfuse.loop.lint_plan import read_frontmatter
from specfuse.loop.plan_baseline import load_plan_graph

__all__ = (
    "HALT_ADVANCED",
    "HALT_AWAITING_REVIEW",
    "HALT_NOT_ARMED",
    "HALT_BLOCKED",
    "HALT_FEATURE_DONE",
    "HALT_DRIVER_ERROR",
    "build_invocation",
    "classify_halt",
    "advance_feature",
    "FeatureState",
    "HaltResult",
)

HALT_ADVANCED = "advanced"
HALT_AWAITING_REVIEW = "awaiting_review"
HALT_NOT_ARMED = "not_armed"
HALT_BLOCKED = "blocked"
HALT_FEATURE_DONE = "feature_done"
HALT_DRIVER_ERROR = "driver_error"

_DEFAULT_COMMAND = ("specfuse", "run")
_STDERR_TAIL_LINES = 20

FeatureState = namedtuple(
    "FeatureState", ["feature_dir", "plan_status", "gates", "event_count"]
)
HaltResult = namedtuple("HaltResult", ["halt_class", "detail", "argv"])


def build_invocation(feature_id: str, *, command=_DEFAULT_COMMAND) -> list:
    """Build the argv for one `specfuse run --feature <feature_id>`
    invocation. Runs nothing — the caller passes this to its runner."""
    return list(command) + ["--feature", feature_id]


def _find_feature_dir(features_root, feature_id: str) -> Optional[Path]:
    features_root = Path(features_root)
    if not features_root.is_dir():
        return None
    for entry in sorted(p for p in features_root.iterdir() if p.is_dir()):
        plan_path = entry / "PLAN.md"
        if not plan_path.is_file():
            continue
        try:
            plan_fm, _ = read_frontmatter(plan_path)
        except Exception:  # noqa: BLE001 - unreadable folder, keep scanning
            continue
        if plan_fm.get("feature_id", entry.name) == feature_id:
            return entry
    return None


def _read_gate_statuses(feature_dir: Path) -> dict:
    try:
        graph = load_plan_graph(feature_dir)
    except Exception:  # noqa: BLE001 - no graph block yet, no gates to read
        return {}
    gates = {}
    for gate_entry in graph.get("gates") or []:
        gate_num = gate_entry.get("gate")
        gate_file = gate_entry.get("file")
        gate_status = None
        if gate_file:
            gate_path = feature_dir / gate_file
            if gate_path.is_file():
                gate_fm, _ = read_frontmatter(gate_path)
                gate_status = gate_fm.get("status")
        gates[gate_num] = gate_status
    return gates


def _count_events(feature_dir: Path) -> int:
    events_path = feature_dir / "events.jsonl"
    if not events_path.is_file():
        return 0
    with events_path.open() as fh:
        return sum(1 for _ in fh)


def read_feature_state(features_root, feature_id: str) -> FeatureState:
    """Read the feature's `PLAN.md` status, each gate's status, and the
    current `events.jsonl` line count. Never writes; never runs a command."""
    feature_dir = _find_feature_dir(features_root, feature_id)
    if feature_dir is None:
        return FeatureState(feature_dir=None, plan_status=None, gates={}, event_count=0)
    plan_fm, _ = read_frontmatter(feature_dir / "PLAN.md")
    return FeatureState(
        feature_dir=feature_dir,
        plan_status=plan_fm.get("status"),
        gates=_read_gate_statuses(feature_dir),
        event_count=_count_events(feature_dir),
    )


def _read_new_events(feature_dir: Optional[Path], since_count: int) -> list:
    if feature_dir is None:
        return []
    events_path = feature_dir / "events.jsonl"
    if not events_path.is_file():
        return []
    lines = events_path.read_text().splitlines()[since_count:]
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def _find_human_escalation(events: list) -> Optional[dict]:
    for event in events:
        if event.get("event_type") == "human_escalation":
            return event
    return None


def _tail(text: str, *, lines: int = _STDERR_TAIL_LINES) -> str:
    parts = text.splitlines()
    return "\n".join(parts[-lines:]).strip()


def classify_halt(returncode: int, before: FeatureState, after: FeatureState,
                   new_events: list, stderr: str = "") -> tuple:
    """Classify one `specfuse run` halt into one of the six `HALT_*`
    classes, using only the exit code plus feature state read before and
    after the run and the events the run appended. Returns
    `(halt_class, detail)`."""
    if returncode == 2:
        return HALT_NOT_ARMED, None

    if returncode == 1:
        escalation = _find_human_escalation(new_events)
        if escalation is not None:
            payload = escalation.get("payload") or {}
            detail = {
                "wu_id": escalation.get("correlation_id"),
                "reason": payload.get("reason"),
            }
            return HALT_BLOCKED, detail
        return HALT_DRIVER_ERROR, _tail(stderr or "")

    # returncode == 0
    if after.plan_status == "done":
        return HALT_FEATURE_DONE, None

    after_gates = after.gates
    if after_gates and all(status == "passed" for status in after_gates.values()):
        return (
            HALT_AWAITING_REVIEW,
            f"all gates passed but PLAN.md status is '{after.plan_status}', "
            "not 'done' — the terminal flips were withheld",
        )

    for gate_num, status_before in before.gates.items():
        status_after = after_gates.get(gate_num)
        if status_before != "passed" and status_after == "passed":
            return HALT_ADVANCED, {"gate": gate_num}

    for gate_num, status_after in after_gates.items():
        if status_after == "awaiting_review":
            return HALT_AWAITING_REVIEW, {"gate": gate_num}

    return HALT_AWAITING_REVIEW, None


def advance_feature(runner: Callable, feature_id: str, *, features_root,
                     command=_DEFAULT_COMMAND) -> HaltResult:
    """Issue exactly one `specfuse run --feature <feature_id>` subprocess
    through `runner` and return its classified halt.

    Reads the feature's `PLAN.md`/gate/`events.jsonl` state before the
    call and again after, so `classify_halt` sees both snapshots plus
    whatever `events.jsonl` rows the run appended. Issues no `git` command,
    no `gh` command, and writes no file itself."""
    before = read_feature_state(features_root, feature_id)
    argv = build_invocation(feature_id, command=command)
    result = runner(argv, check=False)
    after = read_feature_state(features_root, feature_id)
    new_events = _read_new_events(after.feature_dir or before.feature_dir, before.event_count)
    stderr = getattr(result, "stderr", "") or ""
    halt_class, detail = classify_halt(result.returncode, before, after, new_events, stderr)
    return HaltResult(halt_class=halt_class, detail=detail, argv=argv)
