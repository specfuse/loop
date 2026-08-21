#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`DECISIONS.md` format — schema, parser (FEAT-2026-0058/T01).

Defines the entry shape for a feature's `DECISIONS.md`: one registry, cited by
ID from other artifacts instead of restated. Replaces the incumbent
`## Decisions taken at draft time` prose section (present in 6 of this
repository's PLAN.md files at draft time).

Each entry carries an id, statement, owner, a `status` drawn from a closed
set (`STATUS_VALUES`), and a `provenance` link to where the decision was
taken. A decision that reached `ratified` via an override additionally
carries `overridden_from`, `signed_off_by`, and `signed_off_at` — so it stays
distinguishable from one ratified from the start (`[FEAT-2026-0070/G1-CLOSE-
INTERMEDIATE]`).

Data and parsing only — no file I/O, no lint wiring (T02/T03 own the lint
that reads this). See FEAT-2026-0058/PLAN.md and WU-01 for the design this
module encodes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

#: A decision's lifecycle status — the closed set `status` must be a member
#: of. `proposed`: stated, not yet ratified. `ratified`: the decision stands,
#: whether or not it was ever overridden (see `overridden_from`).
#: `overridden-pending-signoff`: a human or later decision has overridden the
#: original statement, awaiting a named sign-off before it can move back to
#: `ratified`. `rejected`: considered and not taken. `superseded`: replaced
#: outright by a later decision (see the superseding decision's provenance).
STATUS_VALUES: frozenset = frozenset(
    {"proposed", "ratified", "overridden-pending-signoff", "rejected", "superseded"}
)

#: Fields required on every entry regardless of status.
_REQUIRED_FIELDS = ("statement", "owner", "status", "provenance")

#: Fields required in addition once an entry carries override provenance —
#: either because its status is `overridden-pending-signoff`, or because it
#: reached `ratified` (or any other status) by way of a prior override.
_OVERRIDE_FIELDS = ("overridden_from", "signed_off_by", "signed_off_at")

_ENTRY_HEADING_RE = re.compile(r"^### (\S+)\s*$", re.MULTILINE)

_FIELD_PATTERNS = {
    "statement": re.compile(r"^- \*\*statement:\*\*\s*(.+)$", re.MULTILINE),
    "owner": re.compile(r"^- \*\*owner:\*\*\s*(.+)$", re.MULTILINE),
    "status": re.compile(r"^- \*\*status:\*\*\s*`([^`]+)`", re.MULTILINE),
    "provenance": re.compile(r"^- \*\*provenance:\*\*\s*(.+)$", re.MULTILINE),
    "overridden_from": re.compile(r"^- \*\*overridden_from:\*\*\s*`([^`]+)`", re.MULTILINE),
    "signed_off_by": re.compile(r"^- \*\*signed_off_by:\*\*\s*(.+)$", re.MULTILINE),
    "signed_off_at": re.compile(r"^- \*\*signed_off_at:\*\*\s*(.+)$", re.MULTILINE),
}


@dataclass(frozen=True)
class DecisionEntry:
    """One `### <decision_id>` block in a `DECISIONS.md` registry."""

    decision_id: str
    statement: Optional[str]
    owner: Optional[str]
    status: Optional[str]
    provenance: Optional[str]
    overridden_from: Optional[str] = None
    signed_off_by: Optional[str] = None
    signed_off_at: Optional[str] = None

    def was_overridden(self) -> bool:
        """True if this entry carries any override provenance."""
        return self.overridden_from is not None


@dataclass(frozen=True)
class DecisionParseError:
    """One malformed entry — reported, never silently dropped."""

    decision_id: str
    reason: str


@dataclass(frozen=True)
class ParseResult:
    """Parse outcome: well-formed entries, and errors for the rest."""

    entries: list
    errors: list

    def ok(self) -> bool:
        return not self.errors


def _extract_field(block: str, name: str) -> Optional[str]:
    m = _FIELD_PATTERNS[name].search(block)
    if not m:
        return None
    return m.group(1).strip()


def parse_decisions(text: str) -> ParseResult:
    """Parse a `DECISIONS.md` registry into entries, in document order.

    A malformed entry — a required field missing, a `status` outside
    `STATUS_VALUES`, or override provenance partially populated — is
    collected into `ParseResult.errors` and excluded from `.entries`; it is
    never silently dropped without a trace.
    """
    headings = list(_ENTRY_HEADING_RE.finditer(text))
    entries: list = []
    errors: list = []
    for i, m in enumerate(headings):
        decision_id = m.group(1)
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[start:end]

        fields = {name: _extract_field(block, name) for name in _FIELD_PATTERNS}

        missing = [name for name in _REQUIRED_FIELDS if not fields[name]]
        if missing:
            errors.append(
                DecisionParseError(
                    decision_id=decision_id,
                    reason=f"missing required field(s): {', '.join(missing)}",
                )
            )
            continue

        if fields["status"] not in STATUS_VALUES:
            errors.append(
                DecisionParseError(
                    decision_id=decision_id,
                    reason=f"status {fields['status']!r} is not in STATUS_VALUES",
                )
            )
            continue

        override_present = [name for name in _OVERRIDE_FIELDS if fields[name]]
        override_required = (
            fields["status"] == "overridden-pending-signoff" or override_present
        )
        if override_required:
            override_missing = [name for name in _OVERRIDE_FIELDS if not fields[name]]
            if override_missing:
                errors.append(
                    DecisionParseError(
                        decision_id=decision_id,
                        reason=(
                            "override provenance incomplete, missing: "
                            + ", ".join(override_missing)
                        ),
                    )
                )
                continue

        entries.append(
            DecisionEntry(
                decision_id=decision_id,
                statement=fields["statement"],
                owner=fields["owner"],
                status=fields["status"],
                provenance=fields["provenance"],
                overridden_from=fields["overridden_from"],
                signed_off_by=fields["signed_off_by"],
                signed_off_at=fields["signed_off_at"],
            )
        )

    return ParseResult(entries=entries, errors=errors)


def ratified_after_override(entry: DecisionEntry) -> bool:
    """True iff `entry` reached `ratified` by way of a prior override.

    The query `[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]` records as lost when
    provenance is not carried: this distinguishes an entry ratified from the
    start (`status == "ratified"`, `overridden_from is None`) from one
    overridden then signed off (`status == "ratified"`, `overridden_from`
    set).
    """
    return entry.status == "ratified" and entry.was_overridden()
