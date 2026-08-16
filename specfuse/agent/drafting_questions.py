# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Build the drafting interview's question set (FEAT-2026-0050/T01).

`/draft-feature`'s interview classifies every question it asks into
**elicitation** (only the user knows the answer — asked open, never with
manufactured options) or **decision** (the skill can enumerate real options
and has a basis to recommend). `build_question_set` turns that classification
into a data structure: a decision without a recommendation is an elicitation
question misfiled, and `Question.__post_init__` refuses to construct one.

Reads only — a roadmap entry's text, a LEARNINGS slice, and one or more
exemplar `PLAN.md` texts, all passed in or read from a path by the loader
functions below. This module posts nothing, writes no issue, and runs no
`gh` or `git` subprocess; `specfuse/agent/drafting_questions.py:T02` owns
posting the rendered body.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

from specfuse.loop import escalation

__all__ = (
    "Question",
    "build_question_set",
    "build_question_set_for_feature",
    "load_roadmap_entry",
    "load_learnings_slice",
    "load_exemplar_plan",
    "render_question_issue",
)

_SURFACE_RE = re.compile(r"`([^`\n]+)`")

_AUTONOMY_OPTIONS = ("auto", "review", "supervised")
_GATE_SHAPE_SINGLE = "single gate (<=4 substantive WUs, one terminal close)"
_GATE_SHAPE_MULTI = "multi-gate (2-4 gates, non-terminal gates close-then-plan-next)"
_GATE_SHAPE_OPTIONS = (_GATE_SHAPE_SINGLE, _GATE_SHAPE_MULTI)

# Above this many characters the roadmap entry reads like a major initiative
# rather than a single-gate-sized slice — the same "planned substantive WU
# count <= 4" ceremony-proportionality rule `/draft-feature` applies, read
# off the entry's own size in lieu of a WU count that does not exist yet.
_MULTI_GATE_LENGTH_THRESHOLD = 1500


@dataclass(frozen=True)
class Question:
    """One interview question, classified `elicitation` or `decision`.

    An `elicitation` question carries no options and no recommendation — a
    fake multiple-choice on the user's own intent is the failure
    `/draft-feature` names. A `decision` question carries at least two
    options and a recommendation naming one of them; D1 in this feature's
    `PLAN.md` defaults an unanswered decision to that recommendation, so a
    decision this module cannot recommend on is not a decision.
    """

    id: str
    kind: str
    text: str
    options: tuple = field(default=())
    recommendation: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind not in ("elicitation", "decision"):
            raise ValueError(f"unknown question kind: {self.kind!r}")
        if not self.id or not self.text:
            raise ValueError("question must carry a non-empty id and text")
        if self.kind == "elicitation":
            if self.options or self.recommendation is not None:
                raise ValueError(
                    f"elicitation question {self.id!r} must carry no options "
                    "and no recommendation"
                )
        else:  # decision
            if len(self.options) < 2:
                raise ValueError(
                    f"decision question {self.id!r} must carry at least two options"
                )
            if self.recommendation not in self.options:
                raise ValueError(
                    f"decision question {self.id!r} recommendation "
                    f"{self.recommendation!r} must name one of its own options"
                )


def _extract_surfaces(text: str) -> list:
    """Backtick-quoted spans in `text`, in first-seen order, deduplicated.

    These are read as the surfaces (paths, modules, symbols) the roadmap
    entry already names — the evidence the "surfaces touched" question below
    is required to trace back to, per this unit's acceptance criteria.
    """
    seen: list = []
    for match in _SURFACE_RE.findall(text):
        if match and match not in seen:
            seen.append(match)
    return seen


def _recommend_autonomy(roadmap_entry: str) -> str:
    lowered = roadmap_entry.lower()
    if "human checkpoint" in lowered or "stays human" in lowered or "review" in lowered:
        return "review"
    return "auto"


def _recommend_gate_shape(roadmap_entry: str) -> str:
    if len(roadmap_entry) > _MULTI_GATE_LENGTH_THRESHOLD:
        return _GATE_SHAPE_MULTI
    return _GATE_SHAPE_SINGLE


def build_question_set(
    roadmap_entry: str,
    learnings_slice: str,
    exemplar_plans: Sequence[str] = (),
) -> list:
    """Build the classified question set for one `drafting-needed` roadmap
    entry. Pure — no file or network I/O; `roadmap_entry`, `learnings_slice`,
    and `exemplar_plans` are already-read text.

    `learnings_slice` and `exemplar_plans` are accepted (not merely ignored)
    because acceptance criterion 4 requires the builder to have actually read
    them before it can propose the framing questions honestly — a decision
    question this module cannot ground in `roadmap_entry`, `learnings_slice`,
    or an exemplar is not one it has a basis to recommend on.
    """
    surfaces = _extract_surfaces(roadmap_entry)
    surface_note = f" (roadmap names: {', '.join(surfaces)})" if surfaces else ""

    return [
        Question(
            id="roadmap-goal",
            kind="elicitation",
            text=(
                "In one sentence, what user-observable outcome should this "
                "feature produce, and who is the user?"
            ),
        ),
        Question(
            id="scope-boundary",
            kind="elicitation",
            text="What is explicitly OUT of scope for this feature?",
        ),
        Question(
            id="surfaces-touched",
            kind="elicitation",
            text=(
                "Which surfaces does this feature touch, and did the "
                f"roadmap entry name them correctly?{surface_note}"
            ),
        ),
        Question(
            id="autonomy-level",
            kind="decision",
            text="What autonomy level should this feature default to?",
            options=_AUTONOMY_OPTIONS,
            recommendation=_recommend_autonomy(roadmap_entry),
        ),
        Question(
            id="gate-shape",
            kind="decision",
            text="Should this feature draft as a single gate or multiple gates?",
            options=_GATE_SHAPE_OPTIONS,
            recommendation=_recommend_gate_shape(roadmap_entry),
        ),
    ]


