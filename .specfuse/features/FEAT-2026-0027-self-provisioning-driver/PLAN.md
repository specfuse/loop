---
feature_id: FEAT-2026-0027
title: Self-provisioning driver — auto-sync .specfuse + plugin config on run
slug: self-provisioning-driver
branch: feat/FEAT-2026-0027-self-provisioning-driver
roadmap_goal: Make a plain specfuse-loop run self-provision the project to the installed driver version — create/overlay .specfuse/ (never downgrade) + refresh the Claude plugin config — so adoption is "install global, run anywhere, done".
autonomy_default: review
status: active
planned_cost_usd: 11.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Self-provisioning driver

With FEAT-2026-0026 (scaffold API) and FEAT-2026-0028 (umbrella CLI wiring) done,
`specfuse init`/`upgrade` scaffold explicitly. This feature makes a plain
`specfuse-loop` run **self-provision**: on startup it compares the installed scaffold
version to the project's `.specfuse/VERSION` and creates/overlays the scaffold (never
downgrading), replacing today's fail-loud `check_scaffold_version`. Adoption becomes
"install specfuse globally, run it in any repo, done."

**Decisions (set at draft time):**
- **Local-edit detection** via a `.specfuse/.scaffold-manifest` (sha256 per versioned
  file, written at init/upgrade); auto-sync compares live files vs the manifest to tell a
  pristine versioned file from a user-edited one.
- **Consent:** create + unmodified-overlay proceed (with a notice); overwriting a
  user-modified versioned file PROMPTS on a TTY, else skips it + warns (never blocks the
  run). `--no-autosync` flag + a `.specfuse/config` toggle disable auto-sync. Never
  auto-commits. `--dry-run` does a read-only auto-sync report.
- **Never downgrade:** scaffold newer than the installed driver → warn + refuse (reuses
  `upgrade_specfuse`'s `ScaffoldDowngradeError` direction).
- **Out of scope:** the coordinated PyPI release + version bumps (the operator's step
  after this feature). Nothing else deferred — the legacy `scripts/`/`skills/`
  migration-prune is IN (gate 3).

This file owns the **shape**. Each WU owns its status; each GATE owns its gate status.
Only gate 1 is detailed; later gates are drafted by the prior gate's plan-next.

## Forward arc (gates 2–3 drafted by plan-next)

- **Gate 2 — plugin-config + drift.** Auto-sync refreshes the `.claude` plugin config on
  sync; warn on driver/plugin version drift.
- **Gate 3 — doctor + first-run + migrate (terminal).** `specfuse doctor` (read-only
  diagnosis), the first-run scaffold prompt, and the legacy `scripts/`/`skills/`
  migration-prune (`specfuse init --migrate`).

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0027/T01
        file: WU-01-scaffold-manifest.md
        depends_on: []
      - id: FEAT-2026-0027/T02
        file: WU-02-autosync-core.md
        depends_on: [FEAT-2026-0027/T01]
      - id: FEAT-2026-0027/T03
        file: WU-03-consent-and-toggles.md
        depends_on: [FEAT-2026-0027/T02]
      - id: FEAT-2026-0027/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0027/T01
          - FEAT-2026-0027/T02
          - FEAT-2026-0027/T03
      - id: FEAT-2026-0027/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0027/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units: []   # drafted by gate 1's plan-next (plugin-config + drift)
  - gate: 3
    file: GATE-03.md
    work_units:
      # Terminal close scaffolded now; gate 2's plan-next sets real depends_on.
      - id: FEAT-2026-0027/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on: []
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- Loop-dispatchable — all driver-side Python (`loop.py` startup + `scaffold` helpers),
  unlike FEAT-2026-0028's cross-repo gate 2.
- Auto-sync MUST never auto-commit and must no-op cleanly on an up-to-date repo (no diff
  noise mid-work).
