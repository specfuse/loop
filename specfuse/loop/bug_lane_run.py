# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Run the bug lane end to end (FEAT-2026-0048/T04): fix, PR, guarded merge.

Composes three already-shipped mechanisms and adds the one that does not
exist yet:

- `specfuse.monitor.autofix_invoke.build_invocation` / `classify_outcome` --
  invokes headless `/fix-bug` and classifies its result into `OUTCOMES`.
- `specfuse.loop.bug_lane.evaluate_merge_guardrails` -- the eligibility
  predicate, T02's.
- `specfuse.loop.bug_lane_state.GitHubMergeCapState` / `record_merge` -- the
  durable merge cap, T03's.
- `specfuse.loop.agent_policy.resolve_bug_automerge` / `bug_lane_limits` --
  the dial and the limits it reads.
- `specfuse.loop.escalation.emit_escalation` -- refusal/failure escalation.

`pr_ci_conclusion` is the one wrapper this WU builds: `gh pr checks` has no
existing reader, and this predicate's fail-closed contract (T02's) requires a
bare conclusion string that is never `"success"` on a read it cannot trust.

Merge is gated on exactly one `if dial and decision.eligible:` -- the module
contains exactly one call site that issues `gh pr merge`, reached only there.
Every other path -- dial off, any guardrail failing, a `/fix-bug` refusal or
failure -- leaves the PR open, optionally labelled with the declining reason.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from specfuse.loop.agent_policy import bug_lane_limits, resolve_bug_automerge
from specfuse.loop.bug_lane import (
    DECLINE_LABELS,
    REASON_ELIGIBLE,
    evaluate_merge_guardrails,
)
from specfuse.loop.bug_lane_state import GitHubMergeCapState, record_merge
from specfuse.loop.escalation import emit_escalation
from specfuse.loop.triage import parse_marker
from specfuse.monitor.autofix_invoke import build_invocation, classify_outcome

__all__ = (
    "BugLaneResult",
    "CORRELATION_ID",
    "OUTCOME_REFUSED",
    "OUTCOME_COULD_NOT_PROCEED",
    "OUTCOME_MERGED",
    "OUTCOME_DECLINED",
    "run_bug_lane",
    "pr_ci_conclusion",
)

# This WU's own correlation ID, used verbatim so `emit_escalation`'s
# find-then-create idempotency dedupes repeated refusals into one tracking
# issue rather than filing a duplicate per bug.
CORRELATION_ID = "FEAT-2026-0048/T04"

OUTCOME_REFUSED = "refused"
OUTCOME_COULD_NOT_PROCEED = "could_not_proceed"
OUTCOME_MERGED = "merged"
OUTCOME_DECLINED = "declined"

_ESCALATING_OUTCOMES = (OUTCOME_REFUSED, OUTCOME_COULD_NOT_PROCEED)

_CI_UNKNOWN = "unknown"

_REASON_PR_NOT_FOUND = "pr_not_found"

_DEFAULT_WORKING_DIR = "."


@dataclass(frozen=True)
class BugLaneResult:
    """What `run_bug_lane` decided.

    `reason` is `None` for the two `/fix-bug` outcomes that never reach a
    guardrail evaluation (`refused`, `could_not_proceed`); otherwise it is
    the guardrail's reason constant, `REASON_ELIGIBLE` on a merge, or
    `_REASON_PR_NOT_FOUND` when `/fix-bug` reported `completed` but no PR
    could be found for the issue.
    """

    outcome: str
    reason: Optional[str]
    pr_number: Optional[int]


