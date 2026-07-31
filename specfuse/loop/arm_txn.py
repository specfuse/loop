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
from .closing_requirements import gate_review_filename
from .plan_baseline import load_plan_graph

_FM_DELIM = re.compile(r"^---\s*$")

FEATURE_REVIEW_FILENAME = "FEATURE-REVIEW.md"

_DOUBT_HEADING_RE = re.compile(r"(?m)^## Doubt\s*$")
_NEXT_H2_RE = re.compile(r"(?m)^## ")


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
    feature_review_path: "Path | None" = None
    arm_payload: "dict | None" = None
    arm_timestamp: "str | None" = None


def _read_frontmatter(path: Path) -> dict:
    lines = path.read_text().splitlines()
    if not lines or not _FM_DELIM.match(lines[0]):
        return {}
    j = 1
    while j < len(lines) and not _FM_DELIM.match(lines[j]):
        j += 1
    return _miniyaml.parse("\n".join(lines[1:j])) or {}


def plan_arm_transaction(
    feature_dir: Path,
    just_closed_gate: int,
    arm_payload: "dict | None" = None,
    timestamp: "str | None" = None,
) -> ArmTransaction:
    """Compute the complete write set for arming the gate after `just_closed_gate`.

    Reads the plan graph and the current on-disk status of every gate-`N+1`
    WU and the gate-`N` file; performs no writes.

    `arm_payload` and `timestamp` are the caller's precomputed arm-predicate
    verdict (FEAT-2026-0053/T04's shadow-evaluation payload) and the arm's
    wall-clock timestamp. When both are given and the arm is non-empty (at
    least one drafted WU), `FEATURE-REVIEW.md` joins `paths` so its append
    lands in the same commit as the status flips (WU-08). Callers that don't
    pass them get the T05 write set unchanged — a `review`/`supervised`
    feature never calls this with them set, so it never gets a
    `FEATURE-REVIEW.md` at all.
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

    feature_review_path = None
    if draft_wu_paths and arm_payload is not None and timestamp is not None:
        feature_review_path = feature_dir / FEATURE_REVIEW_FILENAME
        paths.append(feature_review_path)

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
        feature_review_path=feature_review_path,
        arm_payload=arm_payload,
        arm_timestamp=timestamp,
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


def _extract_doubt_section(body: str) -> "str | None":
    """Return the verbatim `## Doubt` section (heading through the next `## `
    heading or EOF), or None when no such section exists."""
    m = _DOUBT_HEADING_RE.search(body)
    if m is None:
        return None
    nl = body.find("\n", m.end())
    tail_start = nl + 1 if nl != -1 else len(body)
    nxt = _NEXT_H2_RE.search(body, tail_start)
    end = nxt.start() if nxt else len(body)
    return body[m.start():end].rstrip("\n") + "\n"


def _read_gate_review(review_path: Path) -> "tuple[list, str | None]":
    """Best-effort read of a `GATE-{N}-REVIEW.md`: its frontmatter
    `open_questions` list and the verbatim `## Doubt` section text.

    Never raises — a missing file, unparseable frontmatter, or an absent
    section all degrade to recorded absence (empty list / None) rather than
    an arm-crashing exception (WU-08 AC7).
    """
    if not review_path.exists():
        return [], None
    text = review_path.read_text()
    lines = text.splitlines()
    open_questions: list = []
    body = text
    if lines and _FM_DELIM.match(lines[0]):
        j = 1
        while j < len(lines) and not _FM_DELIM.match(lines[j]):
            j += 1
        try:
            fm = _miniyaml.parse("\n".join(lines[1:j])) or {}
        except _miniyaml.MiniYAMLError:
            fm = {}
        open_questions = fm.get("open_questions") or []
        body = "\n".join(lines[j + 1:])
    return open_questions, _extract_doubt_section(body)


def _render_verdict_line(arm_payload: dict) -> str:
    lines = [f"would_arm: {arm_payload.get('would_arm')}"]
    for name, v in (arm_payload.get("classes") or {}).items():
        lines.append(f"- {name}: {v.get('status')} — {v.get('reason')}")
    return "\n".join(lines)


def append_feature_review_entry(
    feature_dir: Path,
    just_closed_gate: int,
    arm_payload: dict,
    timestamp: str,
) -> Path:
    """Append one section for `just_closed_gate` to `FEATURE-REVIEW.md`,
    sourced from `GATE-{just_closed_gate + 1}-REVIEW.md`. Append-only: an
    existing file's prior sections are never rewritten or reordered. Returns
    the path written.
    """
    feature_dir = Path(feature_dir)
    review_path = feature_dir / gate_review_filename(just_closed_gate + 1)
    open_questions, doubt = _read_gate_review(review_path)

    oq_text = (
        "\n".join(f"- {q}" for q in open_questions) if open_questions else "(none)"
    )
    doubt_text = doubt if doubt is not None else "(no `## Doubt` section found)"
    verdict_text = _render_verdict_line(arm_payload)

    section = (
        f"## Gate {just_closed_gate} — armed {timestamp}\n\n"
        f"**Open questions:**\n\n{oq_text}\n\n"
        f"{doubt_text}\n"
        f"**Arm verdict:**\n\n{verdict_text}\n"
    )

    path = feature_dir / FEATURE_REVIEW_FILENAME
    existing = path.read_text() if path.exists() else ""
    sep = "\n" if existing else ""
    path.write_text(existing + sep + section)
    return path


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

    # Gated on `applied` (this call's actual flips), not on
    # `txn.feature_review_path` alone: a replay against already-flipped
    # files performs zero flips above, so this stays a true no-op too —
    # the same idempotency contract as the flips it rides alongside.
    if txn.feature_review_path is not None and applied:
        append_feature_review_entry(
            txn.feature_review_path.parent,
            txn.just_closed_gate,
            txn.arm_payload,
            txn.arm_timestamp,
        )
        applied.append(txn.feature_review_path)

    return applied
