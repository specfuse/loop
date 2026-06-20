---
id: FEAT-2026-0027/G1-PLAN
type: plan-next
effort: high
status: done
attempts: 1
planned_cost_usd: 2.50
duration_seconds: 424.175
cost_usd: 2.898847
input_tokens: 9654
output_tokens: 30268
---

<\!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 plan-next — draft gate 2 (plugin-config + drift)

**Objective.** Author gate 2's substantive WU files (auto-sync refreshes the `.claude`
plugin config + driver/plugin version-drift warning), wire them into `PLAN.md`'s gate-2
graph with real `depends_on`, generate gate 2's closing sequence
(`G2-CLOSE-INTERMEDIATE` + `G2-PLAN`, gate 2 non-terminal), and write `GATE-02-REVIEW.md`.

**Context.** This is `FEAT-2026-0027/G1-PLAN`, following G1-CLOSE-INTERMEDIATE. Gate 1
shipped the auto-sync engine. Gate 2 makes auto-sync also keep the Claude plugin config
current and warn on driver/plugin version drift. Note: FEAT-2026-0026's `wire_claude`
already writes the plugin config and `upgrade_specfuse` refreshes `.claude` — so gate 2
may be lighter than expected (ensure auto-sync surfaces/refreshes it + add the drift
warning). `plan-next` takes the strongest model — see `docs/methodology.md` §7.

**Acceptance criteria.**

1. **Gate 2 WU files authored** — each dispatchable (five sections, `status: draft`,
   `planned_cost_usd`); implementation WUs adding behavior carry a red-test (or §12
   exemption). Per-WU craft per `/authoring-work-units`.
2. **`PLAN.md` gate-2 graph updated** — real `id`/`file`/`depends_on` per WU, plus
   `G2-CLOSE-INTERMEDIATE` (deps all gate-2 substantive) and `G2-PLAN`. Gate 3's terminal
   `G3-CLOSE` scaffold left intact.
3. **`GATE-02-REVIEW.md`** written — weighted toward doubt: decisions + rationale, an
   "if you check only three things" list, a roadmap-anchor check, open questions mapped to
   draft WUs (notably: how much plugin-config work remains given 0026's wire_claude
   already does it).
4. **Lint clean** —
   `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0027-self-provisioning-driver`
   passes.
5. **No arming** — gate 2's WUs stay `draft`.

**Do not touch.** Gate 1's WUs and `GATE-01.md` status (driver owns gate flips);
already-passed work; `specfuse/loop/` code; secrets; `.git/`. Drafts gate 2 only.

**Verification.** `plannext` gate set (the linter, AC4) + AC1–AC3 existence checks. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If gate 1's retrospective shows 0026's `wire_claude` already
fully covers gate 2's plugin-config scope (leaving only the drift warning), surface it in
`GATE-02-REVIEW.md` — gate 2 may collapse to a single WU or merge into gate 3; flag rather
than padding it.
