#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Pure, side-effect-scoped arm transaction — the write set behind a one-commit arm.

Mirrors the `arm_eval.py` (T03) split: computation lives in a pure module
with its own tests, driver wiring is a separate unit (T06). This module
performs NO git operations at all, not even tag creation — it returns the
tag name as a string; T06 creates the tag and owns the commit.

An arm consists of exactly these writes: every gate-`N+1` work-unit file
currently `status: draft` flips to `pending`, and the just-closed gate `N`'s
file flips `awaiting_review` -> `passed`. `events.jsonl` is part of the same
write set but is appended by the caller, not this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import _miniyaml
from .plan_baseline import load_plan_graph

_FM_DELIM = re.compile(r"^---\s*$")


def arm_tag_name(feature_id: str, gate: int) -> str:
    """Return the pre-arm revert tag name for `feature_id`'s gate `gate`."""
    return f"pre-arm/{feature_id}/gate-{gate}"


@dataclass(frozen=True)
class ArmTransaction:
    feature_id: str
    just_closed_gate: int
    draft_wu_paths: tuple
    gate_file_path: "Path | None"
    tag_name: str
    paths: tuple


def _read_frontmatter(path: Path) -> dict:
    lines = path.read_text().splitlines()
    if not lines or not _FM_DELIM.match(lines[0]):
        return {}
    j = 1
    while j < len(lines) and not _FM_DELIM.match(lines[j]):
        j += 1
    return _miniyaml.parse("\n".join(lines[1:j])) or {}


def plan_arm_transaction(feature_dir: Path, just_closed_gate: int) -> ArmTransaction:
    """Compute the complete write set for arming the gate after `just_closed_gate`.

    Reads the plan graph and the current on-disk status of every gate-`N+1`
    WU and the gate-`N` file; performs no writes.
    """
    feature_dir = Path(feature_dir)
    plan_fm = _read_frontmatter(feature_dir / "PLAN.md")
    feature_id = plan_fm.get("feature_id", feature_dir.name)

    plan = load_plan_graph(feature_dir)
    gates = plan.get("gates", []) or []

    next_gate_num = just_closed_gate + 1
    next_gate = next((g for g in gates if g.get("gate") == next_gate_num), None)

    draft_wu_paths = []
    if next_gate is not None:
        for ref in next_gate.get("work_units", []) or []:
            wu_path = feature_dir / ref["file"]
            if not wu_path.exists():
                continue
            fm = _read_frontmatter(wu_path)
            if fm.get("status") == "draft":
                draft_wu_paths.append(wu_path)

    # An empty arm (zero drafted WUs at gate N+1) must never produce a
    # commit — so the gate-N flip only enters the write set alongside at
    # least one drafted WU, never on its own.
    gate_file_path = None
    paths = list(draft_wu_paths)
    if draft_wu_paths:
        closed_gate = next((g for g in gates if g.get("gate") == just_closed_gate), None)
        candidate = feature_dir / closed_gate["file"] if closed_gate else None
        if candidate is not None and candidate.exists():
            gate_fm = _read_frontmatter(candidate)
            if gate_fm.get("status") == "awaiting_review":
                gate_file_path = candidate
                paths.append(gate_file_path)

    seen = set()
    deduped_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            deduped_paths.append(p)

    return ArmTransaction(
        feature_id=feature_id,
        just_closed_gate=just_closed_gate,
        draft_wu_paths=tuple(draft_wu_paths),
        gate_file_path=gate_file_path,
        tag_name=arm_tag_name(feature_id, just_closed_gate),
        paths=tuple(deduped_paths),
    )


def _flip_status_field(path: Path, new_status: str) -> None:
    """Replace the `status:` line in `path`'s frontmatter, leaving everything else untouched."""
    lines = path.read_text().splitlines()
    j = 1
    while j < len(lines) and not _FM_DELIM.match(lines[j]):
        j += 1
    block = lines[1:j]
    status_re = re.compile(r"^status:")
    for idx, line in enumerate(block):
        if status_re.match(line):
            block[idx] = f"status: {new_status}"
            break
    else:
        block.append(f"status: {new_status}")
    new_lines = ["---", *block, "---", *lines[j + 1:]]
    path.write_text("\n".join(new_lines) + "\n")


def apply_arm_transaction(txn: ArmTransaction) -> list:
    """Apply `txn`'s writes to disk. Idempotent: re-applying an already-armed
    transaction writes nothing and returns an empty list.

    Draft WUs are re-read from disk at apply time (not trusted from `txn`)
    so a second call against already-flipped files is a true no-op.
    """
    applied = []
    for wu_path in txn.draft_wu_paths:
        fm = _read_frontmatter(wu_path)
        if fm.get("status") != "draft":
            continue
        _flip_status_field(wu_path, "pending")
        applied.append(wu_path)

    if txn.gate_file_path is not None:
        fm = _read_frontmatter(txn.gate_file_path)
        if fm.get("status") == "awaiting_review":
            _flip_status_field(txn.gate_file_path, "passed")
            applied.append(txn.gate_file_path)

    return applied
