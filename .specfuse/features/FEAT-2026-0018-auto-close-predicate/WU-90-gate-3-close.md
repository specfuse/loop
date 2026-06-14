---
id: FEAT-2026-0018/G3-CLOSE
type: close
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
---

# Gate 3 close — terminal: retro + lessons + docs + feature-arc verdict

**Objective.** Terminal close for `FEAT-2026-0018`. Append a `## Gate 3`
section to `RETROSPECTIVE.md` covering T07–T10, extend the existing
`## Cost analysis` table with gate-3 rows, append durable lesson(s) to
`.specfuse/LEARNINGS.md`, reconcile any docs/roadmap state, and write the
terminal **`# Feature-arc verdict`** answering "did the deterministic
predicate + auto-close path land as designed". Sets `verdict: met` (or
`met_locally` / `partially_met` / `not_met`) on this WU's frontmatter so
`fire_terminal_flips` fires.

**Context.** This is `FEAT-2026-0018/G3-CLOSE`. Terminal gate close
(FEAT-2026-0015 contract; single-WU). Gate 3 shipped: T07 (plan-next
lint + driver hook), T08 (`/wrap-feature` trim), T09 (new
`/migrate-to-auto-close` skill), T10 (methodology docs +
`/draft-feature` template tweak).

This is the **recursive-dogfood gate** (per PLAN.md § Notes). If gate 3
ran on-plan, the predicate this feature ships should auto-close this
gate — bypassing THIS WU's dispatch entirely. The RETROSPECTIVE.md
section for gate 3 must document the outcome either way:
- **Auto path:** stub section written by `write_stub_retrospective_terminal`;
  this WU never dispatches; the section will document that fact when a
  human reads it.
- **Ceremony path:** this WU dispatches; you (the agent) author the
  full retrospective section + cost analysis + verdict.

Reference: `.specfuse/rules/result-contract.md` for the RESULT block
contract. `.specfuse/skills/verification/SKILL.md` for how to run
gates. `.specfuse/templates/WU.template.md` notes on `close`.
`[FEAT-2026-0015/T07]`'s closing-deliverable guard runs against this
WU; the `## Cost analysis` section is a required assertion.

**Acceptance criteria.**

1. **`RETROSPECTIVE.md` extended** with a `## Gate 3` section appended
   to the existing file. Per-WU sub-sections for T07, T08, T09, T10:
   attempts, blockers if any, surprises.

2. **`## Cost analysis` section extended** with gate-3 rows. For
   each WU in scope (T07, T08, T09, T10), quote planned, compute
   actual, report delta %. Aggregate to gate-3 total and
   feature total. Reference T01's predicate criterion 3 (≤ 1.5×)
   and criterion 4 (≤ 2×) — note for each WU whether gate 3 would
   have passed the predicate's own self-test (the recursive dogfood
   property). Variance > 50% on any WU requires a one-paragraph
   rationale citing the cause.

3. **Predicate self-check captured.** Run:

   ```bash
   python3 .specfuse/scripts/gate_eval.py backtest FEAT-2026-0018 --gate 3
   ```

   Paste output verbatim into the gate-3 retrospective section.
   Document whether gate 3 auto-closed (it should, if this WU is
   running it didn't — see Context above). The historical record
   of WHICH path fired on the recursive-dogfood gate is the
   single most load-bearing artifact this close produces.

4. **`.specfuse/LEARNINGS.md` appended** with ≥ 1 durable lesson
   from this feature's terminal close (or an explicit
   `[FEAT-2026-0018/G3-CLOSE] nothing generalizes — feature ran
   on-plan` note). Lessons must be phrased as rules that would
   change how a future WU is written or executed. Strong
   candidates:
   - Effort-band ↔ site-count misclassification (T02, T06, possibly
     T07/T09 — same shape seen across multiple gates of this very
     feature).
   - Cache-read amplification on re-dispatch (T01 attempt-2 cost
     near-parity with attempt-1).
   - Recursive-dogfood feedback as a planning hat (predicate
     refuses own gates 1+2 — meta-confirmation worth promoting).

5. **Roadmap row reconciliation.** `.specfuse/roadmap.md` row for
   `FEAT-2026-0018` is auto-flipped to `done` by
   `fire_terminal_flips` IF `verdict: met` (or `met_locally`)
   sets on this WU's frontmatter. Manual roadmap edit is NOT
   required — confirm the driver fires it post-pass.

6. **Docs/roadmap diff guard.** `assert_doc_or_roadmap_diff`
   close-guard (FEAT-2026-0015/T07) requires this WU's commit
   touch either docs/ or roadmap.md. This WU touches
   RETROSPECTIVE.md + LEARNINGS.md (always); if neither
   docs/methodology.md NOR roadmap.md is in this WU's diff
   (T10 already touched methodology.md; roadmap.md is
   driver-flipped), the guard inspects the cumulative gate-3
   diff range — verify the guard's scope before declaring
   complete.

