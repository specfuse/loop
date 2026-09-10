---
id: FEAT-2026-0103/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces_driver_helper:
  - compose_guard_repair_note
produces:
  - specfuse/loop/loop.py
  - tests/test_guard_repair_prompt.py
model: sonnet
---

# The repair turn opens with the complaint, not with a restart

**Objective.** The note a refused attempt hands to the next one must read as a
repair brief: the guard's exact complaint first, then that the tree is retained
and must not be re-authored, then the one action that clears the guard, then
the retained diff. Today the guard notes were written for a session starting
from a bare tree, and `synthesize_retry_directive`'s `retained=True` lead exists
only for convergent units.

**Context.** FEAT-2026-0103/T02. T01 retains the tree and appends the diff; this unit
shapes the words. In `specfuse/loop/loop.py`, `_RETRY_CLASS_HINT` maps a
`failure_class` to a one-sentence remedy and `synthesize_retry_directive(
failure_class, retained=)` composes the lead that is prepended to the failure
note. Add hints for the three guard classes — `guard_refusal`,
`files_changed_mismatch`, `produces_not_in_diff` — each naming the mechanical fix
(declare only files you changed / make the declared deliverable or justify it
under `produces_unchanged:` / touch a deliverable file), and add
`compose_guard_repair_note(failure_class, complaint, retained_diff, retained)`
that builds the whole note — `synthesize_retry_directive(<class>, retained=)`'s
lead, the complaint, the remedy, then the diff — and have the four guard sites
call it instead of assembling their notes inline. The
lead for a retained guard refusal says, in this order: what the guard refused,
that the previous attempt's edits are on disk and verification passed on them,
that re-authoring is the one thing not to do, and that the RESULT block must be
re-emitted in full. Keep the diff last: it is evidence, not the instruction.

**Acceptance criteria.**

1. `tests/test_guard_repair_prompt.py::test_retained_guard_note_leads_with_the_complaint`
   fails on HEAD and passes after: for each of the three classes, the composed
   note's first non-blank line names the guard's complaint, a line before the
   diff says the tree is retained and verification passed, the class's remedy
   sentence is present, and the `Retained diff` line comes after all of them.
2. `::test_unretained_guard_note_is_unchanged`: with the kill switch off the
   note carries neither the retained lead nor a diff, and the remedy sentence
   still appears — the hint is useful either way.
3. `python3 -m unittest tests.test_attempt_outcome_emission tests.test_convergent_iteration -v`
   exits 0 with no edit to those modules (they assert today's leads for
   `lint` / `tests` and the convergent `retained` wording).
4. `python3 -m unittest tests.test_guard_repair_e2e -v` still exits 0.

**Do not touch.** The guards' summaries themselves; `_RETRY_CLASS_HINT`'s
existing four entries; the convergent branch; `.specfuse/rules/`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`.

**Escalation triggers.** Stop with `status: blocked` if the guard sites' notes
cannot be routed through `synthesize_retry_directive` without changing what
`failure_excerpt` records in `events.jsonl` (name the field's before and after).
