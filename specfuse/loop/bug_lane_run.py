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

This module files no issue and posts no comment. Recording a halt for a human
belongs to the caller, which knows the issue the halt is about; the lane
returns a verdict and nothing else.

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
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from specfuse.loop.agent_policy import (
    bug_lane_limits,
    resolve_bug_automerge,
)
from specfuse.loop.bug_lane import (
    DECLINE_LABELS,
    REASON_DIFF_TOO_LARGE,
    REASON_JUDGE_PATH_TOUCHED,
    REASON_NO_TEST_EVIDENCE,
    evaluate_merge_guardrails,
    evaluate_pr_shape_guardrails,
    judge_paths_touched,
)
from specfuse.loop.bug_lane_state import GitHubMergeCapState, record_merge
from specfuse.loop.labels import provision_labels
from specfuse.loop.triage import parse_marker
from specfuse.monitor.autofix_invoke import build_invocation, classify_outcome

__all__ = (
    "BugLaneResult",
    "CORRELATION_ID",
    "OUTCOME_REFUSED",
    "OUTCOME_COULD_NOT_PROCEED",
    "OUTCOME_MERGED",
    "OUTCOME_DECLINED",
    "OUTCOME_AUTOMERGE_OFF",
    "run_bug_lane",
    "pr_ci_conclusion",
    "add_guardrail_label",
    "pr_closes_issue",
)

# This WU's own correlation ID. Retained as the lane's public identity (it is
# exported and referenced by consumers); it is no longer used to file an issue,
# because the lane no longer files one.
CORRELATION_ID = "FEAT-2026-0048/T04"

OUTCOME_REFUSED = "refused"
OUTCOME_COULD_NOT_PROCEED = "could_not_proceed"
OUTCOME_MERGED = "merged"
OUTCOME_DECLINED = "declined"

#: Every guardrail passed and `rules.bugs.automerge` is `off`. Distinct from
#: `OUTCOME_DECLINED` because nothing declined: the PR is mergeable and the
#: operator has simply not armed the dial. Folding the two together produced
#: the self-contradicting report observed live on issue #296 -- "declined by
#: the merge guardrails -- `eligible`", under a "why it did not close
#: automatically" section that read "the merge guardrails declined the PR",
#: when the guardrails had passed and the dial was the only thing in the way.
OUTCOME_AUTOMERGE_OFF = "automerge_off"

_ESCALATING_OUTCOMES = (OUTCOME_REFUSED, OUTCOME_COULD_NOT_PROCEED)

_CI_UNKNOWN = "unknown"
#: Checks exist but have not concluded yet -- internal to this module; never
#: reaches `evaluate_merge_guardrails`, which sees only a conclusion or unknown.
_CI_PENDING = "__pending__"

_REASON_PR_NOT_FOUND = "pr_not_found"

_DEFAULT_WORKING_DIR = "."

#: How many open PRs to scan for the `closes #<n>` linkage.
_PR_LIST_LIMIT = 100


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
    #: Whether the declining reason reached the PR as a label (#1785).
    #: Defaults True so existing callers and their tests are unaffected; only
    #: a declining path that tried and failed sets it False. The lane no
    #: longer dies on that failure -- `reason` above is the verdict, and the
    #: label is a projection of it, so losing the projection must not lose
    #: the item. Mirrors `apply_triage`'s `label_written` row exactly.
    label_written: bool = True
    #: The measurements behind a declining `reason`, as ready-to-read
    #: sentences -- which judge path was touched, how the diff compared to the
    #: cap. Empty for outcomes carrying no measurement. A reason constant on
    #: its own makes the human re-derive from the diff what the lane already
    #: computed, which is the whole content of every escalation the first
    #: unattended run produced.
    evidence: tuple = ()


#: How long to wait for a freshly-opened PR's checks to reach a conclusion,
#: and how often to re-read while waiting (#1786). The lane reads CI moments
#: after `/fix-bug` opens the PR, so a pending conclusion is the GUARANTEED
#: first observation, not an exceptional one.
CI_WAIT_SECONDS = 600
CI_POLL_SECONDS = 15


#: The `--json` fields this module reads. `gh pr checks` has NO `conclusion`
#: field (#1826) -- asking for one exits 1 with `Unknown JSON field`, which is
#: why CI was unreadable on every PR since the lane shipped and
#: `rules.bugs.automerge` could never fire. Verbatim from `gh pr checks --json`:
#: bucket, completedAt, description, event, link, name, startedAt, state,
#: workflow. `tests/test_pr_checks_json_field.py` compares this list against
#: the installed binary, which is the check that was missing.
CI_JSON_FIELDS = "bucket,name,state"

