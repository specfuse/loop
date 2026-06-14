---
id: FEAT-2026-0016/G1-CLOSE-INTERMEDIATE
type: close-intermediate
effort: medium
status: draft
attempts: 0
planned_cost_usd: 1.20
generated_surfaces: []
---

# Gate 1 close-intermediate — retrospective + lessons + docs, single session

**Objective.** Close gate 1 by writing `RETROSPECTIVE.md` (with the
mandatory `## Cost analysis` section), appending durable lessons to
`.specfuse/LEARNINGS.md`, and reconciling any docs/roadmap state
implied by gate 1's substantive WUs.

**Context.** This is `FEAT-2026-0016/G1-CLOSE-INTERMEDIATE`. Gate 1
shipped:
- T01 — `attempt_outcome` emission completion + standardization in
  `loop.py`
- T02 — re-arm WU frontmatter contract + cumulative-fold logic
- T03 — unit tests covering both

This is the **data-layer foundation gate**. Gate 2 wires consumers
(spinning-detector hook, `/gate-status`, `/unblock-wu`). The cost
analysis should note how T01's bootstrap gap manifested (its own
events lacked the new payload fields).

Reference: `.specfuse/rules/result-contract.md`,
`.specfuse/templates/WU.template.md` notes on `close-intermediate`,
`[FEAT-2026-0015/T07]`'s closing-deliverable guards.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` exists** at the feature folder root.
   Non-empty. Contains:
   - `## Gate 1` section.
   - Sub-sections per substantive WU (T01, T02, T03): attempts,
     blockers, surprises.
   - `## Cost analysis` section (required — AC2).
   - Predicate self-check section: paste output of
     `python3 .specfuse/scripts/gate_eval.py backtest FEAT-2026-0016
     --gate 1` verbatim.

2. **`## Cost analysis` section** reconciles `planned_cost_usd` per
   WU (from PLAN.md + per-WU frontmatter) against actual spend (from
   events.jsonl + WU frontmatter). For each WU: planned, actual,
   delta %. Aggregate to gate-1 total. Variance > 50% requires a
   one-paragraph rationale. Reference predicate v1 criteria 3 (1.5×)
   and 4 (2×).

3. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson
   OR explicit `[FEAT-2026-0016/G1-CLOSE-INTERMEDIATE] nothing
   generalizes` note. Likely lessons to consider:
   - Standardized event payload contracts deserve a single
     emission helper (the four-site migration pattern).
   - Failure-class taxonomy locked at v1 with explicit `other`
     bucket avoids mid-feature taxonomy drift.

4. **No code edits required for docs.** Gate 1 ships internal
   driver + test surfaces with no operator-facing prose. If T01
   or T02 surfaced a need for methodology doc updates, fold here
   or defer to gate 3 (T09 docs WU).

5. **NO terminal verdict.** Intermediate close; `verdict:` not
   written here.

6. **Existence check** before declaring complete:

   ```bash
   test -s .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/RETROSPECTIVE.md
   grep -qE '^## Cost analysis' .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/RETROSPECTIVE.md
   grep -q 'predicate=v1' .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/RETROSPECTIVE.md
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0016' || \
     grep -q 'nothing generalizes' .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/RETROSPECTIVE.md
   git diff --name-only HEAD | grep -qx '.specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/RETROSPECTIVE.md'
   ```

**Do not touch.** Files this WU may edit/create:
- `RETROSPECTIVE.md` (new)
- `.specfuse/LEARNINGS.md` (append-only)
- Docs files iff T01/T02 required them (unlikely)

No edits to: `loop.py`, templates, other features, secrets, `.git/`.

**Verification.** `doc` gate set + AC6 + closing-deliverable guards.

**Escalation triggers.**

1. **Cost-analysis data inconsistency.** If WU frontmatter
   `cost_usd` disagrees with events.jsonl sum over attempts, name
   the discrepancy and emit `status: blocked`.
2. **No-op honesty.** If gate 1 ran on-plan with no surprises,
   prefer the explicit "nothing generalizes" note over inventing
   a lesson.
3. **Scope creep.** Drafting gate 2 substantive WUs belongs to
   G1-PLAN. If you find yourself authoring T04/T05/T06 spec
   content, STOP.
