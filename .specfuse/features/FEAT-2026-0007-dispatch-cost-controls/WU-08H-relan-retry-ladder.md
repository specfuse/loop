---
id: FEAT-2026-0007/T08H
type: implementation
model: claude-opus-4-7
effort: high
status: draft
attempts: 0
---

# Hygiene: re-land the retry-ladder code that T04 reported done but never wrote

**Objective.** Re-land T04's required code changes — the `EFFORT_LADDER`
constant, the `effort_for_attempt`/`terseness_for_attempt` helpers, the
`dispatch()` kwarg threading, the attempt-loop wiring, the
`attempts_usage` field additions, and the test file — that T04 claimed
complete (`status: done` in WU-04 frontmatter, `task_completed` in
events.jsonl) but whose code never landed in the repo. T08's telemetry
extension cannot extend fields that don't exist, so this hygiene WU runs
**before** T08.

**Context.** This is `FEAT-2026-0007/T08H` — a hygiene WU precursor to
T08 per `.specfuse/rules/correlation-ids.md` §Hygiene units. The pre-
existing gap is documented in `RETROSPECTIVE.md` under "T04 — CRITICAL
FINDING: Implementation not delivered." The original WU-04 spec is
fully repeated below as the operative contract — this WU re-executes
that contract, with the missing completeness escalation trigger added
per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`.

**Why a hygiene WU and not "re-open T04":** T04 is already committed
with `status: done`; the methodology forbids retro-editing a closed
WU's status (per the never-touch posture toward prior gates' state).
The hygiene WU pattern (LEARNINGS `[meta/first-live-use]`) is the
sanctioned tool for inserting a narrow corrective edit ahead of the
WU that depends on it.

The attempt loop is in `run()` around `.specfuse/scripts/loop.py:774`;
`MAX_ATTEMPTS = 3` at `loop.py:64` is unchanged. Depends on T02 (the
`effort` field exists on `WorkUnit`) and T03 (the caveman directive is
the preamble's terseness lever). Both shipped successfully.

Reference the binding rules under `.specfuse/rules/`. The driver owns
git; edit files only.

**Acceptance criteria.** Re-execute T04's contract, restated here:

1. Module constant `EFFORT_LADDER = ["low", "medium", "high", "xhigh",
   "max"]` in `loop.py`.
2. Pure helper `effort_for_attempt(declared: str, attempt: int) -> str`
   returns `EFFORT_LADDER[min(EFFORT_LADDER.index(declared) + attempt -
   1, len(EFFORT_LADDER) - 1)]`. For `attempt == 1` it returns
   `declared` unchanged.
3. Pure helper `terseness_for_attempt(attempt: int) -> str` returns
   `"caveman-full"` for `attempt == 1`, `"caveman-lite"` for `2`,
   `"normal"` for `>= 3`.
4. `dispatch()` accepts optional `effort` and `terseness` keyword args;
   when provided they override the WU's declared `effort` for the
   `--effort` flag and the preamble selection respectively. When
   omitted, behavior matches T02/T03 (declared effort, caveman directive
   iff `wu.effort in {low, medium}`).
5. Preamble selection (the T03 logic) is extended to honor the
   `terseness` override: `caveman-full` → full directive;
   `caveman-lite` → a softer one-paragraph directive that drops only
   the "no end-of-turn summary" and "no narration" bullets;
   `normal` → no directive regardless of `wu.effort`.
6. The attempt loop in `run()` computes `effort_for_attempt(wu.effort,
   attempt)` and `terseness_for_attempt(attempt)` for each attempt and
   passes both to `dispatch()`.
7. Per-attempt usage records appended to `events.jsonl` (the
   `attempts_usage` list around `loop.py:782`) gain string fields
   `effort_used` and `terseness`.
8. Four new unit tests in `tests/test_loop_retry_ladder.py`:
   (a) ladder bumps `low` → `medium` → `high` across attempts 1-3;
   (b) ladder caps at `max` when declared is `xhigh` and `attempt == 3`;
   (c) terseness map returns the three expected strings for attempts
       1, 2, 3;
   (d) integration through a stubbed `dispatch` asserts both fields
       land in `events.jsonl`.
9. **Existence smoke check** (the missing T04 AC, per LEARNINGS
   `[FEAT-2026-0007/G1-LESSONS]`): `python3 -c "from loop import
   EFFORT_LADDER, effort_for_attempt, terseness_for_attempt"` must
   succeed. Name this in the Verification section below; run it
   yourself before claiming complete.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py`
and one new test file `tests/test_loop_retry_ladder.py`. No edits to:
existing WU files (including WU-04 — its `status: done` is part of the
committed history and stays), `WU.template.md`, `.specfuse/rules/`,
`.specfuse/verification.yml`, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check in AC 9.

**Escalation triggers.**
1. **Completeness.** If any of `EFFORT_LADDER`, `effort_for_attempt`,
   `terseness_for_attempt` is absent from `loop.py` after your edits,
   emit `status: blocked` — do not claim complete. This trigger exists
   precisely because T04's lack of it is why this hygiene WU is needed.
2. **Diff sanity.** Before reporting `status: complete`, confirm your
   `files_changed` list shows `.specfuse/scripts/loop.py` with a
   substantive diff (more than a few lines). A `files_changed` entry
   that lists `loop.py` but produces a near-empty diff is the T04
   failure mode — emit `status: blocked` instead.
3. **`dispatch()` signature drift.** If extending `dispatch()` with the
   `effort` / `terseness` kwargs breaks T05's failure-note cap test or
   any existing test in `tests/`, stop and emit `status: blocked`
   naming the conflict. Default values for new kwargs should preserve
   call-site compatibility.
4. **Schema-consumer drift.** If the `attempts_usage` extension would
   break a documented consumer in `.claude/skills/gate-status/`,
   flag and stop.
