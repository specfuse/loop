---
gate: 1
status: open
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — The lifecycle closes correctly through one owner, end-to-end tested

## Definition of done

- A single driver-side function is the authoritative owner of every terminal
  flip (PLAN.md + GATE + roadmap row + archive), called by BOTH the dispatched
  and auto-close paths; the terminal auto-close no longer leaves PLAN.md
  `active` (#49) (T01).
- `ensure_feature_branch` surfaces git stderr instead of a raw traceback,
  carries `/pick-feature` flips onto the new branch, and detects a
  stale/divergent existing branch (#48) (T03).
- An end-to-end lifecycle integration test drives a synthetic feature through
  draft → pick → loop → close (dispatched AND auto-close) → archive → wrap-ready
  and asserts the terminal invariant; it fails against the pre-fix driver (T02).
- Every implementation WU in this gate is `done`.
- A retrospective exists; durable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Docs reflect what was built (close-WU PLAN-flip AC guidance reconciled).
- The terminal feature-arc verdict is written.

Single-gate feature: the `close` WU collapses retrospective + lessons + docs +
terminal verdict. Autonomy `review` — the driver halts here for human arm.

## Reflection notes

<Written by the human at review time. Did the consolidated terminal-flip owner
actually unify both paths, or just bolt PLAN.md onto the auto-close branch?
Does the lifecycle test exercise the real seams or stub them away? Keep it
honest — this feature's whole point is that the seams were untested.>
