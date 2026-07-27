# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Escalation issue contract: label vocabulary, renderer, validator.

The body shape follows ``.specfuse/rules/operator-escalation.md`` — the six
parts, in order, plus a numbered-answers section and a correlation marker
that lets a caller find an existing issue instead of filing a duplicate.
"""

from __future__ import annotations

NEEDS_HUMAN_LABEL = "needs-human"

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
