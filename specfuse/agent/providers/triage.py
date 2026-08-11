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
from specfuse.loop.triage import CATEGORIES, apply_triage, list_untriaged

_ITEM_ID_PREFIX = "triage-"


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
            )

        title = row.get("title", "")
        body = row.get("body") or ""

        argv, prompt = build_invocation(number, title, body, self._repo, self._working_dir)
        result = self._runner(argv + [prompt], check=False)
        classification = classify_result(getattr(result, "stdout", "") or "")

        if classification is None:
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"issue #{number}: classification session produced no usable marker",
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
            )

        return ActionOutcome(
            status=STATUS_COMPLETED,
            detail=f"issue #{number} triaged as {row_result.get('category')}",
        )

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
