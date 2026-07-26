---
gate: 2
status: passed
cost_budget_usd: 20.0
baseline:
  sha: b8814be7e731f294135178b5329778493db8ecff
  probed_at: 2026-07-26T04:22:40.517192+00:00
  failing: []
---

# Gate 2 — an operator can derive a project's monitoring config

## Definition of done

An operator can run `/derive-monitoring` against a multi-component project and get
a drafted `monitoring.yml` that passes gate 1's validator, plus the local-runner
bootstrap artifacts. Concretely:

- Every implementation work unit in this gate is `done` (drafted by gate 1's
  `plan-next`; this list is filled in then).
- `.specfuse/rules/design-for-diagnosis.md` exists and seeds into scaffolded
  projects, and is **not** added to `CLAUDE.md`'s `@`-import list.
- The component-discovery reference implementation passes its fixture tests.
- The `derive-monitoring` skill exists in `plugins/specfuse/skills/` and is synced
  to `.specfuse/skills/`.
- Every fenced `yaml` block in the skill and the bootstrap artifacts validates
  clean against `lint_monitoring`.
- The terminal close writes the feature-arc verdict, `## Cost analysis`, and
  `## What the loop did NOT verify` — the last of which must name the live run
  against a real backend as post-merge operator work, with the exact re-run
  condition that would upgrade it.

Gate 2 is terminal: a single `close` WU, no `plan-next`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Carried forward from GATE-01's arming section — the diagnosability audit's
WARN-not-ERROR predicate (§2) and the operator-side symlink prerequisite are the
two that bind here.

## Reflection notes

<Written by the human at review time.>
