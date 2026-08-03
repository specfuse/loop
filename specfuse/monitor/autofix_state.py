# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""GitHub-held autofix rate-limit state (FEAT-2026-0042/T02).

The harvester's runners are ephemeral (see ``PLAN.md``): a GitHub Actions
runner today, an AKS CronJob after FEAT-2026-0043. A state file on local
disk is gone by the next invocation, so "one fix run per fingerprint" would
fire once per *run* rather than once ever, and a daily cap built on a local
counter would never bind — silently, since the guardrail would still read
as present in the code. So all durable state here lives on the GitHub
finding issue that ``specfuse.monitor.issues`` already owns the lifecycle
of, following that module's marker convention rather than inventing a
second one: an HTML-comment marker in the issue body, re-checked
client-side on every read, is the sole authority.

Three operations, all taking an injected ``runner`` (never shelling out or
reaching the network directly -- see ``[FEAT-2026-0031/G1-CLOSE]`` on why a
partial seam is worse than none):

    has_prior_attempt(runner, repo, fingerprint) -> bool
    record_attempt(runner, repo, fingerprint)    -> None (idempotent)
    daily_cap_reached(runner, repo)              -> bool

``GitHubAutofixState`` adapts the first and third to
``specfuse.monitor.autofix.RateLimitStateReader`` for T01's predicate.

**"Daily" is a rolling 24-hour window in UTC, not a calendar day.** An
attempt counts toward the cap while ``now - attempt_at < ROLLING_WINDOW_SECONDS``;
at or past that age it does not. A calendar-day boundary would let two
attempts land seconds apart across midnight UTC and both count as "today",
which is not a meaningfully different cap and is a boundary two callers are
more likely to disagree about by accident. ``test_autofix_state.py`` holds
this boundary at both edges so it cannot silently drift.

**Fail closed.** Any read that cannot be answered -- the injected runner
raises, the finding issue cannot be located -- returns the conservative
answer (an attempt exists; the cap is reached), never the permissive one.
An unreadable state read that returns "no attempt yet" would let a retry
storm through; "unknown" must resolve to "don't fire" the same way T01
resolves an unparseable diagnosis to DECLINE.

**``AUTOFIX_FAILED_LABEL`` is registered here and not yet applied here.**
This module ships the state a *decision* needs (T01) before any code fires
a real fix, so nothing in this feature's gate 1 has an outcome to label yet
-- that is gate 2's job, once a fired attempt's result is known. Registering
the label now, ahead of that consumer, is the fix for issue #300: code that
queries or applies a label the registry never declared gets every
``gh issue create``/``--add-label`` call rejected until a human notices and
creates it by hand. See ``specfuse/loop/labels.py``.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional

from specfuse.monitor.issues import DEFAULT_LIST_LIMIT, FINDING_LABEL, find_finding_issue

# Reserved for FEAT-2026-0042 gate 2: applied to a finding issue once a fired
# autofix attempt is known to have failed. See module docstring.
AUTOFIX_FAILED_LABEL = "auto-fix-attempted-failed"

# Hardcoded for the same reason CONFIDENCE_THRESHOLD is hardcoded in
# autofix.py: a cap that lives in a config file can be tuned into
# uselessness by the person it is meant to stop.
ROLLING_WINDOW_SECONDS = 24 * 60 * 60
DAILY_CAP = 5

_ATTEMPT_PREFIX_TEMPLATE = "<!-- specfuse:autofix-attempt fingerprint={fingerprint} "
_ATTEMPT_MARKER_TEMPLATE = "<!-- specfuse:autofix-attempt fingerprint={fingerprint} at={at} -->"
_ATTEMPT_MARKER_RE = re.compile(
    r"<!-- specfuse:autofix-attempt fingerprint=(?P<fingerprint>\S+) at=(?P<at>[0-9.]+) -->"
)


def _attempt_prefix(fingerprint: str) -> str:
    return _ATTEMPT_PREFIX_TEMPLATE.format(fingerprint=fingerprint)


