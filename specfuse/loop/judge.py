#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The judge's evidence bundle, prompt, and RESULT parser (FEAT-2026-0100/T01).

Three pure pieces, no I/O beyond reading the feature dir's own artifacts and
no driver state: `build_judge_bundle` collects the evidence a fresh evaluator
is allowed to see, `render_judge_prompt` turns it into that session's prompt,
and `parse_judge_result` reads the verdict back out. The close path that
dispatches the session and acts on the verdict is T02's; nothing here writes a
file, runs a command, or knows what a `WorkUnit` is.

**What the judge may see.** The gate's `## Definition of done`, the
`GATE-NN-CRITERIA.md` entries (via `criteria_state.parse_criteria_state` — the
shipped parser, not a fork), the gate's diff as the caller captured it, and the
close's `## Measurements` section. **What it may not see** is the close's own
opinion of its work: any `Verdict` or `Retrospective` section is stripped out of
every evidence string before it reaches the prompt (`strip_forbidden_sections`),
including when it arrives inside a diff hunk. A judge that reads "verdict: met —
every criterion holds" before deciding is the same session grading itself with
extra steps, which is the failure this feature exists to remove.

**Escapes and truncation** follow `loop.py`: evidence and captured output are
capped at the 8,000-character failure-note limit (`JUDGE_MAX_EVIDENCE_CHARS`),
and every `reason` this module produces is a single line, so `loop.py`'s
`_yaml_double_quote` renders it as a valid one-line frontmatter scalar. Those
helpers are deliberately not imported: `loop.py` imports this module, so the
reverse import would be a cycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import criteria_state
from ._wu_sections import slice_wu_section
from .criteria_state import CriterionStateEntry

#: The only two verdicts a judge may return. Deliberately narrower than
#: `loop.VERDICT_VALUES`: the judge answers the binary question, and a hedge
#: is an unparseable answer, not a third state.
JUDGE_VERDICT_VALUES: frozenset = frozenset({"met", "not_met"})

#: Per-evidence-string character cap. Mirrors the 8,000-character failure-note
#: limit in `loop.truncate_failure_note` (see the module docstring on why it is
#: mirrored rather than imported).
JUDGE_MAX_EVIDENCE_CHARS = 8000

#: Section titles carrying the close's own judgement of its work. Matched on a
#: heading's first word, so `## Verdict and rationale` is caught too.
FORBIDDEN_SECTION_TITLES: frozenset = frozenset({"verdict", "retrospective"})

#: What replaces a stripped section. Plain ASCII, no triple-backtick, so it
#: cannot disturb the judge's own RESULT block.
REDACTION_MARKER = "[redacted: the close's own prose, which the judge does not read]"

RETROSPECTIVE_FILENAME = "RETROSPECTIVE.md"
DEFINITION_OF_DONE_SECTION = "Definition of done"
MEASUREMENTS_SECTION = "Measurements"

_JUDGE_RESULT_BLOCK_RE = re.compile(r"```result\s*\n(.*?)\n```", re.DOTALL)
_VERDICT_LINE_RE = re.compile(r"(?m)^\s*verdict:\s*(.*?)\s*$")
_FINDING_HEADING_RE = re.compile(r"(?m)^###\s+(.+?)\s*$")

# A heading line, optionally carrying a unified-diff prefix (`+`, `-`, or the
# context space) so a retrospective's headings are recognised inside a diff too.
_HEADING_LINE_RE = re.compile(r"^[+\- ]?(#{1,6})\s*(.+?)\s*$")
# Where a redacted run ends when no further heading appears: the next file or
# hunk boundary in a diff.
_DIFF_BOUNDARY_RE = re.compile(r"^(?:diff --git |@@ |--- |\+\+\+ |index )")


@dataclass(frozen=True)
class JudgeBundle:
    """The complete evidence a judge session is given, and nothing else."""

    gate_number: int
    definition_of_done: str
    criteria: list[CriterionStateEntry]
    diff_text: str
    measurements: str


@dataclass(frozen=True)
class JudgeFinding:
    """One `### <criterion>` block a judge wrote to explain a `not_met`."""

    criterion: str
    #: The finding's section exactly as the judge wrote it, heading included.
    text: str


@dataclass(frozen=True)
class JudgeResult:
    """A parsed judge session outcome.

    `verdict` is `met`, `not_met`, or `None`. `None` means the output could not
    be read as a verdict — empty, no `result` block, no `verdict:` field, or a
    value outside `JUDGE_VERDICT_VALUES` — and `reason` says which. A `None`
    verdict is not a `not_met`: T02 leaves the close's own verdict standing.
    """

    verdict: Optional[str]
    findings: list[JudgeFinding] = field(default_factory=list)
    raw: str = ""
    reason: Optional[str] = None


