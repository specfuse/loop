# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The triage provider (FEAT-2026-0049/T07): T05's protocol over
`specfuse.loop.triage.list_untriaged` / `apply_triage`, with
`specfuse.agent.triage_invoke` supplying the headless classification step
that `apply_triage` itself does not perform.

Selection is client-side filtering of `list_untriaged`'s rows: one
`kind="triage"` item per open, untriaged issue that is not already flagged
`already_structured` (a harvester finding, criterion 6). Classification
judgment stops at the marker `triage_invoke.classify_result` hands back --
this module validates the named category against `triage.CATEGORIES`
before ever calling `apply_triage` (which would raise `ValueError` on an
unknown category) and escalates instead of guessing when it is not one.
A row flagged `needs_repair` (already marked, only its projected label is
missing -- `[FEAT-2026-0045/T01/marker-label-desync]`) skips
classification entirely: its `category`/`confidence` come straight from
`list_untriaged`'s marker read, and `execute` hands them to `apply_triage`
directly.
`auto` is read once per `advertise()` call from
`AgentSnapshot.triage_auto` and passed straight through to `apply_triage`;
the low-confidence-under-auto downgrade to `question` is `apply_triage`'s
job alone -- this module holds no copy of that rule.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from specfuse.agent.run import (
    KIND_TRIAGE,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    _default_runner,
)
from specfuse.agent.state import AgentSnapshot
from specfuse.agent.triage_invoke import build_invocation, classify_result
from specfuse.loop.escalation import CATEGORY_LABELS
from specfuse.loop.triage import CATEGORIES, apply_triage, list_untriaged

_ITEM_ID_PREFIX = "triage-"


def _triage_options() -> list:
    """The two routes open on any triage halt: hand-triage, or leave it."""
    return [
        ("Triage the issue by hand", "unblocks the issue directly", "costs a human's time"),
        (
            "Leave the issue untriaged",
            "no immediate cost",
            "the issue stays unrouted and no lane will pick it up",
        ),
    ]


def _label_repair_failed_payload(number: int, error: str) -> EscalationPayload:
    return EscalationPayload(
        target_issue=number,
        done_so_far=(
            f"This issue already carried a triage marker but was missing its "
            f"projected label. The agent tried to repair the label and the "
            f"write failed: {error}"
        ),
        issue_summary=(
            f"Issue #{number}'s triage label could not be written, so its "
            f"marker and its labels still disagree."
        ),
        decision_needed="Whether a human should apply the label by hand.",
        why_not_auto=(
            "The label write failed and the agent does not retry it a second "
            "time; the category itself is already decided and recorded in the "
            "issue's marker, so only the label projection is missing."
        ),
        options=_triage_options(),
        recommendation=(
            "Apply the label by hand -- the category is already decided, so "
            "this is a one-command fix rather than a triage judgement."
        ),
        category="blocked-wu",
    )


def _no_marker_payload(number: int) -> EscalationPayload:
    return EscalationPayload(
        target_issue=number,
        done_so_far=(
            "The agent ran a headless classification session against this "
            "issue. The session returned no usable triage marker."
        ),
        issue_summary=(
            f"Issue #{number} could not be triaged automatically -- the "
            f"classification session produced no usable marker."
        ),
        decision_needed="Whether a human should categorise this issue by hand.",
        why_not_auto=(
            "Nothing in the session's output parsed as a triage marker, so "
            "there is no category to apply. Re-running unchanged will most "
            "likely reach the same result."
        ),
        options=_triage_options(),
        recommendation=(
            "Read the issue and categorise it by hand. A body the classifier "
            "cannot read is usually one a human should look at anyway."
        ),
        category="triage-question",
    )


def _marker_write_failed_payload(number: int, error: str) -> EscalationPayload:
    return EscalationPayload(
        target_issue=number,
        done_so_far=(
            f"The agent classified this issue and tried to record the triage "
            f"marker on it. The write failed: {error}"
        ),
        issue_summary=(
            f"Issue #{number} was classified but the triage marker could not "
            f"be written, so the categorisation was lost."
        ),
        decision_needed="Whether a human should record the triage decision by hand.",
        why_not_auto=(
            "The marker is the authoritative record of a triage decision. "
            "Without it the issue reads as untriaged, and the label alone "
            "would leave marker and labels disagreeing."
        ),
        options=_triage_options(),
        recommendation=(
            "Check why the write failed before re-running -- a permissions or "
            "rate-limit failure will repeat, and a repeated write failure is "
            "worth diagnosing rather than retrying."
        ),
        category="blocked-wu",
    )


