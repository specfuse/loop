---
id: FEAT-2026-0018/G1-CLOSE-INTERMEDIATE
type: close-intermediate
effort: medium
status: done
attempts: 2
planned_cost_usd: 1.20
generated_surfaces: []
duration_seconds: 382.639
cost_usd: 2.530078
input_tokens: 42
output_tokens: 21475
---

# Gate 1 close-intermediate — retrospective + lessons + docs, single session

**Objective.** Close gate 1 by writing `RETROSPECTIVE.md` (with the
mandatory `## Cost analysis` section), appending durable lessons to
`.specfuse/LEARNINGS.md`, and reconciling any docs/roadmap state
implied by gate 1's substantive WUs. Does NOT flip gate or feature
status — that's `G1-PLAN`'s sibling responsibilities + the driver.

**Context.** This is `FEAT-2026-0018/G1-CLOSE-INTERMEDIATE`. Gate
1 shipped `.specfuse/scripts/gate_eval.py` (T01), its tests (T02),
and its CLI + calibration regression (T03). No driver wiring yet
— that's gate 2.

This is a **`close-intermediate`** WU (FEAT-2026-0015 contract):
folds retrospective + lessons + docs into one session for gate 1
(non-terminal). The companion `plan-next` WU (G1-PLAN) drafts
gate 2's substantive WUs afterward.

Reference: `.specfuse/rules/result-contract.md` for the RESULT
block contract. `.specfuse/skills/verification/SKILL.md` for how
to run gates. `.specfuse/templates/WU.template.md` notes on
`close-intermediate`. `[FEAT-2026-0015/T07]`'s closing-deliverable
guard runs against this WU; the `## Cost analysis` section is a
required assertion.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` exists** at
   `.specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md`.
   Non-empty. Contains, at minimum:
   - One `## Gate 1` section (or the gate's natural heading).
   - One sub-section per substantive WU (T01, T02, T03):
     attempts, blockers if any, surprises.
   - A `## Cost analysis` section (required — see AC2).

2. **`## Cost analysis` section** present in RETROSPECTIVE.md.
   Reconciles `planned_cost_usd` (from PLAN.md + per-WU
   frontmatter) against actual spend (from events.jsonl). For
   each WU in scope, quote planned, compute actual, report
   delta %. Then aggregate to gate total. Variance > 50% on
   any WU requires a one-paragraph rationale citing the cause
   (per `[FEAT-2026-0013/Planned-cost-capture]` /
   FEAT-2026-0015 docs). Reference T01's predicate criterion 3
   (≤ 1.5×) — note for each WU whether it would have passed the
   gate-3 self-predicate.

3. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson
   from this gate, OR an explicit `[FEAT-2026-0018/G1-CLOSE-INTERMEDIATE]
   nothing generalizes — gate ran on-plan` note acknowledging
   the no-op. (The hollow-pass guard accepts either; explicit
   no-op is the honest path when nothing new emerged.) Each
   appended lesson MUST be phrased as a rule that would change
   how a future WU is written or executed (per LEARNINGS.md
   format).

4. **No docs/roadmap diff required** — gate 1 ships an internal
   module with no operator-facing surface. If T01/T02/T03's
   work happens to require a docs update (e.g., a methodology
   doc reference to `gate_eval.py`), include it in this WU's
   squash; otherwise the docs/roadmap-diff assertion is
   satisfied by the RETROSPECTIVE.md write alone (the
   `assert_doc_or_roadmap_diff` assertion accepts either path
   per FEAT-2026-0015/T07).

5. **NO terminal verdict.** This is intermediate close;
   `verdict:` is not written here. Terminal feature-arc
   verdict belongs to G3-CLOSE.

6. **Existence check** before declaring complete:

   ```bash
   # a. RETROSPECTIVE.md exists and is non-empty
   test -s .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # b. Cost analysis section present
   grep -qE '^## Cost analysis' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # c. LEARNINGS appended OR no-op acknowledged
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \[FEAT-2026-0018' || \
     grep -q 'nothing generalizes' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # d. Working-tree diff touches RETROSPECTIVE.md
   git diff --name-only HEAD | grep -qx '.specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md'
   ```

   If any check fails, emit `status: blocked`. RETROSPECTIVE-only
   frontmatter flips reproduce the documented hollow-pass shape
   (per `[FEAT-2026-0015/T07]` guard's purpose).

**Do not touch.** Files this WU may edit/create:
- `RETROSPECTIVE.md` (new file in this feature's folder).
- `.specfuse/LEARNINGS.md` (append-only).
- Docs files iff a gate-1 WU touched something that requires
  doc reconciliation (unlikely; gate 1 is internal-module
  only).

No edits to: `gate_eval.py` or its tests (gate 1 substantive WUs
own them — this is the close, not a re-edit), `loop.py`, other
features, secrets, `.git/`. Driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set in `.specfuse/verification.yml`
(this WU is `close-intermediate` type → doc gates). Plus AC6
existence checks. Plus
`[FEAT-2026-0015/T07]` closing-deliverable guards
(`assert_retrospective_exists`, `assert_learnings_appended_or_noop`,
`assert_doc_or_roadmap_diff`, `assert_cost_analysis_section`).

**Escalation triggers.**

1. **Cost-analysis ambiguity.** If a WU's `cost_usd` /
   `planned_cost_usd` field disagrees with events.jsonl summed
   over its attempts (data drift between frontmatter and the
   per-attempt log), emit `status: blocked` naming the
   discrepancy. The cost-analysis section depends on a
   trustworthy data source; if the sources disagree, the
   analysis is fiction.
2. **No-op vs nothing-generalizes ambiguity.** If gate 1 ran
   genuinely on-plan with no surprises, prefer the explicit
   "nothing generalizes" note (per the LEARNINGS rule on
   append-only honesty) over an invented lesson. Do not pad
   LEARNINGS with rules that don't trace to a real failure
   mode.
3. **Compound retrospective scope.** If you find yourself
   wanting to also reconcile docs OR set up gate-2 drafts
   inside this WU, STOP — gate-2 drafting is G1-PLAN's job.
   This WU is retrospective + lessons + docs ONLY (per
   FEAT-2026-0015's close-intermediate contract).
