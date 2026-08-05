#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Per-criterion close state — schema, parser, renderer (FEAT-2026-0056/T01).

Defines the entry shape for `GATE-NN-CRITERIA.md`, the per-gate artifact that
lets a close remember, per acceptance criterion, which oracle proved it, that
oracle's exit code, and the tree state it ran against. Follows the shape of
`closing_requirements.py`'s hedged-verdict follow-up record: a per-entry
classified record living inside a markdown artifact, regex-parsed, with the
classification written by the close that ran the oracle and never inferred by
a reader.

Data and parsing only — no file I/O, no driver wiring, no skip policy. See
FEAT-2026-0056/PLAN.md and GATE-01.md for the design this module encodes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

#: An oracle's scope classification. `narrow` oracles (a scoped test nodeid,
#: a symbol-existence import, a structural assert, a countable grep) survive
#: a re-close; `broad` oracles (the full suite, a full regen, a scenario
#: matrix) re-run unconditionally on every close attempt.
ORACLE_KINDS: frozenset = frozenset({"narrow", "broad"})

#: A criterion's recorded verification outcome for a given close attempt.
CRITERION_STATES: frozenset = frozenset({"pass", "fail", "unverified"})

_ENTRY_HEADING_RE = re.compile(r"^### (\S+)\s*$", re.MULTILINE)

_FIELD_PATTERNS = {
    "criterion": re.compile(r"^- \*\*criterion:\*\*\s*(.+)$", re.MULTILINE),
    "oracle": re.compile(r"^- \*\*oracle:\*\*\s*(.+)$", re.MULTILINE),
    "kind": re.compile(r"^- \*\*kind:\*\*\s*`([^`]+)`", re.MULTILINE),
    "state": re.compile(r"^- \*\*state:\*\*\s*`([^`]+)`", re.MULTILINE),
    "proved_at_sha": re.compile(r"^- \*\*proved_at_sha:\*\*\s*`([^`]+)`", re.MULTILINE),
    "attempt": re.compile(r"^- \*\*attempt:\*\*\s*`?([^`\n]+)`?", re.MULTILINE),
}


@dataclass(frozen=True)
class CriterionStateEntry:
    """One `### <criterion_id>` block in a `GATE-NN-CRITERIA.md` artifact."""

    criterion_id: str
    criterion: Optional[str]
    oracle: Optional[str]
    kind: Optional[str]
    state: Optional[str]
    proved_at_sha: Optional[str]
    attempt: Optional[str]


def criterion_id_for(wu_sub_id: str, ordinal: int) -> str:
    """Stable criterion identity: producing WU's sub-ID + 1-based ordinal.

    Ordinal, not a hash of the criterion text — a criterion whose wording is
    edited between attempts is still the same criterion, and a hash would
    silently orphan its recorded state.
    """
    return f"{wu_sub_id}#{ordinal}"


def _extract_field(block: str, name: str) -> Optional[str]:
    m = _FIELD_PATTERNS[name].search(block)
    if not m:
        return None
    return m.group(1).strip()


def parse_criteria_state(text: str) -> list[CriterionStateEntry]:
    """Parse a `GATE-NN-CRITERIA.md` artifact into entries, in document order.

    A block missing a field yields that field as `None` rather than raising —
    the artifact is written incrementally across attempts, so a partially
    populated block is a normal, not exceptional, state.
    """
    headings = list(_ENTRY_HEADING_RE.finditer(text))
    entries: list[CriterionStateEntry] = []
    for i, m in enumerate(headings):
        criterion_id = m.group(1)
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[start:end]
        entries.append(
            CriterionStateEntry(
                criterion_id=criterion_id,
                criterion=_extract_field(block, "criterion"),
                oracle=_extract_field(block, "oracle"),
                kind=_extract_field(block, "kind"),
                state=_extract_field(block, "state"),
                proved_at_sha=_extract_field(block, "proved_at_sha"),
                attempt=_extract_field(block, "attempt"),
            )
        )
    return entries


def render_criteria_state(entries: list[CriterionStateEntry]) -> str:
    """Render entries back into `GATE-NN-CRITERIA.md` markdown.

    Round-trips through `parse_criteria_state` — a missing field is simply
    omitted from its block rather than rendered as a literal `None`.
    """
    blocks = []
    for entry in entries:
        lines = [f"### {entry.criterion_id}", ""]
        if entry.criterion is not None:
            lines.append(f"- **criterion:** {entry.criterion}")
        if entry.oracle is not None:
            lines.append(f"- **oracle:** {entry.oracle}")
        if entry.kind is not None:
            lines.append(f"- **kind:** `{entry.kind}`")
        if entry.state is not None:
            lines.append(f"- **state:** `{entry.state}`")
        if entry.proved_at_sha is not None:
            lines.append(f"- **proved_at_sha:** `{entry.proved_at_sha}`")
        if entry.attempt is not None:
            lines.append(f"- **attempt:** `{entry.attempt}`")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)
