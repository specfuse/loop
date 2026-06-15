---
id: FEAT-2026-0020/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
generated_surfaces: []
oracle_env: macos_local
planned_cost_usd: 1.50
---

# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1 by writing `RETROSPECTIVE.md` (with the mandatory
`## Cost analysis` and `## What the loop did NOT verify` sections), appending durable
lessons to `.specfuse/LEARNINGS.md`, and reconciling any docs/roadmap state implied by
gate 1's substantive WUs. Does NOT flip gate or feature status — that's `G1-PLAN`'s
sibling responsibilities + the driver. Does NOT draft gate 2 — that is `G1-PLAN`'s job.

**Context.** This is `FEAT-2026-0020/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped `AUDIT.md`
across five audit classes (T01..T05) and the post-remediation rescan verdict (T06).
Destructive remediation operations ran OUTSIDE the loop per PLAN.md "Notes" — that is the
main candidate for the `## What the loop did NOT verify` section.

`close-intermediate` WU (FEAT-2026-0015 contract): folds retrospective + lessons + docs
into one session for gate 1 (non-terminal). The companion `plan-next` WU (G1-PLAN) drafts
gate 2's substantive WUs afterward.

Binding rules: `.specfuse/rules/{result-contract,never-touch,security-boundaries,
correlation-ids}.md`. Verification: `.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` exists** at
   `.specfuse/features/FEAT-2026-0020-public-readiness-prep/RETROSPECTIVE.md`. Non-empty.
   Contains:
   - One `## Gate 1` section.
   - One sub-section per substantive WU (T01..T06): attempts, blockers if any, surprises.
   - The required `## Cost analysis` and `## What the loop did NOT verify` sections
     (see AC2, AC3).

2. **`## Cost analysis` section** reconciles `planned_cost_usd` (from PLAN.md + per-WU
   frontmatter) against actual spend (from `events.jsonl`). For each WU: planned, actual,
   delta %. Aggregate to gate total. Variance > 50% on any WU requires a one-paragraph
   rationale. Note per WU whether each would pass the auto-close predicate's per-WU ratio
   check (≤ 1.5×).

3. **`## What the loop did NOT verify` section** enumerates each acceptance criterion
   whose verification was deferred (loop-sandbox limit, cross-repo coordination, real-
   system access). Each row: the criterion, why deferred, where verification actually
   happens (post-merge step / operator action / follow-up feature). Write "(nothing —
   every acceptance criterion was verified in-loop)" when the list is empty, so the
   explicit count is visible. Expected entries for this gate: every destructive
   remediation command logged in `AUDIT.md` was executed by the operator outside the
   loop; the loop verified post-state via T06's rescan. If the section has > 2 entries OR
   > 30% of the gate's criteria, flag the gate's sizing under `## What I'd change`.

4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson from this gate, OR an
   explicit `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE] nothing generalizes — gate ran
   on-plan` note. Each lesson MUST be phrased as a rule that would change how a future
   WU is written or executed.

5. **Docs reconciliation.** No docs/roadmap diff is expected unless an audit finding
   surfaced something documented elsewhere (e.g. methodology doc reference that needed
   redaction). If so, include the doc edit in this WU's squash; otherwise the
   docs/roadmap-diff assertion is satisfied by the RETROSPECTIVE.md write alone.

6. **NO terminal verdict.** This is intermediate close; `verdict:` is not written here.
   Terminal feature-arc verdict belongs to G2-CLOSE.

7. **Existence check** before declaring complete:

   ```bash
   FEAT=.specfuse/features/FEAT-2026-0020-public-readiness-prep
   test -s "$FEAT/RETROSPECTIVE.md"
   grep -qE '^## Cost analysis' "$FEAT/RETROSPECTIVE.md"
   grep -qE '^## What the loop did NOT verify' "$FEAT/RETROSPECTIVE.md"
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0020' || \
     grep -q 'nothing generalizes' "$FEAT/RETROSPECTIVE.md"
   git diff --name-only HEAD | grep -qx "$FEAT/RETROSPECTIVE.md"
   ```

   If any check fails, emit `status: blocked`.

**Do not touch.** Files this WU may edit/create:
- `RETROSPECTIVE.md` (new file in this feature's folder).
- `.specfuse/LEARNINGS.md` (append-only).
- Docs files iff a gate-1 WU surfaced something requiring doc reconciliation.

No edits to: gate 1's substantive WU files (T01..T06 own them), `loop.py`, other
features, secrets, `.git/`. Driver owns all git. See `.specfuse/rules/never-touch.md`.

**Verification.** `doc` gate set in `.specfuse/verification.yml` (this WU is
`close-intermediate` type → doc gates). Plus AC7 existence checks. Plus
[FEAT-2026-0015/T07] closing-deliverable guards (`assert_retrospective_exists`,
`assert_learnings_appended_or_noop`, `assert_doc_or_roadmap_diff`,
`assert_cost_analysis_section_when_met`).

**Escalation triggers.**

1. **Cost-analysis ambiguity.** If a WU's `cost_usd` / `planned_cost_usd` field disagrees
   with `events.jsonl` summed over its attempts, emit `status: blocked` naming the
   discrepancy.
2. **No-op vs nothing-generalizes ambiguity.** Prefer the explicit "nothing generalizes"
   note over an invented lesson.
3. **Compound scope.** If you find yourself wanting to draft gate 2 inside this WU —
   STOP. That is G1-PLAN's job.
