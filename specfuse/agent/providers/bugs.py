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

import subprocess
import time
from typing import Any, Callable, Optional, Sequence

from specfuse.agent.invoke import resolve_item_timeout_seconds
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
from specfuse.loop.agent_policy import bug_lane_ci_wait_seconds
from specfuse.loop.bug_lane import REASON_CI_PENDING
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

def _bounded_runner(runner: Callable, timeout_seconds: float) -> Callable:
    """Wrap *runner* so the headless `claude` dispatch inside `run_bug_lane`
    (`specfuse.loop.bug_lane_run:595`, off-limits to this WU) gets a real
    wall-clock timeout without editing that module.

    Applies *timeout_seconds* only to the one call whose argv starts with
    `claude` -- `run_bug_lane` reuses this same runner for every `gh` read
    and write along the way, and those must not inherit an item-scale
    deadline meant for one long-running session.
    """

    def wrapped(argv, check: bool = False):
        kwargs = {"check": check}
        if argv and argv[0] == "claude":
            kwargs["timeout"] = timeout_seconds
        return runner(argv, **kwargs)

    return wrapped


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


def _stopped_with_open_pr_payload(
    issue_number: int, outcome: str, pr_number: int, rationale: str = ""
) -> EscalationPayload:
    """The session stopped, but it had already opened a PR (#3178).

    Item #1481 in the 2026-09-02 run opened PR #1532 and then reported
    `could_not_proceed` -- `_fix_bug_stopped_payload`'s "the bug lane never
    reached a guardrail or merge decision on this path" was false for it: a
    PR existed, ready for the guardrails a re-run (or a human) can still
    evaluate. Naming and linking that PR is the whole point of this payload.
    """
    ref = _pr_ref(pr_number)
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"Headless `/fix-bug` ran against this issue, opened {ref}, and "
            f"then reported `{outcome}` before the bug lane evaluated it."
            f"{_rationale_block(rationale)}"
        ),
        issue_summary=(
            f"The bug lane stopped on this issue (`{outcome}`), but {ref} "
            f"already exists and fixes it -- the stop happened after the PR "
            f"was opened and before any guardrail ran."
        ),
        decision_needed=f"Whether to re-run the lane against {ref} or review it by hand.",
        why_not_auto=(
            f"`/fix-bug` reported `{outcome}` before the bug lane could "
            f"evaluate {ref}'s guardrails, so nothing merged it."
        ),
        options=[
            (
                f"Re-run the lane against {ref}",
                "the guardrails evaluate it and merge if eligible",
                "costs another lane run",
            ),
            (
                f"Review and merge {ref} by hand",
                "unblocks immediately without waiting for a retry",
                "costs a human's time",
            ),
            (
                "Close the PR and fix by hand",
                "right call if the fix turned out to be wrong",
                "discards work that may be correct",
            ),
        ],
        recommendation=(
            f"Check {ref} before doing anything else -- it may already be a "
            f"complete fix that only needs the guardrails run against it."
        ),
        category="blocked-wu",
    )


def _wip_ref_for_item(runner: Callable, item_id: str) -> Optional[tuple]:
    """`(ref, commit_count)` for a `wip/<item_id>` ref left by a prior run's
    per-item worktree (FEAT-2026-0108/T02), else `None`.

    A dirty tree an item's session leaves behind is committed under
    `wip/<item_id>` rather than discarded (`specfuse.agent.worktree`) -- a
    ref this module never created and never mutates, only reads once a
    stopped outcome has neither a PR nor a named fix branch to point at.
    Same shape as `unpushed_work_for_issue`, whose named-branch glob does not
    match this run's own naming convention.
    """
    ref = f"wip/{item_id}"
    try:
        listed = runner(
            ["git", "branch", "--list", ref, "--format=%(refname:short)"],
            check=False,
        )
    except Exception:  # noqa: BLE001 - a reporting aid must never break the lane
        return None
    if getattr(listed, "returncode", 1) != 0:
        return None
    if not (getattr(listed, "stdout", "") or "").strip():
        return None
    try:
        log = runner(
            ["git", "log", ref, "--not", "--remotes", "--format=%H"], check=False
        )
    except Exception:  # noqa: BLE001
        return None
    if getattr(log, "returncode", 1) != 0:
        return None
    commits = [line for line in (getattr(log, "stdout", "") or "").split() if line]
    if not commits:
        return None
    return (ref, len(commits))


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