#: `bucket` is gh's own normalisation across check providers. A skipped check
#: is not a failure: a required check that did not need to run must not block a
#: merge forever.
_BUCKETS_OK = frozenset({"pass", "skipping"})
_BUCKET_PENDING = "pending"

_CI_FAILING = "fail"


def _read_ci_conclusion_once(runner: Callable, repo: str, pr_number: int) -> str:
    """One `gh pr checks` read, mapped through `bucket`.

    `_CI_PENDING` when any check is queued or running, or when no check is
    registered yet; `_CI_UNKNOWN` when the output cannot be parsed at all.
    """
    try:
        result = runner(
            ["gh", "pr", "checks", str(pr_number), "--repo", repo,
             "--json", CI_JSON_FIELDS],
            check=False,
        )
    except Exception:  # noqa: BLE001 - a raising runner still fails closed
        return _CI_UNKNOWN

    # Deliberately NOT gated on returncode. `gh pr checks` exits non-zero when
    # checks are FAILING (1) or partly skipped (8), not only when the
    # invocation is bad -- so exit code alone cannot distinguish "CI is red"
    # from "the command broke". The output is the authority; the exit code is
    # only a fallback when there is no parseable output.
    stdout = getattr(result, "stdout", None)
    if not stdout:
        return _CI_UNKNOWN

    try:
        rows = json.loads(stdout)
    except ValueError:
        return _CI_UNKNOWN

    if not isinstance(rows, list):
        return _CI_UNKNOWN
    if not rows:
        # No check registered yet -- the first state of a brand-new PR, which
        # is pending rather than unreadable. Bounded by the caller's deadline.
        return _CI_PENDING

    buckets = set()
    for row in rows:
        if not isinstance(row, dict):
            return _CI_UNKNOWN
        bucket = row.get("bucket")
        if not isinstance(bucket, str) or not bucket:
            return _CI_UNKNOWN
        buckets.add(bucket.lower())

    if _BUCKET_PENDING in buckets:
        return _CI_PENDING
    if buckets <= _BUCKETS_OK:
        return "success"
    return _CI_FAILING


def pr_ci_conclusion(
    runner: Callable,
    repo: str,
    pr_number: int,
    *,
    sleep: Callable = time.sleep,
    clock: Callable = time.monotonic,
    deadline_seconds: float = CI_WAIT_SECONDS,
    poll_seconds: float = CI_POLL_SECONDS,
) -> str:
    """Wait for `pr_number`'s CI to reach a conclusion, then return it.

    Returns a bare conclusion string (e.g. `"success"`, `"failure"`) once every
    check has one. Returns `_CI_UNKNOWN` -- never raises -- when the command
    fails, the output cannot be parsed, the conclusions disagree, or the
    checks are still pending when *deadline_seconds* expires.
    `evaluate_merge_guardrails` declines on anything but a literal `"success"`,
    so an unreadable conclusion still fails closed.

    Polls rather than reading once (#1786). `run_bug_lane` calls this moments
    after `/fix-bug` opens the PR, when checks are queued by definition, so the
    single read returned `_CI_UNKNOWN` every time: `rules.bugs.automerge` could
    never fire, and a green PR was labelled `bug-lane:ci-not-green`. A settled
    PR still costs exactly one call -- the wait is paid only when there is
    something to wait for.

    A pending-at-deadline result is still reported as `_CI_UNKNOWN` rather
    than a distinct reason. When this landed, the argument was that a new
    reason needs a new label and an unprovisioned label was fatal here --
    #1785 has since fixed that half, so the objection is now only that a
    ninth guardrail label is a contract change owing its own issue, not that
    it would break the lane. Splitting the pending case out is safe whenever
    someone wants it.
    """
    started = clock()
    while True:
        conclusion = _read_ci_conclusion_once(runner, repo, pr_number)
        if conclusion != _CI_PENDING:
            return conclusion
        if clock() - started >= deadline_seconds:
            return _CI_UNKNOWN
        sleep(poll_seconds)


