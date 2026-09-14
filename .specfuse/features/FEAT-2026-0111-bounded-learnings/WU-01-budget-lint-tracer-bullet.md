---
id: FEAT-2026-0111/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
produces_driver_helper:
  - binding_block_word_count
produces:
  - tests/test_binding_block_budget.py
---

# Measure the binding block, and report what could be trimmed

**Objective.** Make gate 1's `feature_oracle` runnable: count the binding
block's words across every `@`-referenced file, wire a minimal distilled file
into `.specfuse/rules-local/`, and **report the trimmable headroom** the rest
of the gate is drafted against.

**Context.** FEAT-2026-0111/T01. This is the gate's **tracer bullet**
(`/authoring-work-units` §14): stubs are permitted here and nowhere else. The
slot already exists — the binding block documents
`.specfuse/rules-local/<rule>.md` as upgrade-safe and asks for one `@` line
per rule. The cap already exists as a comment at `scaffold.py:227`, set
because "a 7,213-word set was read past rather than read". Today the block is
**2,574 words against 2,500, with `rules-local/` empty**.

This unit's real output is the headroom number. T04 allocates a budget against
it; drafting T04 without it would be guessing.

**Acceptance criteria.**

- `python3 -m unittest tests.test_binding_block_budget -v -b` fails on HEAD
  before this unit's edits (the module does not exist) and passes after.
- The word count is computed from the binding block's **actual `@` references**,
  resolved and summed, not from a hardcoded list of three filenames — a
  consumer's block carries `rules-local` lines this repo's does not.
- The unit reports, in its attempt record: the current total, the cap, and a
  per-file breakdown with a stated view of what could be trimmed from each and
  what could not. This is the evidence T04 is drafted against.
- A minimal `.specfuse/rules-local/learnings-distilled.md` is loaded by one
  `@` line and is counted by the lint — proving the path end to end, whatever
  its content.

**Do not touch.** The content of `result-contract.md`, `never-touch.md` or
`security-boundaries.md` — measuring what could be trimmed is this unit's job;
trimming is T04's, after a human has seen the number. `LEARNINGS.md`'s append
contract. The sibling WU files in this gate.

**Verification.** The narrow tier is NOT sufficient: this touches the
scaffold's binding-block wiring, which `scaffold.py` writes into every
consuming project, so run the **full** suite —
`python3 -m unittest discover -s tests -b` — before reporting complete. Plus
`python3 -m unittest tests.test_binding_block_budget -v -b` and the symbol
check (§9):
`python3 -c "from specfuse.loop.loop import binding_block_word_count"`.

**Escalation triggers.** Stop with `status: blocked` and report the headroom
if the honest finding is that **nothing can defensibly be trimmed** from the
three binding rules. Raising a cap set on measured evidence is an operator
decision, not this unit's. Stop also if making the oracle green would require
editing a binding rule's content — that is T04's work and it needs the number
this unit produces first.
