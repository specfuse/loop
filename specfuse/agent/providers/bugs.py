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
    REASON_PR_NOT_FOUND,
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


def _abandoned_work_payload(
    issue_number: int, outcome: str, branch: str, commits: int, rationale: str = ""
) -> EscalationPayload:
    """The stop left committed work behind. Say so, first and loudest.

    `refused` / `could_not_proceed` is accurate for the step the session
    reached and says nothing about what it finished before reaching it. Issue
    #1859's session wrote a skill fix, a new test file and a CHANGELOG entry,
    committed all of it, then stopped -- and the escalation offered "fix it by
    hand", "promote to a feature" and "close the issue", none of which was
    "push the branch that already exists". The work was invisible until
    someone went looking by hand.
    """
    plural = "commit" if commits == 1 else "commits"
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"Headless `/fix-bug` ran against this issue and reported "
            f"`{outcome}` -- but it had already committed work first. Branch "
            f"`{branch}` carries {commits} {plural} that no remote has. The "
            f"most likely reading is that the fix itself completed and the "
            f"push or the PR open is what failed."
            f"{_rationale_block(rationale)}"
        ),
        issue_summary=(
            f"The bug lane stopped on this issue (`{outcome}`), leaving "
            f"{commits} committed {plural} on the local branch `{branch}` "
            f"that was never pushed."
        ),
        decision_needed=(
            "Whether that branch is worth pushing and reviewing, or should be "
            "discarded and the issue fixed another way."
        ),
        why_not_auto=(
            "The lane merges only what reaches a pull request, and this work "
            "never got that far. It is not lost -- it is on the branch named "
            "above, on the machine that ran the agent, and nothing else "
            "references it."
        ),
        options=[
            (
                f"Review `{branch}`, then push it and open a PR",
                "recovers work that is already done and may be complete",
                "needs a human to confirm the work is sound first",
            ),
            (
                "Discard the branch and fix the issue by hand",
                "right call if the committed work is wrong or half-finished",
                "throws away whatever was already correct",
            ),
            (
                "Leave the branch and re-run the lane later",
                "cheap",
                "the branch is local only, so a fresh clone or a wiped "
                "machine loses it silently",
            ),
        ],
        recommendation=(
            f"Look at `{branch}` before deciding anything else. Run the "
            f"project's gates against it -- if they pass, this is a push away "
            f"from being a reviewable PR, and the outcome constant above is "
            f"describing the push step rather than the fix."
        ),
        category="blocked-wu",
    )


def _rationale_block(rationale: str) -> str:
    """The session's own words, quoted, or a statement that it gave none."""
    if not rationale:
        return (
            "\n\nThe session recorded no reason for stopping. That is itself "
            "worth noting -- `/fix-bug`'s contract says the recorded reason "
            "names which criterion fired."
        )
    return f"\n\nIts own account of why:\n\n> {rationale}"


def _fix_bug_stopped_payload(
    issue_number: int, outcome: str, rationale: str = ""
) -> EscalationPayload:
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"Headless `/fix-bug` ran against this issue and stopped without "
            f"opening a mergeable PR -- it reported `{outcome}`."
            f"{_rationale_block(rationale)}"
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


