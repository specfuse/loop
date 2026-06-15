---
id: FEAT-2026-0020/T17
type: implementation
status: draft
attempts: 0
oracle_env: macos_local
planned_cost_usd: 0.80
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Write FLIP-CHECKLIST.md — every visibility-flip step with owner + rollback

**Objective.** Author `FLIP-CHECKLIST.md` at the feature-folder root: an ordered, operator-
runnable checklist of every step to flip the repo from private to public, each step naming
its **owner** and its **rollback**.

**Context.** Final authoring WU of FEAT-2026-0020 gate 2. The visibility flip itself happens
outside the loop (GitHub UI, human decision); this checklist is what makes the operator's
flip path explicit enough to run unaided (the feature-arc verdict question in `G2-CLOSE`).
Correlation ID `FEAT-2026-0020/T17`. Depends on every hygiene + guard WU (T01–T07) because
the checklist references their outputs as pre-flip gates: README/CONTRIBUTING/SECURITY/
CODE_OF_CONDUCT present (T01–T03), issue/PR templates + dependabot landed (T04–T05), the
leak-scan guard installed + CI gate green (T06–T07), the deferred history-rewrite open
action from gate 1 (`RETROSPECTIVE.md` §"What the loop did NOT verify" entries 5–6) closed
or explicitly accepted.

Grounding: `RETROSPECTIVE.md` (gate-1 open actions, especially the phase-2 history rewrite
and the GitHub edit-history residual risk), `history-scrub/RUNBOOK.md`, `GATE-02-REVIEW.md`
(the PyPi-tag-step open verification — whether the checklist stops at the GitHub flip or
includes FEAT-2026-0019's first PyPi tag).

Binding rules in `.specfuse/rules/` apply.

Red-test exempt: markdown runbook artifact — no executable shipped (the guard scripts ship
in T06/T07), no behavioral surface introduced here. `/authoring-work-units` §11 does not
apply (pure-file artifact).

**Acceptance criteria.**

1. `FLIP-CHECKLIST.md` exists at the feature-folder root with an **ordered** list of flip
   steps from pre-flip verification through the GitHub visibility change to post-flip
   confirmation.
2. **Every step names an explicit owner** (operator / maintainer / CI) and an explicit
   **rollback** (how to revert that step, or an explicit "not recoverable — proceed only
   when X" note for irreversible steps).
3. Pre-flip steps reference the gate-2 deliverables as gating checks: hygiene files present
   (T01–T05), leak-scan guard installed + CI gate green (T06–T07), gate-1 deferred
   history-rewrite open action closed or explicitly operator-accepted.
4. The checklist's scope boundary is explicit: it either stops at the GitHub visibility
   flip OR includes the FEAT-2026-0019 PyPi-tag step — per the operator's decision recorded
   in `GATE-02-REVIEW.md` Open Verifications (do not silently pull 0019 scope in).
5. No private-org names, personal paths, or internal URLs introduced.

**Do not touch.**

- Any gate-2 WU output files (the checklist *references* them; it does not edit them).
- `RETROSPECTIVE.md`, `PLAN.md`, gate-1 WU files (read-only references).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` — pass unchanged on a docs-only edit.
- Existence: `test -s .specfuse/features/FEAT-2026-0020-public-readiness-prep/FLIP-CHECKLIST.md`.
- Owner+rollback coverage: every step row carries an owner and a rollback field
  (mechanically checkable — e.g. each step line/section contains `Owner:` and `Rollback:`).
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. **Step with unclear owner or unrecoverable rollback.** Any step whose owner is unclear
   or whose rollback is "not recoverable" must be flagged in `GATE-02-REVIEW.md`, not
   papered over with a vague entry — emit `status: blocked` if the gap is load-bearing
   (`GATE-02.md` escalation trigger 3).
2. **PyPi-tag scope undecided.** If `GATE-02-REVIEW.md`'s PyPi-tag Open Verification is
   still unchecked at dispatch, emit `status: blocked` — do not unilaterally decide whether
   to include FEAT-2026-0019 scope (cross-feature coupling).
