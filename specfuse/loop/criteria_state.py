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
from dataclasses import dataclass, field
from pathlib import Path
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
    "carried_from_attempt": re.compile(
        r"^- \*\*carried_from_attempt:\*\*\s*`?([^`\n]+)`?", re.MULTILINE
    ),
    "covers": re.compile(r"^- \*\*covers:\*\*\s*(.+)$", re.MULTILINE),
    "invalidated_by": re.compile(r"^- \*\*invalidated_by:\*\*\s*(.+)$", re.MULTILINE),
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
    #: Set by `reset_stale_criteria_entries` when a re-arm carries this
    #: entry's narrow green past the attempt cycle that proved it — the
    #: attempt number it was carried FROM, not the current attempt.
    carried_from_attempt: Optional[str] = None
    #: Paths this criterion's proof depends on — its producing WU's
    #: `produces:` plus its oracle's test file, when derivable
    #: (`derive_criterion_covers`, FEAT-2026-0117/T02). Empty when never
    #: seeded with a `- **covers:**` line: an entry the skeleton step hasn't
    #: backfilled yet, or one predating this field.
    covers: list = field(default_factory=list)
    #: Set by `invalidate_carried_entries` when a re-close's gate diff
    #: touches a path this (formerly carried) entry `covers` — names that
    #: path, not the whole diff.
    invalidated_by: Optional[str] = None


#: Matches `GATE-NN-CRITERIA.md` basenames (any `NN`), and nothing else —
#: not `GATE-NN.md`, not `GATE-NN-REVIEW.md`, not `RETROSPECTIVE.md`.
CRITERIA_FILENAME_RE = re.compile(r"^GATE-\d+-CRITERIA\.md$")


def criteria_filename(gate_n: int) -> str:
    """The single source of truth for a gate's criteria-artifact basename."""
    return f"GATE-{gate_n:02d}-CRITERIA.md"


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
        covers_raw = _extract_field(block, "covers")
        covers = [c.strip() for c in covers_raw.split(",") if c.strip()] if covers_raw else []
        entries.append(
            CriterionStateEntry(
                criterion_id=criterion_id,
                criterion=_extract_field(block, "criterion"),
                oracle=_extract_field(block, "oracle"),
                kind=_extract_field(block, "kind"),
                state=_extract_field(block, "state"),
                proved_at_sha=_extract_field(block, "proved_at_sha"),
                attempt=_extract_field(block, "attempt"),
                carried_from_attempt=_extract_field(block, "carried_from_attempt"),
                covers=covers,
                invalidated_by=_extract_field(block, "invalidated_by"),
            )
        )
    return entries


def resolve_carry_forward_narrow_greens(cfg: "dict | None") -> bool:
    """Whether a re-armed close carries a `narrow`/`pass` entry's green
    forward past the attempt cycle that proved it (FEAT-2026-0117/T01).

    Reads `verification.yml` `defaults.carry_forward_narrow_greens` — default
    True, same project-default precedence tier as `loop.py`'s other
    `resolve_*` readers. *cfg* is the already-loaded `verification.yml` dict;
    this module does no file I/O of its own.
    """
    if not cfg:
        return True
    return (cfg.get("defaults") or {}).get("carry_forward_narrow_greens", True) is not False


def reset_stale_criteria_entries(
    entries: list[CriterionStateEntry], current_attempt: int, carry_narrow: bool,
) -> list[CriterionStateEntry]:
    """Reset entries left behind by a superseded attempt cycle (#3279).

    An entry whose recorded `attempt` exceeds *current_attempt* was measured
    in a cycle a re-arm has since superseded. With *carry_narrow* true, an
    entry that is also `kind: narrow` and `state: pass` is provably safe to
    keep — its oracle's scope was knowable, so a re-arm does not invalidate
    what it proved — and keeps every field, gaining `carried_from_attempt`
    set to the attempt it was proved on. Every other stale entry resets to
    `unverified` with its per-attempt fields cleared, exactly as if it had
    never been verified. Entries at or below the current attempt, and
    entries with no recorded attempt, are returned unchanged.
    """
    refreshed: list[CriterionStateEntry] = []
    for entry in entries:
        recorded = entry.attempt
        try:
            is_stale = recorded is not None and int(str(recorded).strip()) > current_attempt
        except (TypeError, ValueError):
            is_stale = False       # unparseable attempt: leave it for the close
        if is_stale:
            if carry_narrow and entry.kind == "narrow" and entry.state == "pass":
                entry = CriterionStateEntry(
                    criterion_id=entry.criterion_id,
                    criterion=entry.criterion,
                    oracle=entry.oracle,
                    kind=entry.kind,
                    state=entry.state,
                    proved_at_sha=entry.proved_at_sha,
                    attempt=entry.attempt,
                    carried_from_attempt=str(recorded).strip(),
                )
            else:
                entry = CriterionStateEntry(
                    criterion_id=entry.criterion_id,
                    criterion=entry.criterion,
                    oracle=None,
                    kind=None,
                    state="unverified",
                    proved_at_sha=None,
                    attempt=None,
                    carried_from_attempt=None,
                )
        refreshed.append(entry)
    return refreshed


