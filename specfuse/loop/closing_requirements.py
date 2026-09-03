#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Closing-ceremony requirement registry (FEAT-2026-0054/T01).

One machine-readable home for every closing-artifact requirement that the
post-squash guards in ``specfuse/loop/loop.py`` enforce for ``close``,
``close-intermediate``, and ``plan-next`` work units. The guards import the
constants and helpers below instead of spelling headings, filenames, and
verdict values inline, so a later lint mode and skeleton writer can read
``CLOSING_REQUIREMENTS`` and stay in lockstep with what the guards actually
check — durable rule FEAT-2026-0070/G1-CLOSE-INTERMEDIATE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# --------------------------------------------------------------------------- #
# Shared literal values — the single spelling every guard body imports        #
# --------------------------------------------------------------------------- #

#: The verdict a close may record. Binary since FEAT-2026-0085: across 273
#: features, 48% of verdict-bearing closes hedged, and 59 of those were later
#: flipped to `met` with nothing re-run. What a hedge used to carry now has
#: three honest channels instead — a `not_met` close with a tracked follow-up
#: per failed criterion, a `human` work unit for a step a human must perform,
#: and an auto-close stub that states what the gates proved.
VERDICT_VALUES = frozenset({"met", "not_met"})

#: The two values FEAT-2026-0085 retired. They stay *readable*: 42 closes are
#: `status: done` carrying one, and `load_wu` / `recheck_terminal_verdict`
#: must parse them rather than crash. They are not *writable* —
#: `assert_verdict_well_formed` rejects them on a close dispatched now, and
#: `VERDICT_VALUES` deliberately does not contain them, so no guard that reads
#: the legal set can accept one by accident.
LEGACY_VERDICT_VALUES = frozenset({"met_locally", "partially_met"})

#: Where an operator holding a standing hedged close goes. Named in every
#: refusal that reports a legacy value, because "not in VERDICT_VALUES" alone
#: tells them what is wrong and nothing about what to do.
VERDICT_MIGRATION_NOTE = "docs/methodology.md § Migrating a hedged close"

RETROSPECTIVE_FILENAME = "RETROSPECTIVE.md"

#: Where a `not_met` close records one tracked follow-up per failed criterion.
#: Named here — the single-spelling home every guard imports — so the artifact
#: and the messages that point at it cannot drift apart. FEAT-2026-0085/T03
#: creates the artifact and the requirement that a `not_met` close carry it.
FOLLOW_UPS_FILENAME = "FOLLOW-UPS.md"
FOLLOW_UP_ENTRY_RE = re.compile(r"^### ", re.MULTILINE)

#: `## Post-merge checklist` — the optional PLAN.md section a `met` close
#: files as one `specfuse:post-merge` issue (FEAT-2026-0085/T03).
POST_MERGE_CHECKLIST_HEADING = "Post-merge checklist"
POST_MERGE_CHECKLIST_HEADING_RE = re.compile(
    rf"^##+ {re.escape(POST_MERGE_CHECKLIST_HEADING)}\b.*$", re.MULTILINE,
)

FOLLOW_UP_LABEL = "specfuse:follow-up"
POST_MERGE_LABEL = "specfuse:post-merge"


def parse_followup_entries(text: str) -> list[str]:
    """Split `FOLLOW-UPS.md` into its `### `-headed entry bodies, in order.

    Each returned entry is the exact text a follow-up issue's body carries —
    heading through the next `### ` (or end of file), whitespace-trimmed.
    Text before the first `### ` (a title, an intro line) is discarded.
    """
    matches = list(FOLLOW_UP_ENTRY_RE.finditer(text))
    entries = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries.append(text[m.start():end].strip("\n") + "\n")
    return entries


