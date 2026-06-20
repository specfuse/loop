---
id: FEAT-2026-0027/G2-PLAN
type: plan-next
effort: high
status: done
attempts: 1
planned_cost_usd: 2.50
duration_seconds: 604.285
cost_usd: 2.561614
input_tokens: 9378
output_tokens: 30319
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 plan-next — draft gate 3 (doctor + first-run + migrate, terminal)

**Objective.** Author gate 3's substantive WU files (`specfuse doctor` read-only
diagnosis, the first-run scaffold prompt, the legacy `scripts/`/`skills/`
migration-prune via `specfuse init --migrate`), wire them into `PLAN.md`'s gate-3
graph with real `id`/`file`/`depends_on`, set the **real `depends_on`** on the
already-scaffolded terminal `G3-CLOSE` (`WU-90-gate-3-close.md`), and write
`GATE-03-REVIEW.md`. Gate 3 is **terminal** — it keeps the single-WU `close`, not a
close-intermediate/plan-next pair.

**Context.** This is `FEAT-2026-0027/G2-PLAN`, following `G2-CLOSE-INTERMEDIATE`.
Gate 2 shipped T04 (plugin-config refresh + in-repo drift warning). Gate 3 is the
terminal gate; its skeleton (`GATE-03.md`) names the scope: `specfuse doctor`
(read-only diagnosis of driver/scaffold versions, plugin state, **cross-process
drift** the in-repo warning can't see), the first-run scaffold prompt, and the legacy
`scripts/`/`skills/` migration-prune (`specfuse init --migrate`). Note the umbrella
`specfuse` CLI is **cross-repo** (FEAT-2026-0026/0028 split — this repo ships
`specfuse-loop` / `specfuse-lint` only); confirm where `doctor` / `--migrate` land
before drafting their CLI surface (it may be the `specfuse.loop.scaffold` API + a
cross-repo CLI hook, mirroring init/upgrade). `plan-next` takes the strongest model —
see `docs/methodology.md` §7.

**Acceptance criteria.**

1. **Gate 3 substantive WU files authored** — each dispatchable (five sections,
   `status: draft`, `planned_cost_usd`); implementation WUs adding behavior carry a
   red-test (or §12 exemption). Per-WU craft per `/authoring-work-units`. Mint IDs
   from the next unused ordinal (T05 onward — T01–T04 are spent).
2. **`PLAN.md` gate-3 graph updated** — real `id`/`file`/`depends_on` per gate-3
   substantive WU, and the existing terminal `G3-CLOSE` row's `depends_on` set to all
   gate-3 substantive WUs (it is `[]` today). Keep `G3-CLOSE` the single terminal
   `close` WU — do **not** convert gate 3 to a close-intermediate/plan-next pair.
   Gate 1 + gate 2 graphs left intact.
3. **`GATE-03-REVIEW.md`** written — weighted toward doubt: decisions + rationale, an
   "if you check only three things" list, a roadmap-anchor check, a **Cross-repo /
   invented-value contracts** table (per `/authoring-work-units` §8 — `doctor` and
   `--migrate` CLI names/flags are cross-repo values to verify, not invent), and open
   questions mapped to draft WUs (notably: can `doctor` actually read the Claude-Code
   installed plugin version, and what the migration-prune must NOT delete).
4. **Lint clean** —
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0027-self-provisioning-driver`
   passes.
5. **No arming** — gate 3's WUs stay `draft` (including `G3-CLOSE`).

**Do not touch.** Gate 1 + gate 2 WUs and their `GATE-0N.md` status (driver owns gate
flips); already-passed work; `specfuse/loop/` code; secrets; `.git/`. Drafts gate 3
only. The driver owns all git — edit files only.

**Verification.** `plannext` gate set (the linter, AC4) + AC1–AC3 existence checks
(the new gate-3 WU files exist + are non-empty; `GATE-03-REVIEW.md` exists). See
`.specfuse/skills/verification/SKILL.md`. Filename note: the driver's
`assert_gate_review_exists` expects `GATE-{this_gate+1:02d}-REVIEW.md`; for a gate-2
plan-next that is `GATE-03-REVIEW.md` (the gate this WU plans), even though the WU is
in gate 2.

**Escalation triggers.** If `doctor` cannot read the Claude-Code-installed plugin
version from any repo-readable surface (so its "plugin state / drift" diagnosis is
necessarily partial), surface it in `GATE-03-REVIEW.md` rather than drafting a WU that
silently degrades. If the legacy `scripts/`/`skills/` migration-prune risks deleting a
file the loop still depends on (e.g. `.specfuse/scripts/lint_plan.py`, which is a live
shim), flag the keep-list as an open question rather than drafting a blanket prune.
