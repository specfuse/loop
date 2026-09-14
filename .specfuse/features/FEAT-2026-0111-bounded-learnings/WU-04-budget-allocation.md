---
id: FEAT-2026-0111/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
produces:
  - tests/test_binding_block_allocation.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.19.0
started_at: 2026-09-14T14:51:42.026158+00:00
duration_seconds: 592.108
cost_usd: 1.368262
input_tokens: 98
output_tokens: 26750
---

# Allocate the budget, and make the cap blocking once the tree can pass it

**Objective.** Give the distilled file an explicit sub-budget, land the trim
that pays for it, and flip the binding-block cap from advisory to blocking —
in that order.

**Context.** FEAT-2026-0111/T04. The cap has lived in a `scaffold.py:227`
comment since FEAT-2026-0084/T01 and nothing enforces it, which is why the
block sits at 2,574 against 2,500 with `rules-local/` empty. This unit is
drafted against **T01's measured headroom**, not against a guess.

Ordering is load-bearing and `PLAN.md` §2 answers it: the predicate fails on
the current tree, so the severity flip may not ship before the allocation. A
blocking cap introduced against a tree that cannot pass it is precisely the
unsatisfiable-predicate defect `planning-discipline.md` §2 exists to prevent.

**Acceptance criteria.**

- `python3 -m unittest tests.test_binding_block_allocation -v -b` fails on HEAD
  before this unit's edits and passes after.
- With the distilled file present, the resolved binding block totals **under
  2,500 words**, asserted by summing the same `@` references T01's counter
  resolves — not a hardcoded file list.
- The distilled file has its own stated sub-budget, and exceeding it fails
  before the total does, so the failure names the right cause.
- The cap is blocking **only** in the same change that brings the tree under
  it; a test asserts the tree passes at the moment the severity flips. This
  unit carries a flag-scope table naming every `@`-referenced file and whether
  the budget covers it (`planning-discipline.md` §3).

**Do not touch.** `LEARNINGS.md`. T02's scoring and T03's accept step. A
consumer's own `@` lines — the scaffold writes its block and must not clobber
project-authored entries.

**Verification.** The narrow tier is NOT sufficient: this edits the binding
block `scaffold.py` writes into every consuming project, so run the **full**
suite — `python3 -m unittest discover -s tests -b` — before reporting complete.
Plus `python3 -m unittest tests.test_binding_block_allocation tests.test_binding_block_budget -v -b`.

**Escalation triggers.** Stop with `status: blocked` if the trim T01's
headroom implied turns out to require cutting something an implementation
session depends on. Shipping a smaller block that drops a binding contract is
worse than shipping nothing, and which contract may shrink is an operator
decision.

## Flag-scope table (`planning-discipline.md` §3)

The flag is `check_binding_block_budget`'s severity: measured-only before this
unit, blocking (raises `AssertionError`) after. Every path the block's `@`
lines reference today, and whether the new blocking check covers it:

| Code path | Gated by the new blocking check? | Why |
|---|---|---|
| `.specfuse/rules/result-contract.md` | yes | Summed into `binding_block_word_count`'s `total`; `check_binding_block_budget` raises if `total > cap`. |
| `.specfuse/rules/never-touch.md` | yes | Same total-cap path as above. |
| `.specfuse/rules/security-boundaries.md` | yes | Same total-cap path as above. |
| `.specfuse/rules-local/learnings-distilled.md` | yes, twice | Counted into `total` like the three above, and checked separately against its own `LEARNINGS_DISTILLED_WORD_CAP` sub-budget first, so a bloated distillate is named directly. |
| A consumer project's own `@.specfuse/rules-local/<rule>.md` lines | yes, by the same total-cap path | `binding_block_word_count` reads the block's actual `@` references, not a hardcoded list, so any rules-local import a project adds is summed and capped identically. Only the one line this repo names above resolves against `LEARNINGS_DISTILLED_WORD_CAP` specifically — a project's *other* `rules-local` files are covered by the total cap only, not by that sub-budget. |
