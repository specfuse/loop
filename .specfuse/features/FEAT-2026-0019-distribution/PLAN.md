---
feature_id: FEAT-2026-0019
title: Distribution — PyPI driver + Claude Code plugin
slug: distribution
branch: feat/FEAT-2026-0019-distribution
roadmap_goal: Replace the curl-bash / init.sh-copy install with a PyPI-installable driver and a native Claude Code plugin, so consumers pip install the code and install Claude assets from a marketplace — one source of truth, versioned, pinnable.
autonomy_default: review
status: done
planned_cost_usd: 11.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Distribution — PyPI driver + Claude Code plugin

Today the driver + scaffold ship by `init.sh` copying `.specfuse/scripts/*.py` into
each consumer repo, and Claude assets ship via a `.specfuse/skills/` →
`.claude/skills/` symlink trick. Both put a bash installer in charge of state that
Python (pip) and Claude Code (plugins) already have first-class delivery channels
for. This feature moves the code into a pip package and the Claude assets into a
marketplace plugin, leaving `.specfuse/` as pure per-repo **state** (features,
`LEARNINGS.md`, `roadmap.md`, `verification.yml`) that stays in the consumer repo.

**Naming (decided at draft time, refines the roadmap):** the driver distribution is
`specfuse-loop`, imported as the `specfuse.loop` PEP 420 namespace package. The bare
`specfuse` name is **reserved** for a future umbrella meta/CLI package (introduced
with the Part C bridge command, or when the orchestrator lands) so `specfuse.loop`
and a future `specfuse.orchestrator` share one import root without the loop
monopolizing the umbrella name.

**The `.specfuse/` vs `specfuse/` split:** `.specfuse/` (dot) = per-repo state,
unchanged, always present. `specfuse/` (no dot) = Python package source, shipped via
PyPI, never copied into a consumer tree. Only executable code leaves `.specfuse/`.

This file owns the **shape**: the gate order, work-unit membership, and dependency
edges. Each WU file owns its own status; each GATE file owns its gate's status.
Only gate 1 is detailed; each later gate is drafted by the prior gate's `plan-next`.

## Forward arc (gates 2–4 drafted by plan-next)

The intended arc, captured for human forward-visibility — `plan-next` materializes
and may re-scope each gate as gate 1's results land:

- **Gate 2 — Publish.** Build wheel + sdist in GitHub Actions, OIDC trusted
  publishing, first tagged release on a `v*` tag; add the `DRIVER_VERSION` vs
  `.specfuse/VERSION` (`MIN_SCAFFOLD_VERSION`) startup skew check.
- **Gate 3 — Plugin.** Specfuse Claude assets as a marketplace plugin
  (`/plugin install specfuse@specfuse`); skills move to the `/specfuse:` namespace
  with one release of back-compat aliases; caveman hooks into the plugin's
  `hooks.json`.
- **Gate 4 — Bridge + deprecate.** `specfuse` umbrella CLI (`specfuse init/upgrade`)
  bridges pip → plugin; `init.sh` shrinks to bootstrap-then-handoff with a v1.0
  deprecation banner. Terminal gate.

## Task graph

```yaml
# Closing shape (FEAT-2026-0015):
#   Non-terminal gate (gate 1): 2-WU → close-intermediate + plan-next.
#   Terminal gate (gate 4): 1-WU → close.
#   Gates 2-3 are empty until the prior gate's plan-next drafts them. Gate 4's
#   close is scaffolded now so lint can identify gate 1 as non-terminal and the
#   terminal gate from the start; plan-next sets gate 4's real depends_on later.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0019/T01
        file: WU-01-extract-namespace-package.md
        depends_on: []
      - id: FEAT-2026-0019/T02
        file: WU-02-vendored-shims.md
        depends_on: [FEAT-2026-0019/T01]
      - id: FEAT-2026-0019/T03
        file: WU-03-test-coverage-migration.md
        depends_on: [FEAT-2026-0019/T01, FEAT-2026-0019/T02]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0019/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0019/T01
          - FEAT-2026-0019/T02
          - FEAT-2026-0019/T03
      - id: FEAT-2026-0019/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0019/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units: []   # drafted by gate 1's plan-next (Publish)
  - gate: 3
    file: GATE-03.md
    work_units: []   # drafted by gate 2's plan-next (Plugin)
  - gate: 4
    file: GATE-04.md
    work_units:
      # Terminal close scaffolded now; gate 3's plan-next sets real depends_on.
      - id: FEAT-2026-0019/G4-CLOSE
        file: WU-90-gate-4-close.md
        depends_on: []
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- WU file numbers track the correlation sub-ID (`WU-01` ↔ `/T01`); closing units use
  the reserved 90+ range so they sort last.
- T01/T02/T03 are refactor/migration WUs (moving code, switching import style, moving
  the test harness). They carry an explicit red-test exemption per
  `/authoring-work-units` §12 — the existing suite, migrated in T03, is the behavior
  safety net.
