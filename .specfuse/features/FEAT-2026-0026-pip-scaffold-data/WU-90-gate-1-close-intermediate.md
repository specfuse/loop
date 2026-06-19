---
id: FEAT-2026-0026/G1-CLOSE-INTERMEDIATE
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


# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1: write `RETROSPECTIVE.md` (with `## Cost analysis` and
`## What the loop did NOT verify`), promote durable lessons to `.specfuse/LEARNINGS.md`,
and reconcile any docs implied by the new package-data layer.

**Context.** This is `FEAT-2026-0026/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped: T01
(scaffold seed as package data + packaging config), T02 (`specfuse.loop.scaffold`
resource API), T03 (`sync-scaffold.sh` + drift guard). This is the data-substrate gate;
gate 2 (`specfuse init`) builds on it. Reference `.specfuse/rules/result-contract.md`,
the `close-intermediate` notes in `.specfuse/templates/WU.template.md`, and
`docs/methodology.md` §6.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md`** at the feature root, non-empty, with a `## Gate 1` section and
   a sub-section per substantive WU (T01, T02, T03): attempts, blockers, surprises.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` (PLAN.md + per-WU
   frontmatter) against actual spend (events.jsonl + WU frontmatter): per-WU
   planned/actual/delta %, aggregated to a gate total; variance > 50% gets a rationale.
   Reference predicate v1 criteria 3 (1.5×) and 4 (2×).
3. **`## What the loop did NOT verify`** present, enumerating each deferred acceptance
   criterion (e.g. wheel-build steps verified only in CI, not the loop sandbox) — for
   each: the criterion, why deferred, where verified. Required even when empty — write
   `(nothing — every acceptance criterion was verified in-loop)`. If > 2 entries OR >
   30% of the gate's criteria, flag sizing under `## What I'd change`.
4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson OR an explicit
   `[FEAT-2026-0026/G1-CLOSE-INTERMEDIATE] nothing generalizes` note. Candidate: the
   package-data + drift-guard pattern for any canonical→packaged duplication.
5. **Docs reconciliation** — if the package-data layer changes how the scaffold is
   delivered, note it; user-facing install docs change in gate 2/3.
6. **NO terminal verdict** — intermediate close; `verdict:` not written.
7. **Existence check:**

   ```bash
   FD=.specfuse/features/FEAT-2026-0026-pip-scaffold-data
   test -s "$FD/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FD/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FD/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0026' || \
     grep -q 'nothing generalizes' "$FD/RETROSPECTIVE.md"
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx "$FD/RETROSPECTIVE.md"
   ```

**Do not touch.** May edit/create: `RETROSPECTIVE.md` (new), `.specfuse/LEARNINGS.md`
(append-only), docs iff AC5. No edits to `specfuse/loop/`, `.specfuse/scripts/`,
templates, other features, secrets, `.git/`. Drafting gate 2's WUs belongs to G1-PLAN.

**Verification.** `doc` gate set + AC7 + closing-deliverable guards. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Cost-analysis data inconsistency (frontmatter vs events.jsonl)
→ name it, emit `status: blocked`. No-op honesty: prefer "nothing generalizes" over an
invented lesson. Scope creep: if authoring gate 2 WU bodies, STOP.
