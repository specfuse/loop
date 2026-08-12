# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Build a headless `fix-bug` invocation and classify its result (FEAT-2026-0042/T04).

Public contract:

- `OUTCOMES` -- the closed tuple of the three outcome strings the `## Headless
  mode` section of `plugins/specfuse/skills/fix-bug/SKILL.md` defines:
  `refused`, `could_not_proceed`, `completed`. No fourth member.
- `build_invocation(...)` -- given an issue number, a repository, and a working
  directory, returns the argv and prompt text for a headless `fix-bug` session.
  It returns them; it does not run them.
- `classify_outcome(...)` -- given a completed session's result text, returns
  exactly one member of `OUTCOMES`. Fails closed to `could_not_proceed` on
  anything it cannot classify.

This module runs nothing itself: no process spawn, no network, no `gh`, no
`claude` launch. The caller (`specfuse/monitor/autofix_run.py`, T05) is the
only place that executes the argv this module builds.
"""

OUTCOMES = ("refused", "could_not_proceed", "completed")

_SAFETY_FLOOR = (
    "Safety floor (binding, not a judgement call): you must NOT merge a pull "
    "request, enable auto-merge, or push to a protected branch under any "
    "circumstance. The ceiling for this run is an unwanted pull request on a "
    "branch -- nothing more."
)


def build_invocation(issue_number, repo, working_dir, model="sonnet", effort="medium"):
    """Build argv and prompt text for a headless `fix-bug` session.

    Returns a `(argv, prompt)` tuple. `argv` follows the loop driver's own
    dispatch shape (`claude -p` with an explicit model and effort); the prompt
    is meant to be piped to the session on stdin, not appended to argv.
    """
    argv = ["claude", "-p", "--model", model, "--effort", effort]
    prompt = (
        f"/fix-bug {issue_number}\n\n"
        f"Repository: {repo}\n"
        f"Working directory: {working_dir}\n"
        f"Issue number: {issue_number}\n\n"
        "Run the fix-bug skill in headless mode (mode: headless) against the "
        f"issue named above. {_SAFETY_FLOOR}\n\n"
        "Resolve to exactly one of the closed outcome set: refused, "
        "could_not_proceed, completed."
    )
    return argv, prompt


def classify_outcome(result_text):
    """Classify a completed headless session's result text into `OUTCOMES`.

    Fails closed to `could_not_proceed` on empty output, output naming no
    outcome, or output naming more than one outcome -- never `completed` for
    an unclassifiable result.
    """
    if not result_text or not result_text.strip():
        return "could_not_proceed"

    found = [outcome for outcome in OUTCOMES if outcome in result_text]
    if len(found) != 1:
        return "could_not_proceed"
    return found[0]


#: How much of the session's own words to carry. Long enough for a paragraph
#: of reasoning, short enough that an escalation stays readable.
STOP_RATIONALE_LIMIT = 700


def extract_stop_rationale(result_text: str, *, limit: int = STOP_RATIONALE_LIMIT) -> str:
    """The session's own account of why it stopped, or `""`.

    `classify_outcome` reduces an entire headless session to one of four
    words and discards everything else -- including the reason. `/fix-bug`'s
    contract is explicit that there is one to keep: *"The recorded reason
    names which criterion fired."*

    Losing it is not cosmetic. Three consecutive refusals in one run produced
    three byte-identical escalations reading only "`/fix-bug` reported
    `refused`", so nothing distinguished a correct refusal on
    architectural work from a questionable one on a two-line prose fix, and
    the operator could not tell which without redoing the analysis by hand.

    Prefers an explicit `blocked_reason:` (the RESULT-block field
    `result-contract.md` defines) and otherwise falls back to the output's
    tail, which is where a session's closing explanation lands. Returns `""`
    rather than guessing when there is nothing usable -- an empty rationale
    is honest; an invented one is worse than none.
    """
    if not result_text or not result_text.strip():
        return ""

    lines = [line.rstrip() for line in result_text.strip().splitlines()]

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower().startswith("blocked_reason:"):
            reason = stripped.split(":", 1)[1].strip()
            # A wrapped value continues on the following indented lines.
            for continuation in lines[index + 1:]:
                if not continuation.strip() or not continuation.startswith((" ", "\t")):
                    break
                reason = f"{reason} {continuation.strip()}"
            if reason:
                return reason[:limit].strip()

    tail = [line.strip() for line in lines if line.strip()][-6:]
    return " ".join(tail)[:limit].strip()
