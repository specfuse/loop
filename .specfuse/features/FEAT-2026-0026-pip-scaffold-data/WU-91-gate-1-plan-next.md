---
id: FEAT-2026-0026/G1-PLAN
type: plan-next
effort: high
status: pending
attempts: 0
planned_cost_usd: 2.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 plan-next — draft gate 2's (`specfuse init`) work units

**Objective.** Author gate 2's substantive WU files (`specfuse init` from package
resources), wire them into `PLAN.md`'s gate-2 graph with real `depends_on`, generate
gate 2's closing sequence (`G2-CLOSE-INTERMEDIATE` + `G2-PLAN`, gate 2 being
non-terminal), and write `GATE-01-REVIEW.md`.

**Context.** This is `FEAT-2026-0026/G1-PLAN`, following G1-CLOSE-INTERMEDIATE. Drafts
gate 2 from gate 1's retrospective + the `PLAN.md` forward-arc. Gate 1 delivered the
package data + `specfuse.loop.scaffold` API; gate 2 makes `specfuse init <repo>` lay a
fresh `.specfuse/` + `.claude` wiring from it. `plan-next` takes the strongest model —
see `docs/methodology.md` §7.

Gate 2's expected scope (refine against the retrospective; re-scope loudly if needed):

- **`specfuse init <repo>` core** — write `.specfuse/` from `specfuse.loop.scaffold`:
  templates, rules, features/, verification.yml seed (or detect ci-check like init.sh),
  roadmap + LEARNINGS seeds, VERSION stamp. Refuse if `.specfuse/` exists (point at
  `specfuse upgrade`). Lives in `specfuse.loop.scaffold`, called by the umbrella CLI.
- **`.gitignore` + `.claude` wiring** — write the gitignore snippet; wire CLAUDE.md
  `@rules` imports, the loop-script settings allowlist, and the plugin config
  (`extraKnownMarketplaces` + `enabledPlugins`), merge-safe. Parity with init.sh INIT
  minus the symlink trick.
- **Tests** against a temp repo: full `.specfuse/` + `.claude` produced from the
  installed wheel; idempotency/refusal behavior; gitignore + plugin-config correctness.

**Acceptance criteria.**

1. **Gate 2 WU files authored** (e.g. `WU-04-*.md`, `WU-05-*.md`) — each dispatchable,
   five mandatory sections, `status: draft`, a `planned_cost_usd`. Per-WU craft per
   `/authoring-work-units`; implementation WUs adding behavior carry a red-test (or §12
   exemption).
2. **`PLAN.md` gate-2 graph updated** — real `id`/`file`/`depends_on` per WU, plus
   `G2-CLOSE-INTERMEDIATE` (deps all gate-2 substantive) and `G2-PLAN` (deps
   `G2-CLOSE-INTERMEDIATE`). Gate 3's terminal `G3-CLOSE` scaffold left intact.
3. **`GATE-01-REVIEW.md`** written — weighted toward doubt: decisions + rationale, an
   "if you check only three things" list, a roadmap-anchor check against `roadmap_goal`,
   and open questions mapped to draft WUs.
4. **Lint clean** —
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0026-pip-scaffold-data`
   passes.
5. **No arming** — gate 2's WUs stay `draft`.

**Do not touch.** Gate 1's WUs and `GATE-01.md` status (driver owns gate flips);
already-passed work; `specfuse/loop/` code; secrets; `.git/`. Drafts gate 2 only —
not gates 3 (its prior gate's plan-next does that).

**Verification.** `plannext` gate set (the linter, AC4) + AC1–AC3 existence checks. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If gate 1's retrospective implies the `roadmap_goal` or arc
should change (e.g. the `.claude` plugin-config write belongs in 0027 after all, or the
init/upgrade logic should live in the umbrella not the driver), surface it loudly in
`GATE-01-REVIEW.md` and emit `status: blocked` if it blocks a coherent gate-2 draft.
