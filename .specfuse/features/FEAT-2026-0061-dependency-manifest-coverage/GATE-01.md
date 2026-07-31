---
gate: 1
status: open
cost_budget_usd: 16.50
baseline:
  sha: 190e01d3b61c3e77ab372a6c2537e9579ce20dec
  probed_at: 2026-07-31T13:51:05.659154+00:00
  failing: []
---

# Gate 1 — `decision_class_paths` sees the ecosystems Specfuse targets, and says what it sees

## Definition of done

A work unit producing `pom.xml`, `build.gradle(.kts)`, `Cargo.toml`, `go.mod`,
`Gemfile`, `composer.json`, or a `*.csproj` fires `decision_class_paths` instead of
passing as `clean`; a work unit whose `produces:` the class cannot decide reports
`not_evaluable` rather than `clean`; and both the coverage scope and its limits are
documented where an operator reads them — in the `clean` reason string and in
`docs/concepts/autonomy-stop-classes.md` §3.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU, not
`close-intermediate` + `plan-next`. There is no next gate to draft.

## Cost budget

`cost_budget_usd: 16.50` — the $11.50 sum of WU estimates plus one re-attempt of
the largest WU ($5.00, the close), per the defensive padding the GATE template
prescribes while the closing-WU retry defect (#260) is open.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate's WUs are armed at draft time (`status: pending`), so the discipline below
applies to this drafting rather than to a later arm:

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md` — zero on a
  correct input, measured at 0 of 169 corpus `produces:` entries for the glob
  trigger. Confirmed before drafting.
- **Runtime probe for a default/severity flip (§4).** Not applicable: this gate adds
  a new fail-closed branch to a predicate, it does not flip an existing default or
  raise an existing check's severity. No existing verdict becomes stricter except on
  paths that genuinely are dependency manifests.
- **Flag-scope table (§3).** Not applicable: no behavior flag is introduced.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
