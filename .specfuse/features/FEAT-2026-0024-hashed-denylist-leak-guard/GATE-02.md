---
gate: 2
status: awaiting_review
cost_budget_usd: 8.0
# Per-gate cumulative-cost ceiling. The implementing gate (gate 1) omits this;
# the successor gate sets it to exercise the brake for the first time, per the
# GATE.template.md convention. Gate 2 ships the issue/PR-body Action (#46) plus
# the terminal close.
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 — GitHub Action scans issue/PR bodies for leaks (#46)

## Definition of done

- A GitHub Action, triggered on `issues` + `pull_request` (open/edit) and
  optionally scheduled, runs the leak-scan patterns + the committed hashed
  denylist over issue/PR titles, bodies, and comments, and fails / comments on
  a hit.
- The scan-runner logic is unit-tested in-loop against fixture issue/PR JSON
  (planted hit fails; clean passes).
- The documented limitation — edit-history is not expunged by this guard — is
  written into the Action's docs.
- Terminal close (`G2-CLOSE`) writes the feature-arc verdict; the live-Action
  trigger is operator-verified post-merge and logged in `## What the loop did
  NOT verify`.

This gate's substantive work units are drafted by gate 1's `plan-next`
(`G1-PLAN`). Until then this gate carries only the scaffolded `G2-CLOSE` entry
so lint can identify gate 1 as non-terminal.

## Reflection notes

<Written by the human at review/close time.>
