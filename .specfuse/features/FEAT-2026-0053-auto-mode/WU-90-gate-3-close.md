---
id: FEAT-2026-0053/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
auto_close_disabled: true
---

# Close the feature — terminal verdict (placeholder)

**Objective.** Terminal close for FEAT-2026-0053: retrospective, lessons, docs,
and the feature-arc verdict, collapsed into one session. This file is a
`status: draft` placeholder — `G2-PLAN` rewrites it (and sets real
`depends_on`) when it drafts gate 3's substantive work units.

**Context.** Correlation ID `FEAT-2026-0053/G3-CLOSE`. Pre-declared at feature
drafting so the linter reads gate 3 as the non-empty terminal gate and gate 1
as non-terminal. Read `.specfuse/rules/close-discipline.md` §4 before drafting
the real body — `assert_verdict_well_formed` applies here.

**Close obligations** (to be made concrete by `G2-PLAN`):

1. **Oracles re-run fresh (§1)** — every oracle the feature's criteria name,
   full commands, exit codes read directly.
2. **Hedged follow-up record (§2)** — on `met_locally`, a named record per
   unmet criterion with the exact re-run condition that upgrades it to `met`.
3. **Consumer-visible contract changes (§3)** — enumerate across all gates, or
   write exactly `n/a — no consumer-visible contract change`.

**Acceptance criteria.**

1. Placeholder — drafted by `G2-PLAN` from gate 2's retrospective. Must include
   the `## Cost analysis` reconciliation bullet and the
   `## What the loop did NOT verify` enumeration bullet.

**Do not touch.** Placeholder — `G2-PLAN` writes the real boundaries. The
driver owns all git.

**Verification.** The `plannext` gate set; real oracle list drafted by
`G2-PLAN`.

**Escalation triggers.** Placeholder — drafted by `G2-PLAN`. Blocked remains a
respectable outcome (`result-contract.md` rule 4).
