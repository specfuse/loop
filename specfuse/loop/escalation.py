# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Escalation issue contract: label vocabulary, renderer, validator.

The body shape follows ``.specfuse/rules/operator-escalation.md`` — the six
parts, in order, plus a numbered-answers section and a correlation marker
that lets a caller find an existing issue instead of filing a duplicate.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Callable, Optional

NEEDS_HUMAN_LABEL = "needs-human"

#: Empty by default (#1762). A username that is valid on no repository is
#: not a safe default -- it failed every `gh issue create` on every repo
#: that had not happened to create that user. Callers pass the operator's
#: own `escalation.assignee` from agent-policy.yml; empty means unassigned.
DEFAULT_ASSIGNEE = ""

CATEGORY_LABELS = frozenset(
    {
        "gate-review",
        "blocked-wu",
        "triage-question",
        "drafting-needed",
        "merge-approval",
    }
)

# The six part names, verbatim from operator-escalation.md's "six parts" list,
# in order. Both the renderer and the validator key off this sequence.
_PART_HEADINGS = (
    "What has been done so far",
    "What this issue is about",
    "What decision is needed, and why",
    "Why it did not, or could not, close automatically",
    "Options, each with pros and cons",
    "A recommendation",
)

_NUMBERED_ANSWERS_HEADING = "Reply with a number"

_CORRELATION_MARKER_TEMPLATE = "<!-- specfuse:escalation id={correlation_id} -->"


def _correlation_marker(correlation_id: str) -> str:
    return _CORRELATION_MARKER_TEMPLATE.format(correlation_id=correlation_id)


def render_escalation_body(
    correlation_id: str,
    *,
    category: str,
    done_so_far: str,
    issue_summary: str,
    decision_needed: str,
    why_not_auto: str,
    options: list[tuple[str, str, str]],
    recommendation: str,
) -> str:
    """Render a conforming escalation issue body.

    ``options`` is a list of ``(label, pros, cons)`` tuples; each becomes one
    numbered option in both the options part and the numbered-answers section.
    """
    if category not in CATEGORY_LABELS:
        raise ValueError(f"unknown escalation category: {category!r}")
    if len(options) < 2:
        raise ValueError("render_escalation_body requires at least two options")

    lines: list[str] = [_correlation_marker(correlation_id), ""]

    lines.append(f"## {_PART_HEADINGS[0]}")
    lines.append(done_so_far)
    lines.append("")

    lines.append(f"## {_PART_HEADINGS[1]}")
    lines.append(issue_summary)
    lines.append("")

    lines.append(f"## {_PART_HEADINGS[2]}")
    lines.append(decision_needed)
    lines.append("")

    lines.append(f"## {_PART_HEADINGS[3]}")
    lines.append(why_not_auto)
    lines.append("")

    lines.append(f"## {_PART_HEADINGS[4]}")
    for idx, (label, pros, cons) in enumerate(options, start=1):
        lines.append(f"{idx}. **{label}** — pros: {pros}; cons: {cons}")
    lines.append("")

    lines.append(f"## {_PART_HEADINGS[5]}")
    lines.append(recommendation)
    lines.append("")

    lines.append(f"## {_NUMBERED_ANSWERS_HEADING}")
    lines.append("Reply with the number of your choice, or prose if none fit:")
    for idx, (label, _pros, _cons) in enumerate(options, start=1):
        lines.append(f"{idx}. {label}")
    lines.append("")

    return "\n".join(lines)


def validate_escalation_body(text: str) -> list[str]:
    """Return a list of findings naming what a body is missing.

    Empty list means the body conforms: all six parts, the numbered-answers
    section, and the correlation marker are present.
    """
    findings: list[str] = []

    for heading in _PART_HEADINGS:
        if heading not in text:
            findings.append(f"missing required part: {heading!r}")

    if "reply" not in text.lower():
        findings.append("missing numbered-answers section: no 'reply' instruction found")
    elif not _has_two_numbered_options(text):
        findings.append(
            "missing numbered-answers section: fewer than two numbered options found"
        )

    if "<!-- specfuse:escalation id=" not in text:
        findings.append("missing correlation marker: no '<!-- specfuse:escalation id=... -->' found")

    return findings


def _has_two_numbered_options(text: str) -> bool:
    found = set()
    for line in text.splitlines():
        stripped = line.strip()
        for n in (1, 2, 3, 4, 5, 6, 7, 8, 9):
            prefix = f"{n}."
            if stripped.startswith(prefix):
                found.add(n)
                break
    return len(found) >= 2


def _default_runner(args: list, check: bool = True):
    """Shell out to gh with the given argument list. Not called in tests."""
    return subprocess.run(args, check=check, capture_output=True, text=True)


def _find_existing_issue(
    runner: Callable, repo: str, correlation_id: str
) -> Optional[str]:
    """Search for an open needs-human issue already carrying this marker."""
    marker = _correlation_marker(correlation_id)
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--label", NEEDS_HUMAN_LABEL,
            "--state", "open",
            "--search", marker,
            "--json", "number,body",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        issues = json.loads(result.stdout)
    except ValueError:
        return None
    for issue in issues:
        if marker in issue.get("body", ""):
            return str(issue["number"])
    return None


def _extract_issue_number(stdout: str) -> str:
    match = re.search(r"/issues/(\d+)", stdout)
    if match:
        return match.group(1)
    return stdout.strip()


def emit_escalation(
    correlation_id: str,
    *,
    category: str,
    repo: str,
    done_so_far: str,
    issue_summary: str,
    decision_needed: str,
    why_not_auto: str,
    options: list[tuple[str, str, str]],
    recommendation: str,
    assignee: str = DEFAULT_ASSIGNEE,
    runner: Optional[Callable] = None,
) -> str:
    """File a needs-human GitHub issue for an escalating unit.

    Idempotent: searches for an open issue carrying the ``needs-human`` label
    and this correlation ID's marker before creating; a second call for the
    same ``correlation_id`` returns the existing issue's identifier instead
    of filing a duplicate. Mirrors the find-then-create seam used by
    ``GitHubBackend.on_feature_complete`` in ``gh_backend.py``.
    """
    runner = runner if runner is not None else _default_runner

    existing = _find_existing_issue(runner, repo, correlation_id)
    if existing is not None:
        return existing

    body = render_escalation_body(
        correlation_id,
        category=category,
        done_so_far=done_so_far,
        issue_summary=issue_summary,
        decision_needed=decision_needed,
        why_not_auto=why_not_auto,
        options=options,
        recommendation=recommendation,
    )

    argv = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", f"[{correlation_id}] {issue_summary}",
        "--body", body,
        "--label", NEEDS_HUMAN_LABEL,
        "--label", category,
    ]
    # Assign only when an assignee is actually configured (#1762). The old
    # default was the literal `specfuse-operator`, a placeholder assignable on
    # no repository, so `gh issue create` exited 1 on that flag and the whole
    # escalation was lost -- the caller recorded "escalated" and the human
    # inbox stayed empty. An unassigned needs-human issue is strictly better
    # than an unfiled one. An empty value must OMIT the flag rather than pass
    # `--assignee ""`, which fails the same way.
    if assignee and assignee.strip():
        argv += ["--assignee", assignee.strip()]

    result = runner(argv, check=True)
    return _extract_issue_number(result.stdout)
