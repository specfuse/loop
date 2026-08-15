# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""GitHub-held bug-lane state (FEAT-2026-0048/T03): the durable merge cap and
the triaged-bug intake.

Both readers exist for the same reason: the process's memory must survive
to the next invocation, and the runner's disk does not. Per
`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]` --
the runner is a GitHub Actions container today and an AKS CronJob tomorrow,
so each invocation starts with an empty disk. A disk-backed merge counter
would never reach its cap: nothing errors, no log line appears, and code
review sees a rate limiter. The guarantee would be decorative.

This module copies `specfuse.monitor.autofix_state`'s convention -- an
HTML-comment marker written onto the artifact the cap is about, a rolling
24-hour window, a count re-derived from that state on every read, an
injected `runner` -- without importing from it: the two caps count
different events on different artifacts.

`GitHubMergeCapState` satisfies `bug_lane.MergeCapStateReader`: it counts
merged bug-lane PRs by re-reading `<!-- specfuse:bug-automerge at={at} -->`
markers this module writes onto merged PRs via `record_merge`.

`triaged_bug_intake` is the lane's second intake door -- triaged bug issues,
alongside the diagnosed monitoring findings `monitor/autofix_run.py`
already handles. It classifies via `specfuse.loop.triage`'s own
`parse_marker` / `CATEGORIES` rather than re-parsing the triage marker
format here.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional

from specfuse.loop.triage import CATEGORIES, parse_marker
from specfuse.monitor.autofix_state import AUTOFIX_FAILED_LABEL

# Hardcoded for the same reason it is hardcoded in autofix_state.py: a
# rolling 24-hour window, not a calendar day, so an accident of midnight UTC
# never lets two merges within a day both count as "today".
ROLLING_WINDOW_SECONDS = 24 * 60 * 60

_BUG_CATEGORY = "bug"
assert _BUG_CATEGORY in CATEGORIES

_MERGE_MARKER_PREFIX = "<!-- specfuse:bug-automerge at="
_MERGE_MARKER_TEMPLATE = "<!-- specfuse:bug-automerge at={at} -->"
_MERGE_MARKER_RE = re.compile(r"<!-- specfuse:bug-automerge at=(?P<at>[0-9.]+) -->")

# A read that cannot be answered fails closed: report a count far above any
# realistic cap so the guardrail declines, never a count that reads as "safe".
_FAIL_CLOSED_COUNT = 10**9

DEFAULT_LIST_LIMIT = 100


def render_merge_marker(at: float) -> str:
    return _MERGE_MARKER_TEMPLATE.format(at=at)


def parse_merge_marker(body: str) -> Optional[float]:
    """Return the `at` timestamp carried by `body`'s merge marker, or `None`
    if `body` carries none or the marker is malformed."""
    match = _MERGE_MARKER_RE.search(body or "")
    if match is None:
        return None
    try:
        return float(match.group("at"))
    except ValueError:
        return None


def _list_merged_prs(runner: Callable, repo: str, *, limit: int) -> list:
    result = runner(
        [
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "merged",
            "--limit", str(limit),
            "--json", "number,body",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []


def merges_last_24h(
    runner: Callable,
    repo: str,
    *,
    now: Optional[float] = None,
    limit: int = DEFAULT_LIST_LIMIT,
) -> int:
    """Count merged bug-lane PRs whose merge marker falls inside the rolling
    24-hour window, re-derived from GitHub on every call -- never a
    maintained counter. A malformed or unparseable marker is ignored, not
    fatal, and neither inflates nor deflates the count. Any failure to
    answer fails closed: a count above any realistic cap.
    """
    now = time.time() if now is None else now
    try:
        rows = _list_merged_prs(runner, repo, limit=limit)
    except Exception:  # noqa: BLE001 - fail closed on any read failure
        return _FAIL_CLOSED_COUNT

    count = 0
    for row in rows:
        at = parse_merge_marker(row.get("body", ""))
        if at is None:
            continue
        if now - at < ROLLING_WINDOW_SECONDS:
            count += 1
    return count


def record_merge(
    runner: Callable,
    repo: str,
    pr_number: int,
    *,
    at: float,
) -> None:
    """Idempotently write the merge marker onto PR `pr_number`.

    A second call for the same PR is a no-op: no marker is added and no
    `gh` write happens, so recording twice never produces two markers or
    counts twice toward the merge cap.
    """
    result = runner(
        ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "body"],
        check=True,
    )
    body = json.loads(result.stdout).get("body") or "" if result.stdout else ""

    if _MERGE_MARKER_PREFIX in body:
        return

    new_body = body + f"\n\n{render_merge_marker(at)}\n"
    runner(
        ["gh", "pr", "edit", str(pr_number), "--repo", repo, "--body", new_body],
        check=True,
    )


@dataclass(frozen=True)
class GitHubMergeCapState:
    """Adapts this module's `merges_last_24h` to
    `bug_lane.MergeCapStateReader` -- accepted by
    `evaluate_merge_guardrails` with no adapter."""

    runner: Callable
    repo: str
    now: Optional[float] = None
    limit: int = DEFAULT_LIST_LIMIT

    def merges_last_24h(self) -> int:
        return merges_last_24h(self.runner, self.repo, now=self.now, limit=self.limit)


def _list_open_issues(runner: Callable, repo: str, *, limit: int) -> list:
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--state", "open",
            "--limit", str(limit),
            "--json", "number,title,body,labels",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []


def _has_label(issue: dict, label: str) -> bool:
    for entry in issue.get("labels") or []:
        if isinstance(entry, dict):
            if entry.get("name") == label:
                return True
        elif entry == label:
            return True
    return False


def triaged_bug_intake(runner: Callable, repo: str, *, limit: int = DEFAULT_LIST_LIMIT) -> list:
    """Return open issues eligible to enter the bug lane: triaged as `bug`
    category via `triage.parse_marker`, not already carrying
    `AUTOFIX_FAILED_LABEL` from a failed prior automated attempt.

    Calls `triage.parse_marker` rather than re-parsing the triage marker
    format -- a second parser for one format is drift waiting to happen.
    """
    issues = _list_open_issues(runner, repo, limit=limit)
    intake = []
    for issue in issues:
        parsed = parse_marker(issue.get("body") or "")
        if parsed is None:
            continue
        category, _confidence = parsed
        if category != _BUG_CATEGORY:
            continue
        if _has_label(issue, AUTOFIX_FAILED_LABEL):
            continue
        intake.append(issue)
    return intake
