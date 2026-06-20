---
id: FEAT-2026-0028/T01
type: implementation
status: done
attempts: 2
planned_cost_usd: 1.50
oracle_env: macos_local
produces:
  - specfuse/loop/data/docs/methodology.md
  - scripts/sync-scaffold.sh
duration_seconds: 842.88
cost_usd: 2.076964
input_tokens: 87
output_tokens: 28858
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Add the methodology docs to the pip seed

**Objective.** Ship the `deploy_docs` doc set as package data under
`specfuse/loop/data/docs/`, and extend `sync-scaffold.sh` + the drift guard to keep it
in step with the canonical `docs/`.

**Context.** This is `FEAT-2026-0028/T01`, gate 1. FEAT-2026-0026 packaged the scaffold
seed (`templates/`, `rules/`, examples, `VERSION`) but not `docs/`, so a pip-scaffolded
repo is missing `.specfuse/docs/` that `init.sh`'s `deploy_docs` provides. This WU adds
the docs to the seed (T02 makes `init`/`upgrade` write them). Canonical source is the
repo's own `docs/`; copy into the package, guarded by the drift test the way T03 of
FEAT-2026-0026 did for templates/rules. Ground in `.specfuse/rules/never-touch.md` and
`/authoring-work-units` §11.

**Red-test (§12):** the extended drift guard
(`tests/test_scaffold_data_in_sync.py::test_package_docs_match_canonical`) fails on HEAD
(docs absent from the seed) and passes after this WU syncs them.

**Acceptance criteria.**

1. `specfuse/loop/data/docs/` contains, byte-for-byte from canonical `docs/`:
   `getting-started.md`, `methodology.md`, `skills.md`,
   `concepts/ralph-lineage.md`,
   `concepts/architecture-addendum-gates-and-iterative-planning.md` (the `deploy_docs`
   set; `concepts/` subdir preserved).
2. `python -m build` produces a wheel whose contents include
   `specfuse/loop/data/docs/...` (the existing `package-data` glob `specfuse/loop/data/**`
   covers it; verify by listing the wheel).
3. `scripts/sync-scaffold.sh` also syncs `docs/` (the `deploy_docs` set) from canonical
   `docs/` into `specfuse/loop/data/docs/`. `shellcheck` clean, `bash -n` parses, the
   bats happy-path covers the docs sync.
4. The drift guard asserts every file under `specfuse/loop/data/docs/` byte-matches its
   canonical `docs/` source (and no orphans) — fails before the sync, passes after.

**Do not touch.** Canonical `docs/` content (copy FROM it); the driver modules;
`.specfuse/features/`, LEARNINGS, roadmap, verification.yml; secrets; `.git/`.

**Verification.** AC2 wheel-content listing; AC4 drift-guard (red→green); `shellcheck` +
`bash -n` + bats on the script (AC3). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If the canonical→seed mapping for any doc is ambiguous (e.g. a
doc moved/renamed since the `deploy_docs` set was defined in init.sh), emit
`status: blocked` and name the mismatch rather than guessing which file to ship.