def truncate_evidence(text: str, max_chars: int = JUDGE_MAX_EVIDENCE_CHARS) -> str:
    """Return *text* unchanged when within the cap; otherwise head + marker + tail.

    Head and tail split the budget evenly, which keeps a diff's first hunk and
    a test run's final summary — the two ends a reader actually needs. The
    marker is plain ASCII with no triple-backtick, so truncating a captured
    session's output cannot forge or break a fenced block.
    """
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    head, tail = text[:half], text[len(text) - half:]
    elided = len(text) - len(head) - len(tail)
    return f"{head}\n... [{elided} chars elided] ...\n{tail}"


def _heading_first_word(title: str) -> str:
    words = re.sub(r"[^0-9A-Za-z ]+", " ", title).split()
    return words[0].lower() if words else ""


def strip_forbidden_sections(text: str) -> str:
    """Remove every `Verdict` / `Retrospective` section from *text*.

    Line-oriented rather than regex-over-the-whole-string because the same
    headings must be caught inside a unified diff, where each line carries a
    `+`/`-`/space prefix. A stripped run ends at the next heading or, in a
    diff, at the next file/hunk boundary — so the code half of a diff that also
    touched `RETROSPECTIVE.md` survives intact.
    """
    out: list[str] = []
    skipping = False
    skip_level = 0
    for line in text.splitlines():
        m = _HEADING_LINE_RE.match(line)
        if m:
            level = len(m.group(1))
            if skipping and level <= skip_level:
                skipping = False
            if not skipping and _heading_first_word(m.group(2)) in FORBIDDEN_SECTION_TITLES:
                out.append(REDACTION_MARKER)
                skipping = True
                skip_level = level
                continue
            if skipping:
                continue
        elif skipping and _DIFF_BOUNDARY_RE.match(line):
            skipping = False
        if not skipping:
            out.append(line)
    result = "\n".join(out)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def _clean_evidence(text: str) -> str:
    return truncate_evidence(strip_forbidden_sections(text or ""))


def _read_text(path: Path) -> str:
    """Read a feature artifact, treating an absent file as empty.

    Absent is a normal state for every artifact the judge reads: a gate that
    never recorded per-criterion state has no `GATE-NN-CRITERIA.md`, and an
    auto-closing feature may have no retrospective yet. None of that is an
    error the judge should raise on — it is simply less evidence.
    """
    try:
        return path.read_text()
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
        return ""


def build_judge_bundle(
    feature_dir: Path,
    gate_number: int,
    *,
    diff_text: str,
    measurements: Optional[str] = None,
) -> JudgeBundle:
    """Collect the four evidence pieces a judge is allowed to see.

    `diff_text` is the gate's diff, captured by the caller (T02 owns which
    revision range that is). `measurements` is the close's measurements: pass
    the retrospective's text and the `## Measurements` section is sliced out of
    it; pass an already-sliced body and it is kept as-is; pass nothing and this
    reads `RETROSPECTIVE.md` from *feature_dir*. Whichever way it arrives, the
    close's `Verdict` and `Retrospective` prose is stripped, never carried.

    A missing `GATE-NN.md` yields an empty definition of done and a missing
    `GATE-NN-CRITERIA.md` yields an empty criteria list — an absent artifact is
    less evidence, not an exception.
    """
    feature_dir = Path(feature_dir)

    gate_text = _read_text(feature_dir / f"GATE-{gate_number:02d}.md")
    definition_of_done = slice_wu_section(gate_text, DEFINITION_OF_DONE_SECTION).strip()

    criteria_path = feature_dir / criteria_state.criteria_filename(gate_number)
    criteria = criteria_state.parse_criteria_state(_read_text(criteria_path))

    source = measurements
    if source is None:
        source = _read_text(feature_dir / RETROSPECTIVE_FILENAME)
    sliced = slice_wu_section(source, MEASUREMENTS_SECTION)
    # No `## Measurements` heading in the source means the caller handed over
    # the section's body already; using the source as-is is what keeps the
    # evidence rather than silently dropping it. Either way it is stripped.
    measurements_text = sliced.strip() if sliced.strip() else source

    return JudgeBundle(
        gate_number=gate_number,
        definition_of_done=_clean_evidence(definition_of_done),
        criteria=criteria,
        diff_text=_clean_evidence(diff_text),
        measurements=_clean_evidence(measurements_text),
    )


