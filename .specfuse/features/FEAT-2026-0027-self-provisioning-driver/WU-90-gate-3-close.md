---
id: FEAT-2026-0027/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 1.50
---

<\!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 3 close — terminal: retrospective + lessons + docs + feature verdict

**Objective.** Close the feature: final `RETROSPECTIVE.md` section, promote lessons to
`.specfuse/LEARNINGS.md`, reconcile docs/roadmap, record the terminal verdict.

**Context.** This is `FEAT-2026-0027/G3-CLOSE`, the terminal close. Scaffolded at draft
time so the linter identifies gate 1 as non-terminal and gate 3 as terminal; gate 2's
`plan-next` sets its real `depends_on` and arms it. By run time the feature has shipped:
auto-sync engine (gate 1), plugin-config + drift (gate 2), doctor + first-run + legacy
migration-prune (gate 3). Reference `.specfuse/rules/result-contract.md` and
`docs/methodology.md` §6. Do NOT add a "flip PLAN.md status to done" criterion — the
driver owns the terminal flip.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` has a `## Gate 3` section + a feature-arc summary across the three
   gates, non-empty.
2. **`## Cost analysis`** reconciling each gate's planned vs actual, aggregated to a
   feature total, variances > 50% explained.
3. **`## What the loop did NOT verify`** enumerating every deferred criterion (notably
   anything needing a real multi-version upgrade across machines, or the first-run prompt
   exercised against a real TTY the loop sandbox lacks) — criterion, why, where verified.
   Required even when empty.
4. `.specfuse/LEARNINGS.md` appended with ≥ 1 durable lesson OR an explicit
   `[FEAT-2026-0027/G3-CLOSE] nothing generalizes` note.
5. Docs + roadmap reconciled — README/docs describe self-provisioning ("install global,
   run anywhere"); note the coordinated release (specfuse-loop v0.3.0 + specfuse) remains
   the operator's next step, and init.sh's v1.1 deletion is now unblocked.
6. **Terminal verdict** in this WU's `verdict:` frontmatter (`met`/`partial`/`unmet`)
   with a one-line justification.

**Do not touch.** `PLAN.md status` (driver-owned); already-passed gates' WUs; secrets;
`.git/`. May edit/create: `RETROSPECTIVE.md`, `.specfuse/LEARNINGS.md`, docs, roadmap.

**Verification.** close gate set + closing-deliverable guards + AC1–AC5 existence checks.
See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** If any gate shipped `partial` or left work blocked, reflect it in
the verdict rather than `met`. Cost-analysis inconsistency → name it, emit `status: blocked`.
