---
id: FEAT-2026-0007/T04
type: implementation
model: claude-opus-4-7
status: done
attempts: 1
duration_seconds: 224.43
cost_usd: 1.260735
input_tokens: 16
output_tokens: 12451
---

# Retry escalation ladder for effort and terseness

**Objective.** Retry attempts escalate compute: each attempt bumps the
declared `effort` by one tier (capped at `max`) and loosens the terseness
directive (attempt 1 = caveman-full, attempt 2 = caveman-lite, attempt 3 =
no directive). A failed attempt's signal is "needs more compute or more
reasoning out loud", not "try again the same way".

**Context.** This is `FEAT-2026-0007/T04`. The attempt loop is in `run()`
around `loop.py:715`; `MAX_ATTEMPTS = 3` at `loop.py:64` is unchanged.
Depends on T02 (the `effort` field exists on `WorkUnit`) and T03 (the
caveman directive is the preamble's terseness lever). Model is Opus
because this WU edits the control flow of the attempt loop and the
`dispatch()` signature in tandem with T02/T03's changes; forward-design
risk is highest here. Reference the binding rules under `.specfuse/rules/`.
The driver owns git; edit files only.

**Acceptance criteria.**
1. New helper `effort_for_attempt(declared: str, attempt: int) -> str` —
   pure function — returns
   `EFFORT_LADDER[min(EFFORT_LADDER.index(declared) + attempt - 1, len(EFFORT_LADDER) - 1)]`
   where `EFFORT_LADDER = ["low", "medium", "high", "xhigh", "max"]`.
   For `attempt == 1` it returns `declared` unchanged.
2. New helper `terseness_for_attempt(attempt: int) -> str` returns
   `"caveman-full"` for `attempt == 1`, `"caveman-lite"` for `2`,
   `"normal"` for `>= 3`.
3. `dispatch()` accepts optional `effort` and `terseness` keyword args; when
   provided they override the WU's declared `effort` for the `--effort`
   flag and the preamble selection respectively. When omitted, behavior
   matches T02/T03 (declared effort, caveman directive iff
   `wu.effort in {low, medium}`).
4. Preamble selection in T03 is extended to honor the `terseness` override:
   `caveman-full` → full directive; `caveman-lite` → a softer one-paragraph
   directive that drops only the "no end-of-turn summary" and "no narration"
   bullets; `normal` → no directive regardless of `wu.effort`.
5. The attempt loop in `run()` computes `effort_for_attempt(wu.effort,
   attempt)` and `terseness_for_attempt(attempt)` for each attempt and
   passes both to `dispatch()`.
6. Per-attempt usage records appended to `events.jsonl` (via the existing
   `attempts_usage` path) gain string fields `effort_used` and `terseness`.
7. Four new unit tests in `tests/`: (a) ladder bumps `low` → `medium` →
   `high` across attempts 1-3; (b) ladder caps at `max` when declared is
   `xhigh` and `attempt == 3`; (c) terseness map returns the three expected
   strings for attempts 1, 2, 3; (d) integration through a stubbed
   `dispatch` asserts both fields land in `events.jsonl`.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py` and
one new test file under `tests/` (suggested
`tests/test_loop_retry_ladder.py`). No edits to: `WU.template.md` (the
ladder is runtime, not declared), `.specfuse/rules/`, `.specfuse/verification.yml`,
existing WU files, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`.

**Escalation triggers.** Stop and emit `status: blocked` if: (a) changing
`dispatch()`'s signature breaks T02 or T03 tests that have not yet landed
in this gate's sequence (depends_on says they have, but verify before
extending); or (b) the `attempts_usage` schema change would break a
documented consumer in `.claude/skills/gate-status/` such that the field
addition is not backward-compatible — flag and stop.