def _render_criteria(criteria: list[CriterionStateEntry]) -> str:
    if not criteria:
        return (
            "No per-criterion state was recorded for this gate. Judge from the "
            "definition of done, the diff, and the measurements below.\n"
        )
    return criteria_state.render_criteria_state(criteria)


def render_judge_prompt(bundle: JudgeBundle) -> str:
    """Render the session prompt for a judge dispatch.

    States the job (decide the binary verdict from the evidence, re-running any
    oracle a criterion names), the finding shape for a `not_met`, and the one
    thing the judge must not open. That prohibition is worded without quoting
    the banned headings, because a prompt that quotes them would put the very
    strings this bundle strips back into the judge's context.
    """
    return f"""\
You are the judge for gate {bundle.gate_number}. A separate session did the work
and wrote a close; you decide whether the gate's definition of done is met. You
did not do this work and have no stake in the answer.

## Your job

1. Read the definition of done, the per-criterion state, the diff, and the
   measurements below. That is the whole evidence bundle — the session that
   did the work is not here to explain itself, and its explanation is not
   evidence.
2. Re-run every oracle a criterion names. A criterion whose oracle you did not
   run is not proved; recorded state from a previous attempt is a claim, and
   your own run is the evidence.
3. Decide `met` or `not_met`. `met` means every item in the definition of done
   is demonstrably true on this tree. Anything else is `not_met` — there is no
   partial verdict, and a criterion you could not verify is `not_met`, not a
   hedge.
4. Do not open `{RETROSPECTIVE_FILENAME}`. Its closing sections carry the other
   session's own opinion of its work; reading them is how a judge stops being
   one. The measurements it recorded are already below.
5. Change nothing. You run no git command, edit no file, and fix nothing you
   find. You report.

## Definition of done (gate {bundle.gate_number})

{bundle.definition_of_done or "(none recorded)"}

## Per-criterion state

{_render_criteria(bundle.criteria)}
## Gate diff

```
{bundle.diff_text or "(empty)"}
```

## Measurements recorded by the close

{bundle.measurements or "(none recorded)"}

## Your answer

End your turn with one fenced `result` block and nothing after it. For `met`:

```result
verdict: met
```

For `not_met`, follow the verdict with one `### <criterion>` section per
failure — the criterion's ID from the per-criterion state above, or its text
when it has no ID — each naming the command you ran and the exit code you saw:

```result
verdict: not_met

### T01#1

<what is not true, in your own words>

- command: `<the command you ran>`
- exit: <its exit code>
```

Report only failures you observed. A finding with no command behind it is an
opinion, and the close already had one of those.
"""


def _single_line(text: str, limit: int = 200) -> str:
    """Collapse to one line so `loop._yaml_double_quote` can render it."""
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 3] + "..."


def _parse_findings(block_body: str) -> list[JudgeFinding]:
    headings = list(_FINDING_HEADING_RE.finditer(block_body))
    findings: list[JudgeFinding] = []
    for i, m in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(block_body)
        findings.append(
            JudgeFinding(criterion=m.group(1), text=block_body[m.start():end].strip())
        )
    return findings


def parse_judge_result(text: str) -> JudgeResult:
    """Read a judge session's output into a verdict and its findings.

    Forgiving in the same way `loop.parse_result_block` is: the input is a
    language model's free-form stdout, so every malformed shape degrades to
    `verdict=None` with a `reason` rather than raising. `None` is a real
    outcome the close path handles (the close's own verdict stands), which is
    why it carries a reason instead of a default verdict — defaulting to `met`
    would launder a broken judge into a pass, and defaulting to `not_met` would
    let a flaky session veto finished work.
    """
    raw = truncate_evidence(text or "")
    if not (text or "").strip():
        return JudgeResult(verdict=None, raw=raw, reason="judge produced no output")

    matches = list(_JUDGE_RESULT_BLOCK_RE.finditer(text))
    if not matches:
        return JudgeResult(
            verdict=None, raw=raw, reason="no fenced result block in judge output"
        )
    body = matches[-1].group(1)  # LAST block — a judge may reconsider before it

    m = _VERDICT_LINE_RE.search(body)
    if not m:
        return JudgeResult(
            verdict=None, raw=raw, reason="result block has no verdict field"
        )

    value = m.group(1).strip().strip("`'\"").strip()
    if value not in JUDGE_VERDICT_VALUES:
        return JudgeResult(
            verdict=None,
            raw=raw,
            reason=_single_line(f"unrecognized judge verdict: {value or '(empty)'}"),
        )

    return JudgeResult(verdict=value, findings=_parse_findings(body), raw=raw)
