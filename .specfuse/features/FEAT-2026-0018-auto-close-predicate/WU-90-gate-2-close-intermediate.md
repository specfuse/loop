---
id: FEAT-2026-0018/G2-CLOSE-INTERMEDIATE
type: close-intermediate
effort: medium
status: done
attempts: 2
planned_cost_usd: 1.20
generated_surfaces: []
duration_seconds: 428.61
cost_usd: 2.971527
input_tokens: 53
output_tokens: 26912
---

# Gate 2 close-intermediate — retrospective + lessons + docs, single session

**Objective.** Close gate 2 by appending a `## Gate 2` section to
`RETROSPECTIVE.md` (with its own per-WU sub-sections and an extended
`## Cost analysis` covering gate 2), appending a durable lesson to
`.specfuse/LEARNINGS.md`, and reconciling any docs/roadmap state
implied by gate 2's substantive WUs. Does NOT flip gate or feature
status — that's `G2-PLAN`'s sibling responsibilities + the driver.

**Context.** This is `FEAT-2026-0018/G2-CLOSE-INTERMEDIATE`. Gate 2
shipped the driver-wiring trio: T04 (terminal-gate path —
`maybe_auto_close_terminal`, `write_stub_retrospective_terminal`,
`mark_close_wu_auto_closed`), T05 (intermediate-gate path, option A —
`maybe_auto_close_intermediate`, `append_stub_retrospective_intermediate`),
and T06 (operator escapes — `--force-full-close` CLI flag and the
`auto_close_disabled: true` PLAN.md frontmatter override —
`resolve_auto_close_override`). All three WUs landed in 2 attempts.
No blocked_human escalations, no replan events.

This is a **`close-intermediate`** WU (FEAT-2026-0015 contract):
folds retrospective + lessons + docs into one session for gate 2
(non-terminal). The companion `plan-next` WU (G2-PLAN) drafts
gate 3's substantive WUs afterward.

Reference: `.specfuse/rules/result-contract.md` for the RESULT
block contract. `.specfuse/skills/verification/SKILL.md` for how
to run gates. `.specfuse/templates/WU.template.md` notes on
`close-intermediate`. `[FEAT-2026-0015/T07]`'s closing-deliverable
guard runs against this WU; the `## Cost analysis` section is a
required assertion.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` extended** at
   `.specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md`.
   The existing gate-1 content is preserved; a new `## Gate 2`
   section is appended (or the gate's natural heading), containing:
   - One sub-section per substantive WU (T04, T05, T06):
     attempts, blockers if any, surprises.
   - Gate-2 entries inside the file's `## Cost analysis` section
     (extending the gate-1 table — see AC2).

2. **`## Cost analysis` section** updated in RETROSPECTIVE.md
   to cover gate 2. Reconciles `planned_cost_usd` (from PLAN.md
   + per-WU frontmatter) against actual spend (from events.jsonl).
   For each WU in scope (T04, T05, T06), quote planned, compute
   actual, report delta %. Then aggregate to gate-2 total. Variance
   > 50% on any WU requires a one-paragraph rationale citing the
   cause (per `[FEAT-2026-0013/Planned-cost-capture]` /
   FEAT-2026-0015 docs). Reference T01's predicate criterion 3
   (≤ 1.5×) and criterion 4 (≤ 2×) — note for each WU whether
   gate 2 would have passed the predicate's own self-test.

3. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson
   from this gate, OR an explicit `[FEAT-2026-0018/G2-CLOSE-INTERMEDIATE]
   nothing generalizes — gate ran on-plan` note acknowledging
   the no-op. (The hollow-pass guard accepts either; explicit
   no-op is the honest path when nothing new emerged.) Each
   appended lesson MUST be phrased as a rule that would change
   how a future WU is written or executed (per LEARNINGS.md
   format).

4. **No docs/roadmap diff required** — gate 2 wires existing
   `gate_eval` symbols into `loop.py` plus a CLI flag and a
   PLAN.md frontmatter override. The `--force-full-close` flag
   and `auto_close_disabled` field ARE operator-facing, but the
   `assert_doc_or_roadmap_diff` close-guard is satisfied by this
   RETROSPECTIVE.md write per FEAT-2026-0015/T07. (Operator docs
   for the flag + frontmatter belong to gate 3's docs WU.)

5. **NO terminal verdict.** This is intermediate close;
   `verdict:` is not written here. Terminal feature-arc
   verdict belongs to G3-CLOSE.

6. **Existence check** before declaring complete:

   ```bash
   # a. RETROSPECTIVE.md exists and is non-empty
   test -s .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # b. Cost analysis section present and now mentions gate 2
   grep -qE '^## Cost analysis' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md
   grep -qE '(T04|gate 2)' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # c. LEARNINGS appended OR no-op acknowledged
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \*?\*?\[FEAT-2026-0018/G2' || \
     grep -q 'nothing generalizes — gate 2' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # d. Working-tree diff touches RETROSPECTIVE.md
   git diff --name-only HEAD | grep -qx '.specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md'
   ```

   If any check fails, emit `status: blocked`. RETROSPECTIVE-only
   frontmatter flips reproduce the documented hollow-pass shape
   (per `[FEAT-2026-0015/T07]` guard's purpose).

**Do not touch.** Files this WU may edit/create:
- `RETROSPECTIVE.md` (extend the existing file in this feature's folder).
- `.specfuse/LEARNINGS.md` (append-only).
- Docs files iff a gate-2 WU touched something that requires
  doc reconciliation (unlikely; gate-2 surfaces are operator-facing
  but their docs belong to gate 3).

No edits to: `loop.py` (T04/T05/T06 own them — this is the close,
not a re-edit), `gate_eval.py` or its tests, other features,
secrets, `.git/`. Driver owns all git. See
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
2. **No-op vs nothing-generalizes ambiguity.** If gate 2 ran
   genuinely on-plan with no surprises, prefer the explicit
   "nothing generalizes" note (per the LEARNINGS rule on
   append-only honesty) over an invented lesson. Do not pad
   LEARNINGS with rules that don't trace to a real failure
   mode.
3. **Compound retrospective scope.** If you find yourself
   wanting to also reconcile docs OR set up gate-3 drafts
   inside this WU, STOP — gate-3 drafting is G2-PLAN's job.
   This WU is retrospective + lessons + docs ONLY (per
   FEAT-2026-0015's close-intermediate contract).
