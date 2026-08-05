#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Stamp `folded_through_re_arm` onto every already-re-armed work unit
(FEAT-2026-0067/T02).

T01 (`detect_rearm_dispatch`, `specfuse/loop/loop.py`) reads an absent marker
as `0`. Six WUs in this repository were folded under the pre-T01 `cost_usd >
0` guard and carry no marker at all — indistinguishable, under T01's rule,
from "never folded". This module closes that gap by giving every re-armed WU
an explicit marker, without re-running the fold logic T01 owns.

Two shapes, two treatments:

  * **fold-ran** (`cumulative_cost_usd` present) — the fold already moved the
    prior cycle's spend. Stamping `folded_through_re_arm = re_arm_count` is
    the whole fix; `cumulative_*` is read, never written.
  * **fold-never-ran** (`cumulative_cost_usd` absent, `re_arm_history[]`
    populated) — the prior cycle's spend survives only as
    `re_arm_history[].prior_cost_usd` / `prior_duration_seconds`. This module
    folds those two recorded fields into `cumulative_cost_usd` /
    `cumulative_duration_seconds` before stamping the marker, so every
    re-armed WU ends up the same shape (PLAN.md's "converge" decision,
    applied retroactively). No number is invented: only figures already
    present in `re_arm_history` are summed. `prior_input_tokens` /
    `prior_output_tokens` were never recorded on either fold-never-ran WU in
    this repository, so `cumulative_input_tokens` / `cumulative_output_tokens`
    are left unset rather than backfilled from `events.jsonl` — that would be
    a second, undeclared source of truth for the same accumulator.

A WU never re-armed (`re_arm_count` absent or `0`) is untouched: no read,
no write, not even a no-op frontmatter round-trip.

Writes go through `specfuse.loop.loop.write_frontmatter_field`, the same
single-key, no-reflow writer `fold_cumulative_on_rearm` uses — every other
line in the file, marker or not, keeps its original text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import loop as _loop

_COST_TOLERANCE_USD = 0.02


