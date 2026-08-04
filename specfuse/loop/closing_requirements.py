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

VERDICT_VALUES = frozenset({"met", "met_locally", "partially_met", "not_met"})

RETROSPECTIVE_FILENAME = "RETROSPECTIVE.md"
LEARNINGS_PATH = ".specfuse/LEARNINGS.md"
LEARNINGS_PENDING_FILENAME = "LEARNINGS-pending.md"
ROADMAP_PATH = ".specfuse/roadmap.md"
DOCS_PREFIX = "docs/"
NOTHING_GENERALIZES_PHRASE = "nothing generalizes"

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


DEFERRAL_HEADING_TEXT = "What the loop did NOT verify"
DEFERRAL_HEADING_RE = re.compile(rf"(?m)^#{{1,3}}\s*{re.escape(DEFERRAL_HEADING_TEXT)}.*$")

AUTOCLOSE_DEBT_MARKER_RE = re.compile(r"<!--\s*specfuse:autoclose-debt\s+gate=(\d+)")


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
# Hedged-verdict follow-up `kind:` contract (FEAT-2026-0059/T01)              #
# --------------------------------------------------------------------------- #

#: The four classifications a close-discipline.md §2 follow-up entry may
#: carry, and what each means for the verdict ceiling. `inherent` is not in
#: the roadmap row's original three — see PLAN.md for why it was added.
FOLLOW_UP_KIND_MEANINGS: dict[str, str] = {
    "acceptance-discharged": "needs a human signature; accepting IS the discharge",
    "externally-verifiable-later": (
        "needs a real run or environment; upgradeable at the named condition"
    ),
    "routed-finding": "now owned elsewhere; tracked on another surface",
    "inherent": "not assertable, ever",
}

FOLLOW_UP_KINDS: frozenset[str] = frozenset(FOLLOW_UP_KIND_MEANINGS)

#: Verdicts that require a §2 follow-up record at all (close-discipline §2).
HEDGED_VERDICT_VALUES: frozenset[str] = frozenset({"met_locally", "partially_met"})

HEDGED_RECORD_HEADING = "Hedged-verdict follow-up record"
HEDGED_RECORD_HEADING_RE = re.compile(
    rf"^##+ {re.escape(HEDGED_RECORD_HEADING)}\b.*$", re.MULTILINE,
)

#: Matches a per-entry `- **kind:** `<value>`` line inside a §2 record.
KIND_FIELD_RE = re.compile(r"\*\*kind:\*\*\s*`([a-zA-Z0-9-]+)`")

REWORK_EXISTS = "rework exists"
NO_IN_REPO_REWORK = "no in-repo rework can raise this verdict"


def verdict_ceiling_for_kinds(kinds) -> str:
    """The verdict ceiling implied by a hedged close's set of follow-up kinds.

    Mechanical, not a judgment call: if any entry is
    `externally-verifiable-later`, a real re-run condition exists and the
    operator has a choice. Otherwise `met` is unreachable by any in-repo
    work — the empty set (no entries at all) also lands here.
    """
    if any(kind == "externally-verifiable-later" for kind in kinds):
        return REWORK_EXISTS
    return NO_IN_REPO_REWORK


# --------------------------------------------------------------------------- #
# Requirement records                                                         #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Requirement:
    """One closing-artifact requirement, as data.

    ``applies_when`` names the condition under which the requirement fires:
    ``always``, ``verdict_met``, ``verdict_hedged``, ``failures_present``, or
    ``autoclose_debt_marker``. ``phase`` is ``pre-squash`` (checked by
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
                "LEARNINGS.md gains >=1 line in the squash, or RETROSPECTIVE.md "
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
            id="close-g", wu_type="close", phase="post-pass",
            description=(
                "Predecessor auto-close debt markers are named in the terminal "
                f"close's '{DEFERRAL_HEADING_TEXT}' section"
            ),
            file=RETROSPECTIVE_FILENAME,
            applies_when="autoclose_debt_marker",
            enforced_by="assert_autoclose_debt_reconciled",
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
        Requirement(
            id="close-j", wu_type="close", phase="pre-squash",
            description=(
                "On a hedged verdict, every entry in the "
                f"'{HEDGED_RECORD_HEADING}' section carries a valid `kind:` "
                f"field ({', '.join(sorted(FOLLOW_UP_KINDS))})"
            ),
            file=RETROSPECTIVE_FILENAME,
            applies_when="verdict_hedged",
            enforced_by="assert_hedged_followup_kinds_classified",
        ),
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
                "LEARNINGS.md gains >=1 line in the squash, or RETROSPECTIVE.md "
                f"says '{NOTHING_GENERALIZES_PHRASE}'"
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
