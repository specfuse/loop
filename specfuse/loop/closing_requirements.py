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
# Requirement records                                                         #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Requirement:
    """One closing-artifact requirement, as data.

    ``applies_when`` names the condition under which the requirement fires:
    ``always``, ``verdict_met``, ``failures_present``, or
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
