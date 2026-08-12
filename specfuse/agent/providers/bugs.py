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
    OUTCOME_AUTOMERGE_OFF,
    OUTCOME_COULD_NOT_PROCEED,
    OUTCOME_DECLINED,
    OUTCOME_MERGED,
    OUTCOME_REFUSED,
    pr_closes_issue,
    run_bug_lane,
)
from specfuse.loop.escalation import NEEDS_HUMAN_LABEL

_ITEM_ID_PREFIX = "bug-"

#: The two outcomes where `/fix-bug` stopped before a PR existed. The lane
#: used to file its own tracking issue for these; it no longer files anything
#: -- every escalation this provider produces is recorded on the bug's own
#: issue, through the one owner in `run.py`.
_FIX_BUG_STOPPED_OUTCOMES = (OUTCOME_REFUSED, OUTCOME_COULD_NOT_PROCEED)

#: Labels that mean "a human already owns this issue". An issue carrying one
#: is parked awaiting a decision, so re-running the lane against it can only
#: repeat the outcome that parked it. Observed live: issue #1183 was refused
#: on three separate runs, and every escalation the agent filed was itself
#: triaged `bug` and became a candidate on the next run -- the lane trying to
#: "fix" its own "PR was declined by the merge guardrails" report.
_HUMAN_OWNED_LABELS = frozenset({NEEDS_HUMAN_LABEL, "blocked-wu"})

def _has_open_pr(snapshot: AgentSnapshot, issue_number: int) -> bool:
    """Whether an open PR already cites `closes #issue_number`.

    Delegates to `bug_lane_run.pr_closes_issue` rather than carrying its own
    regex: selection's "this issue already has a fix in review" and the
    lane's "which PR fixes this issue" are the same question, and two copies
    of the answer is how they drift.
    """
    return any(pr_closes_issue(pr.body or "", issue_number) for pr in snapshot.prs)


def _pr_ref(pr_number: Optional[int]) -> str:
    return f"PR #{pr_number}" if pr_number else "the PR"


def _evidence_block(evidence: Sequence[str]) -> str:
    """Render the lane's own measurements as prose the human can act on.

    An escalation that names a reason constant and nothing else -- every one
    the first unattended run produced -- makes the reader re-derive the
    measurement by hand. `diff_too_large` without the numbers, or
    `judge_path_touched` without the path, is a label, not a report.
    """
    if not evidence:
        return ""
    return " " + " ".join(evidence)


def _fix_bug_stopped_payload(issue_number: int, outcome: str) -> EscalationPayload:
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"Headless `/fix-bug` ran against this issue and stopped without "
            f"opening a mergeable PR -- it reported `{outcome}`."
        ),
        issue_summary=(
            f"The bug lane could not fix this issue automatically -- "
            f"`/fix-bug` reported `{outcome}`."
        ),
        decision_needed=(
            "Whether a human should fix this bug directly, promote it to a "
            "feature, or close it."
        ),
        why_not_auto=(
            "`/fix-bug`'s own refusal or precondition check stopped the run "
            "before a PR existed; the bug lane never reached a guardrail or "
            "merge decision on this path."
        ),
        options=[
            ("Fix it by hand", "unblocks the issue directly", "costs a human's time"),
            (
                "Promote to a feature via /draft-feature",
                "right call if the fix turned out to be feature-scoped",
                "slower than a bug fix would have been",
            ),
            (
                "Close the issue",
                "right call if it is not actionable",
                "loses whatever the report was pointing at",
            ),
        ],
        recommendation=(
            "Read `/fix-bug`'s own reasoning first -- a `refused` outcome "
            "usually means the fix is feature-scoped, which points at "
            "promoting rather than forcing a bug-sized fix. Re-running the "
            "lane unchanged will reach the same outcome."
        ),
        category="blocked-wu",
    )


def _automerge_off_payload(
    issue_number: int, pr_number: Optional[int]
) -> EscalationPayload:
    ref = _pr_ref(pr_number)
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"The bug lane fixed this issue, opened {ref}, and evaluated the "
            f"merge guardrails. Every guardrail passed."
        ),
        issue_summary=(
            f"{ref} fixes this issue and is eligible to merge; "
            f"`rules.bugs.automerge` is `off`, so the lane did not merge it."
        ),
        decision_needed=f"Whether to merge {ref}.",
        why_not_auto=(
            "Nothing declined this PR. The merge guardrails returned "
            "`eligible`, and the only thing between it and a merge is the "
            "`rules.bugs.automerge` dial in `.specfuse/agent-policy.yml`, "
            "which is set to `off`."
        ),
        options=[
            (
                f"Review and merge {ref}",
                "lands a fix that already passed every guardrail",
                "costs a review",
            ),
            (
                'Turn `rules.bugs.automerge` to "on"',
                "future eligible PRs merge without this round trip",
                "the guardrails become the only reviewer, on every bug",
            ),
            (
                "Leave the PR open",
                "no immediate cost",
                "the fix sits unmerged and drifts from main",
            ),
        ],
        recommendation=(
            f"Review and merge {ref}. Flipping the dial is a separate, "
            f"wider decision -- make it deliberately, not as a side effect of "
            f"one PR."
        ),
        category="merge-approval",
    )


def _declined_payload(
    issue_number: int,
    pr_number: Optional[int],
    reason: str,
    evidence: Sequence[str] = (),
) -> EscalationPayload:
    ref = _pr_ref(pr_number)
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"The bug lane fixed this issue, opened {ref}, and evaluated the "
            f"merge guardrails."
        ),
        issue_summary=(
            f"{ref} fixes this issue but was declined by the merge "
            f"guardrails -- `{reason}`.{_evidence_block(evidence)}"
        ),
        decision_needed=f"Whether a human should review and merge {ref} by hand.",
        why_not_auto=(
            f"The `{reason}` guardrail declined the PR. The bug lane merges "
            f"only when every guardrail returns eligible, so this PR is left "
            f"open for a human."
        ),
        options=[
            (
                f"Review and merge {ref} by hand",
                "unblocks the fix directly",
                "costs a human's time",
            ),
            (
                "Close the PR and fix by hand",
                "right call if the lane's fix is wrong rather than just unmergeable",
                "discards work that may be correct",
            ),
            (
                "Leave the PR open",
                "no immediate cost",
                "the bug stays unfixed",
            ),
        ],
        recommendation=(
            f"Review {ref} by hand. `{reason}` is a policy limit on what may "
            f"merge unattended, not a judgement that the fix is wrong."
        ),
        category="blocked-wu",
    )


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

        if result.outcome in _FIX_BUG_STOPPED_OUTCOMES:
            escalation = _fix_bug_stopped_payload(issue_number, result.outcome)
        elif result.outcome == OUTCOME_AUTOMERGE_OFF:
            escalation = _automerge_off_payload(issue_number, result.pr_number)
        else:
            assert result.outcome == OUTCOME_DECLINED
            escalation = _declined_payload(
                issue_number, result.pr_number, detail, result.evidence
            )

        return ActionOutcome(status=STATUS_ESCALATED, detail=detail, escalation=escalation)

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
