#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Post a one-liner and a link when an escalation issue is filed
(FEAT-2026-0047/T02).

`emit_escalation` in `escalation.py` is the system of record: it files the
GitHub issue and owns idempotency. This module is a separate, callable
notification step a caller invokes *after* `emit_escalation` returns — it
never wraps or patches `emit_escalation`, so a failure here can never affect
whether an escalation is filed.

The message is a one-liner and a link, nothing else. The channel is a
loudspeaker; the audit trail is the issue itself. Reproducing the issue body
in chat invites people to answer there, where the answer is lost.
"""

from __future__ import annotations

from typing import Callable, Optional

from .escalation import CATEGORY_LABELS, NEEDS_HUMAN_LABEL
from .notify import post_notification

__all__ = ("notify_new_escalation",)


def _issue_url(repo: str, issue_number: str) -> str:
    return f"https://github.com/{repo}/issues/{issue_number}"


def notify_new_escalation(
    correlation_id: str,
    *,
    repo: str,
    issue_number: str,
    category: str,
    summary: str,
    policy_path: Optional[str] = None,
    poster: Optional[Callable] = None,
) -> bool:
    """Post a one-line notification for a newly filed escalation issue.

    Returns `False` (never raises) when no webhook is configured or the
    poster fails — a failed notification can never undo or block the
    escalation it announces. Raises `ValueError` for an unknown *category*,
    matching `render_escalation_body`, before any post is attempted.
    """
    if category not in CATEGORY_LABELS:
        raise ValueError(f"unknown escalation category: {category!r}")

    summary_line = summary.splitlines()[0].strip() if summary else ""
    url = _issue_url(repo, issue_number)
    message = f"[{NEEDS_HUMAN_LABEL}:{category}] {summary_line} — {url}"

    return post_notification(message, policy_path=policy_path, poster=poster)