def find_post_merge_checklist_section(plan_body: str) -> str | None:
    """Body text of PLAN.md's `## Post-merge checklist` section, or None."""
    m = POST_MERGE_CHECKLIST_HEADING_RE.search(plan_body)
    if not m:
        return None
    start = m.end()
    next_heading = re.search(r"^##+\s", plan_body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(plan_body)
    return plan_body[start:end].strip("\n") + "\n"
LEARNINGS_PATH = ".specfuse/LEARNINGS.md"
LEARNINGS_PENDING_FILENAME = "LEARNINGS-pending.md"
ROADMAP_PATH = ".specfuse/roadmap.md"
DOCS_PREFIX = "docs/"
NOTHING_GENERALIZES_PHRASE = "nothing generalizes"

#: The `autonomy_default` value under which `close-i` / `close-intermediate-e`
#: forbid a closing WU from touching `LEARNINGS_PATH` directly.
AUTO_AUTONOMY = "auto"


def learnings_staging_is_required(autonomy_default: str | None) -> bool:
    """True when a closing WU's lessons belong in `LEARNINGS_PENDING_FILENAME`.

    `close-i` / `close-intermediate-e` forbid appending to `LEARNINGS_PATH`
    under `auto`, so the feature-local staging file is where a generalizable
    lesson lands. `close-b` / `close-intermediate-b` read the same predicate,
    which is what keeps the two requirements from contradicting: without it,
    `auto` closes off the append route and leaves the
    `NOTHING_GENERALIZES_PHRASE` note as the only way to satisfy `close-b` —
    forcing a close whose lessons *do* generalize to write a sentence saying
    they do not (#1419).
    """
    return autonomy_default == AUTO_AUTONOMY

COST_ANALYSIS_HEADING = "Cost analysis"
COST_ANALYSIS_HEADING_RE = re.compile(
    r"^##+ " + re.escape(COST_ANALYSIS_HEADING), re.MULTILINE | re.IGNORECASE,
)

FAILURE_CLASS_HEADING = "Failure-class breakdown"
FAILURE_CLASS_HEADING_LEVEL = 3
FAILURE_CLASS_HEADING_MARKDOWN = "#" * FAILURE_CLASS_HEADING_LEVEL + " " + FAILURE_CLASS_HEADING
FAILURE_CLASS_HEADING_RE = re.compile(
    rf"^#{{{FAILURE_CLASS_HEADING_LEVEL}}} {re.escape(FAILURE_CLASS_HEADING)}\b",
    re.MULTILINE,
)
NO_FAILURES_SENTINEL = (
    f"{FAILURE_CLASS_HEADING_MARKDOWN}\n\n(no non-passing attempts in scope)\n"
)

GATE_SECTION_HEADING_LEVELS = "1,3"


def gate_section_heading_re(gate_n: int) -> re.Pattern:
    """Regex matching the `## Gate N` / `### Gate N` retrospective section."""
    return re.compile(
        rf"^#{{{GATE_SECTION_HEADING_LEVELS}}} Gate {gate_n}\b", re.MULTILINE,
    )


GATE_REVIEW_FILENAME_TEMPLATE = "GATE-{next_gate:02d}-REVIEW.md"


def gate_review_filename(next_gate: int) -> str:
    """Filename of the review doc a plan-next WU must draft for the next gate."""
    return GATE_REVIEW_FILENAME_TEMPLATE.format(next_gate=next_gate)


# --------------------------------------------------------------------------- #
# §3 contract-change enumeration -> CHANGELOG.md linkage (FEAT-2026-0064/T02) #
# --------------------------------------------------------------------------- #

#: `close-discipline.md` §3's heading, formalized so it is machine-findable —
#: matches the `## ` or `### ` level already in use across existing closes.
CONSUMER_VISIBLE_HEADING = "Consumer-visible contract changes"
CONSUMER_VISIBLE_HEADING_RE = re.compile(
    rf"^#{{2,3}} {re.escape(CONSUMER_VISIBLE_HEADING)}\b.*$", re.MULTILINE,
)

#: §3's required exact line when a feature makes no consumer-visible change.
#: Matched by substring, case-insensitively, so an em-dash/hyphen variant
#: still counts — the words are the contract, not the punctuation.
CONSUMER_VISIBLE_NA_PHRASE = "n/a — no consumer-visible contract change"

CHANGELOG_PATH = "CHANGELOG.md"


def find_consumer_visible_section(retrospective_text: str) -> str | None:
    """Body text of the §3 section, or None if the heading is absent.

    A missing heading is out of this check's scope — enforcing that §3 was
    *written at all* is a separate, larger surface than the one this feature
    builds: linking an enumeration that already exists to `CHANGELOG.md`.
    """
    m = CONSUMER_VISIBLE_HEADING_RE.search(retrospective_text)
    if not m:
        return None
    start = m.end()
    next_heading = re.search(r"^##+\s", retrospective_text[start:], re.MULTILINE)
    if next_heading:
        return retrospective_text[start:start + next_heading.start()]
    return retrospective_text[start:]


def consumer_visible_section_is_na(section_text: str) -> bool:
    """True if a §3 section body is the explicit `n/a` line, not a real list."""
    lowered = section_text.lower()
    return "n/a" in lowered and "no consumer-visible contract change" in lowered


def changelog_has_entry_for(unreleased_entries, feature_id: str) -> bool:
    """True if any Unreleased entry's trace names *feature_id* (or a sub-WU of it)."""
    return any(
        entry.trace == feature_id or entry.trace.startswith(feature_id + "/")
        for entry in unreleased_entries
    )


# --------------------------------------------------------------------------- #
# Requirement records                                                         #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Requirement:
    """One closing-artifact requirement, as data.

    ``applies_when`` names the condition under which the requirement fires:
    ``always``, ``verdict_met``, ``failures_present``, or
    ``criteria_artifact_present`` (the gate's
    ``GATE-NN-CRITERIA.md`` exists). ``phase`` is ``pre-squash`` (checked by
    ``assert_closing_deliverables`` right after the WU's own squash) or
    ``post-pass`` (checked by ``verify_post_pass_invariants`` after the
    gate-boundary state flips run).
    """

    id: str
    wu_type: str
    phase: str
    description: str
    enforced_by: str
    applies_when: str = "always"
    file: Optional[str] = None
    file_derivation: Optional[str] = None
    heading: Optional[str] = None
    heading_level: Optional[int] = None
    frontmatter_field: Optional[str] = None
    allowed_values: Optional[frozenset] = field(default=None)


CLOSING_REQUIREMENTS: dict[str, list[Requirement]] = {
    "close": [
        Requirement(
            id="close-a", wu_type="close", phase="pre-squash",
            description="RETROSPECTIVE.md exists and is non-empty in the feature dir",
            file=RETROSPECTIVE_FILENAME,
            enforced_by="assert_retrospective_exists",
        ),
        Requirement(
            id="close-b", wu_type="close", phase="pre-squash",
            description=(
                "LEARNINGS.md gains >=1 line in the squash — or, under "
                f"autonomy_default={AUTO_AUTONOMY} where close-i forbids that, "
                f"{LEARNINGS_PENDING_FILENAME} does — or RETROSPECTIVE.md "
                f"says '{NOTHING_GENERALIZES_PHRASE}'"
            ),
            file=LEARNINGS_PATH,
            enforced_by="assert_learnings_appended_or_noop",
        ),
        Requirement(
            id="close-c", wu_type="close", phase="pre-squash",
            description=(
                f"A documentation deliverable ({DOCS_PREFIX}*, {ROADMAP_PATH}, "
                f"{LEARNINGS_PATH}, or a {RETROSPECTIVE_FILENAME}) appears in "
                "the squash diff"
            ),
            enforced_by="assert_doc_or_roadmap_diff",
        ),
        Requirement(
            id="close-d", wu_type="close", phase="pre-squash",
            description="verdict frontmatter field is present and in VERDICT_VALUES",
            frontmatter_field="verdict", allowed_values=VERDICT_VALUES,
            enforced_by="assert_verdict_well_formed",
        ),
        Requirement(
            id="close-e", wu_type="close", phase="pre-squash",
            description=f"RETROSPECTIVE.md has a '{COST_ANALYSIS_HEADING}' heading",
            file=RETROSPECTIVE_FILENAME, heading=COST_ANALYSIS_HEADING,
            applies_when="verdict_met",
            enforced_by="assert_cost_analysis_section_when_met",
        ),
        Requirement(
            id="close-f", wu_type="close", phase="pre-squash",
            description=f"RETROSPECTIVE.md has a '{FAILURE_CLASS_HEADING}' heading",
            file=RETROSPECTIVE_FILENAME, heading=FAILURE_CLASS_HEADING,
            heading_level=FAILURE_CLASS_HEADING_LEVEL,
            applies_when="failures_present",
            enforced_by="assert_failure_class_breakdown_when_failures_present",
        ),
        Requirement(
            id="close-h", wu_type="close", phase="post-pass",
            description=(
                "Terminal gate status, roadmap row, and roadmap-archive anchor "
                "flip when verdict=met"
            ),
            applies_when="verdict_met",
            enforced_by="assert_terminal_flips_fired",
        ),
        Requirement(
            id="close-i", wu_type="close", phase="post-pass",
            description=(
                f"Under autonomy_default=auto, {LEARNINGS_PATH} is not "
                f"modified — lessons stage to {LEARNINGS_PENDING_FILENAME} "
                "in the feature directory instead"
            ),
            file=LEARNINGS_PATH,
            enforced_by="assert_learnings_staged_under_auto",
        ),
        # The requirement ID between close-i and close-k is deliberately
        # unused. It required a per-entry classification on the hedged-verdict
        # follow-up record, and FEAT-2026-0085 retired the verdicts that record
        # served. The ID is not reused: it appears in event logs and
        # retrospectives written before the narrowing, and rebinding it would
        # make that history say something it never said.
        Requirement(
            id="close-k", wu_type="close", phase="pre-squash",
            description=(
                f"When the '{CONSUMER_VISIBLE_HEADING}' section (close-discipline.md "
                f"§3) is not the '{CONSUMER_VISIBLE_NA_PHRASE}' line, "
                f"{CHANGELOG_PATH}'s Unreleased section gains an entry carrying "
                "this feature's FEAT-ID — the same enumeration §3 already "
                "requires, appended where a consumer reads it, not re-derived"
            ),
            file=RETROSPECTIVE_FILENAME,
            enforced_by="assert_changelog_entry_for_contract_changes",
        ),
        Requirement(
            id="close-m", wu_type="close", phase="pre-squash",
            description=(
                f"When verdict is not_met, {FOLLOW_UPS_FILENAME} exists in "
                "the feature dir with at least one '### ' entry — one "
                "tracked follow-up per failed criterion"
            ),
            file=FOLLOW_UPS_FILENAME,
            applies_when="verdict_not_met",
            enforced_by="assert_followups_recorded",
        ),
        Requirement(
            id="close-l", wu_type="close", phase="pre-squash",
            description=(
                "Every entry in GATE-NN-CRITERIA.md carries a kind: in "
                "criteria_state.ORACLE_KINDS and a state: in "
                "criteria_state.CRITERION_STATES, and every entry whose kind "
                "has no knowable scope and whose state reads pass carries an "
                "attempt: equal to the current attempt"
            ),
            applies_when="criteria_artifact_present",
            enforced_by="check_criteria_state_well_formed",
        ),
    ],
    "close-intermediate": [
        Requirement(
            id="close-intermediate-a", wu_type="close-intermediate", phase="pre-squash",
            description="RETROSPECTIVE.md has a 'Gate N' heading for this gate",
            file=RETROSPECTIVE_FILENAME, heading="Gate {gate_n}",
            enforced_by="assert_retrospective_gate_section",
        ),
        Requirement(
            id="close-intermediate-b", wu_type="close-intermediate", phase="pre-squash",
            description=(
                "LEARNINGS.md gains >=1 line in the squash — or, under "
                f"autonomy_default={AUTO_AUTONOMY} where close-intermediate-e "
                f"forbids that, {LEARNINGS_PENDING_FILENAME} does — or "
                f"RETROSPECTIVE.md says '{NOTHING_GENERALIZES_PHRASE}'"
            ),
            file=LEARNINGS_PATH,
            enforced_by="assert_learnings_appended_or_noop",
        ),
        Requirement(
            id="close-intermediate-c", wu_type="close-intermediate", phase="pre-squash",
            description=(
                f"A documentation deliverable ({DOCS_PREFIX}*, {ROADMAP_PATH}, "
                f"{LEARNINGS_PATH}, or a {RETROSPECTIVE_FILENAME}) appears in "
                "the squash diff"
            ),
            enforced_by="assert_doc_or_roadmap_diff",
        ),
        Requirement(
            id="close-intermediate-d", wu_type="close-intermediate", phase="pre-squash",
            description=f"RETROSPECTIVE.md has a '{FAILURE_CLASS_HEADING}' heading",
            file=RETROSPECTIVE_FILENAME, heading=FAILURE_CLASS_HEADING,
            heading_level=FAILURE_CLASS_HEADING_LEVEL,
            applies_when="failures_present",
            enforced_by="assert_failure_class_breakdown_when_failures_present",
        ),
        Requirement(
            id="close-intermediate-e", wu_type="close-intermediate", phase="post-pass",
            description=(
                f"Under autonomy_default=auto, {LEARNINGS_PATH} is not "
                f"modified — lessons stage to {LEARNINGS_PENDING_FILENAME} "
                "in the feature directory instead"
            ),
            file=LEARNINGS_PATH,
            enforced_by="assert_learnings_staged_under_auto",
        ),
        Requirement(
            id="close-intermediate-f", wu_type="close-intermediate", phase="pre-squash",
            description=(
                "Every entry in GATE-NN-CRITERIA.md carries a kind: in "
                "criteria_state.ORACLE_KINDS and a state: in "
                "criteria_state.CRITERION_STATES, and every entry whose kind "
                "has no knowable scope and whose state reads pass carries an "
                "attempt: equal to the current attempt"
            ),
            applies_when="criteria_artifact_present",
            enforced_by="check_criteria_state_well_formed",
        ),
    ],
    "plan-next": [
        Requirement(
            id="plan-next-a", wu_type="plan-next", phase="pre-squash",
            description="GATE-(N+1)-REVIEW.md exists and is non-empty, or no next gate",
            file_derivation=GATE_REVIEW_FILENAME_TEMPLATE,
            enforced_by="assert_gate_review_exists",
        ),
        Requirement(
            id="plan-next-b", wu_type="plan-next", phase="pre-squash",
            description="Next gate has >=1 drafted WU in PLAN.md, or PLAN.md/roadmap is terminal",
            enforced_by="assert_next_gate_drafted_or_terminal",
        ),
    ],
}


def all_requirements() -> list[Requirement]:
    """Flatten CLOSING_REQUIREMENTS into a single list, registry order preserved."""
    out: list[Requirement] = []
    for reqs in CLOSING_REQUIREMENTS.values():
        out.extend(reqs)
    return out


def requirements_for(wu_type: str) -> list[Requirement]:
    return CLOSING_REQUIREMENTS.get(wu_type, [])
