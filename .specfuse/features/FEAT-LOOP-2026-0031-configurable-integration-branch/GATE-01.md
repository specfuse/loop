---
gate: 1
status: passed
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — A feature's base branch is declared once and honored everywhere

## Definition of done

- A feature can declare `base:` in PLAN.md frontmatter; absent, resolution falls
  through to `_default_branch()` and behavior is unchanged from today.
- The declared base is honored by branch creation, by the staleness guard and its
  hint text, and by PR creation — each reading one resolver, not a threaded arg.
- A declared base that is missing locally is classified (typo / unfetched /
  remote-unreachable) and each case reports its own cause; the happy path makes no
  network call.
- Every implementation work unit in this gate is `done`.
- The terminal `close` WU has written RETROSPECTIVE.md, promoted generalizable
  lessons to `.specfuse/LEARNINGS.md`, reconciled planned vs actual cost, and
  enumerated what the loop did not verify.

Single gate → single terminal `close` (3 substantive WUs, per `docs/methodology.md`
§6 ceremony proportionality). No `close-intermediate`, no `plan-next`. If the gate
goes off-plan (blocked WU, replan, cost overrun) the `gate_eval` predicate disables
auto-close and dispatches the close as a normal reflective session.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
