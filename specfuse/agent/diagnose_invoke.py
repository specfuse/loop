# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Build a headless finding-diagnosis invocation and read its result
(FEAT-2026-0049/T10).

Modelled on `specfuse/monitor/autofix_invoke.py`'s shape and on
`specfuse/agent/triage_invoke.py`, which T07 built the same way for the same
reason: `build_invocation` returns the argv and prompt for one headless
analysis session, this module runs nothing itself, and `read_result` reads
back what the session produced.

The prompt asks for exactly the five fields
`specfuse.monitor.diagnose_cli._REQUIRED_FIELDS` names, as one JSON object,
and nothing else -- the field list is `diagnose_cli`'s, not re-derived here.
`read_result` delegates entirely to
`specfuse.monitor.diagnose_cli.render_headless`: this module holds no
parsing logic of its own and raises `AnalysisParseError` -- the same
exception `render_headless` raises -- on anything unparseable, empty output
included. It never returns a rendered body built from a defaulted field.
"""

from __future__ import annotations

from specfuse.agent.invoke import build_claude_argv
from specfuse.monitor.diagnose_cli import AnalysisParseError, render_headless
from specfuse.monitor.diagnosis import FIX_SCOPES

__all__ = ("AnalysisParseError", "build_invocation", "read_result")

_DEFAULT_WORKING_DIR = "."

_REQUIRED_FIELDS = ("root_cause", "evidence", "candidate_fix", "confidence", "fix_scope")


def build_invocation(
    issue_number: int,
    title: str,
    body: str,
    repo: str,
    working_dir: str = _DEFAULT_WORKING_DIR,
    model: str = "sonnet",
    effort: str = "medium",
):
    """Build argv and prompt text for a headless finding-analysis session
    against one `monitoring-finding` issue. Returns a `(argv, prompt)`
    tuple; runs nothing."""
    argv = build_claude_argv(model, effort)
    prompt = (
        f"Repository: {repo}\n"
        f"Working directory: {working_dir}\n"
        f"Finding issue number: {issue_number}\n"
        f"Finding issue title: {title}\n\n"
        f"Finding issue body:\n{body}\n\n"
        "Read the finding above and the component source it implicates, "
        "and produce a root-cause diagnosis. Respond with exactly one JSON "
        f"object and nothing else, carrying exactly these fields: "
        f"{', '.join(_REQUIRED_FIELDS)}.\n\n"
        "- root_cause: the specific mechanism, tied to the code you read. "
        "If the evidence does not clearly support one mechanism over "
        "another, say so here rather than picking one.\n"
        "- evidence: the trail -- what in the finding and what in the "
        "source led to the root-cause claim. Concrete: file, function, the "
        "specific line of reasoning.\n"
        "- candidate_fix: the shape of a plausible fix, not a diff. If no "
        "evidence supports a specific fix, say what additional evidence "
        "would be needed instead of proposing one anyway.\n"
        "- confidence: a number in [0.0, 1.0] reflecting how well the "
        "evidence trail actually supports the root-cause claim. Weak or "
        "partial evidence gets a low number.\n"
        f"- fix_scope: exactly one of {', '.join(FIX_SCOPES)} -- do not "
        "invent or default this value; if none plainly fits, say so in "
        "candidate_fix and still pick the closest of the three.\n\n"
        "Do not post anything and do not run `gh issue comment` yourself; "
        "the caller renders and posts the diagnosis this session produces."
    )
    return argv, prompt


def read_result(result_text: str) -> str:
    """Render a diagnosis comment body from a completed analysis session's
    result text.

    Delegates entirely to `diagnose_cli.render_headless` -- raises
    `AnalysisParseError` on invalid JSON, a missing required field, a
    non-numeric `confidence`, or a `fix_scope` outside `FIX_SCOPES`. Empty
    output is not special-cased: it is simply invalid JSON, and
    `render_headless` raises for it the same as for any other malformed
    input.
    """
    return render_headless(result_text or "")
