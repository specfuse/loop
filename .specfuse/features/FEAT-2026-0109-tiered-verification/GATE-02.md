---
gate: 2
status: open
---

# Gate 2 — the per-attempt tier

Drafted by gate 1's `plan-next`, not now. Its definition of done, its work
units and its own `feature_oracle` are authored together at that point — a gate
with no substantive units carries no oracle requirement (#3262), and the
requirement lands the moment `plan-next` gives this gate real work.

Scope, per `PLAN.md`: per attempt, the unit's declared tests, tests touching
changed files, lint, and the feature oracle; once per gate before the close,
the full suite with coverage, bats, leak-scan and security.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Authored with this gate's work units by the prior gate's `plan-next`. The
runtime-probe (§4), flag-scope (§3) and predicate-satisfiability (§2) checks
are assessed against the units drafted then, not now — there is nothing to arm
until this gate has work.
