---
id: FEAT-2026-0026/G2-CLOSE-INTERMEDIATE
type: close-intermediate
effort: medium
status: draft
attempts: 0
planned_cost_usd: 1.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 2 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 2: append a `## Gate 2` section to `RETROSPECTIVE.md` (with
`## Cost analysis` and `## What the loop did NOT verify`), promote durable lessons to
`.specfuse/LEARNINGS.md`, and reconcile docs implied by `specfuse init`.

**Context.** This is `FEAT-2026-0026/G2-CLOSE-INTERMEDIATE`. Gate 2 shipped the
`specfuse init` substrate: T04 (`init_specfuse` core writer + refusal contract), T05
(`.claude` wiring + `.gitignore`, merge-safe, plugin config replacing the symlink trick),
T06 (end-to-end init against the installed wheel + temp repo). This is intermediate —
gate 3 (`specfuse upgrade` + init.sh shim, terminal) builds on it. Reference
`.specfuse/rules/result-contract.md`, the `close-intermediate` notes in
`.specfuse/templates/WU.template.md`, and `docs/methodology.md` §6.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md`** gains a `## Gate 2` section (append; do not clobber gate 1's),
   non-empty, with a sub-section per substantive WU (T04, T05, T06): attempts, blockers,
   surprises.
2. **`## Cost analysis`** reconciling each gate-2 WU's `planned_cost_usd` against actual
   spend (events.jsonl + WU frontmatter): per-WU planned/actual/delta %, aggregated to a
   gate-2 total; variance > 50% gets a rationale. Reference predicate v1 criteria 3 (1.5×)
   and 4 (2×). (If gate 1's `## Cost analysis` already exists, extend it with gate 2 —
   keep one coherent section.)
3. **`## What the loop did NOT verify`** present, enumerating each deferred acceptance
   criterion (notably T06's installed-wheel leg if it ran skip-guarded in the sandbox) —
   for each: the criterion, why deferred, where verified. Required even when empty — write
   `(nothing — every acceptance criterion was verified in-loop)`.
4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson OR an explicit
   `[FEAT-2026-0026/G2-CLOSE-INTERMEDIATE] nothing generalizes` note. Candidate: merge-safe
   `.claude`-config writing (parse-merge-rewrite JSON vs blind append) as a reusable
   scaffolding pattern.
5. **Docs reconciliation** — if `specfuse init` changes how a repo is bootstrapped, note
   it; the full user-facing install-docs rewrite + init.sh shim land in gate 3.
6. **NO terminal verdict** — intermediate close; `verdict:` not written.
7. **Existence check:**

   ```bash
   FD=.specfuse/features/FEAT-2026-0026-pip-scaffold-data
   test -s "$FD/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FD/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FD/RETROSPECTIVE.md"
   grep -qE '^#{1,3} Gate 2' "$FD/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0026' || \
     grep -q 'nothing generalizes' "$FD/RETROSPECTIVE.md"
   ```

**Do not touch.** May edit/create: `RETROSPECTIVE.md` (append gate 2), `.specfuse/LEARNINGS.md`
(append-only), docs iff AC5. No edits to `specfuse/loop/`, `specfuse/loop/data/`,
`.specfuse/scripts/`, templates, other features, secrets, `.git/`. Drafting gate 3's WUs
belongs to G2-PLAN — if you start authoring gate 3 WU bodies here, STOP.

**Verification.** `doc` gate set + AC7 + closing-deliverable guards. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Cost-analysis data inconsistency (frontmatter vs events.jsonl) →
name it, emit `status: blocked`. No-op honesty: prefer "nothing generalizes" over an
invented lesson. Scope creep: authoring gate 3 WU bodies is G2-PLAN's job.