def _ci_pending_payload(
    issue_number: int, pr_number: Optional[int], wait_minutes: int
) -> EscalationPayload:
    """`ci_pending` is a "wait and retry" verdict, not a red build (#3177).

    The generic `_declined_payload` text says "declined by the merge
    guardrails" and recommends a by-hand review -- correct for a real
    guardrail failure, misleading for a build that simply had not finished.
    Seven escalations on 2026-09-02 read that generic text about a PR that
    went green minutes later and was merged by hand.
    """
    ref = _pr_ref(pr_number)
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"The bug lane fixed this issue and opened {ref}, but its CI had "
            f"not concluded after {wait_minutes} minutes; re-run the lane."
        ),
        issue_summary=(
            f"{ref} fixes this issue. Its checks were still pending when the "
            f"bug lane's wait ran out, so no guardrail verdict was reached -- "
            f"CI had not concluded after {wait_minutes} minutes; re-run the "
            f"lane."
        ),
        decision_needed=f"Whether to re-run the lane against {ref} once CI concludes.",
        why_not_auto=(
            f"CI had not concluded after {wait_minutes} minutes; re-run the "
            f"lane. This is not a guardrail failure -- the PR may already be "
            f"green."
        ),
        options=[
            (
                "Re-run the lane once CI finishes",
                "the usual, unattended path once checks conclude",
                "costs another lane run",
            ),
            (
                f"Check {ref}'s CI status and merge by hand if green",
                "unblocks immediately without waiting for a retry",
                "costs a human's time",
            ),
            (
                "Leave the PR open",
                "no immediate cost",
                "the fix sits unmerged until someone retries",
            ),
        ],
        recommendation=(
            f"Check {ref}'s CI status; if it has since concluded, re-run the "
            f"lane rather than merging by hand."
        ),
        category="blocked-wu",
    )


def _timed_out_payload(issue_number: int, elapsed_seconds: float) -> EscalationPayload:
    """The headless `/fix-bug` session ran past the item timeout.

    Distinct from `_fix_bug_stopped_payload`: that one reports what the
    session itself said before stopping; this one fires when the session
    never got the chance to say anything, because the runner cut it off
    (FEAT-2026-0108/T03, #3178) rather than the skill reaching its own
    `could_not_proceed`.
    """
    elapsed = f"{elapsed_seconds:.0f}s"
    return EscalationPayload(
        target_issue=issue_number,
        done_so_far=(
            f"Headless `/fix-bug` was dispatched against this issue and ran "
            f"for {elapsed} without finishing -- the run's own timeout ended "
            f"the session before it reported an outcome."
        ),
        issue_summary=(
            f"The bug lane's `could_not_proceed`: the `/fix-bug` session "
            f"exceeded its `budgets.item_timeout_minutes` deadline "
            f"({elapsed} elapsed) with no recorded outcome."
        ),
        decision_needed=(
            "Whether the fix was likely close to done (raise the timeout and "
            "re-run) or the issue needs a human to work it directly."
        ),
        why_not_auto=(
            "A session that outran its deadline may have left partial, "
            "uncommitted work on its own branch or none at all -- the lane "
            "has no way to tell which without a human looking."
        ),
        options=[
            (
                "Raise `budgets.item_timeout_minutes` and re-run the lane",
                "cheap if the fix was genuinely close to finishing",
                "wastes another full timeout if the issue was never bug-sized",
            ),
            (
                "Fix it by hand",
                "unblocks the issue directly",
                "costs a human's time",
            ),
            (
                "Re-run the lane unchanged",
                "cheap if the timeout was a one-off (e.g. a slow CI runner)",
                "repeats the same timeout if the fix itself is what's slow",
            ),
        ],
        recommendation=(
            "Check for a local branch named for this issue before deciding "
            "anything else -- a session that timed out mid-gate-run may have "
            "already committed a working fix."
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
        timeout_seconds = resolve_item_timeout_seconds(self._policy_path)
        started = time.monotonic()
        try:
            result = run_bug_lane(
                _bounded_runner(self._runner, timeout_seconds),
                self._repo,
                issue_number,
                working_dir=self._working_dir,
                policy_path=self._policy_path,
                now=self._now,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - started
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=(
                    f"could_not_proceed: headless /fix-bug session timed out "
                    f"after {elapsed:.0f}s"
                ),
                escalation=_timed_out_payload(issue_number, elapsed),
                spend=0,
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
            if result.pr_number:
                escalation = _stopped_with_open_pr_payload(
                    issue_number, result.outcome, result.pr_number,
                    result.stop_rationale,
                )
                detail = f"{detail} — PR #{result.pr_number} already open"
            elif result.unpushed_work:
                branch, commits = result.unpushed_work
                escalation = _abandoned_work_payload(
                    issue_number, result.outcome, branch, commits,
                    result.stop_rationale,
                )
                detail = f"{detail} — {commits} committed on `{branch}`, unpushed"
            else:
                wip = _wip_ref_for_item(self._runner, item.item_id)
                if wip is not None:
                    wip_ref, commits = wip
                    escalation = _abandoned_work_payload(
                        issue_number, result.outcome, wip_ref, commits,
                        result.stop_rationale,
                    )
                    detail = f"{detail} — {commits} committed on `{wip_ref}`, unpushed"
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
        elif result.reason == REASON_CI_PENDING:
            # "Retry", not "red" (#3177): the generic declined text below
            # would say the merge guardrails declined this PR, which is not
            # what happened -- CI simply had not concluded yet.
            wait_minutes = bug_lane_ci_wait_seconds(self._policy_path) // 60
            escalation = _ci_pending_payload(issue_number, result.pr_number, wait_minutes)
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
