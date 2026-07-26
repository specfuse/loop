---
gate: 1
status: awaiting_review
baseline:
  sha: cd3e78fc9eaca96d17486a8b35c748a5517fb293
  probed_at: 2026-07-26T03:57:33.045223+00:00
  failing: []
---

# Gate 1 — the monitoring contract is machine-checkable

## Definition of done

A `monitoring.yml` can be structurally validated by a committed linter, the shipped
example is validated by this repo's own `code` gates, and the example seeds into
freshly-scaffolded projects. Concretely:

- Every implementation work unit in this gate is `done` (T01, T02, T03).
- `python3 -c "from specfuse.loop.lint_monitoring import validate_monitoring"` exits 0.
- The `monitoring-example-lint` gate in `.specfuse/verification.yml` passes.
- A retrospective exists (feature-local `RETROSPECTIVE.md`) with `## Cost analysis`
  and `## What the loop did NOT verify`.
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Gate 2's work units are drafted (`status: draft`) and `GATE-02-REVIEW.md` is written.

The closing sequence for this non-terminal gate is `close-intermediate` →
`plan-next`. The driver runs the gate unattended, then stops here for human
review-and-arm: read `GATE-02-REVIEW.md`, accept or edit the drafted gate-2 work
units, flip the accepted ones to `pending`, set this gate's status to `passed`, and
re-run.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Escalation-predicate satisfiability (§2).** Gate 2 introduces the
  diagnosability audit. Confirm its gap findings are **WARN, not ERROR** before
  arming — a populated codebase predating the design-for-diagnosis rule violates it
  everywhere by construction, so an ERROR predicate is unsatisfiable on real input.
  PLAN.md records the answer; the arming review confirms the drafted WU honors it.
- **Runtime probe for a default/severity flip (§4).** If any gate-2 WU flips a
  default or a severity, apply it locally, run the exact command that WU's tests
  gate will run, and paste the failure list into `GATE-02-REVIEW.md`.
- **Flag-scope table (§3).** Applies to any gate-2 WU introducing a behavior dial
  (`runner`, `diagnose`, `autofix` are dials, but gate 2 only *declares* them — a
  WU that makes one change driver behavior needs the table).
- **Operator prerequisite.** If a gate-2 WU ships the `derive-monitoring` skill,
  confirm the `.claude/skills/derive-monitoring` symlink is listed as an
  operator-side pre-dispatch step, not agent work — the sandbox denies it to a
  dispatched session even with `unsandboxed: true`.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted gate 2 and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
