---
feature_id: FEAT-2026-0026
title: Scaffold-data in the pip package
slug: pip-scaffold-data
branch: feat/FEAT-2026-0026-pip-scaffold-data
roadmap_goal: Ship the scaffold seed inside the pip package so specfuse init/upgrade lay down .specfuse/ from package resources, fully replacing init.sh (unblocking its v1.1 deletion).
autonomy_default: review
status: active
planned_cost_usd: 22.00
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Scaffold-data in the pip package

FEAT-2026-0019 shipped the pip driver (`specfuse-loop`), the `specfuse` umbrella CLI,
and the Claude Code plugin — but the scaffold seed (templates, rules, examples,
roadmap/LEARNINGS templates, gitignore lines, VERSION) still lives only in the loop
repo and ships only via the bash `init.sh`. So `specfuse init` cannot scaffold a repo
from pip, and `init.sh`'s deprecation banner cannot yet be honored (v1.1 deletion is
blocked).

This feature packages that seed as package data, exposes a resource API over it, and
has `specfuse init`/`upgrade` lay it down in-process — `init.sh` becomes a thin shim.

**Decisions (set at draft time):**
- Scaffold data is sourced from the canonical `.specfuse/{templates,rules,...}` (the
  repo dogfoods them) and copied into `specfuse/loop/data/` by a `sync-scaffold` step;
  a drift-guard test keeps package data == canonical (mirrors `sync-skills.sh`).
- init/upgrade logic lives in the driver package (`specfuse.loop.scaffold`), called by
  the thin umbrella `specfuse` CLI.
- `specfuse init`/`upgrade` write `.specfuse/` **and** the `.claude` wiring (CLAUDE.md
  `@rules`, settings allowlist, plugin config `extraKnownMarketplaces`+`enabledPlugins`)
  + `.gitignore` + VERSION — a scaffolded repo is immediately working.
- `init.sh` becomes a thin shim calling `specfuse init`/`upgrade`; actual deletion is a
  later v1.1 cut.
- **Out of scope (FEAT-2026-0027):** auto-sync on a plain `specfuse-loop` run,
  `specfuse doctor`, the first-run prompt. This feature delivers the explicit
  `init`/`upgrade` commands + the data substrate they need.

This file owns the **shape**. Each WU owns its own status; each GATE owns its gate
status. Only gate 1 is detailed; later gates are drafted by the prior gate's plan-next.

## Forward arc (gates 2–3 drafted by plan-next)

- **Gate 2 — `specfuse init`.** Lay down a fresh `.specfuse/` + `.claude` wiring + plugin
  config + `.gitignore` + VERSION from package resources. Parity with init.sh INIT
  (minus the symlink trick — the plugin replaces it).
- **Gate 3 — `specfuse upgrade` + shim (terminal).** Overlay versioned files (preserve
  user-authored, prune internal, stamp VERSION, refresh `.claude`), **version-gated /
  never-downgrade**; `init.sh` → thin shim calling the CLI.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0026/T01
        file: WU-01-package-scaffold-data.md
        depends_on: []
      - id: FEAT-2026-0026/T02
        file: WU-02-resource-api.md
        depends_on: [FEAT-2026-0026/T01]
      - id: FEAT-2026-0026/T03
        file: WU-03-sync-scaffold-drift-guard.md
        depends_on: [FEAT-2026-0026/T01]
      - id: FEAT-2026-0026/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0026/T01
          - FEAT-2026-0026/T02
          - FEAT-2026-0026/T03
      - id: FEAT-2026-0026/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0026/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0026/T04
        file: WU-04-init-specfuse-core.md
        depends_on: [FEAT-2026-0026/T02]
      - id: FEAT-2026-0026/T05
        file: WU-05-claude-wiring-gitignore.md
        depends_on: [FEAT-2026-0026/T04]
      - id: FEAT-2026-0026/T06
        file: WU-06-init-integration-tests.md
        depends_on:
          - FEAT-2026-0026/T04
          - FEAT-2026-0026/T05
      - id: FEAT-2026-0026/G2-CLOSE-INTERMEDIATE
        file: WU-92-gate-2-close-intermediate.md
        depends_on:
          - FEAT-2026-0026/T04
          - FEAT-2026-0026/T05
          - FEAT-2026-0026/T06
      - id: FEAT-2026-0026/G2-PLAN
        file: WU-93-gate-2-plan-next.md
        depends_on: [FEAT-2026-0026/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      - id: FEAT-2026-0026/T07
        file: WU-07-upgrade-specfuse-core.md
        depends_on: [FEAT-2026-0026/T04]
      - id: FEAT-2026-0026/T08
        file: WU-08-init-sh-shim.md
        depends_on:
          - FEAT-2026-0026/T04
          - FEAT-2026-0026/T05
          - FEAT-2026-0026/T07
      - id: FEAT-2026-0026/T09
        file: WU-09-upgrade-integration-tests.md
        depends_on: [FEAT-2026-0026/T07]
      # Terminal gate: single G3-CLOSE collapses retro+lessons+docs+verdict.
      - id: FEAT-2026-0026/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on:
          - FEAT-2026-0026/T07
          - FEAT-2026-0026/T08
          - FEAT-2026-0026/T09
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- Packaging/build-coupled (per LEARNINGS `[FEAT-2026-0019/G1]`) — expect to run
  interactively (atomic) rather than per-WU loop dispatch where the build is involved.