def pr_ci_conclusion(runner: Callable, repo: str, pr_number: int) -> str:
    """Read `pr_number`'s CI conclusion via `gh pr checks`.

    Returns a bare conclusion string (e.g. `"success"`, `"failure"`) on a
    clean, unanimous read. Returns `_CI_UNKNOWN` -- never raises -- when the
    command fails, the output cannot be parsed, or the conclusion is missing
    or malformed. `evaluate_merge_guardrails` declines on anything but a
    literal `"success"`, so an unreadable conclusion fails closed.
    """
    try:
        result = runner(
            ["gh", "pr", "checks", str(pr_number), "--repo", repo, "--json", "conclusion"],
            check=False,
        )
    except Exception:  # noqa: BLE001 - a raising runner still fails closed
        return _CI_UNKNOWN

    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return _CI_UNKNOWN

    try:
        rows = json.loads(result.stdout)
    except ValueError:
        return _CI_UNKNOWN

    if not isinstance(rows, list) or not rows:
        return _CI_UNKNOWN

    conclusions = set()
    for row in rows:
        if not isinstance(row, dict):
            return _CI_UNKNOWN
        conclusion = row.get("conclusion")
        if not isinstance(conclusion, str) or not conclusion:
            return _CI_UNKNOWN
        conclusions.add(conclusion)

    if len(conclusions) != 1:
        return _CI_UNKNOWN

    return conclusions.pop()


def _find_pr_for_issue(runner: Callable, repo: str, issue_number: int) -> Optional[int]:
    """Find the open PR `/fix-bug` opened for `issue_number`.

    `fix-bug`'s PR body cites `closes #<issue-number>` by hard contract
    (SKILL.md Step 7) -- this searches open PRs for that marker rather than
    inventing a second linkage mechanism.
    """
    result = runner(
        [
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--search", f"closes #{issue_number} in:body",
            "--json", "number,body",
        ],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return None
    try:
        rows = json.loads(result.stdout)
    except ValueError:
        return None
    if not isinstance(rows, list):
        return None

    marker = f"#{issue_number}"
    for row in rows:
        if not isinstance(row, dict):
            continue
        if marker in (row.get("body") or ""):
            number = row.get("number")
            if isinstance(number, int) and not isinstance(number, bool):
                return number
    return None


def _pr_changed_files_and_diff_lines(
    runner: Callable, repo: str, pr_number: int
) -> tuple[list[str], int]:
    result = runner(
        ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "files"],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return [], 0
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return [], 0
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list):
        return [], 0

    changed_files: list[str] = []
    diff_lines = 0
    for entry in files:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if isinstance(path, str):
            changed_files.append(path)
        for key in ("additions", "deletions"):
            value = entry.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                diff_lines += value
    return changed_files, diff_lines


def _issue_provenance(runner: Callable, repo: str, issue_number: int) -> Optional[dict]:
    """Trace `issue_number` back to a triaged-bug marker (T01's format,
    `specfuse.loop.triage`) on the issue body. Returns `None` -- untraceable
    -- when the issue cannot be read or carries no `bug`-category marker.

    This is a defense-in-depth re-check, not a duplicate of
    `bug_lane_state.triaged_bug_intake`'s own filtering: that list may be
    stale by the time a fix lands, so the merge decision re-reads the
    issue's own marker rather than trusting the caller's earlier scan.
    """
    result = runner(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "body"],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return None
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return None
    body = data.get("body") if isinstance(data, dict) else None
    parsed = parse_marker(body or "")
    if parsed is None:
        return None
    category, _confidence = parsed
    if category != "bug":
        return None
    return {"kind": "triaged_issue", "ref": str(issue_number)}