def _attempt_marker(fingerprint: str, at: float) -> str:
    return _ATTEMPT_MARKER_TEMPLATE.format(fingerprint=fingerprint, at=at)


def has_prior_attempt(runner: Callable, repo: str, fingerprint: str) -> bool:
    """True iff `fingerprint`'s finding issue body carries an attempt marker.

    Locates the issue via `issues.find_finding_issue`, which re-checks the
    finding marker client-side rather than trusting `gh issue list`'s
    listing -- a too-broad or coincidental match that does not carry the
    marker is never treated as a hit (criterion 3). Any failure to answer
    (the runner raises, the listing is truncated) fails closed: True.
    """
    try:
        issue = find_finding_issue(runner, repo, fingerprint, limit=DEFAULT_LIST_LIMIT)
    except Exception:  # noqa: BLE001 - fail closed on any read failure
        return True
    if issue is None:
        return False
    return _attempt_prefix(fingerprint) in issue.get("body", "")


def record_attempt(
    runner: Callable,
    repo: str,
    fingerprint: str,
    *,
    now: Optional[float] = None,
) -> None:
    """Idempotently record an autofix attempt against `fingerprint`'s finding.

    A second call for the same fingerprint is a no-op: no marker is added
    and no `gh` write happens, so recording twice never produces two
    markers or counts twice toward the daily cap (criterion 2). Requires a
    pre-existing finding issue -- `issues.py` owns creating it -- and raises
    `LookupError` if none carries this fingerprint, rather than filing one
    under a different convention.
    """
    now = time.time() if now is None else now
    issue = find_finding_issue(runner, repo, fingerprint, limit=DEFAULT_LIST_LIMIT)
    if issue is None:
        raise LookupError(f"no finding issue carries fingerprint {fingerprint!r}")

    body = issue.get("body", "")
    if _attempt_prefix(fingerprint) in body:
        return

    number = str(issue["number"])
    new_body = body + f"\n\n{_attempt_marker(fingerprint, now)}\n"
    runner(
        ["gh", "issue", "edit", number, "--repo", repo, "--body", new_body],
        check=True,
    )


def _list_attempted_issues(runner: Callable, repo: str, *, limit: int) -> list:
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--label", FINDING_LABEL,
            "--state", "open",
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


def daily_cap_reached(
    runner: Callable,
    repo: str,
    *,
    now: Optional[float] = None,
    cap: int = DAILY_CAP,
    limit: int = DEFAULT_LIST_LIMIT,
) -> bool:
    """True iff `cap` or more autofix attempts fall inside the rolling window.

    Scans the same recently-labelled issue set `issues.py` already
    maintains (`FINDING_LABEL`) rather than trusting a counter anyone would
    have to keep in sync -- the count is always re-derivable from GitHub
    itself. Any failure to answer fails closed: True.
    """
    now = time.time() if now is None else now
    try:
        rows = _list_attempted_issues(runner, repo, limit=limit)
    except Exception:  # noqa: BLE001 - fail closed on any read failure
        return True

    attempted = 0
    for row in rows:
        match = _ATTEMPT_MARKER_RE.search(row.get("body", ""))
        if match is None:
            continue
        at = float(match.group("at"))
        if now - at < ROLLING_WINDOW_SECONDS:
            attempted += 1

    return attempted >= cap


@dataclass(frozen=True)
class GitHubAutofixState:
    """Adapts this module's readers to `autofix.RateLimitStateReader`.

    A thin, frozen binding of `runner`/`repo` (and an optional fixed `now`
    for reproducible cap checks) so T01's predicate can hold one object
    rather than threading both readers' arguments through separately.
    """

    runner: Callable
    repo: str
    now: Optional[float] = None
    cap: int = DAILY_CAP
    limit: int = DEFAULT_LIST_LIMIT

    def has_prior_attempt(self, fingerprint: str) -> bool:
        return has_prior_attempt(self.runner, self.repo, fingerprint)

    def daily_cap_reached(self) -> bool:
        return daily_cap_reached(
            self.runner, self.repo, now=self.now, cap=self.cap, limit=self.limit
        )
