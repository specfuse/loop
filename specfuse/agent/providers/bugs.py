# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The bugs provider (FEAT-2026-0049/T06): T05's protocol over
`specfuse.loop.bug_lane_run.run_bug_lane`.

Selection is the only judgment this module adds: one `kind="bug"` item per
open snapshot issue whose triage category is `"bug"`. Everything downstream
of the invocation -- fix, PR, guardrail evaluation, guarded merge, and the
needs-human issue on `refused` / `could_not_proceed` -- belongs to the lane,
consumed here unmodified.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional, Sequence

from specfuse.agent.run import (
    KIND_BUG,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    _default_runner,
)
from specfuse.agent.state import AgentSnapshot
from specfuse.loop.bug_lane_run import (
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_DECLINED,
    OUTCOME_MERGED,
    OUTCOME_REFUSED,
    run_bug_lane,
)
from specfuse.loop.escalation import NEEDS_HUMAN_LABEL

_ITEM_ID_PREFIX = "bug-"

_LANE_FILED_OUTCOMES = (OUTCOME_REFUSED, OUTCOME_COULD_NOT_PROCEED)

#: Labels that mean "a human already owns this issue". An issue carrying one
#: is parked awaiting a decision, so re-running the lane against it can only
#: repeat the outcome that parked it. Observed live: issue #1183 was refused
#: on three separate runs, and every escalation the agent filed was itself
#: triaged `bug` and became a candidate on the next run -- the lane trying to
#: "fix" its own "PR was declined by the merge guardrails" report.
_HUMAN_OWNED_LABELS = frozenset({NEEDS_HUMAN_LABEL, "blocked-wu"})

#: `/fix-bug` cites its issue as `closes #<n>` in the PR body by hard
#: contract (SKILL.md Step 7); `bug_lane_run._find_pr_for_issue` already
#: relies on exactly this. Matched case-insensitively against every open PR
#: body so an issue whose fix is already open for review is not re-fixed.
_CLOSES_RE_TEMPLATE = r"\bcloses\s+#{number}\b"


def _has_open_pr(snapshot: AgentSnapshot, issue_number: int) -> bool:
    pattern = re.compile(
        _CLOSES_RE_TEMPLATE.format(number=issue_number), re.IGNORECASE
    )
    return any(pattern.search(pr.body or "") for pr in snapshot.prs)


class BugsProvider:
    """`ActionProvider` over the bug lane."""

    def __init__(
        self,
        *,
        repo: str,
        runner: Callable = _default_runner,
        working_dir: str = ".",
        policy_path: Any = None,
        now: Optional[float] = None,
    ):
        self._repo = repo
        self._runner = runner
        self._working_dir = working_dir
        self._policy_path = policy_path
        self._now = now

    def advertise(self, snapshot: AgentSnapshot) -> Sequence[ActionItem]:
        items = []
        for issue in snapshot.issues:
            if issue.triage_category != "bug":
                continue
            if _HUMAN_OWNED_LABELS.intersection(issue.labels or ()):
                continue
            if _has_open_pr(snapshot, issue.number):
                continue
            items.append(
                ActionItem(
                    item_id=f"{_ITEM_ID_PREFIX}{issue.number}",
                    kind=KIND_BUG,
                    summary=issue.title,
                    queue_key=None,
                )
            )
        return items

    def execute(self, item: ActionItem) -> ActionOutcome:
        issue_number = int(item.item_id[len(_ITEM_ID_PREFIX) :])
        result = run_bug_lane(
            self._runner,
            self._repo,
            issue_number,
            working_dir=self._working_dir,
            policy_path=self._policy_path,
            now=self._now,
        )

        if result.outcome == OUTCOME_MERGED:
            return ActionOutcome(status=STATUS_COMPLETED, detail=result.reason or "")

        detail = result.reason if result.reason is not None else result.outcome

        if result.outcome in _LANE_FILED_OUTCOMES:
            # The lane itself already filed the needs-human issue for these
            # two outcomes (`bug_lane_run.py:306-308`) -- leaving
            # `escalation` unset here stops the loop from filing a second.
            return ActionOutcome(status=STATUS_ESCALATED, detail=detail, escalation=None)

        assert result.outcome == OUTCOME_DECLINED
        escalation = EscalationPayload(
            done_so_far=(
                f"The bug lane ran against issue #{issue_number}, opened a PR, "
                f"and evaluated the merge guardrails."
            ),
            issue_summary=(
                f"Issue #{issue_number}'s PR was declined by the merge "
                f"guardrails -- `{detail}`."
            ),
            decision_needed="Whether a human should review and merge the PR by hand.",
            why_not_auto=(
                "The merge guardrails declined the PR; the bug lane only "
                "merges automatically when the guardrails are eligible."
            ),
            options=[
                (
                    "Review and merge by hand",
                    "unblocks the fix directly",
                    "costs a human's time",
                ),
                (
                    "Leave the PR open",
                    "no immediate cost",
                    "the bug stays unfixed",
                ),
            ],
            recommendation="Review the declined PR by hand.",
            category="blocked-wu",
        )
        return ActionOutcome(status=STATUS_ESCALATED, detail=detail, escalation=escalation)

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
