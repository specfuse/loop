---
feature_id: FEAT-2026-0028
title: Umbrella CLI scaffold-API wiring + docs in the pip seed
slug: umbrella-cli-wiring
branch: feat/FEAT-2026-0028-umbrella-cli-wiring
roadmap_goal: Make specfuse init/upgrade scaffold end-to-end — rewire the umbrella CLI to call specfuse.loop.scaffold and ship docs/ in the pip seed — the last gap before init.sh deletion and the coordinated release.
autonomy_default: review
status: active
planned_cost_usd: 13.75
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Umbrella CLI scaffold-API wiring + docs in the pip seed

FEAT-2026-0026 shipped `specfuse.loop.scaffold` (`init`, `init_specfuse`,
`upgrade_specfuse`, `wire_claude`) and made `init.sh` a thin shim, but two gaps remain
(captured in 0026's gate-3 review / PR #68):

1. The umbrella `specfuse` CLI's `init`/`upgrade` subcommands are still the FEAT-2026-0019
   stubs (print curl-bash / pip-only) — they do **not** call the scaffold API, so
   `specfuse init`/`upgrade` and the init.sh shim don't scaffold end-to-end.
2. The pip seed (`specfuse/loop/data/`) ships `templates/`, `rules/`, examples, `VERSION`
   — but **no `docs/`**, whereas `init.sh` ships the methodology docs via `deploy_docs`.

This feature closes both: docs into the seed (gate 1, this repo) and the umbrella CLI
rewire (gate 2, the `specfuse/specfuse` repo).

**Decisions (set at draft time):**
- This feature builds against an **editable** `specfuse-loop` (the scaffold API is on
  `main`); it does **not** require a released `specfuse-loop`. The coordinated PyPI
  release (`specfuse-loop` v0.3.0 + `specfuse`) is the post-FEAT-2026-0027 step, OUT of
  this feature's scope.
- **Cross-repo:** gate 1 (docs-in-seed) is loop-repo work the driver can dispatch; gate 2
  (umbrella CLI rewire) lives in `specfuse/specfuse` and is done **interactively** — the
  loop driver runs in this repo and cannot cleanly drive a sibling repo (same limit as
  FEAT-2026-0019's PyPI work).
- **Out of scope:** the coordinated release/version-bumps, and FEAT-2026-0027's
  auto-sync-on-run / `doctor` / first-run prompt.

This file owns the **shape**. Each WU owns its status; each GATE owns its gate status.
Only gate 1 is detailed; gate 2 is drafted by gate 1's plan-next.

## Forward arc (gate 2 drafted by plan-next)

- **Gate 2 — umbrella CLI rewire (terminal, interactive, `specfuse/specfuse`).** Rewire
  `cli.py`: `cmd_init` → `specfuse.loop.scaffold.init(target, ci_check=...)`; `cmd_upgrade`
  → `upgrade_specfuse(target)` then pip-upgrade + plugin hint; wire `--dry-run`; tests
  against the real (no longer stub) API.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0028/T01
        file: WU-01-docs-in-seed.md
        depends_on: []
      - id: FEAT-2026-0028/T02
        file: WU-02-scaffold-writes-docs.md
        depends_on: [FEAT-2026-0028/T01]
      - id: FEAT-2026-0028/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0028/T01
          - FEAT-2026-0028/T02
      - id: FEAT-2026-0028/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0028/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    # Gate 2 is INTERACTIVE / CROSS-REPO: its substantive WUs (T03-T05) are
    # specs for work done by hand in the `specfuse/specfuse` umbrella repo, and
    # are verified THERE, not by this loop. The loop runs only the structural
    # lint of these drafts; G2-CLOSE records what the loop could not verify.
    work_units:
      - id: FEAT-2026-0028/T03
        file: WU-03-cmd-init-rewire.md
        depends_on: []
      - id: FEAT-2026-0028/T04
        file: WU-04-cmd-upgrade-rewire.md
        depends_on: []
      - id: FEAT-2026-0028/T05
        file: WU-05-dry-run-and-test-sweep.md
        depends_on:
          - FEAT-2026-0028/T03
          - FEAT-2026-0028/T04
      - id: FEAT-2026-0028/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on:
          - FEAT-2026-0028/T03
          - FEAT-2026-0028/T04
          - FEAT-2026-0028/T05
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- Gate 2 is cross-repo + interactive; its close will record what the loop could not
  verify (the umbrella repo's tests run there, not in this loop run).
