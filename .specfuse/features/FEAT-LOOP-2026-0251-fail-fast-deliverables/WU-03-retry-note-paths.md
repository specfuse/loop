---
id: FEAT-LOOP-2026-0251/T03
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 1.00
produces:
  - specfuse/loop/loop.py
  - tests/test_fail_fast_deliverables.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.33.2
started_at: 2026-11-25T23:32:32.585980+00:00
duration_seconds: 135.836
cost_usd: 0.55332
input_tokens: 32
output_tokens: 10935
---

# T03 — the retry note lists the paths the attempt did change

**Objective.** Turn Definition-of-done clause 4 green.

**Context.** `FEAT-LOOP-2026-0251/T03`; decisions 1 and 5 in `PLAN.md`. The note already names
the missing path and shows `PRODUCES_REPAIR_EXAMPLE`; keep both.

- For all three refusals, early or late, the retry note gains a line listing the paths this
  attempt changed, from the same diff the guard judged, or "this attempt changed no files".
  Cap the list (for example, the first 20 paths and a count of the rest) so a large diff
  cannot flood the note.
- The early refusal's note says verification did not run, under both tree outcomes
  (`retain_on_guard_refusal` true and false).

**Acceptance criteria.**

1. `tests.test_fail_fast_deliverables.TestTreeAndNote` fails on HEAD and passes after. It
   asserts, for an early `produces_not_in_diff` refusal: the note names the missing path, lists
   each changed path, and says verification did not run; with `retain_on_guard_refusal: true`
   the tree is kept and with `false` it is reset; an attempt that changed nothing says so.
2. The cap holds: a diff of 30 paths lists 20 and the count of the remaining 10.

**Do not touch.** The order of the early and late checks (T01, T02). `lint_plan.py` and docs
(T04).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** None expected.
