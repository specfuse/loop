#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""One lifetime-cost reader shared by both cost-gated consumers.

`wu_lifetime_cost_usd` answers "what has this work unit cost over its whole
life." FEAT-2026-0067 converged the fold onto one path: every re-arm now
unconditionally folds the prior cycle's spend into `cumulative_cost_usd`
(driven by an explicit `folded_through_re_arm` marker, not by inferring state
from a value), so `cumulative_cost_usd` is the lifetime accumulator and
`re_arm_history[].prior_cost_usd` is a pure audit record of what each cycle
cost — not a second place the fold might or might not have run.

Before that migration, some already-re-armed WUs had a prior cycle's spend
survive only in `re_arm_history[].prior_cost_usd` with `cumulative_cost_usd`
absent — a pre-migration legacy shape that this module's frontmatter fallback
still tolerates for projects that have not run the FEAT-2026-0067 migration,
not an ongoing design a reader needs to branch on.

Summing frontmatter fields cannot distinguish "already folded" from "never
folded" without replaying fold history, and naive summation double-counts a
folded record. Instead this module sums `payload.cost_usd` across every
`attempt_outcome` event for the work unit in `events.jsonl` — a source that
already carries every dispatch cycle's cost exactly once, independent of fold
shape. Frontmatter is used only as a fallback for the units this repo's
corpus shows have no usable event history (see FEAT-2026-0062 criterion 9's
measurement).

Deliberately dependency-light: this module must not import `loop.py` or
`arm_eval.py` (see `arm_eval.py`'s module docstring on the `loop -> arm_eval`
direction; both existing consumers would otherwise need to reach across each
other to share this function). It imports only the standard library and the
sibling `_miniyaml` parser already used to read WU frontmatter elsewhere.

This function is called from budget brakes, so it never raises: a missing
file, an unreadable line, an absent field, or a `bool` where a number is
expected all contribute 0.0 rather than propagating an exception.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import _miniyaml

_FM_MARKER = re.compile(r"^---\s*$")


def _read_frontmatter(path: Path) -> dict:
    """Best-effort frontmatter read. Any failure yields `{}`."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return {}
    if not lines or not _FM_MARKER.match(lines[0]):
        return {}
    j = 1
    while j < len(lines) and not _FM_MARKER.match(lines[j]):
        j += 1
    try:
        return _miniyaml.parse("\n".join(lines[1:j])) or {}
    except _miniyaml.MiniYAMLError:
        return {}


def _numeric(value: object) -> float:
    """Coerce a frontmatter/event scalar to a cost float, or 0.0.

    A `bool` is rejected even though `bool` is an `int` subclass — a stray
    `cost_usd: true` must contribute nothing, not 1.0.
    """
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _events_cost_sum(events_path: Path, wu_id: str) -> tuple[float, bool]:
    """Return (sum, any_attempt_outcome_seen) for this WU's events.

    `any_attempt_outcome_seen` distinguishes "no events for this WU" (fall
    back to frontmatter) from "events exist but none had cost_usd" (still
    the events path — contributes 0.0, not a fallback).
    """
    try:
        lines = events_path.read_text().splitlines()
    except OSError:
        return 0.0, False

    total = 0.0
    seen = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "attempt_outcome":
            continue
        if event.get("correlation_id") != wu_id:
            continue
        seen = True
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        total += _numeric(payload.get("cost_usd"))
    return total, seen


def wu_lifetime_cost_usd(wu_path: Path, events_path: Path) -> float:
    """Sum this work unit's cost across its whole life.

    Events first: sum `payload.cost_usd` across every `attempt_outcome`
    event in `events_path` whose `correlation_id` is this WU's `id`. Falls
    back to `cost_usd + cumulative_cost_usd` from `wu_path`'s frontmatter
    only when the WU has no `attempt_outcome` events at all. Never both —
    see the module docstring for why summing all three fields double-counts.
    """
    wu_path = Path(wu_path)
    events_path = Path(events_path)

    fm = _read_frontmatter(wu_path)
    wu_id = fm.get("id")

    if isinstance(wu_id, str) and wu_id:
        events_total, seen = _events_cost_sum(events_path, wu_id)
        if seen:
            return events_total

    return _numeric(fm.get("cost_usd")) + _numeric(fm.get("cumulative_cost_usd"))
