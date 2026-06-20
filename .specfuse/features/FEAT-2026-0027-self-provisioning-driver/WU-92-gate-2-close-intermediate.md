---
id: FEAT-2026-0027/G2-CLOSE-INTERMEDIATE
type: close-intermediate
effort: medium
status: pending
attempts: 0
planned_cost_usd: 1.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 2: write its `RETROSPECTIVE.md` section (with `## Cost
analysis` and `## What the loop did NOT verify`), promote durable lessons to
`.specfuse/LEARNINGS.md`, reconcile docs implied by the plugin-config refresh +
drift-warning behavior. Non-terminal close — no feature verdict.

**Context.** This is `FEAT-2026-0027/G2-CLOSE-INTERMEDIATE`. Gate 2 shipped T04:
`auto_sync` now refreshes the `.claude` plugin config on every applied run (closing
the equal-branch + additive-only gaps left by FEAT-2026-0026's `wire_claude`) and
warns when it corrects in-repo driver/plugin drift. Gate 3 (doctor + first-run +
legacy migration-prune) is terminal and builds on this. Append to the existing
`RETROSPECTIVE.md` (gate 1's section is already there); do not rewrite it. Reference
`.specfuse/rules/result-contract.md` and `docs/methodology.md` §6.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md`** gains a `## Gate 2` section, non-empty, covering T04:
   attempts, blockers, surprises (notably whether gate 2 collapsing to one
   substantive WU held up, and whether the marketplace value-drift decision flagged
   in `GATE-02-REVIEW.md` Open question 1 needed an escalation).
2. **`## Cost analysis`** updated (or a gate-2 sub-section added) reconciling
   `planned_cost_usd` (PLAN.md + per-WU frontmatter) against actual spend
   (events.jsonl + WU frontmatter): per-WU planned/actual/delta %, gate-2 total;
   variance > 50% gets a rationale. Reference predicate v1 criteria 3 (1.5×) and 4 (2×).
3. **`## What the loop did NOT verify`** updated, enumerating each deferred gate-2
   acceptance criterion — for each: criterion, why, where verified. Notably the
   cross-process driver-vs-Claude-Code-plugin drift (not repo-readable; deferred to
   gate 3 `doctor`). Required even when empty — write `(nothing — every acceptance
   criterion was verified in-loop)`. If > 2 entries OR > 30% of the gate's criteria,
   flag sizing under `## What I'd change`.
4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson OR an explicit
   `[FEAT-2026-0027/G2-CLOSE-INTERMEDIATE] nothing generalizes` note. Candidate
   lesson: "additive-only config writers silently drift when a driver-owned value
   changes; a refresh-on-every-run path is the fix."
5. **Docs reconciliation** — note that auto-sync now keeps the plugin config current
   on every run (not just at init/upgrade); getting-started/operating docs may need a
   line distinguishing the in-repo drift warning from gate 3's `doctor`.
6. **NO terminal verdict** — intermediate close. Drafting gate 3's WUs belongs to
   `G2-PLAN`, not here.
7. **Existence check:**

   ```bash
   FD=.specfuse/features/FEAT-2026-0027-self-provisioning-driver
   test -s "$FD/RETROSPECTIVE.md"
   grep -qE '^## Gate 2' "$FD/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FD/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FD/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0027' || \
     grep -q 'nothing generalizes' "$FD/RETROSPECTIVE.md"
   ```

**Do not touch.** May edit/create: `RETROSPECTIVE.md` (append gate-2 section),
`.specfuse/LEARNINGS.md` (append-only), docs iff AC5. No edits to `specfuse/loop/`
code, gate 1/gate 3 WUs, `PLAN.md status`, other features, secrets, `.git/`. Drafting
gate 3's WUs belongs to `G2-PLAN`. The driver owns all git.

**Verification.** `doc` gate set + AC7 + closing-deliverable guards. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Cost-analysis inconsistency → name it, emit `status: blocked`.
No-op honesty: prefer "nothing generalizes" over an invented lesson. Scope creep: if
authoring gate 3 WU bodies, STOP — that is `G2-PLAN`'s job.
