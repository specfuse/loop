---
id: FEAT-2026-0026/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.50
produces:
  - specfuse/loop/data/VERSION
  - pyproject.toml
duration_seconds: 285.068
cost_usd: 0.999448
input_tokens: 32
output_tokens: 11644
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Package the scaffold seed as package data

**Objective.** Ship the scaffold seed inside the `specfuse-loop` wheel as package data
under `specfuse/loop/data/`, copied from the canonical `.specfuse/` sources.

**Context.** This is `FEAT-2026-0026/T01`, gate 1. Today the scaffold seed (templates,
rules, examples, VERSION) ships only via `init.sh` copying from the loop repo. To let
`specfuse init`/`upgrade` (gates 2–3) scaffold from pip, the seed must live in the
package. Canonical home stays `.specfuse/{templates,rules,...}` (this repo dogfoods
them); this WU copies them into `specfuse/loop/data/` and makes setuptools ship them.
T03 adds the sync script + drift guard that keep the two in step. Ground in
`.specfuse/rules/never-touch.md`.

**Red-test exempt:** pure-data — this WU adds data files + packaging config, no behavior.

**Acceptance criteria.**

1. `specfuse/loop/data/` contains, copied byte-for-byte from canonical sources:
   `templates/` (PLAN/GATE/WU), `rules/` (all four), `verification.yml.example`,
   `roadmap.template.md`, `LEARNINGS.template.md`, `VERSION`, and a `gitignore.snippet`
   holding the loop's gitignore lines (the `!.specfuse/` + `.specfuse/**/work/` block
   init.sh writes).
2. `pyproject.toml` ships the data: `[tool.setuptools.package-data]` (or equivalent)
   includes `specfuse/loop/data/**`, and `packages.find` still scopes to `specfuse*`.
3. `python -m build` produces a wheel whose contents include `specfuse/loop/data/...`
   (verified by listing the wheel).
4. Each packaged data file byte-matches its canonical `.specfuse/` source
   (e.g. `diff specfuse/loop/data/rules/never-touch.md .specfuse/rules/never-touch.md`
   is empty for every file).

**Do not touch.** Canonical `.specfuse/{templates,rules,...}` content (this WU copies
FROM them, does not edit them); `.specfuse/features/`, LEARNINGS, roadmap,
verification.yml; the internal leak-guard files; secrets; `.git/`.

**Verification.** AC3 wheel-content listing; AC4 byte-equality `diff` over every seed
file; `ruff check specfuse` (data dir is non-python, unaffected). See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If `python -m build` cannot include the data dir without an
`importlib.resources`-incompatible layout (e.g. data outside the package), emit
`status: blocked` and name the packaging constraint rather than relocating the package.