@dataclass(frozen=True)
class ReverificationWorklist:
    """Partition of a gate's recorded entries for a re-dispatched close attempt.

    `carry_forward` entries are provably safe to skip re-verifying this
    attempt; `reverify` entries must re-run their oracle. `oracle_groups`
    collapses byte-identical oracle commands among `reverify` entries so each
    runs once per attempt rather than once per criterion.
    """

    carry_forward: list[CriterionStateEntry]
    reverify: list[CriterionStateEntry]
    oracle_groups: list[tuple[str, list[str]]]


def build_reverification_worklist(
    entries: list[CriterionStateEntry], current_attempt: str
) -> ReverificationWorklist:
    """Partition recorded entries into what a re-close may carry vs. re-verify.

    An entry carries forward only when it is provably safe: `kind ==
    "narrow"`, `state == "pass"`, a non-empty `oracle`, and a non-empty
    `attempt`. Everything else — a missing or unrecognized `kind`, `state:
    fail` or `state: unverified`, and every `broad` entry regardless of
    state — goes to `reverify`. Fail-safe default: unclassifiable entries
    land in `reverify`, never in `carry_forward`.

    `covers` plays no part in this partition — a `carried_from_attempt`
    entry with an empty `covers` is kept out of `carry_forward` by
    `loop.invalidate_carried_entries` resetting it to `unverified` before
    this runs (FEAT-2026-0117/T02), not by a check here.
    """
    carry_forward: list[CriterionStateEntry] = []
    reverify: list[CriterionStateEntry] = []
    for entry in entries:
        if (
            entry.kind == "narrow"
            and entry.state == "pass"
            and entry.oracle
            and entry.attempt
        ):
            carry_forward.append(entry)
        else:
            reverify.append(entry)

    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for entry in reverify:
        if not entry.oracle:
            continue
        if entry.oracle not in groups:
            groups[entry.oracle] = []
            order.append(entry.oracle)
        groups[entry.oracle].append(entry.criterion_id)
    oracle_groups = [(oracle, groups[oracle]) for oracle in order]

    return ReverificationWorklist(
        carry_forward=carry_forward,
        reverify=reverify,
        oracle_groups=oracle_groups,
    )


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
        if entry.carried_from_attempt is not None:
            lines.append(f"- **carried_from_attempt:** `{entry.carried_from_attempt}`")
        if entry.covers:
            lines.append(f"- **covers:** {', '.join(entry.covers)}")
        if entry.invalidated_by is not None:
            lines.append(f"- **invalidated_by:** {entry.invalidated_by}")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)


_UNITTEST_ORACLE_RE = re.compile(r"-m\s+unittest\s+([\w.]+)")
_MAVEN_DTEST_RE = re.compile(r"-Dtest=([A-Za-z_][A-Za-z0-9_]*)")


def _unittest_module_path(oracle_command: str) -> "Optional[str]":
    """`tests.foo_bar[.TestX.test_y]` -> `tests/foo_bar.py`, the file the
    unittest oracle actually runs regardless of which class/method suffix it
    names. Tries the longest dotted prefix that exists on disk first, so a
    package (`tests/foo_bar/__init__` style) is not required; falls back to
    the full dotted-to-slash mapping when nothing on disk matches yet."""
    m = _UNITTEST_ORACLE_RE.search(oracle_command)
    if not m:
        return None
    parts = m.group(1).split(".")
    for i in range(len(parts), 0, -1):
        candidate = "/".join(parts[:i]) + ".py"
        if Path(candidate).is_file():
            return candidate
    return "/".join(parts) + ".py"


def _maven_test_class_path(oracle_command: str) -> "Optional[str]":
    """`-Dtest=FooBarTest` -> its `src/test/**/FooBarTest.java`, only when
    one actually exists — unlike the unittest case, a Maven class name gives
    no reliable package-to-path mapping without a filesystem lookup."""
    m = _MAVEN_DTEST_RE.search(oracle_command)
    if not m:
        return None
    root = Path("src/test")
    if not root.is_dir():
        return None
    matches = sorted(root.rglob(f"{m.group(1)}.java"))
    return str(matches[0]) if matches else None


def derive_criterion_covers(wu, oracle_command: "Optional[str]") -> list:
    """Paths a criterion's proof depends on (FEAT-2026-0117/T02): its
    producing WU's `produces:` plus the test file its oracle command names,
    when derivable. Feeds a seeded entry's `- **covers:**` line so a re-close
    can tell whether a later diff touched what a carried green actually
    measured — see `invalidate_carried_entries` in `loop.py`.

    *wu* is anything with a `.produces` list (a `WorkUnit`, or a duck-typed
    stand-in built from a WU read off disk); *oracle_command* is the entry's
    recorded `oracle`, or `None` before a close has run it.
    """
    covers = list(getattr(wu, "produces", None) or [])
    if oracle_command:
        test_path = _unittest_module_path(oracle_command) or _maven_test_class_path(oracle_command)
        if test_path and test_path not in covers:
            covers.append(test_path)
    return covers
