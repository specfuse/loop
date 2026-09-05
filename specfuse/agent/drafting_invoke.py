# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Build a headless `/draft-feature` invocation from a `draft_ready` answer
gate result, and read that session's result back (FEAT-2026-0050/T06).

Modelled on `specfuse/agent/triage_invoke.py`, `specfuse/agent/diagnose_invoke.py`,
and `specfuse/monitor/autofix_invoke.py`'s shared shape: `build_invocation`
returns the argv and prompt for one headless session, this module runs
nothing itself, and `read_result` reads back what the session produced.

`build_invocation` takes T03's `drafting_answers.AnswerGateResult` as-is --
it re-parses no reply text and adds no second answer parser (T04 owns that
side; `GATE-02-REVIEW.md` § Runtime probe is explicit that no real operator
reply has ever been observed, so this unit works only from the already-bound
`answers`/`assumptions` T03 produced). D1's rule --  a `fallback` result
means the agent may not draft -- is enforced mechanically by raising rather
than building a prompt from a partial answer set.

`read_result` delegates to `specfuse.loop.loop.parse_result_block`, the same
parser the driver itself uses to read a work-unit session's RESULT block,
rather than restating `.specfuse/rules/result-contract.md`'s shape here.
"""

from __future__ import annotations

from specfuse.agent.drafting_answers import AnswerGateResult, OUTCOME_FALLBACK
from specfuse.agent.invoke import build_claude_argv
from specfuse.loop.loop import parse_result_block

__all__ = ("DraftingInvokeError", "build_invocation", "read_result")

_DEFAULT_WORKING_DIR = "."


class DraftingInvokeError(Exception):
    """Raised when a gate result cannot be turned into a drafting session,
    or a completed session's RESULT block cannot be read as a drafted
    folder."""


def build_invocation(
    feature_id: str,
    gate_result: AnswerGateResult,
    working_dir: str = _DEFAULT_WORKING_DIR,
    model: str = "sonnet",
    effort: str = "medium",
):
    """Build argv and prompt text for a headless `/draft-feature` session
    against one `draft_ready` answer gate result.

    Returns a `(argv, prompt)` tuple; runs nothing. Raises
    `DraftingInvokeError` if `gate_result.outcome` is `OUTCOME_FALLBACK` --
    D1's rule that a fallback result blocks drafting outright, enforced here
    rather than left to the caller to remember.
    """
    if gate_result.outcome == OUTCOME_FALLBACK:
        raise DraftingInvokeError(
            f"{feature_id}: answer gate outcome is fallback; the agent may "
            "not draft from a partial answer set"
        )

    argv = build_claude_argv(model, effort)

    answer_lines = "\n".join(
        f"- {question_id}: {answer}"
        for question_id, answer in gate_result.answers.items()
    )
    if gate_result.assumptions:
        assumption_lines = "\n".join(
            f"- {assumption.question_id}: assumed {assumption.assumed_value!r} "
            "(the operator left this question unanswered; record it as an "
            "explicit assumption)"
            for assumption in gate_result.assumptions
        )
    else:
        assumption_lines = "(none -- every question was answered)"

    prompt = (
        f"/draft-feature {feature_id}\n\n"
        f"Working directory: {working_dir}\n\n"
        "The interview's answer gate has already run and returned "
        "draft_ready. Every question's effective answer -- given or "
        f"defaulted -- follows:\n{answer_lines}\n\n"
        "Of those, the following were defaulted to the interview's own "
        "recommendation because the operator left them unanswered. Record "
        "each one, verbatim, as an explicit assumption in the drafted "
        f"PLAN.md:\n{assumption_lines}\n\n"
        "Draft the feature's gate skeleton and gate 1 work units from these "
        "answers. Do not re-ask any question named above."
    )
    return argv, prompt


def read_result(result_text: str) -> dict:
    """Read a completed `/draft-feature` session's RESULT block.

    Raises `DraftingInvokeError` if the block is missing, malformed, or
    carries any `status` other than `complete` -- a `blocked` drafting
    session must not be read as a drafted folder.
    """
    parsed = parse_result_block(result_text or "")
    if not parsed:
        raise DraftingInvokeError(
            "drafting session produced no parseable RESULT block"
        )
    status = parsed.get("status")
    if status != "complete":
        raise DraftingInvokeError(
            f"drafting session did not complete (status: {status!r}); a "
            "non-complete session must not be read as a drafted folder"
        )
    return parsed
