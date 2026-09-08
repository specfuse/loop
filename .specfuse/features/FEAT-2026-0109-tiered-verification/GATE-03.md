---
gate: 3
status: open
---

# Gate 3 — the driver runs from an installed copy

Drafted by gate 2's `plan-next`, not now.

**This gate is deliberately alone.** `[FEAT-2026-0019/G1]` records that a
feature migrating the harness the driver itself runs cannot be decomposed into
separately-gated work units: each unit's exit oracle is the very surface being
migrated, so no unit can pass alone and the driver thrashes. The last attempt
cost $5.63 and 49 minutes before abandonment. Whoever drafts this gate should
plan it as a single atomic change, or complete it interactively — not as one
unit among several.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Authored with this gate's work units by the prior gate's `plan-next`. The
runtime-probe (§4), flag-scope (§3) and predicate-satisfiability (§2) checks
are assessed against the units drafted then, not now — there is nothing to arm
until this gate has work.
