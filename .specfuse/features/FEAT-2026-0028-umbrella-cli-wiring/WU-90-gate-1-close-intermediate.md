---
id: FEAT-2026-0028/G1-CLOSE-INTERMEDIATE
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
reconcile any docs implied by the docs-in-seed change.

**Context.** This is `FEAT-2026-0028/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped: T01 (docs in
the pip seed + sync/drift guard), T02 (`scaffold.py` writes/overlays `.specfuse/docs/`).
Gate 2 (the umbrella CLI rewire) is interactive/cross-repo. Reference
`.specfuse/rules/result-contract.md` and `docs/methodology.md` §6.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md`** at the feature root, non-empty, `## Gate 1` section with a
   sub-section per substantive WU (T01, T02): attempts, blockers, surprises.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` (PLAN.md + per-WU
   frontmatter) against actual spend (events.jsonl + WU frontmatter): per-WU
   planned/actual/delta %, gate total; variance > 50% gets a rationale. Reference
   predicate v1 criteria 3 (1.5×) and 4 (2×).
3. **`## What the loop did NOT verify`** present, enumerating each deferred acceptance
   criterion (e.g. wheel build verified only in CI) — for each: criterion, why, where
   verified. Required even when empty — write
   `(nothing — every acceptance criterion was verified in-loop)`. If > 2 entries OR >
   30% of the gate's criteria, flag sizing under `## What I'd change`.
4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson OR an explicit
   `[FEAT-2026-0028/G1-CLOSE-INTERMEDIATE] nothing generalizes` note.
5. **Docs reconciliation** — note that the methodology docs now ship in the pip seed.
6. **NO terminal verdict** — intermediate close.
7. **Existence check:**

   ```bash
   FD=.specfuse/features/FEAT-2026-0028-umbrella-cli-wiring
   test -s "$FD/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FD/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FD/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0028' || \
     grep -q 'nothing generalizes' "$FD/RETROSPECTIVE.md"
   { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | grep -qx "$FD/RETROSPECTIVE.md"
   ```

**Do not touch.** May edit/create: `RETROSPECTIVE.md` (new), `.specfuse/LEARNINGS.md`
(append-only), docs iff AC5. No edits to `specfuse/loop/`, templates, other features,
secrets, `.git/`. Drafting gate 2's WUs belongs to G1-PLAN.

**Verification.** `doc` gate set + AC7 + closing-deliverable guards. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Cost-analysis data inconsistency → name it, emit
`status: blocked`. No-op honesty: prefer "nothing generalizes" over an invented lesson.
Scope creep: if authoring gate 2 WU bodies, STOP.
