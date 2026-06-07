---
id: FEAT-2026-0007/T05
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
duration_seconds: 186.293
cost_usd: 0.589728
input_tokens: 27
output_tokens: 9237
---

# Cap failure-note size piped into retry attempts

**Objective.** The failure note concatenated to the retry-attempt prompt
is bounded at 200 lines and 8000 characters, with head + tail
preservation. Prevents the retry ladder (T04) from compounding into
runaway prompt sizes when a test failure produces a verbose stack or log.

**Context.** This is `FEAT-2026-0007/T05`. `dispatch()` accepts a
`failure_note` parameter that, when non-empty, is concatenated to the
prompt under a `## Previous attempt failed verification` header (see the
existing logic around `loop.py:435`). It is unbounded today. Test-failure
evidence is most actionable at the head (first assertion line, root of
stack) and the tail (summary line); the middle is noise. Independent of
T01–T04 and may run in any order within Gate 1. Reference the binding
rules under `.specfuse/rules/`. The driver owns git; edit files only.

**Acceptance criteria.**
1. New helper `truncate_failure_note(note: str, max_lines: int = 200,
   max_chars: int = 8000) -> str` returns `note` unchanged when both
   limits are satisfied; otherwise returns `head + marker + tail` where
   `marker` is a single plain-ASCII line of the form
   `\n... [N lines / M chars elided] ...\n` and `head` / `tail` split the
   surviving budget roughly 50/50 by line count.
2. `dispatch()` calls `truncate_failure_note(failure_note)` before
   concatenating to the prompt.
3. The truncation marker is plain ASCII and contains no triple-backtick
   so RESULT-block parsing remains unaffected.
4. Three new unit tests in `tests/`: (a) under-limit input is returned
   unchanged; (b) over-line-limit input is truncated and both the first
   and last lines of the input appear in the output; (c) over-char-limit
   input is truncated and the marker reports the elided counts.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py` and
one new test file under `tests/` (suggested
`tests/test_loop_failure_note_cap.py`). No edits to: `WU.template.md`,
`.specfuse/rules/`, `.specfuse/verification.yml`, the `events.jsonl`
schema (the truncated note is not logged separately), existing WU files,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`.

**Escalation triggers.** Stop and emit `status: blocked` if an existing
test in `tests/` asserts the verbatim full content of a `failure_note`
that exceeds the proposed defaults — truncation would break it; flag the
conflict rather than relaxing the cap or rewriting unrelated tests.
