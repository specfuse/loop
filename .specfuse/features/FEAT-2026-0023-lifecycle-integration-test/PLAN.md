---
feature_id: FEAT-2026-0023
title: Lifecycle integration test + consolidate terminal-state ownership
slug: lifecycle-integration-test
branch: feat/FEAT-2026-0023-lifecycle-integration-test
roadmap_goal: Close the close/branch-path seam-bug class — one driver-side owner for every terminal flip (PLAN+GATE+roadmap+archive) called by both close paths, a hardened branch seam, and an end-to-end lifecycle integration test that would have caught all three bugs (#47/#48/#49) before they hit a live run.
autonomy_default: review
status: done
planned_cost_usd: 8.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Lifecycle integration test + consolidate terminal-state ownership

Three driver bugs surfaced in a single session (2026-06-16), all the same
shape — **seam bugs at handoffs between subsystems**, none catchable by the
existing unit tests because unit tests stub the handoffs:

- **#47** (fixed) — `/draft-feature` emitted a roadmap row only; auto-archive
  assumed an inline detail section, so an auto-closed drafted feature halted on
  `archive_anchor_missing`.
- **#48** — `ensure_feature_branch` crashes with a raw traceback when a dirty
  working tree (the `/pick-feature` status flips) or a stale pre-existing branch
  blocks the checkout.
- **#49** — terminal **auto-close** leaves `PLAN.md status: active`: the normal
  close path relies on the close WU's *agent* to flip PLAN.md, and the
  auto-close path runs no agent while `fire_terminal_flips` never touches
  PLAN.md.

Root pattern: the methodology's machinery (auto-close predicate 0018,
draft-feature skill, archive automation 0010) grew faster than its integration
coverage, and the gaps only execute at real feature boundaries — rare events
that the first true end-to-end **autonomous** runs finally exercised without a
human silently papering over each seam.

This feature closes the **class**, not the three instances:

1. **Consolidate terminal-state ownership** — one driver-side function is the
   authoritative owner of every terminal flip (PLAN.md included), called
   identically by both close paths. Subsumes the #49 fix.
2. **Harden the branch seam** — `ensure_feature_branch` surfaces git's stderr,
   carries expected `/pick-feature` flips onto the new branch, and detects a
   stale/divergent existing branch. Fixes #48.
3. **End-to-end lifecycle integration test** — a harness that drives a synthetic
   feature through draft → pick → loop → terminal close (BOTH the dispatched and
   auto-close paths) → archive → wrap-ready, asserting the terminal invariant.
   The layer that would have caught all three bugs.

This file owns the **shape** of the feature: the gate order, which work units
belong to each gate, and the dependency edges between them. It does **not** own
status — each WU file owns its own status, and each GATE file owns its gate's
status.

## Scope OUT

- **New lifecycle behavior.** This adds test + refactor coverage of the existing
  lifecycle, not new capability.
- **Rewriting the auto-close predicate** (FEAT-2026-0018). It stands; T01 only
  changes who applies the terminal flips, not when the gate auto-closes.
- **Broadening the close ceremony** beyond the terminal-flip ownership move.
- **Cost levers.** Methodology robustness, not cost control.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0023/T01
        file: WU-01-consolidate-terminal-flips.md
        depends_on: []
      - id: FEAT-2026-0023/T03
        file: WU-03-branch-seam-hardening.md
        depends_on: []
      - id: FEAT-2026-0023/T02
        file: WU-02-lifecycle-integration-test.md
        depends_on:
          - FEAT-2026-0023/T01
          - FEAT-2026-0023/T03
      - id: FEAT-2026-0023/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0023/T01
          - FEAT-2026-0023/T02
          - FEAT-2026-0023/T03
```

## Notes

- **Single terminal gate, three substantive WUs, one `close` ceremony.** Three
  substantive WUs (≤ 4) → single gate + single `close` per the ceremony-
  proportionality size rule (`docs/methodology.md §6`, landed FEAT-2026-0021).
- **T01** (terminal-state consolidation) and **T03** (branch-seam hardening) are
  independent driver refactors and can land in either order. **T02** (the
  lifecycle test) depends on both — it asserts the consolidated flips and the
  hardened branch seam end-to-end.
- Dependencies live here, not in WU frontmatter.
- Each substantive WU declares `model: opus` and `effort: high`: the changes are
  in the driver's terminal-flip correctness path (a regression silently breaks
  every future close) and the integration test is intricate (real git tmp repo +
  stubbed dispatch + the auto-close predicate). LEARNINGS
  `[FEAT-2026-0017/G1-CLOSE]` documents Sonnet hollow-passing driver-guard
  shapes.
- Each substantive WU is red-test-first (`/authoring-work-units` §12): the
  #49 reproduction is T01's red test, the #48 crash reproduction is T03's, and
  T02's lifecycle assertions fail against the pre-T01/T03 driver.
- **Autonomy `review`**: the driver halts at the gate boundary for human arm.
  Apt — this feature fixes the auto-close terminal path, so dogfooding `auto`
  here would run the very path under repair.
