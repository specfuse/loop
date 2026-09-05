# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The answered-escalation provider (FEAT-2026-0049/T08).

Reads escalation issues -- open, `NEEDS_HUMAN_LABEL`-carrying, marked with
`specfuse.loop.escalation`'s correlation marker -- and looks for a comment
that picks one of the numbered options `render_escalation_body` writes.
Every shape this module parses against (the label, the marker template, the
numbered-answers heading) is read from `specfuse.loop.escalation`'s own
constants and renderer output, never retyped here.

This provider does not carry out the chosen option -- see the WU's note on
`GATE-02-REVIEW.md`'s OQ-2. It records the answer as one acknowledgment
comment, naming the option and the correlation id, and leaves
`NEEDS_HUMAN_LABEL` in place: the label stays until whichever future
provider executes the option removes it. The acknowledgment itself is a
second HTML-comment marker posted as a comment, following the same
re-derived-from-comments idiom `notify_sla`'s re-ping marker uses, so a
second pass over an already-acknowledged issue writes nothing.

Comments are not part of `AgentSnapshot` (`state.py`'s `_read_issues`
requests `body` only to feed triage-marker parsing and keeps none of it on
`IssueSummary`) -- this module reads an issue's body and comments itself,
through the injected runner, the same read-only `gh issue view --json
body,comments` shape `monitor/autofix_run.py`'s `_read_finding_issue` uses.
"""

from __future__ import annotations

import json
import re
from typing import Callable, Optional, Sequence

from specfuse.agent.run import (
    KIND_ESCALATION_ANSWER,
    STATUS_COMPLETED,
    ActionItem,
    ActionOutcome,
    _default_runner,
)
from specfuse.agent.state import AgentSnapshot
from specfuse.loop.escalation import (
    NEEDS_HUMAN_LABEL,
    _CORRELATION_MARKER_TEMPLATE,
    _NUMBERED_ANSWERS_HEADING,
)

_ITEM_ID_PREFIX = "escalation-answer-"

_ACK_MARKER_TEMPLATE = "<!-- specfuse:answered-escalation id={correlation_id} -->"
_ACK_MARKER_RE = re.compile(
    re.escape(_ACK_MARKER_TEMPLATE).replace(
        re.escape("{correlation_id}"), r"(?P<correlation_id>\S+)"
    )
)

_MARKER_RE = re.compile(
    re.escape(_CORRELATION_MARKER_TEMPLATE).replace(
        re.escape("{correlation_id}"), r"(?P<correlation_id>\S+)"
    )
)

_OPTION_LINE_RE = re.compile(r"^(?P<num>\d+)\.\s*(?P<label>.+)$")
_LEADING_NUMBER_RE = re.compile(r"^\s*(?P<num>\d+)\b")


def _ack_marker(correlation_id: str) -> str:
    return _ACK_MARKER_TEMPLATE.format(correlation_id=correlation_id)


def _has_ack_marker(comments: list) -> bool:
    for comment in comments or []:
        body = comment.get("body", "") if isinstance(comment, dict) else ""
        if _ACK_MARKER_RE.search(body):
            return True
    return False


def _correlation_id(body: str) -> Optional[str]:
    match = _MARKER_RE.search(body or "")
    return match.group("correlation_id") if match else None


def _numbered_answers_section(body: str) -> str:
    heading = f"## {_NUMBERED_ANSWERS_HEADING}"
    idx = (body or "").find(heading)
    if idx == -1:
        return ""
    rest = body[idx:]
    next_heading = rest.find("\n## ", 1)
    return rest if next_heading == -1 else rest[:next_heading]


def _parse_options(body: str) -> dict:
    options = {}
    for line in _numbered_answers_section(body).splitlines():
        match = _OPTION_LINE_RE.match(line.strip())
        if match:
            options[int(match.group("num"))] = match.group("label").strip()
    return options


def _selected_option(comments: list, options: dict):
    for comment in reversed(comments or []):
        body = comment.get("body", "") if isinstance(comment, dict) else ""
        if _ACK_MARKER_RE.search(body):
            continue
        match = _LEADING_NUMBER_RE.match(body.strip())
        if not match:
            continue
        num = int(match.group("num"))
        if num in options:
            return num, options[num]
    return None


def _read_issue(runner: Callable, repo: str, number: int) -> dict:
    result = runner(
        [
            "gh", "issue", "view", str(number),
            "--repo", repo,
            "--json", "body,comments",
        ],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return {}
    try:
        parsed = json.loads(result.stdout)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


class AnsweredEscalationProvider:
    """`ActionProvider` over answered-but-unacted escalation issues."""

    def __init__(self, *, repo: str, runner: Callable = _default_runner):
        self._repo = repo
        self._runner = runner
        self._rows: dict = {}

    def advertise(self, snapshot: AgentSnapshot) -> Sequence[ActionItem]:
        self._rows = {}
        items = []
        for issue in snapshot.issues:
            if NEEDS_HUMAN_LABEL not in issue.labels:
                continue

            raw = _read_issue(self._runner, self._repo, issue.number)
            body = raw.get("body") or ""
            comments = raw.get("comments") or []

            correlation_id = _correlation_id(body)
            if correlation_id is None:
                continue
            if _has_ack_marker(comments):
                continue

            options = _parse_options(body)
            if len(options) < 2:
                continue

            selected = _selected_option(comments, options)
            if selected is None:
                continue
            option_number, option_label = selected

            item_id = f"{_ITEM_ID_PREFIX}{issue.number}"
            self._rows[item_id] = {
                "number": issue.number,
                "correlation_id": correlation_id,
                "option_number": option_number,
                "option_label": option_label,
            }
            items.append(
                ActionItem(
                    item_id=item_id,
                    kind=KIND_ESCALATION_ANSWER,
                    summary=issue.title,
                    queue_key=None,
                )
            )
        return items

    def execute(self, item: ActionItem) -> ActionOutcome:
        row = self._rows.get(item.item_id)
        if row is None:
            return ActionOutcome(status=STATUS_COMPLETED, detail="nothing to acknowledge")

        number = row["number"]
        correlation_id = row["correlation_id"]

        raw = _read_issue(self._runner, self._repo, number)
        if _has_ack_marker(raw.get("comments") or []):
            return ActionOutcome(status=STATUS_COMPLETED, detail="already acknowledged")

        ack_body = "\n".join(
            [
                f"Recorded option {row['option_number']} -- "
                f"{row['option_label']} -- for {correlation_id}.",
                _ack_marker(correlation_id),
            ]
        )
        self._runner(
            [
                "gh", "issue", "comment", str(number),
                "--repo", self._repo,
                "--body", ack_body,
            ],
            check=False,
        )
        return ActionOutcome(
            status=STATUS_COMPLETED,
            detail=f"issue #{number} answer acknowledged: option {row['option_number']}",
            # This provider never dispatches a `claude` session -- it only
            # posts an acknowledgment comment -- so there is never usage to
            # report. Explicit rather than the implicit `spend=0` default,
            # so a reader auditing every provider that could spend tokens
            # can see this one considered it and found nothing to report.
            spend=0,
        )

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
