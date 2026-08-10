#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Re-ping an unanswered escalation once, then park it (FEAT-2026-0047/T03).

Depends on ``escalation.py`` (T02's ``NEEDS_HUMAN_LABEL``) and ``notify.py``
(``post_notification``). "Exactly once" is the whole rule: unbounded
re-pinging trains the operator to mute the channel, which is worse than no
channel at all — see the roadmap row this WU implements.

The re-ping count is never a stored counter. The runner this module talks to
is a GitHub Actions container today and may be an AKS CronJob tomorrow —
either way it is ephemeral, so any disk-backed "already re-pinged" flag
disappears silently between runs and every sweep re-pings every issue
forever. Instead, following the same shape ``monitor/autofix_state.py`` and
``monitor/issues.py`` already use, the state lives as an HTML-comment marker
posted as an issue *comment* and is re-derived from the issue's comment list
on every call.

Parked is a label, not a close: ``PARKED_LABEL`` is added alongside
``NEEDS_HUMAN_LABEL``, which is never removed, and no path in this module
ever closes an issue — a parked escalation is still awaiting a human.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Callable, Optional

from . import agent_policy
from .escalation import NEEDS_HUMAN_LABEL
from .notify import post_notification

__all__ = ("sla_sweep", "PARKED_LABEL")

PARKED_LABEL = "escalation-parked"

_DEFAULT_SLA_HOURS = 24

_REPING_MARKER_TEMPLATE = "<!-- specfuse:sla-repinged at={at} -->"
_REPING_MARKER_RE = re.compile(
    r"<!-- specfuse:sla-repinged at=(?P<at>[0-9]+(?:\.[0-9]+)?) -->"
)


def _reping_marker(at: str) -> str:
    return _REPING_MARKER_TEMPLATE.format(at=at)


def _has_reping_marker(comments: list) -> bool:
    for comment in comments:
        body = comment.get("body", "") if isinstance(comment, dict) else ""
        if _REPING_MARKER_RE.search(body):
            return True
    return False


def _resolve_sla_hours(policy_path: Optional[str]) -> int:
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return _DEFAULT_SLA_HOURS
    escalation = policy.get("escalation") if isinstance(policy, dict) else None
    if not isinstance(escalation, dict):
        return _DEFAULT_SLA_HOURS
    sla_hours = escalation.get("sla_hours")
    if not isinstance(sla_hours, int) or isinstance(sla_hours, bool) or sla_hours <= 0:
        return _DEFAULT_SLA_HOURS
    return sla_hours


def _parse_created_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _list_open_needs_human_issues(runner: Callable, repo: str) -> list:
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--label", NEEDS_HUMAN_LABEL,
            "--state", "open",
            "--json", "number,createdAt,comments",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []


def sla_sweep(
    runner: Callable,
    repo: str,
    *,
    now: datetime,
    policy_path: Optional[str] = None,
    poster: Optional[Callable] = None,
) -> list:
    """Re-ping each open needs-human issue past the SLA window, once.

    Returns one record ``{"number": ..., "action": ...}`` per issue acted
    on — ``"repinged"`` or ``"parked"`` — for issues still inside the
    window. ``now`` is injected so the sweep is deterministic; this module
    calls no clock directly. Every GitHub read/write goes through *runner*.
    """
    sla_hours = _resolve_sla_hours(policy_path)

    records: list = []
    for issue in _list_open_needs_human_issues(runner, repo):
        number = str(issue["number"])
        created_at = _parse_created_at(issue["createdAt"])
        elapsed_hours = (now - created_at).total_seconds() / 3600.0
        if elapsed_hours <= sla_hours:
            continue

        comments = issue.get("comments") or []
        if _has_reping_marker(comments):
            runner(
                [
                    "gh", "issue", "edit", number,
                    "--repo", repo,
                    "--add-label", PARKED_LABEL,
                ],
                check=True,
            )
            records.append({"number": number, "action": "parked"})
            continue

        message = f"[sla-reping] issue #{number} unanswered past the SLA window"
        post_notification(message, policy_path=policy_path, poster=poster)
        runner(
            [
                "gh", "issue", "comment", number,
                "--repo", repo,
                "--body", _reping_marker(str(now.timestamp())),
            ],
            check=True,
        )
        records.append({"number": number, "action": "repinged"})

    return records
