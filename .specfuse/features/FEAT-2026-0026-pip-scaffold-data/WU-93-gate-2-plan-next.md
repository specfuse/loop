---
id: FEAT-2026-0026/G2-PLAN
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


# Gate 2 plan-next — draft gate 3's (`specfuse upgrade` + init.sh shim) work units

**Objective.** Author gate 3's substantive WU files (`specfuse upgrade` from package
resources + the `init.sh` thin shim), set the real `depends_on` on the already-scaffolded
terminal `G3-CLOSE`, and write `GATE-03-REVIEW.md`. Gate 3 is terminal — no
`G3-CLOSE-INTERMEDIATE`/`G3-PLAN`; the lone `G3-CLOSE` collapses the closing ceremony.

**Context.** This is `FEAT-2026-0026/G2-PLAN`, following `G2-CLOSE-INTERMEDIATE`. Drafts
gate 3 from gate 2's retrospective + the `PLAN.md` forward arc. Gate 2 delivered
`specfuse init` (write `.specfuse/` + `.claude` wiring from package resources); gate 3
makes `specfuse upgrade <repo>` **overlay** versioned files onto an existing `.specfuse/`
and shrinks `init.sh` to a shim. `plan-next` takes the strongest model — see
`docs/methodology.md` §7.

Gate 3's expected scope (refine against the retrospective; re-scope loudly if needed):

- **`specfuse upgrade <repo>` core** — overlay versioned files (`templates/`, `rules/`,
  `verification.yml.example`, `VERSION`) from package resources onto an existing
  `.specfuse/`: **preserve** user-authored files (`LEARNINGS.md`, `verification.yml`,
  `roadmap.md`, `features/`), prune internal/removed versioned files, refresh the `.claude`
  wiring, and stamp `VERSION` — **version-gated / never-downgrade** (refuse if the
  installed seed is older than the target's `.specfuse/VERSION`). Parity with `init.sh
  --upgrade` (`init.sh:90-108` VERSIONED vs USER_AUTHORED split; `init.sh:457-475`).
- **`init.sh` thin shim** — shrink `init.sh` to delegate to the pip CLI
  (`specfuse init` / `specfuse upgrade`), preserving the deprecation banner; actual
  deletion is the later v1.1 cut, out of scope here.
- **Tests** — upgrade against a temp repo with an existing `.specfuse/`: versioned files
  refreshed, user-authored files untouched, never-downgrade refusal, VERSION stamped.

**Acceptance criteria.**

1. **Gate 3 WU files authored** (e.g. `WU-07-*.md`, `WU-08-*.md`) — each dispatchable,
   five mandatory sections, `status: draft`, a positive `planned_cost_usd`. Per-WU craft
   per `/authoring-work-units`; implementation WUs adding behavior carry a red-test (or a
   §12 exemption noted in the body).
2. **`PLAN.md` gate-3 graph updated** — real `id`/`file`/`depends_on` per drafted WU, and
   the existing terminal `G3-CLOSE` gets real `depends_on` (all gate-3 substantive WUs).
   Do **not** add a `G3-CLOSE-INTERMEDIATE`/`G3-PLAN` (gate 3 is terminal).
3. **`GATE-03-REVIEW.md`** written — the operator's pre-arm review of the gate-3 draft:
   decisions + rationale, an "if you check only three things" list, a roadmap-anchor check
   against `roadmap_goal` (does gate 3 close the init.sh-deletion arc?), and open questions
   mapped to draft WUs. (The driver's `assert_gate_review_exists` computes the filename as
   `GATE-{this_gate+1}-REVIEW.md` = `GATE-03-REVIEW.md`.)
4. **Lint clean** —
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0026-pip-scaffold-data`
   passes.
5. **No arming** — gate 3's WUs stay `draft`.

**Do not touch.** Gate 1's and gate 2's WUs and `GATE-0{1,2}.md` status (driver owns gate
flips); already-passed work; `specfuse/loop/` code and `specfuse/loop/data/`; secrets;
`.git/`. Drafts gate 3 only.

**Verification.** `plannext` gate set (the linter, AC4) + AC1–AC3 existence checks
(notably `GATE-03-REVIEW.md` non-empty). See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If gate 2's retrospective implies the `roadmap_goal` or arc
should change (e.g. the init.sh shim should be its own feature, or `specfuse upgrade`'s
prune semantics need a spec decision the loop can't make), surface it loudly in
`GATE-03-REVIEW.md` and emit `status: blocked` if it blocks a coherent gate-3 draft.
