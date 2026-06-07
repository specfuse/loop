---
id: FEAT-2026-0008/T01
type: implementation
model: claude-opus-4-7
effort: high
status: pending
attempts: 0
---

# Zero-token attempt guard

**Objective.** The driver treats a dispatched session that bills 0 input
tokens (and therefore 0 output tokens) as a **failed attempt**, not a
completed one. The attempt's RESULT block is ignored; the attempt
counter increments; the next attempt (or the spinning escalation) runs as
normal.

**Context.** This is `FEAT-2026-0008/T01`. The post-mortem in
`.specfuse/features/FEAT-2026-0007-dispatch-cost-controls/RETROSPECTIVE.md`
documents T08H billing `input_tokens: 0, output_tokens: 0` yet committing
`status: done`. The `usage` dict already parsed in `loop.py` at the
`_parse_dispatch_result` / `parse_claude_json_output` boundary
(around `loop.py:449`) carries `input_tokens` when cost tracking is on;
when it is off, `usage` is `None`. The guard fires only when `usage` is a
dict AND `input_tokens == 0` — `usage is None` (cost tracking disabled)
must NOT trigger the guard, because the prior behavior must be preserved
for users who opt out of cost tracking.

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit files only.

**Acceptance criteria.**
1. New helper `is_zero_token_attempt(usage: dict | None) -> bool` returns
   `True` iff `usage` is a dict whose `input_tokens` key is `0`; returns
   `False` for `None`, missing key, or any positive integer.
2. In the attempt loop in `run()` (around `loop.py:715`), immediately after
   `dispatch()` returns and before the RESULT-block parse, call
   `is_zero_token_attempt(usage)`. When `True`:
   (a) skip RESULT-block parsing for this attempt (the agent produced no
       output, so the block is missing or hallucinated upstream),
   (b) append an event `attempt_outcome` with `outcome: "zero_token_skip"`
       and the attempt number,
   (c) treat the attempt as a verification failure for the purposes of the
       attempt loop — increment the attempt counter, write the per-attempt
       record, continue to the next attempt or the spinning escalation
       (whichever fires per `MAX_ATTEMPTS`).
3. A WU whose three attempts all return zero-token results escalates to
   `blocked_human` via the existing spinning path with
   `reason: "all_attempts_zero_token"` distinguishable from generic
   spinning in the event payload.
4. When cost tracking is disabled (`usage is None`), the guard does NOT
   fire — the WU executes exactly as it does today. This preserves the
   contract for users who opt out of cost tracking.
5. New unit tests in `tests/test_loop_zero_token_guard.py`:
   (a) `is_zero_token_attempt({"input_tokens": 0, "output_tokens": 0})` is
       `True`.
   (b) `is_zero_token_attempt({"input_tokens": 1234})` is `False`.
   (c) `is_zero_token_attempt(None)` is `False`.
   (d) `is_zero_token_attempt({})` is `False` (missing key).
   (e) Integration via a stubbed dispatch returning `usage = {"input_tokens":
       0, "output_tokens": 0}` three times in a row: the WU ends
       `blocked_human` with the new reason; no `task_completed` event was
       written; no squash commit landed for the WU.
6. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from loop import is_zero_token_attempt"` must succeed
   before declaring complete.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py` and
one new test file `tests/test_loop_zero_token_guard.py`. No edits to:
`WU.template.md`, `.specfuse/rules/`, `.specfuse/verification.yml`,
existing WU files under `.specfuse/features/`, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check named in AC 6. Run the smoke check first;
if `ImportError` fires, the helper is not authored — emit
`status: blocked` rather than claim complete.

**Escalation triggers.**
1. **Completeness.** If `is_zero_token_attempt` is absent from `loop.py`
   after your edits, emit `status: blocked` — do not claim complete.
   (Mirrors the T04/T08H/T08 failure mode this feature is built to fix.)
2. **Cost-tracking-disabled regression.** If your implementation makes the
   guard fire on `usage is None`, stop and emit `status: blocked` — the
   guard must be opt-in via the existing cost-tracking flag, not the
   inverse. A user running with cost tracking off must see no behavior
   change from this WU.
3. **Spinning-path overlap.** If injecting the new "zero-token skip"
   outcome into the existing attempt loop forces a refactor of the
   spinning-detection logic (e.g. the existing failure-note threading), do
   the minimum needed — do not redesign the spinning path. If the minimum
   change would break existing FEAT-2026-0002 tests, flag and stop.