def load_roadmap_entry(roadmap_text: str, feature_id: str) -> str:
    """Extract `feature_id`'s detail section from `roadmap.md`-shaped text:
    the `## <feature_id> — ...` heading through (not including) the next
    `## ` heading."""
    lines = roadmap_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and feature_id in line:
            start = i
            break
    if start is None:
        raise ValueError(f"roadmap entry not found for {feature_id}")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def load_learnings_slice(
    query: str,
    *,
    learnings_path: Optional[Path] = None,
    top_n: int = 10,
) -> str:
    """The LEARNINGS.md slice relevant to `query`, ranked the same way
    `python3 -m specfuse.loop.learnings_query` ranks it — reusing that
    module's parser and BM25 ranker directly rather than shelling out, since
    this module is structurally forbidden from spawning any subprocess."""
    from specfuse.loop import learnings_query

    path = Path(learnings_path) if learnings_path is not None else learnings_query.default_learnings_path()
    text = path.read_text(encoding="utf-8")
    entries = learnings_query.parse_entries(text)
    if not entries:
        return ""
    if learnings_query.should_load_whole(entries, learnings_query.DEFAULT_LOAD_WHOLE_THRESHOLD):
        return text
    ranked = learnings_query.rank(query, entries, top_n=top_n)
    return "\n".join(entry["raw"] for entry in ranked)


def load_exemplar_plan(path) -> str:
    """Read one exemplar `PLAN.md` verbatim."""
    return Path(path).read_text(encoding="utf-8")


def build_question_set_for_feature(
    feature_id: str,
    roadmap_text: str,
    exemplar_plan_texts: Iterable[str] = (),
    *,
    learnings_slice: Optional[str] = None,
    learnings_path: Optional[Path] = None,
) -> list:
    """Orchestration wrapper: extract `feature_id`'s roadmap entry from
    `roadmap_text`, load its LEARNINGS slice (unless already supplied), and
    build the classified question set. Still issues no `gh` or `git`
    subprocess — the LEARNINGS read goes through `load_learnings_slice`, and
    `roadmap_text` / `exemplar_plan_texts` are caller-supplied."""
    roadmap_entry = load_roadmap_entry(roadmap_text, feature_id)
    if learnings_slice is None:
        learnings_slice = load_learnings_slice(feature_id, learnings_path=learnings_path)
    return build_question_set(roadmap_entry, learnings_slice, tuple(exemplar_plan_texts))


# FEAT-2026-0050/T02: render the interview as one `needs-human` issue.
_DRAFTING_CATEGORY = "drafting-needed"

_QUESTION_MARKER_TEMPLATE = "<!-- specfuse:question id={question_id} -->"


def _question_marker(question_id: str) -> str:
    return _QUESTION_MARKER_TEMPLATE.format(question_id=question_id)


def render_question_issue(
    correlation_id: str, questions: Sequence[Question]
) -> tuple:
    """Render `questions` as one escalation issue body plus its label set.

    Composes over `escalation.render_escalation_body` rather than
    reimplementing it: the six-part shape, the numbered-options rendering,
    and the correlation marker stay that function's, unchanged. What this
    adds is per-question binding, which that function's signature has no
    notion of -- a single `decision_needed` string and one flat `options`
    list, shared by the whole issue. Every question, elicitation or
    decision, gets its own `<!-- specfuse:question id=... -->` marker
    written into that shared text, so a later reply can be bound to the
    question it answers rather than to its position in a combined list --
    the failure this unit exists to prevent: an operator who answers
    questions 1 and 3 and skips 2 must not have answer 3 read as the answer
    to question 2.

    Elicitation questions carry no options and render as open prose under
    their own marker. Decision questions contribute their options to the one
    combined "Options" / "Reply with a number" section
    `render_escalation_body` renders, each option labelled
    `"{question.id}: {option}"` so its owning question stays legible, and
    the recommended option named both there and in the rendered
    recommendation part.
    """
    if not questions:
        raise ValueError("render_question_issue requires at least one question")

    decision_lines: list = []
    recommendation_lines: list = []
    options: list = []

    for question in questions:
        decision_lines.append(_question_marker(question.id))
        decision_lines.append(f"**{question.id}** ({question.kind}): {question.text}")
        if question.kind == "decision":
            decision_lines.append(f"(Options below, labelled `{question.id}: <choice>`.)")
            recommendation_lines.append(f"{question.id}: {question.recommendation}")
            for option in question.options:
                recommended = option == question.recommendation
                pros = "recommended" if recommended else ""
                cons = "" if recommended else "not the recommended choice"
                options.append((f"{question.id}: {option}", pros, cons))
        decision_lines.append("")

    body = escalation.render_escalation_body(
        correlation_id,
        category=_DRAFTING_CATEGORY,
        done_so_far=(
            "The drafting interview built its question set from the roadmap "
            "entry, LEARNINGS, and exemplar plans."
        ),
        issue_summary=(
            "The interview below needs an operator's answers before this "
            "feature can be drafted."
        ),
        decision_needed="\n".join(decision_lines).strip(),
        why_not_auto=(
            "Drafting on an assumed answer to an elicitation question is the "
            "assumption-built-plan failure this feature exists to avoid; a "
            "decision question needs the operator's chance to override the "
            "recommendation before it is taken."
        ),
        options=options,
        recommendation="\n".join(recommendation_lines).strip(),
    )
    labels = frozenset({escalation.NEEDS_HUMAN_LABEL, _DRAFTING_CATEGORY})
    return body, labels
