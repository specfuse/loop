---
id: FEAT-2026-0019/G1-CLOSE-INTERMEDIATE
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


# Gate 1 close-intermediate — retrospective + lessons + docs, single session

**Objective.** Close gate 1 by writing `RETROSPECTIVE.md` (with the mandatory
`## Cost analysis` and `## What the loop did NOT verify` sections), appending durable
lessons to `.specfuse/LEARNINGS.md`, and reconciling any docs/roadmap state implied by
gate 1's repackaging.

**Context.** This is `FEAT-2026-0019/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped:
- T01 — `specfuse.loop` namespace package + `pip install -e .` + console scripts.
- T02 — `.specfuse/scripts/*.py` thin shims over the package (dogfood + back-compat).
- T03 — test harness + coverage + smoke migrated to the package; full suite green.

This is the **repackaging foundation gate**. Gate 2 (Publish) builds the CI release on
top. The cost analysis should note the offline-vendored `init.sh` deferral (a known
gap T02 left explicit) and whether it should pull forward. Reference
`.specfuse/rules/result-contract.md`, `.specfuse/templates/WU.template.md` notes on
`close-intermediate`, and `docs/methodology.md` §6.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` exists** at the feature folder root, non-empty, with a
   `## Gate 1` section and a sub-section per substantive WU (T01, T02, T03) covering
   attempts, blockers, and surprises.
2. **`## Cost analysis` section** present, reconciling `planned_cost_usd` (from PLAN.md
   and per-WU frontmatter) against actual spend (from `events.jsonl` and WU
   frontmatter): per WU planned/actual/delta %, aggregated to a gate-1 total, with any
   variance > 50% given a one-paragraph rationale. Reference predicate v1 criteria 3
   (1.5×) and 4 (2×).
3. **`## What the loop did NOT verify` section** present, enumerating each acceptance
   criterion whose verification was deferred (loop-sandbox limit, cross-repo
   coordination, real-system access) — for each: the criterion, why deferred, and where
   it is actually verified. Required even when empty — write
   `(nothing — every acceptance criterion was verified in-loop)`. If the list has more
   than 2 entries OR more than 30% of the gate's criteria, flag the gate's sizing under
   a `## What I'd change` note.
4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson OR an explicit
   `[FEAT-2026-0019/G1-CLOSE-INTERMEDIATE] nothing generalizes` note. Candidate lessons:
   the PEP 420 namespace + console-scripts packaging recipe; the package-canonical /
   vendored-shim pattern for keeping one source of truth.
5. **Docs/roadmap reconciliation.** If T01–T03 changed how the driver is invoked or
   installed, reconcile `README.md` / `docs/` and the roadmap detail accordingly, or
   note explicitly that user-facing docs change in a later gate (publish/plugin).
6. **NO terminal verdict** — this is an intermediate close; `verdict:` is not written.
7. **Existence check** before declaring complete:

   ```bash
   FD=.specfuse/features/FEAT-2026-0019-distribution
   test -s "$FD/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FD/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FD/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0019' || \
     grep -q 'nothing generalizes' "$FD/RETROSPECTIVE.md"
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx "$FD/RETROSPECTIVE.md"
   ```

**Do not touch.** Files this WU may edit/create: `RETROSPECTIVE.md` (new),
`.specfuse/LEARNINGS.md` (append-only), and docs/roadmap iff AC5 requires. No edits to
`specfuse/loop/`, `.specfuse/scripts/`, templates, other features, secrets, `.git/`.
Drafting gate 2's WUs belongs to G1-PLAN, not here.

**Verification.** `doc` gate set + AC7 + the closing-deliverable guards. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.**

1. **Cost-analysis data inconsistency** — if WU frontmatter `cost_usd` disagrees with
   the `events.jsonl` attempt sum, name the discrepancy and emit `status: blocked`.
2. **No-op honesty** — if gate 1 ran on-plan with no surprises, prefer the explicit
   "nothing generalizes" note over inventing a lesson.
3. **Scope creep** — if you find yourself authoring gate 2's substantive WU bodies,
   STOP; that is G1-PLAN's job.