def _escalate_fix_bug_outcome(
    runner: Callable, repo: str, issue_number: int, outcome: str
) -> None:
    emit_escalation(
        CORRELATION_ID,
        category="blocked-wu",
        repo=repo,
        done_so_far=(
            f"Headless `/fix-bug` ran against issue #{issue_number} and "
            f"stopped without opening a mergeable PR."
        ),
        issue_summary=(
            f"The bug lane could not fix issue #{issue_number} automatically "
            f"-- `/fix-bug` reported `{outcome}`."
        ),
        decision_needed=(
            "Whether a human should fix this bug directly, promote it to a "
            "feature, or close it."
        ),
        why_not_auto=(
            "`/fix-bug`'s own refusal or precondition check stopped the run "
            "before a PR existed; the bug lane never reaches a guardrail or "
            "merge decision on this path."
        ),
        options=[
            (
                "Fix it by hand",
                "unblocks the issue directly",
                "costs a human's time",
            ),
            (
                "Promote to a feature via /draft-feature",
                "right call if the fix turned out to be feature-scoped",
                "slower than a bug fix would have been",
            ),
            (
                "Leave it and re-run the bug lane later",
                "cheap, no immediate cost",
                "the same outcome likely repeats until something changes",
            ),
        ],
        recommendation=(
            "Read the issue and `/fix-bug`'s own reasoning first -- a "
            "`refused` outcome usually means the fix is feature-scoped, "
            "which points at promoting rather than forcing a bug-sized fix."
        ),
        runner=runner,
    )


def run_bug_lane(
    runner: Callable,
    repo: str,
    issue_number: int,
    *,
    working_dir: str = _DEFAULT_WORKING_DIR,
    policy_path: Any = None,
    now: Optional[float] = None,
) -> BugLaneResult:
    """Run the bug lane for one issue: fix, PR, guarded merge.

    Invokes headless `/fix-bug` at every dial setting -- the dial governs
    merging, never whether the fix runs. On `refused` / `could_not_proceed`,
    escalates and returns with no PR. On `completed`, evaluates the merge
    guardrails (always, regardless of the dial, so the declining reason is
    always accurate) and merges only when the dial is `on` *and* the
    guardrails are eligible -- the module's single merge call site.
    """
    argv, prompt = build_invocation(issue_number, repo, working_dir)
    invocation = runner(argv + [prompt], check=False)
    outcome = classify_outcome(getattr(invocation, "stdout", "") or "")

    if outcome in _ESCALATING_OUTCOMES:
        _escalate_fix_bug_outcome(runner, repo, issue_number, outcome)
        return BugLaneResult(outcome=outcome, reason=None, pr_number=None)

    pr_number = _find_pr_for_issue(runner, repo, issue_number)
    if pr_number is None:
        return BugLaneResult(outcome=OUTCOME_DECLINED, reason=_REASON_PR_NOT_FOUND, pr_number=None)

    changed_files, diff_lines = _pr_changed_files_and_diff_lines(runner, repo, pr_number)
    ci_conclusion = pr_ci_conclusion(runner, repo, pr_number)
    limits = bug_lane_limits(policy_path)
    provenance = _issue_provenance(runner, repo, issue_number)
    state_reader = GitHubMergeCapState(runner=runner, repo=repo, now=now)

    decision = evaluate_merge_guardrails(
        changed_files=changed_files,
        ci_conclusion=ci_conclusion,
        diff_lines=diff_lines,
        max_diff_lines=limits["max_diff_lines"],
        provenance=provenance,
        max_merges_per_day=limits["max_merges_per_day"],
        test_paths=limits["test_paths"],
        state_reader=state_reader,
    )
    dial = resolve_bug_automerge(policy_path)

    if dial and decision.eligible:
        runner(
            ["gh", "pr", "merge", str(pr_number), "--repo", repo, "--squash", "--delete-branch"],
            check=True,
        )
        record_merge(runner, repo, pr_number, at=time.time() if now is None else now)
        return BugLaneResult(outcome=OUTCOME_MERGED, reason=decision.reason, pr_number=pr_number)

    if decision.reason != REASON_ELIGIBLE:
        # The public label name, never the raw reason constant (#1420): the
        # constant is an internal identifier that provision_labels does not
        # create, so labelling with it failed on every declining path.
        label = DECLINE_LABELS.get(decision.reason)
        if label is not None:
            runner(
                ["gh", "pr", "edit", str(pr_number), "--repo", repo, "--add-label", label],
                check=True,
            )

    return BugLaneResult(outcome=OUTCOME_DECLINED, reason=decision.reason, pr_number=pr_number)