def _int_or_zero(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _classify(fm: dict) -> str:
    """Return "not_rearmed", "fold_ran", or "fold_never_ran"."""
    re_arm_count = fm.get("re_arm_count", 0)
    if not isinstance(re_arm_count, int) or isinstance(re_arm_count, bool) or re_arm_count <= 0:
        return "not_rearmed"
    if "cumulative_cost_usd" in fm:
        return "fold_ran"
    return "fold_never_ran"


def _history_sums(fm: dict) -> tuple[float, float]:
    """Sum `prior_cost_usd` and `prior_duration_seconds` across every
    `re_arm_history` entry. Non-numeric or missing fields contribute 0."""
    history = fm.get("re_arm_history") or []
    cost = 0.0
    duration = 0.0
    if isinstance(history, list):
        for entry in history:
            if not isinstance(entry, dict):
                continue
            pc = entry.get("prior_cost_usd")
            if isinstance(pc, (int, float)) and not isinstance(pc, bool):
                cost += float(pc)
            pd = entry.get("prior_duration_seconds")
            if isinstance(pd, (int, float)) and not isinstance(pd, bool):
                duration += float(pd)
    return cost, duration


def _events_cost_before(
    events_path: Path, wu_id: str, cutoff_iso: str
) -> tuple[float, bool]:
    """Sum `attempt_outcome` `cost_usd` for `wu_id` at or before `cutoff_iso`.

    Returns `(total, seen)`; `seen` is False when the events file is
    missing/unreadable or carries no matching `attempt_outcome` for this WU
    — that means "nothing to cross-check against", not "prior cost was
    zero", so the caller must not treat it as a disagreement. ISO-8601
    timestamps with a fixed-offset suffix compare correctly as strings, so
    this avoids a datetime dependency.
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
        timestamp = event.get("timestamp")
        if not isinstance(timestamp, str) or timestamp > cutoff_iso:
            continue
        seen = True
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        cost = payload.get("cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            total += float(cost)
    return total, seen


@dataclass
class CensusResult:
    fold_ran: list[Path] = field(default_factory=list)
    fold_never_ran: list[Path] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"re-armed WUs: fold ran = {len(self.fold_ran)}"
            f"    fold never ran = {len(self.fold_never_ran)}"
        )


def census(root: Path) -> CensusResult:
    """Classify every re-armed WU under `root` by fold shape.

    `root` is a directory searched recursively for `WU-*.md` files (the
    repository's `.specfuse/features/` tree, or a fixture directory in
    tests).
    """
    result = CensusResult()
    for wu_path in sorted(Path(root).glob("**/WU-*.md")):
        fm, _ = _loop.read_frontmatter(wu_path)
        shape = _classify(fm)
        if shape == "fold_ran":
            result.fold_ran.append(wu_path)
        elif shape == "fold_never_ran":
            result.fold_never_ran.append(wu_path)
    return result


class PriorCostDisagreement(RuntimeError):
    """Raised when a fold-never-ran WU's recorded prior cost disagrees with
    its own `events.jsonl` total by more than a rounding tolerance."""


@dataclass
class MigrationOutcome:
    path: Path
    action: str  # "not_rearmed" | "fold_ran_stamped" | "fold_never_ran_migrated" | "already_migrated"


def migrate_file(wu_path: Path, *, events_path: Path | None = None) -> MigrationOutcome:
    """Migrate one WU file in place. Idempotent: a second call for an
    already-migrated file is a no-op read, no writes.

    `events_path` defaults to `events.jsonl` next to `wu_path` (the feature
    folder layout `correlation-ids.md` documents); pass explicitly for a
    fixture that does not follow that layout.
    """
    wu_path = Path(wu_path)
    fm, _ = _loop.read_frontmatter(wu_path)
    shape = _classify(fm)

    if shape == "not_rearmed":
        return MigrationOutcome(wu_path, "not_rearmed")

    re_arm_count = _int_or_zero(fm.get("re_arm_count", 0))
    folded_through = fm.get("folded_through_re_arm", 0)
    if not isinstance(folded_through, int) or isinstance(folded_through, bool):
        folded_through = 0

    if shape == "fold_ran":
        if folded_through == re_arm_count:
            return MigrationOutcome(wu_path, "already_migrated")
        _loop.write_frontmatter_field(wu_path, "folded_through_re_arm", re_arm_count)
        return MigrationOutcome(wu_path, "fold_ran_stamped")

    # fold_never_ran
    if folded_through == re_arm_count and "cumulative_cost_usd" in fm:
        return MigrationOutcome(wu_path, "already_migrated")

    prior_cost, prior_duration = _history_sums(fm)

    wu_id = fm.get("id")
    history = fm.get("re_arm_history") or []
    last_entry_ts = None
    if isinstance(history, list):
        for entry in history:
            if isinstance(entry, dict) and isinstance(entry.get("timestamp"), str):
                last_entry_ts = entry["timestamp"]
    if isinstance(wu_id, str) and wu_id and last_entry_ts:
        resolved_events_path = events_path or (wu_path.parent / "events.jsonl")
        events_total, seen = _events_cost_before(
            resolved_events_path, wu_id, last_entry_ts
        )
        if seen and abs(events_total - prior_cost) > _COST_TOLERANCE_USD:
            raise PriorCostDisagreement(
                f"{wu_path}: re_arm_history prior_cost_usd sums to "
                f"{prior_cost:.6f} but events.jsonl attempt_outcome total "
                f"through {last_entry_ts} is {events_total:.6f} "
                f"(tolerance {_COST_TOLERANCE_USD})"
            )

    _loop.write_frontmatter_field(
        wu_path, "cumulative_cost_usd", round(prior_cost, 6)
    )
    _loop.write_frontmatter_field(
        wu_path, "cumulative_duration_seconds", round(prior_duration, 3)
    )
    _loop.write_frontmatter_field(wu_path, "folded_through_re_arm", re_arm_count)
    return MigrationOutcome(wu_path, "fold_never_ran_migrated")


def migrate_repo(root: Path) -> list[MigrationOutcome]:
    """Migrate every `WU-*.md` file under `root`. Returns one outcome per
    file that was inspected (including untouched `not_rearmed` files, so
    callers can audit that nothing else was written)."""
    return [migrate_file(wu_path) for wu_path in sorted(Path(root).glob("**/WU-*.md"))]
