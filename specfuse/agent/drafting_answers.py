# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Read the drafting interview's answers and apply the D1 gate
(FEAT-2026-0050/T03).

`PLAN.md`'s D1: any unanswered *elicitation* question forces fallback to the
plain `drafting-needed` escalation; an unanswered *decision* question takes
the agent's own recommendation, logged as an explicit assumption. The rule
reuses T01's `Question.kind` classification rather than inventing a
threshold -- if the agent could enumerate options and recommend one, silence
safely means "your recommendation"; if it could not, silence carries no
information and drafting on it is the assumption-built-plan failure this
feature exists to avoid.

Binding is by question id, not by position -- extending the labelling idiom
`drafting_questions.render_question_issue` already established for decision
options (`f"{question.id}: {option}"`), rather than adding a second reply
convention. An operator's reply line is expected as `"{question.id}:
<answer>"`, one per answered question; `parse_reply_answers` binds by that
id regardless of order, so a reply answering questions 1 and 3 while
skipping 2 leaves question 2 unanswered rather than shifting answer 3 onto
it -- a mis-binding here would feed D1 a wrong classification, which is the
one input D1 cannot tolerate being wrong. This is `answers.py`'s existing
numbered-reply idiom extended to per-question binding, not a second reader:
that module's `_numbered_answers_section` and ack-marker machinery answer a
single-question escalation, where position and question are the same thing;
this module's questions are plural, so position stops being a safe key.

This module reads no issue, runs no `gh` or `git` subprocess, and posts
nothing: it is handed already-fetched reply text and returns a verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

from specfuse.agent.drafting_questions import Question
from specfuse.agent.run import EscalationPayload

__all__ = (
    "Assumption",
    "AnswerGateResult",
    "OUTCOME_DRAFT_READY",
    "OUTCOME_FALLBACK",
    "MAX_ROUNDS",
    "parse_reply_answers",
    "next_round_questions",
    "reask_allowed",
    "fallback_escalation",
    "evaluate_answer_gate",
)

_ANSWER_LINE_RE = re.compile(r"^(?P<qid>[A-Za-z0-9_-]+):\s*(?P<answer>.+)$")

#: A round-two re-ask is allowed once; a third round is never posted. Two
#: covers the real shape D1 describes -- ask, re-ask what elicitation went
#: unanswered, then fall back -- with no open-ended retry.
MAX_ROUNDS = 2

OUTCOME_DRAFT_READY = "draft_ready"
OUTCOME_FALLBACK = "fallback"

#: Mirrors `specfuse.agent.providers.feature.FeatureProvider`'s
#: `needs_drafting` branch exactly -- D1's fallback is that existing
#: escalation, not a new shape, so D3's "worst case is status quo" holds
#: mechanically. Kept as a literal copy rather than an import from
#: `providers.feature` because that module builds the payload inline inside
#: `execute()`, not as a reusable function; duplicating five string
#: constants is cheaper than reaching into a provider's execute path from a
#: pure gate function, and the equality is asserted by test.
_ARM_GATE_DRAFTING_FEATURE = "FEAT-2026-0050"


@dataclass(frozen=True)
class Assumption:
    """One decision question D1 defaulted, and the value assumed."""

    question_id: str
    assumed_value: str


@dataclass(frozen=True)
class AnswerGateResult:
    """D1's verdict. `outcome` is `OUTCOME_DRAFT_READY` or `OUTCOME_FALLBACK`.

    On `OUTCOME_DRAFT_READY`, `answers` carries every question's effective
    answer (given or defaulted) and `assumptions` names every defaulted
    decision. On `OUTCOME_FALLBACK`, `answers` and `assumptions` stay empty
    and `escalation` carries the plain `drafting-needed` payload.
    """

    outcome: str
    answers: dict = field(default_factory=dict)
    assumptions: tuple = ()
    escalation: Optional[EscalationPayload] = None


