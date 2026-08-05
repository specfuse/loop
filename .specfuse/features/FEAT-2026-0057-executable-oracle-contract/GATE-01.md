---
gate: 1
status: awaiting_review
cost_budget_usd: 40.00
baseline:
  sha: bf0098ef496286b1982818d88abd3b0df5fc34ea
  probed_at: 2026-08-05T14:56:04.254614+00:00
  failing: []
---

# Gate 1 — a work unit can declare prep steps and oracles that run before its session

## Definition of done

- A work unit can declare `prep:` and `oracles:` in its frontmatter, both
  resolving against `.specfuse/verification.yml` set names.
- The driver runs prep fail-fast and oracles capture-all **before** dispatching
  the session, and halts distinctly when prep fails.
- The captured oracle output reaches the session as input, under a byte budget
  that preserves verdicts rather than tails.
- This repo declares and uses one real oracle set, guarded structurally, with the
  contract documented alongside `extra_gates` so the difference between
  pre-dispatch and exit is written down.
- Every implementation work unit in this gate is `done`.
- The terminal close has run: retrospective, lessons, docs, and verdict.

This is the feature's only gate, so its closing sequence is a single `close` work
unit (`docs/methodology.md §6`, ceremony proportionality). There is no
`close-intermediate` and no `plan-next`.

`cost_budget_usd: 30.00`. The original $19.00 was the $15.00 plan plus one
re-attempt of the largest unit. It is raised because the per-gate brake sums
**lifetime** cost across the gate's work units (FEAT-2026-0062), so the first
pass's recorded $14.74 counts against the ceiling even though those units are
`done`. $30.00 leaves roughly $15 of headroom for T04 and the re-armed close.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate's work units were armed at draft time. Recording the three checks
against them:

- **Runtime probe for a default/severity flip (§4).** Not applicable — no work
  unit in this gate flips a default value or a severity. Both new frontmatter
  keys are opt-in and absent-by-default; a work unit declaring neither produces
  no pre-dispatch work and no behavior change.
- **Flag-scope table (§3).** Not applicable — no work unit introduces or flips a
  behavior flag. `prep:` and `oracles:` are declarations, not flags: they name
  work to run rather than switching between code paths.
- **Escalation-predicate satisfiability (§2).** Not applicable — no check is
  raised to `ERROR` and no "zero issues" predicate is asserted. Recorded in
  PLAN.md's own section.

## Verification note — the one file two work units share

T03 edits `.specfuse/verification.yml`, which is the same file the `code` gate
set is read from. This is the harness-migration shape `.specfuse/LEARNINGS.md`
warns about: *"if a WU edits `verification.yml`, the test loader, or how the
driver's own code is imported, its sibling WUs share a broken oracle until all
land together."*

It is safe here because T03 **adds** a top-level key and edits no existing set.
Sets are read by name, so `code`, `doc`, and `plannext` resolve unchanged
throughout. T03's escalation trigger fires if that additivity turns out to be
false, which is the assumption worth blocking on rather than working around.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and
why, anything the retrospective got wrong. This is your record, not the agent's —
keep it honest.>
