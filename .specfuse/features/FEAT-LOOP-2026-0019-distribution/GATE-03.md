---
gate: 3
status: passed
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 3 — Plugin

Completed **interactively**. The plugin + marketplace live in the separate
`specfuse/specfuse` umbrella repo (the decided home — roadmap Part B), so this gate's
deliverable is mostly an external repo; the loop-side change is the skill-frontmatter
fix (commit `dfee510`) needed for strict plugin validation.

## Definition of done

- New repo **`specfuse/specfuse`** (public, Apache-2.0): a Claude Code marketplace
  + the `specfuse` plugin. `/plugin marketplace add specfuse/specfuse` →
  `/plugin install specfuse@specfuse`; skills namespaced `/specfuse:`. ✓
- The 18 gate-cycle skills ship in the plugin (copied from `.specfuse/skills/`;
  loop stays canonical, sync formalized in gate 4). ✓
- `claude plugin validate` passes for both marketplace and plugin. ✓
- Skill `description:` frontmatter quoted for strict-YAML validity (loop-side fix,
  `dfee510`). ✓

## Decisions (refining roadmap Part B)

- **No caveman / personal hooks** bundled — the public plugin ships methodology
  skills only (caveman is external + per-operator). The roadmap's "caveman hooks →
  plugin hooks.json" line was written pre-public-release and is intentionally
  dropped.
- **Hard cut to `/specfuse:`** — no back-compat aliases (nothing external consumes
  the bare skill names yet).

## What the loop did NOT verify

- **Live marketplace install** — `claude plugin validate` passes, but actually
  running `/plugin marketplace add specfuse/specfuse` + `/plugin install` against
  the pushed repo is an operator step (needs a fresh Claude Code session).
- **Dogfood cutover** — this repo still uses the `.claude/skills/` symlinks (bare
  names) for its own runs; switching this repo to consume the published plugin and
  retiring the symlinks is gate 4 (cutover + init.sh deprecation).

## Reflection notes

<Written by the human at review time.>
