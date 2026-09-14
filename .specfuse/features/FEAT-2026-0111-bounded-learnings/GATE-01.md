---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_binding_block_budget -v -b"
---

# Gate 1 — the distilled set reaches dispatch, inside an enforced budget

## Definition of done

`.specfuse/rules-local/learnings-distilled.md` is loaded by the binding block;
its content was accepted by a human rather than generated unattended; and the
whole block — distilled file included — is under 2,500 words and stays there
because a lint says so.

The `feature_oracle` is red today on both counts: the block is at 2,574 words
and no distilled file exists. T01 is the tracer bullet that makes it runnable;
T02–T04 make each part correct.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## The blocking question this gate may not answer

Where the trim comes from is unknown. All three binding rules are contracts.
**T01 must report the trimmable headroom it found and block rather than trim a
binding contract to make room.** If the honest answer is that nothing can go,
this gate stops and a human decides whether to raise a cap set on measured
evidence — that is not a decision any unit here is authorized to make by
default.

## What this gate must not break

The binding block is what every dispatched session in every consuming project
reads. A change that pushes it further over budget, or that drops a rule an
implementation session depends on, is worse than shipping nothing. The
2,500-word figure exists because a 7,213-word block was measured being read
past (`scaffold.py:227`, FEAT-2026-0084/T01) — a larger block is not a
neutral trade, it is the failure mode.

`.specfuse/rules-local/` is documented as never touched by
`specfuse upgrade`. Anything this gate writes there must survive an upgrade,
and anything it writes to the scaffold's own block must not clobber a
consumer's `@` lines.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** This gate makes a cap
  blocking, and the cap **fails on the current tree** (2,574 vs 2,500). PLAN.md
  answers §2 explicitly: the lint may not become blocking until the tree can
  pass it. Confirm at arming that T04 lands the allocation before, or with,
  the severity flip — never after.
- **Runtime probe for a default/severity flip (§4).** The flip above is a
  severity flip. Apply it locally and paste the failing set into
  `GATE-01-REVIEW.md` before arming anything that depends on it.
- **Flag-scope table (§3).** T04 introduces the budget that gates what loads.
  Confirm it names every `@`-referenced file and whether the budget covers it.

## Reflection notes

<Written by the human at review time.>
