---
gate: 1
status: open
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — Package the scaffold data + resource API

## Definition of done

- The scaffold seed (templates, rules, examples, roadmap/LEARNINGS templates, VERSION,
  gitignore snippet) ships as package data under `specfuse/loop/data/` and is present
  in the built wheel.
- A resource API (`specfuse.loop.scaffold`) reads the packaged seed via
  `importlib.resources`, resolving from an installed wheel (not just the source tree).
- A `sync-scaffold` step copies canonical `.specfuse/` sources into the package data,
  and a drift-guard test fails CI if they diverge.
- A retrospective exists; lessons promoted to `.specfuse/LEARNINGS.md`; docs/roadmap
  reconciled. Gate 2 (`specfuse init`) work units are drafted; `GATE-01-REVIEW.md` written.

The closing sequence (close-intermediate → plan-next) is enforced by the linter. The
driver stops here for human review-and-arm.

## Reflection notes

<Written by the human at review time.>