def _pr_not_found_payload(issue_number: int) -> EscalationPayload:
    """`pr_not_found` is a lookup failure, not a guardrail decline (#3180).

    `/fix-bug` reported `completed`, so a branch and very likely a PR exist,
    but the lane could not find a PR whose body closes this issue. The
    generic declined text asserted the PR existed, fixed the issue, and was
    refused, then offered "merge it by hand" with nothing to link. Say what
    is actually known and where to look.
    """
    branch_hint = f"fix/issue-{issue_number}-*"
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            "Headless `/fix-bug` reported `completed` for this issue, but the "
            "bug lane found no open PR whose body closes it, so no guardrail "
            "was evaluated and nothing was merged."
        ),
        issue_summary=(
            "The bug lane has no PR number for this issue -- `pr_not_found`. "
            f"Look for a pushed branch named `{branch_hint}` and a PR opened "
            "from it; if one exists, its body does not reference this issue "
            "the way the lane matches on (`closes #<n>`)."
        ),
        decision_needed=(
            "Whether the fix exists on a branch or PR that needs linking to "
            "this issue, or whether `/fix-bug`'s report was wrong and the fix "
            "must be redone."
        ),
        why_not_auto=(
            "The lane merges only a PR it can find and evaluate. Without a "
            "PR number it can neither run the guardrails nor merge, and it "
            "will not guess which open PR belongs to this issue."
        ),
        options=[
            (
                f"Find the branch `{branch_hint}` or its PR and add "
                f"`Closes #{issue_number}` to the PR body, then re-run the lane",
                "recovers the completed work; the guardrails then evaluate it",
                "costs a lookup",
            ),
            (
                "Fix it by hand",
                "unblocks the issue directly",
                "discards whatever `/fix-bug` produced",
            ),
            (
                "Re-run the lane",
                "cheap if the lookup failed on GitHub read-after-write lag",
                "repeats the fix session if the PR really was never opened",
            ),
        ],
        recommendation=(
            f"Check `git branch -r --list 'origin/{branch_hint}'` first: a "
            "branch with commits means the work exists and only the PR link "
            "is missing. Re-run the lane only if there is no branch."
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
    label_written: bool = True,
) -> EscalationPayload:
    ref = _pr_ref(pr_number)
    # The declining reason is also written to the PR as a label, which is the
    # only thing making declined PRs findable (`gh pr list --label
    # bug-lane:<reason>`). That write can fail, and until #2081 the failure
    # was computed, returned as `label_written=False`, and read by nobody --
    # so a filter that silently returns nothing looked like "no PR was ever
    # declined for this reason". Say it where the decline is read.
    label_note = (
        ""
        if label_written
        else (
            " The declining reason could NOT be written to the PR as a label, "
            "so this PR will not appear under `gh pr list --label "
            "bug-lane:...`. The verdict above is the record; the label is only "
            "a projection of it."
        )
    )
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"The bug lane fixed this issue, opened {ref}, and evaluated the "
            f"merge guardrails."
        ),
        issue_summary=(
            f"{ref} fixes this issue but was declined by the merge "
            f"guardrails -- `{reason}`.{_evidence_block(evidence)}{label_note}"
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
            # `run_bug_lane` (`specfuse/loop/bug_lane_run.py`, T04's file) does
            # not surface the headless `/fix-bug` session's usage envelope on
            # `BugLaneResult` -- reporting the bug lane's real spend needs a
            # change there, out of this WU's reach (`specfuse/loop/` is
            # off-limits except what T01 declares). Explicit `spend=0` rather
            # than a value this module cannot actually measure.
            return ActionOutcome(status=STATUS_COMPLETED, detail=result.reason or "", spend=0)

        detail = result.reason if result.reason is not None else result.outcome

        if result.outcome in _FIX_BUG_STOPPED_OUTCOMES:
            if result.unpushed_work:
                branch, commits = result.unpushed_work
                escalation = _abandoned_work_payload(
                    issue_number, result.outcome, branch, commits,
                    result.stop_rationale,
                )
                detail = f"{detail} — {commits} committed on `{branch}`, unpushed"
            else:
                escalation = _fix_bug_stopped_payload(
                    issue_number, result.outcome, result.stop_rationale
                )
        elif result.outcome == OUTCOME_AUTOMERGE_OFF:
            escalation = _automerge_off_payload(issue_number, result.pr_number)
        elif result.reason == REASON_PR_NOT_FOUND:
            # A lookup failure, not a decline: no PR number exists to point
            # the operator at, so the declined wording would lie (#3180).
            escalation = _pr_not_found_payload(issue_number)
        else:
            assert result.outcome == OUTCOME_DECLINED
            escalation = _declined_payload(
                issue_number,
                result.pr_number,
                detail,
                result.evidence,
                label_written=result.label_written,
            )

        return ActionOutcome(status=STATUS_ESCALATED, detail=detail, escalation=escalation)

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