def add_guardrail_label(
    runner: Callable,
    repo: str,
    pr_number: int,
    label: str,
    *,
    target: Any = _DEFAULT_WORKING_DIR,
) -> bool:
    """Label *pr_number* with the lane's declining reason. Never raises (#1785).

    Returns True when the label landed, False when it did not.

    This used to run with ``check=True``. A label that is registered in
    ``LABEL_REGISTRY`` but never created on the repository therefore raised
    ``CalledProcessError`` out of the lane, and on a live run that discarded
    29.8 minutes of correct work -- a test-first fix and a mergeable PR --
    replacing the guardrail verdict with an exception repr. Eight of the
    registry's twenty-one labels were absent; the registry was complete and
    nothing had ever provisioned them.

    ``apply_triage`` already treats this exact condition as best-effort,
    recording ``label_written: False`` and continuing. Two consumers of one
    registry must not disagree about whether a missing label is survivable,
    so the lane now matches it: **the reason is the verdict, and the label is
    only a projection of it.** Losing the projection must not lose the item.

    On failure the label is provisioned on demand -- ``provision_labels`` is
    idempotent and captures its own failure modes rather than raising -- and
    the write retried exactly once. A label that already exists costs one
    call and no provisioning, so the happy path is unchanged.
    """
    argv = ["gh", "pr", "edit", str(pr_number), "--repo", repo, "--add-label", label]

    def _attempt() -> bool:
        try:
            result = runner(argv, check=False)
        except Exception:  # noqa: BLE001 - a raising runner must not kill the item
            return False
        return getattr(result, "returncode", 1) == 0

    if _attempt():
        return True

    try:
        provision_labels(target, runner=runner)
    except Exception:  # noqa: BLE001 - best-effort by contract; never fatal here
        return False

    return _attempt()


#: `/fix-bug` cites its issue as `closes #<n>` in the PR body by hard contract
#: (SKILL.md Step 7). Matched with word boundaries on both sides: a bare
#: `f"#{issue_number}"` substring test made `#198` match a PR closing `#1984`,
#: which the search query happened to mask until the search itself was removed.
_CLOSES_RE = r"\bcloses\s+#{number}\b"


def pr_closes_issue(body: str, issue_number: int) -> bool:
    """Whether *body* cites `closes #issue_number`, case-insensitively.

    One predicate, shared with `specfuse.agent.providers.bugs`, so the lane's
    "which PR fixes this issue" and selection's "does this issue already have
    a PR" cannot disagree about what the linkage is.
    """
    return re.search(_CLOSES_RE.format(number=issue_number), body or "", re.IGNORECASE) is not None