def _is_agent_escalation(row: dict) -> bool:
    """Whether this issue was filed by the agent's own escalation path.

    Keyed on `escalation.CATEGORY_LABELS`, which `escalation.py` writes and
    nothing else does, so the label identifies an agent-authored issue on its
    own -- an operator who has released `needs-human` has not thereby made the
    generated body worth classifying.

    Such an issue is **categorised by construction**: the code that wrote it
    chose its category. Re-deriving one adds nothing, and measurably so --
    four near-identical generated bodies came out three `triage:feature` and
    one `triage:question` (#2384). It also costs a second item per escalation,
    which is how one run spent 8 items on 0 units of work.

    `BugsProvider._HUMAN_OWNED_LABELS` is the same rule from the other side;
    its comment records the lane "trying to 'fix' its own 'PR was declined by
    the merge guardrails' report."
    """
    names = {
        label.get("name")
        for label in (row.get("labels") or [])
        if isinstance(label, dict)
    }
    return bool(names & CATEGORY_LABELS)


class TriageProvider:
    """`ActionProvider` over `specfuse.loop.triage` plus headless
    classification."""

    def __init__(
        self,
        *,
        repo: str,
        runner: Callable = _default_runner,
        working_dir: str = ".",
        policy_path: Any = None,
    ):
        self._repo = repo
        self._runner = runner
        self._working_dir = working_dir
        self._policy_path = policy_path
        self._rows: dict = {}
        self._auto = False

    def advertise(self, snapshot: AgentSnapshot) -> Sequence[ActionItem]:
        self._auto = snapshot.triage_auto
        rows = list_untriaged(self._runner, self._repo)

        self._rows = {}
        items = []
        for row in rows:
            if row.get("already_structured"):
                continue
            if _is_agent_escalation(row):
                continue
            item_id = f"{_ITEM_ID_PREFIX}{row['number']}"
            self._rows[item_id] = row
            items.append(
                ActionItem(
                    item_id=item_id,
                    kind=KIND_TRIAGE,
                    summary=row.get("title", ""),
                    queue_key=None,
                )
            )
        return items

    def execute(self, item: ActionItem) -> ActionOutcome:
        number = int(item.item_id[len(_ITEM_ID_PREFIX) :])
        row = self._rows.get(item.item_id)
        if row is None:
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"issue #{number} is no longer available for triage",
                escalation_waived=(
                    "the issue left the untriaged set between the snapshot and "
                    "this item; nothing for a human to decide"
                ),
            )

        title = row.get("title", "")
        body = row.get("body") or ""

        if row.get("needs_repair"):
            decisions = [
                {
                    "number": number,
                    "body": body,
                    "category": row.get("category"),
                    "confidence": row.get("confidence", "high"),
                    "labels": row.get("labels") or [],
                }
            ]
            results = apply_triage(self._runner, self._repo, decisions, auto=self._auto)
            row_result = results[0]
            if row_result.get("label_written"):
                return ActionOutcome(
                    status=STATUS_COMPLETED,
                    detail=f"issue #{number} label repaired",
                )
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=(
                    f"issue #{number}: label repair failed -- "
                    f"{row_result.get('label_error', 'unknown error')}"
                ),
                escalation=_label_repair_failed_payload(
                    number, row_result.get("label_error", "unknown error")
                ),
            )

        argv, prompt = build_invocation(number, title, body, self._repo, self._working_dir)
        result = self._runner(argv + [prompt], check=False)
        classification = classify_result(getattr(result, "stdout", "") or "")

        if classification is None:
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"issue #{number}: classification session produced no usable marker",
                escalation=_no_marker_payload(number),
            )

        category, confidence = classification
        if category not in CATEGORIES:
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=(
                    f"issue #{number}: classifier named category {category!r}, "
                    f"not one of {CATEGORIES!r}"
                ),
                escalation=EscalationPayload(
                    target_issue=number,
                    done_so_far=(
                        f"Classified issue #{number} through the headless "
                        "triage session."
                    ),
                    issue_summary=(
                        f"Issue #{number}'s classification session named "
                        f"category {category!r}, which is not one of "
                        f"{CATEGORIES!r}."
                    ),
                    decision_needed="Whether a human should categorise this issue by hand.",
                    why_not_auto=(
                        "The classification session named a category outside "
                        "the closed triage vocabulary; applying it would "
                        "raise ValueError."
                    ),
                    options=[
                        (
                            "Categorise by hand",
                            "unblocks the issue directly",
                            "costs a human's time",
                        ),
                        (
                            "Leave the issue untriaged",
                            "no immediate cost",
                            "the issue stays unrouted",
                        ),
                    ],
                    recommendation="Categorise the issue by hand.",
                    category="blocked-wu",
                ),
            )

        decisions = [
            {
                "number": number,
                "body": body,
                "category": category,
                "confidence": confidence,
            }
        ]
        results = apply_triage(self._runner, self._repo, decisions, auto=self._auto)
        row_result = results[0]

        if row_result.get("skipped"):
            return ActionOutcome(status=STATUS_COMPLETED, detail="already triaged")

        if not row_result.get("marker_written"):
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=(
                    f"issue #{number}: triage marker write failed -- "
                    f"{row_result.get('marker_error', 'unknown error')}"
                ),
                escalation=_marker_write_failed_payload(
                    number, row_result.get("marker_error", "unknown error")
                ),
            )

        return ActionOutcome(
            status=STATUS_COMPLETED,
            detail=f"issue #{number} triaged as {row_result.get('category')}",
        )

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