7. **`# Feature-arc verdict` section written** in
   RETROSPECTIVE.md with the verdict (met / met_locally /
   partially_met / not_met) + one-sentence rationale anchored to
   PLAN.md's `roadmap_goal`. Verdict semantics:
   - **met** — predicate lands as designed; auto-close path
     functional; recursive dogfood ran (whichever path); all
     deliverables ship.
   - **met_locally** — same as `met` but with a known scope-deferred
     item documented.
   - **partially_met** — predicate ships but one or more
     deliverables (e.g. migrate skill, lint hook) did NOT.
   - **not_met** — auto-close path broken on either gate boundary.

8. **`verdict:` set in this WU's frontmatter** (driver-required for
   `fire_terminal_flips`). Per FEAT-2026-0015/G2-CLOSE LEARNINGS,
   write `verdict: met` (or other) to THIS file's frontmatter
   directly — `fire_terminal_flips` reads it post-squash.

9. **Existence check** before declaring complete:

   ```bash
   # a. RETROSPECTIVE.md exists with gate 3 section
   test -s .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md
   grep -qE '^## Gate 3\b' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # b. Cost analysis covers gate 3
   grep -qE '^## Cost analysis' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md
   grep -qE '(T07|T08|T09|T10|gate 3)' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # c. Predicate self-check output captured
   grep -q 'predicate=v1' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # d. Feature-arc verdict section present
   grep -qE '^# Feature-arc verdict' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # e. LEARNINGS appended OR explicit no-op
   git diff HEAD .specfuse/LEARNINGS.md | grep -qE '^\+- \*?\*?\[FEAT-2026-0018/G3' || \
     grep -q 'nothing generalizes — feature ran on-plan' .specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md

   # f. verdict written to this WU's frontmatter
   grep -qE '^verdict: (met|met_locally|partially_met|not_met)' .specfuse/features/FEAT-2026-0018-auto-close-predicate/WU-90-gate-3-close.md

   # g. Working-tree diff touches RETROSPECTIVE.md
   git diff --name-only HEAD | grep -qx '.specfuse/features/FEAT-2026-0018-auto-close-predicate/RETROSPECTIVE.md'
   ```

   If any check fails, emit `status: blocked`. RETROSPECTIVE-only
   frontmatter flips reproduce the documented hollow-pass shape.

**Do not touch.** Files this WU may edit:
- `RETROSPECTIVE.md` (extend — append gate 3 + verdict)
- `.specfuse/LEARNINGS.md` (append-only)
- This WU's own frontmatter (`verdict: ...` field only — required
  for `fire_terminal_flips`)
- Docs file(s) iff the cumulative gate-3 diff doesn't already
  satisfy `assert_doc_or_roadmap_diff` (T10 should have already
  satisfied it).

No edits to: `loop.py`, `gate_eval.py`, `lint_plan.py` (T07's;
gates 1–2 own remainder), `.specfuse/roadmap.md` (driver-flipped),
PLAN.md, GATE-NN.md status (driver-flipped), other features,
secrets, `.git/`. Driver owns all git. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set in
`.specfuse/verification.yml` (close type → plannext). Plus AC9
existence checks. Plus `[FEAT-2026-0015/T07]` closing-deliverable
guards (`assert_retrospective_exists`,
`assert_retrospective_gate_section`,
`assert_learnings_appended_or_noop`,
`assert_doc_or_roadmap_diff`, `assert_cost_analysis_section`,
`assert_cost_analysis_section_when_met`,
`assert_terminal_flips_fired`).

**Escalation triggers.**

1. **Cost-analysis ambiguity.** If a WU's `cost_usd` /
   `planned_cost_usd` field disagrees with events.jsonl summed
   over its attempts (data drift between frontmatter and the
   per-attempt log), emit `status: blocked` naming the
   discrepancy.
2. **No-op vs nothing-generalizes ambiguity.** If gate 3 ran
   genuinely on-plan with no surprises, prefer the explicit
   "nothing generalizes" note over an invented lesson. Do not
   pad LEARNINGS with rules that don't trace to a real failure
   mode.
3. **Verdict ambiguity.** If a deliverable shipped but is
   degraded (e.g. lint hook landed but disabled; migrate skill
   landed but skips a target case), use `met_locally` or
   `partially_met` not `met`. Per FEAT-2026-0015/G2-CLOSE
   LEARNINGS, a hedged verdict on a terminal close prevents
   silent shipping of a half-feature.
4. **Compound retrospective scope.** Do NOT also re-evaluate
   gate-1 or gate-2 outcomes — those sections are sealed by their
   own close WUs. Gate 3 retrospective covers gate 3 only +
   the terminal feature-arc verdict (across all three gates).
5. **Recursive-dogfood-fired-but-bug.** If gate 3 actually
   auto-closed but the stub RETROSPECTIVE.md is malformed (e.g.
   missing the `## Gate 3` heading), the driver's
   closing-deliverable guard would fail. That is a T04 / T05 bug
   surfacing post-ship — emit `status: blocked` and let the
   operator decide whether to revert this gate or patch T04.
