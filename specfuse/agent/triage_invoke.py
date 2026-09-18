# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Build a headless triage-classification invocation and classify its result
(FEAT-2026-0049/T07).

Modelled on `specfuse/monitor/autofix_invoke.py`'s shape: `build_invocation`
returns the argv and prompt for one headless classification session, this
module runs nothing itself, and `classify_result` reads back what the
session produced.

`classify_result` reuses `specfuse.loop.triage.parse_marker` rather than a
second regex -- the classifier is asked to answer in exactly the marker
format `render_marker` produces, so the same parser that reads a triaged
issue's body reads a classification session's output. The category named is
returned as-is, unvalidated against `triage.CATEGORIES` -- that check
belongs to the caller (`specfuse/agent/providers/triage.py`), which needs
the raw offending value to name in an escalation.
"""

from __future__ import annotations

from typing import Optional

from specfuse.agent.invoke import build_claude_argv
from specfuse.loop.triage import CATEGORIES, parse_marker, parse_marker_fields

_DEFAULT_WORKING_DIR = "."

_BASE_MARKER_INSTRUCTION = (
    "Respond with the triage marker exactly as "
    "`specfuse.loop.triage.render_marker` would produce it -- one line, "
    "nothing else needed in your final output: "
    "`<!-- specfuse:triage category=<category> confidence=<high|low> -->`. "
    "Name confidence `high` only when the issue's language leaves no "
    "reasonable ambiguity about which category applies, `low` "
    "otherwise. Do not run `gh issue edit` yourself; the caller applies "
    "the decision this session produces."
)


def build_invocation(
    issue_number: int,
    title: str,
    body: str,
    repo: str,
    working_dir: str = _DEFAULT_WORKING_DIR,
    model: str = "sonnet",
    effort: str = "medium",
    rubric: Optional[dict] = None,
):
    """Build argv and prompt text for a headless triage-classification
    session against one issue. Returns a `(argv, prompt)` tuple; runs
    nothing.

    `rubric` is the repository's severity rubric as `read_severity_rubric`
    returns it -- `{severity_value: description}`. An empty (or absent)
    rubric is the degradation path (label listing failed) and the prompt is
    byte-identical to the one built with no severity assessment at all. A
    non-empty rubric is folded into the same single prompt -- no second
    session -- and the marker instruction grows a third `severity=` field.
    The prompt is built from `rubric`'s own mapping alone; it holds no copy
    of any shipped default definitions.
    """
    argv = build_claude_argv(model, effort)
    if rubric:
        severity_block = "\n".join(
            f"- {value}: {description}" for value, description in rubric.items()
        )
        marker_instruction = (
            "Respond with the triage marker exactly as "
            "`specfuse.loop.triage.render_marker` would produce it -- one line, "
            "nothing else needed in your final output: "
            "`<!-- specfuse:triage category=<category> confidence=<high|low> "
            "severity=<value> -->`. Name confidence `high` only when the "
            "issue's language leaves no reasonable ambiguity about which "
            "category applies, `low` otherwise. Name `severity` as exactly "
            "one of the values below, matched against the definition given "
            "beside it, and only when confidence is `high`:\n"
            f"{severity_block}\n\n"
            "Do not run `gh issue edit` yourself; the caller applies the "
            "decision this session produces."
        )
    else:
        marker_instruction = _BASE_MARKER_INSTRUCTION
    prompt = (
        f"Repository: {repo}\n"
        f"Working directory: {working_dir}\n"
        f"Issue number: {issue_number}\n"
        f"Issue title: {title}\n\n"
        f"Issue body:\n{body}\n\n"
        "Classify this issue into exactly one of the categories: "
        f"{', '.join(CATEGORIES)}.\n\n"
        f"{marker_instruction}"
    )
    return argv, prompt


def classify_result(result_text: str) -> Optional[tuple]:
    """Return the `(category, confidence)` pair a classification session's
    output names, or `None` if the output carries no parseable triage
    marker. Fails closed to `None` on empty output -- never guesses a
    category."""
    if not result_text or not result_text.strip():
        return None
    return parse_marker(result_text)


def classify_severity(result_text: str, rubric: dict) -> Optional[str]:
    """Return the severity value a classification session's marker named, or
    `None` unless it is one of `rubric`'s own keys and the marker's
    `confidence` is `high`.

    Fails closed on every other shape: no marker, no `severity` field, an
    empty value, a value outside `rubric`, or a `confidence` that is not
    `high` -- nothing here is defaulted or inferred, so a `min_severity`
    floor keeps failing closed exactly as it does without a severity at
    all.
    """
    if not result_text or not result_text.strip():
        return None
    fields = parse_marker_fields(result_text)
    if fields is None:
        return None
    if fields.get("confidence") != "high":
        return None
    severity = fields.get("severity")
    if not severity or severity not in rubric:
        return None
    return severity