def parse_reply_answers(reply_text: str, question_ids: Sequence[str]) -> dict:
    """Bind reply lines to question ids.

    Each line matching `"{question_id}: <answer>"` for a known id records
    that id's answer, last line wins. Lines that don't match a known id are
    ignored -- they are prose surrounding the answers, not an answer
    themselves. This binds by id, never by position: a reply that answers
    question 3 before question 1 still lands question 3's answer on
    question 3.
    """
    known = set(question_ids)
    answers: dict = {}
    for line in (reply_text or "").splitlines():
        match = _ANSWER_LINE_RE.match(line.strip())
        if not match:
            continue
        question_id = match.group("qid")
        if question_id not in known:
            continue
        answers[question_id] = match.group("answer").strip()
    return answers


def next_round_questions(questions: Sequence[Question], answers: dict) -> tuple:
    """The questions round two re-asks: unanswered elicitation only.

    Answered questions are not re-asked -- they don't need to be. Unanswered
    *decision* questions are not re-asked either: D1 already has a
    recommendation to fall back on for those, and re-litigating a decision
    the operator declined to answer would spend their attention on exactly
    what they delegated.
    """
    return tuple(
        question
        for question in questions
        if question.kind == "elicitation" and question.id not in answers
    )


def reask_allowed(round_number: int) -> bool:
    """Whether posting another round is allowed after `round_number` rounds
    have already been posted. `MAX_ROUNDS` caps it at two -- a third round
    is never posted."""
    return round_number < MAX_ROUNDS


def fallback_escalation(feature_id: str) -> EscalationPayload:
    """The plain `drafting-needed` escalation D1 falls back to -- identical
    to what `FeatureProvider`'s `needs_drafting` branch produces today."""
    return EscalationPayload(
        done_so_far=f"{feature_id} is in the queue but has no feature folder.",
        issue_summary=(
            f"{feature_id} needs to be drafted before it can be advanced."
        ),
        decision_needed=f"Draft {feature_id} — its gate skeleton and gate 1 work units.",
        why_not_auto=(
            "Drafting a feature is out of this provider's scope; async "
            f"drafting is tracked by {_ARM_GATE_DRAFTING_FEATURE}, which "
            f"lists this feature as its blocker."
        ),
        options=[
            (
                "Draft the feature by hand or via /draft-feature",
                "unblocks the queue entry",
                "costs a human's time",
            ),
            (
                "Remove it from the queue",
                "no immediate cost",
                "the feature stays undrafted",
            ),
        ],
        recommendation=f"Draft {feature_id} via /draft-feature.",
        category="drafting-needed",
    )


def evaluate_answer_gate(
    feature_id: str, questions: Sequence[Question], answers: dict
) -> AnswerGateResult:
    """Apply D1 to a final answer set (after however many rounds were run).

    Any unanswered elicitation question forces `OUTCOME_FALLBACK`, whatever
    round produced this answer set -- including the round-two-cap case,
    where round two's re-ask still left an elicitation question unanswered.
    Otherwise every unanswered decision defaults to its recommendation,
    logged as an `Assumption`, and the outcome is `OUTCOME_DRAFT_READY`.
    """
    unanswered_elicitation = [
        question
        for question in questions
        if question.kind == "elicitation" and question.id not in answers
    ]
    if unanswered_elicitation:
        return AnswerGateResult(
            outcome=OUTCOME_FALLBACK,
            escalation=fallback_escalation(feature_id),
        )

    effective_answers: dict = {}
    assumptions: list = []
    for question in questions:
        if question.id in answers:
            effective_answers[question.id] = answers[question.id]
            continue
        # Unanswered decision: D1 defaults to the agent's own recommendation.
        effective_answers[question.id] = question.recommendation
        assumptions.append(Assumption(question.id, question.recommendation))

    return AnswerGateResult(
        outcome=OUTCOME_DRAFT_READY,
        answers=effective_answers,
        assumptions=tuple(assumptions),
    )
