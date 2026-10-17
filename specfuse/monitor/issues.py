# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Fingerprint-keyed GitHub issue lifecycle (FEAT-2026-0040/T09).

One issue per fingerprint: find-or-create, bump an occurrence record under a
throttle on repeat sightings, and annotate a fingerprint that has gone quiet.
This module never closes an issue — that is a deliberate scope boundary
(see ``PLAN.md``'s scope-boundary section): a monitoring tool that
auto-closes on silence erases the evidence of an intermittent fault, so
closing stays a human decision. It does reopen one: a fingerprint whose
issue a human closed and that then recurs inside the lookup window is a
regression, and refiling it forks the history (FEAT-2026-0204 decision 1).

Reused from ``specfuse.loop.escalation`` on purpose: the injected-runner seam
(``runner(args, check=...)`` defaulting to ``_default_runner``),
``_extract_issue_number``'s ``/issues/(\\d+)`` parse of ``gh issue create``'s
stdout, the HTML-comment marker convention, and the find-then-create
ordering with a client-side ``marker in body`` re-check on every candidate
row.

**Not** reused: ``_find_existing_issue``'s search strategy. FEAT-2026-0046's
retrospective records that GitHub's issue search index does not reliably
tokenise HTML-comment content passed to ``--search`` — the existing
``marker in body`` re-check makes a too-broad match safe, but a search that
returns *nothing* is indistinguishable from "no existing issue" and silently
files a duplicate on every retry. For an escalation that fires a handful of
times that is noise; for a harvester whose entire value is deduplication
across thousands of occurrences, it is the defect that makes the feature
worthless while every gate stays green.

So ``_list_findings`` below drops ``--search`` entirely and filters
``gh issue list --label ... --json number,body,title`` client-side, with an
explicit ``--limit``. A full page with no match is the same failure by a
different route — pagination instead of a bad search term — so it is never
silently treated as "not found": it raises ``TruncatedListingError`` naming
the truncation. The fingerprint is also embedded in the issue title, since
GitHub does index titles and that keeps a title-scoped narrowing available
for large repositories, but correctness never rests on it — the marker in
the body, re-checked client-side, is the sole authority.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from specfuse.loop.escalation import _default_runner, _extract_issue_number
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.redaction import redact_artifact

# Distinct from escalation.py's NEEDS_HUMAN_LABEL on purpose: these are
# harvester findings, not generic operator escalations, and keeping their
# own label lets `gh issue list` scope to exactly this lifecycle's issues.
FINDING_LABEL = "monitoring-finding"

DEFAULT_LIST_LIMIT = 100
DEFAULT_THROTTLE_SECONDS = 6 * 60 * 60
DEFAULT_QUIET_AFTER_RUNS = 5
# How long after closing an issue still counts as "the same finding" (PLAN.md decision 3).
CLOSED_LOOKUP_DAYS = 90

_MARKER_TEMPLATE = "<!-- specfuse:finding fingerprint={fingerprint} -->"
_QUIET_MARKER = "<!-- specfuse:finding-quiet-annotated -->"


def _marker(fingerprint: str) -> str:
    return _MARKER_TEMPLATE.format(fingerprint=fingerprint)


_MARKER_PREFIX = _MARKER_TEMPLATE.split("{fingerprint}")[0]


def has_finding_marker(body: str) -> bool:
    """True iff `body` carries a specfuse finding marker, any fingerprint.

    Narrow public predicate over the private `_marker` convention this
    module already owns, added for FEAT-2026-0045/T01 so a caller (e.g.
    `specfuse.loop.triage.list_untriaged`) can recognise a harvester issue
    without re-typing the marker literal.
    """
    return _MARKER_PREFIX in (body or "")


class TruncatedListingError(RuntimeError):
    """Raised when a listing page is full and carries no fingerprint match.

    A page of exactly ``--limit`` rows with none matching is indistinguishable
    from "no existing issue" without reading the next page. Reporting
    not-found here would reproduce, via pagination, the exact silent-duplicate
    failure this module exists to close off for ``--search``. This module
    refuses rather than guesses; a caller that wants to page on can catch this
    and retry with a raised ``limit``.
    """


MESSAGES_CAP = 50


@dataclass(frozen=True)
class _Meta:
    occurrences: int
    last_seen: float
    first_seen: Optional[float] = None
    messages: Optional[tuple] = None


def _to_int(value: str) -> Optional[int]:
    try:
        number = int(value)
    except ValueError:
        return None
    return number if number >= 0 else None


def _to_epoch(value: str) -> Optional[float]:
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _to_messages(value: str) -> Optional[tuple]:
    ids = value.split(",")
    if not value or any(not i for i in ids):
        return None
    return tuple(ids[-MESSAGES_CAP:])


def _parse_meta(body: str) -> Optional[_Meta]:
    """Read the finding-meta marker; never raises.

    Anything not fully understood is absent: an unreadable required field
    (``occurrences``, ``last_seen``, or either duplicated) yields ``None`` for
    the whole meta, an unreadable optional field (``first_seen``, ``messages``)
    is absent from an otherwise valid meta.
    """
    body = body or ""
    marker_start = body.find("<!-- specfuse:finding-meta ")
    if marker_start == -1:
        return None
    marker_end = body.find("-->", marker_start)
    if marker_end == -1:
        return None
    seen: dict = {}
    dupes: set = set()
    for token in body[marker_start:marker_end].split():
        key, sep, value = token.partition("=")
        if not sep or key not in ("occurrences", "last_seen", "first_seen", "messages"):
            continue
        if key in seen:
            dupes.add(key)
        seen[key] = value
    occurrences = None if "occurrences" in dupes else _to_int(seen.get("occurrences", ""))
    last_seen = None if "last_seen" in dupes else _to_epoch(seen.get("last_seen", ""))
    if occurrences is None or last_seen is None:
        return None
    first_seen = None if "first_seen" in dupes else _to_epoch(seen.get("first_seen", ""))
    messages = None if "messages" in dupes else _to_messages(seen.get("messages", ""))
    return _Meta(occurrences=occurrences, last_seen=last_seen, first_seen=first_seen, messages=messages)


def _render_meta(*, occurrences: int, last_seen: float, first_seen: float, messages: Optional[tuple]) -> str:
    parts = f"occurrences={occurrences} last_seen={last_seen} first_seen={first_seen}"
    if messages:
        parts += " messages=" + ",".join(messages[-MESSAGES_CAP:])
    return f"<!-- specfuse:finding-meta {parts} -->"


def _iso(ts: float) -> str:
    return _utc(ts).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_title(fingerprint: str, artifact: FailureArtifact) -> str:
    return f"[monitor:{fingerprint[:12]}] {artifact.component}: {artifact.failure_class}"


def _render_body(
    fingerprint: str,
    artifact: FailureArtifact,
    *,
    occurrences: int,
    last_seen: float,
    first_seen: Optional[float] = None,
    messages: Optional[tuple] = None,
) -> str:
    """Render an issue body for `artifact`, redacted at egress.

    Artifacts are expected to already be redacted at the adapter boundary
    (T03), but this is a public GitHub surface and the point of egress, so
    the property is re-asserted here rather than trusted from upstream.
    """
    artifact = redact_artifact(artifact)
    first_seen = last_seen if first_seen is None else first_seen
    lines = [
        _marker(fingerprint),
        _render_meta(occurrences=occurrences, last_seen=last_seen, first_seen=first_seen, messages=messages),
        "",
        f"**Component:** {artifact.component}",
        f"**Check type:** {artifact.check_type}",
        f"**Failure class:** {artifact.failure_class}",
        f"**Failure signature:** {artifact.failure_signature}",
    ]
    if artifact.target_coordinates:
        coords = ", ".join(f"{k}={v}" for k, v in sorted(artifact.target_coordinates.items()))
        lines.append(f"**Target:** {coords}")
    lines.append("")
    lines.append(f"**Occurrences:** {occurrences}")
    lines.append(f"**First seen:** {_iso(first_seen)}")
    lines.append(f"**Last seen:** {_iso(last_seen)}")
    lines.append("")
    lines.append("**Observed:**")
    lines.append("```")
    lines.append(artifact.observed_text)
    lines.append("```")
    return "\n".join(lines)


def _utc(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _closed_bound(now: float) -> datetime:
    return _utc(now - CLOSED_LOOKUP_DAYS * 86400)


def _closed_within(issue: dict, bound: datetime) -> bool:
    """True for an open row, or a closed row whose ``closedAt`` is inside the window."""
    if str(issue.get("state", "OPEN")).upper() != "CLOSED":
        return True
    closed_at = issue.get("closedAt")
    if not closed_at:
        return False
    try:
        return datetime.fromisoformat(str(closed_at).replace("Z", "+00:00")) >= bound
    except ValueError:
        return False


def _list_findings(runner: Callable, repo: str, *, limit: int, now: float) -> list:
    bound = _closed_bound(now)
    # One listing: open issues plus issues closed inside the window. The
    # negated ``closed:<`` qualifier is a date filter, not a search over the
    # marker; the client-side ``closedAt`` check below does not rely on it.
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--label", FINDING_LABEL,
            "--state", "all",
            "--search", f"-closed:<{bound.strftime('%Y-%m-%d')}",
            "--limit", str(limit),
            "--json", "number,body,title,state,closedAt",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    try:
        rows = json.loads(result.stdout)
    except ValueError:
        return []
    return [r for r in rows if _closed_within(r, bound)]


def find_finding_issue(
    runner: Callable,
    repo: str,
    fingerprint: str,
    *,
    limit: int = DEFAULT_LIST_LIMIT,
    now: Optional[float] = None,
) -> Optional[dict]:
    """Return the listing row carrying `fingerprint`'s marker, or None.

    Rows are open issues plus issues closed within `CLOSED_LOOKUP_DAYS` of
    `now`; each carries its `state`.

    Filters client-side over `gh issue list`'s output rather than passing the
    marker to `--search` (see the module docstring). Raises
    `TruncatedListingError` when the returned row count equals `limit` and
    none of them matched, since that page is not proof of absence.
    """
    now = time.time() if now is None else now
    issues = _list_findings(runner, repo, limit=limit, now=now)
    marker = _marker(fingerprint)
    for issue in issues:
        if marker in issue.get("body", ""):
            return issue
    if len(issues) >= limit:
        raise TruncatedListingError(
            f"gh issue list returned {len(issues)} rows (--limit {limit}) with no "
            f"match for fingerprint {fingerprint!r}; a full page is not proof that "
            "no existing issue carries this fingerprint"
        )
    return None


def record_finding(
    fingerprint: str,
    artifact: FailureArtifact,
    repo: str,
    *,
    runner: Optional[Callable] = None,
    now: Optional[float] = None,
    limit: int = DEFAULT_LIST_LIMIT,
    throttle_seconds: float = DEFAULT_THROTTLE_SECONDS,
    message_ids: Sequence[str] = (),
) -> str:
    """Find-or-create the one issue for `fingerprint` and return its number.

    On the first sighting, files a new issue carrying the marker and an
    occurrence record of 1. On a repeat sighting, bumps the occurrence record
    — this module's chosen form is a body edit carrying an updated
    `finding-meta` marker, not a comment, so the throttle state is always
    derivable from the same `gh issue list` read this function already does,
    with no second API call needed to inspect comment history. A repeat
    sighting inside `throttle_seconds` of the last recorded update returns the
    existing issue number and makes no further `gh` call at all. A match whose
    issue is closed (inside the lookup window) is reopened with one comment
    instead of being refiled. Never closes an issue.

    A ``dlq`` artifact's message ids (`message_ids`, defaulting to the
    artifact's own) are recorded in the meta's ``messages``. A closed ``dlq``
    issue whose recorded messages already cover every id stays closed with no
    ``gh`` write; an unseen id reopens it with a comment naming that id.
    """
    runner = runner if runner is not None else _default_runner
    now = time.time() if now is None else now
    ids: tuple = ()
    if artifact.check_type == "dlq":
        ids = tuple(dict.fromkeys(i for i in (*message_ids, artifact.message_id) if i))

    existing = find_finding_issue(runner, repo, fingerprint, limit=limit, now=now)

    if existing is None:
        body = _render_body(
            fingerprint, artifact, occurrences=1, last_seen=now, first_seen=now,
            messages=ids or None,
        )
        title = _render_title(fingerprint, artifact)
        result = runner(
            [
                "gh", "issue", "create",
                "--repo", repo,
                "--title", title,
                "--body", body,
                "--label", FINDING_LABEL,
            ],
            check=True,
        )
        return _extract_issue_number(result.stdout)

    number = str(existing["number"])
    meta = _parse_meta(existing.get("body", ""))
    first_seen = (meta.first_seen if meta.first_seen is not None else meta.last_seen) if meta is not None else now
    messages = meta.messages if meta is not None else None
    unseen = tuple(i for i in ids if i not in (messages or ()))
    if unseen:
        messages = (*(messages or ()), *unseen)
    if str(existing.get("state", "OPEN")).upper() == "CLOSED":
        if ids and not unseen:
            return number
        occurrences = meta.occurrences + 1 if meta is not None else 1
        runner(["gh", "issue", "reopen", number, "--repo", repo], check=True)
        runner(
            [
                "gh", "issue", "comment", number,
                "--repo", repo,
                "--body",
                f"Recurred after close: occurrence {occurrences}, "
                f"first seen {_iso(first_seen)}, last seen {_iso(now)}."
                + (f" New dead-lettered message: {', '.join(unseen)}." if unseen else ""),
            ],
            check=True,
        )
        runner(
            [
                "gh", "issue", "edit", number, "--repo", repo, "--body",
                _render_body(
                    fingerprint, artifact, occurrences=occurrences, last_seen=now,
                    first_seen=first_seen, messages=messages,
                ),
            ],
            check=True,
        )
        return number
    if meta is not None and (now - meta.last_seen) < throttle_seconds:
        return number

    occurrences = meta.occurrences + 1 if meta is not None else 1
    new_body = _render_body(
        fingerprint, artifact, occurrences=occurrences, last_seen=now,
        first_seen=first_seen, messages=messages,
    )
    runner(
        ["gh", "issue", "edit", number, "--repo", repo, "--body", new_body],
        check=True,
    )
    return number


def annotate_if_quiet(
    fingerprint: str,
    repo: str,
    runs_since_last_seen: int,
    *,
    quiet_after_runs: int = DEFAULT_QUIET_AFTER_RUNS,
    runner: Optional[Callable] = None,
    limit: int = DEFAULT_LIST_LIMIT,
) -> Optional[str]:
    """Annotate a fingerprint's issue as a close candidate once it has been
    absent for `quiet_after_runs` consecutive runs. Annotates and stops —
    never closes, reopens, or otherwise transitions the issue's state.

    Idempotent per crossing: the annotation comment is posted once, guarded by
    `_QUIET_MARKER` recorded into the issue body, so a caller invoking this on
    every run after the threshold does not re-annotate on every call.
    """
    if runs_since_last_seen < quiet_after_runs:
        return None

    runner = runner if runner is not None else _default_runner
    existing = find_finding_issue(runner, repo, fingerprint, limit=limit)
    if existing is None:
        return None

    number = str(existing["number"])
    body = existing.get("body", "")
    if _QUIET_MARKER in body:
        return number

    runner(
        [
            "gh", "issue", "comment", number,
            "--repo", repo,
            "--body",
            f"Quiet for {runs_since_last_seen} runs — candidate for close. "
            "This annotation does not close the issue; a human decides.",
        ],
        check=True,
    )
    runner(
        [
            "gh", "issue", "edit", number,
            "--repo", repo,
            "--body", body + f"\n\n{_QUIET_MARKER}\n",
        ],
        check=True,
    )
    return number