def _find_pr_for_issue(runner: Callable, repo: str, issue_number: int) -> Optional[int]:
    """Find the open PR `/fix-bug` opened for `issue_number`.

    **Deliberately does not use `gh pr list --search`.** That hits GitHub's
    search index, which lags object creation by seconds to minutes, and this
    function is called immediately after `/fix-bug` opens the PR. Observed
    live: issue #1984's fix ran 17 minutes, opened PR #2016 with a correct
    `Closes #1984` body, and the lane reported `pr_not_found` -- the same
    search returned the PR minutes later. The result was 17 minutes of
    correct work reported as failure and a PR left un-evaluated by every
    guardrail.

    Listing without `--search` reads the repository's pull requests directly
    rather than an index built from them, so a PR opened one second ago is
    visible. The `closes #<n>` match then happens client-side -- the same
    shape `triage.list_untriaged` uses, which "filters `gh issue list`'s
    output client-side rather than trusting a label listing".

    Bounded by `_PR_LIST_LIMIT`: a repository with more open PRs than that
    could still miss one. That is a far smaller window than the index lag it
    replaces, and it fails the same way -- `pr_not_found`, no merge.
    """
    result = runner(
        [
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--limit", str(_PR_LIST_LIMIT),
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

    for row in rows:
        if not isinstance(row, dict):
            continue
        if pr_closes_issue(row.get("body") or "", issue_number):
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


def _evidence_for(
    reason: str, changed_files: list, diff_lines: int, limits: dict
) -> tuple:
    """Render the measurement behind *reason* as sentences a human can read."""
    if reason == REASON_JUDGE_PATH_TOUCHED:
        hits = judge_paths_touched(changed_files)
        if not hits:
            return ()
        shown = ", ".join(f"`{p}`" for p in hits[:5])
        more = f" (and {len(hits) - 5} more)" if len(hits) > 5 else ""
        return (
            f"Judge paths touched: {shown}{more}. A judge path is one the "
            f"merge decision itself depends on, so a fix that edits it "
            f"cannot approve its own guardrail.",
        )
    if reason == REASON_DIFF_TOO_LARGE:
        return (
            f"Diff is {diff_lines} changed lines against a "
            f"`rules.bugs.max_diff_lines` cap of {limits.get('max_diff_lines')}.",
        )
    if reason == REASON_NO_TEST_EVIDENCE:
        paths = ", ".join(f"`{p}`" for p in limits.get("test_paths") or ())
        return (
            f"No changed file falls under the declared test paths"
            f"{': ' + paths if paths else ''}.",
        )
    return ()


def _declined(
    runner: Callable,
    repo: str,
    pr_number: int,
    reason: str,
    working_dir: str,
    *,
    evidence: tuple = (),
) -> BugLaneResult:
    """Label the PR with *reason* (best-effort) and return the declined result."""
    # The public label name, never the raw reason constant (#1420): the
    # constant is an internal identifier that provision_labels does not
    # create, so labelling with it failed on every declining path.
    label_written = True
    label = DECLINE_LABELS.get(reason)
    if label is not None:
        label_written = add_guardrail_label(
            runner, repo, pr_number, label, target=working_dir,
        )
    return BugLaneResult(
        outcome=OUTCOME_DECLINED,
        reason=reason,
        pr_number=pr_number,
        label_written=label_written,
        evidence=evidence,
    )


def run_bug_lane(
    runner: Callable,
    repo: str,
    issue_number: int,
    *,
    working_dir: str = _DEFAULT_WORKING_DIR,
    policy_path: Any = None,
    now: Optional[float] = None,
    ci_sleep: Callable = time.sleep,
    ci_clock: Callable = time.monotonic,
    ci_deadline_seconds: float = CI_WAIT_SECONDS,
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
        # The lane files nothing. It used to open its own tracking issue here,
        # which meant one halt produced a second issue the human then had to
        # correlate back to the bug by hand -- and a repeated refusal produced
        # a third and a fourth (issue #1183, three runs, three issues). The
        # caller records the halt on the bug's own issue instead, through the
        # single escalation owner in `specfuse.agent.run`.
        return BugLaneResult(outcome=outcome, reason=None, pr_number=None)

    pr_number = _find_pr_for_issue(runner, repo, issue_number)
    if pr_number is None:
        return BugLaneResult(outcome=OUTCOME_DECLINED, reason=_REASON_PR_NOT_FOUND, pr_number=None)

    changed_files, diff_lines = _pr_changed_files_and_diff_lines(runner, repo, pr_number)
    limits = bug_lane_limits(policy_path)
    provenance = _issue_provenance(runner, repo, issue_number)

    # Shape first, CI second. Every guardrail below is decidable from the PR
    # itself, and a PR they decline can never merge whatever CI reports -- so
    # waiting up to `CI_WAIT_SECONDS` for a conclusion first bought nothing
    # but ten minutes per item. Two of eight items in the first unattended
    # run paid that wait to be declined `judge_path_touched`.
    shape = evaluate_pr_shape_guardrails(
        changed_files=changed_files,
        diff_lines=diff_lines,
        max_diff_lines=limits["max_diff_lines"],
        provenance=provenance,
        test_paths=limits["test_paths"],
    )
    if not shape.eligible:
        return _declined(
            runner, repo, pr_number, shape.reason, working_dir,
            evidence=_evidence_for(
                shape.reason, changed_files, diff_lines, limits,
            ),
        )

    ci_conclusion = pr_ci_conclusion(
        runner, repo, pr_number,
        sleep=ci_sleep, clock=ci_clock, deadline_seconds=ci_deadline_seconds,
    )
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

    if decision.eligible:
        # Eligible but not merged: the dial is the only thing in the way, and
        # saying so is the whole point of this branch. No label -- there is no
        # declining reason to project, and `DECLINE_LABELS` deliberately has no
        # entry for `REASON_ELIGIBLE`.
        return BugLaneResult(
            outcome=OUTCOME_AUTOMERGE_OFF, reason=decision.reason, pr_number=pr_number
        )

    # Reaching here means `decision.eligible` is False, so the reason is a real
    # declining one and never `REASON_ELIGIBLE` -- the eligible-but-not-merged
    # case returned above.
    return _declined(
        runner, repo, pr_number, decision.reason, working_dir,
        evidence=_evidence_for(decision.reason, changed_files, diff_lines, limits),
    )
