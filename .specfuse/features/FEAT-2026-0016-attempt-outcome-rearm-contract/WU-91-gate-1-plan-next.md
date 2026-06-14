---
id: FEAT-2026-0016/G1-PLAN
type: plan-next
effort: high
status: pending
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
---

# Gate 1 plan-next — draft gate 2's substantive WUs

**Objective.** Author gate 2's substantive WU files (T04
spinning-detector driver hook, T05 `/gate-status` per-attempt
surface, T06 `/unblock-wu` mandatory rationale + re-arm-history
write) and write `GATE-02-REVIEW.md`. Update `PLAN.md`'s gate-2
`work_units` graph with real `depends_on` edges.

**Context.** This is `FEAT-2026-0016/G1-PLAN`. Follows
G1-CLOSE-INTERMEDIATE. Drafts gate 2 from gate-1's retrospective +
the per-attempt event evidence that T01-T03 now produce.

Gate 2's expected scope:

- **T04 — Spinning-detector active driver hook** (~$2.00, high)
  - Inside the per-WU dispatch loop, after each `attempt_outcome`
    event is emitted with `outcome: failed`, check if the prior
    attempt's `attempt_outcome` event had the same
    `failure_signature`. If yes, halt the WU to `blocked_human`
    BEFORE attempt N+1 dispatches.
  - Emit `human_escalation` event with reason
    `spinning_signature_repeat` carrying the repeated signature.
  - Eliminates this session's operator-monitor pattern (the
    Monitor + manual TaskStop intervention).
  - Edge case: handle the genuine zero-token spinning shape
    (existing path) — repeat-signature halt should NOT collide
    with that detection.

- **T05 — `/gate-status` per-attempt surfacing** (~$1.20, medium)
  - Skill reads events.jsonl filtered to blocked WU's
    `attempt_outcome` events; renders a per-attempt table with
    `attempt | outcome | failure_class | failure_signature |
    duration | cost`.
  - Surfaces `re_arm_count` and the latest `re_arm_history` entry
    if present.
  - Removes the operator's "grep stdout via my session" workaround.

- **T06 — `/unblock-wu` mandatory rationale + history write**
  (~$1.50, high)
  - Skill prompts for mandatory one-line re-arm rationale.
  - Writes a new `re_arm_history` entry: `{timestamp,
    prior_status, prior_attempts, prior_cost_usd,
    prior_duration_seconds, reason}`.
  - Increments `re_arm_count`.
  - Driver's `detect_rearm_dispatch` (T02) detects the
    incremented count on next dispatch and fires the
    cumulative-fold automatically.
  - Refuses re-arm without rationale (mandatory).

Reference binding rules at `.specfuse/rules/`. Driver owns all git.

**Acceptance criteria.**

1. **Gate 2 WU files drafted** (status: `draft`):
   - `WU-04-spinning-detector-driver-hook.md`
   - `WU-05-gate-status-per-attempt-surface.md`
   - `WU-06-unblock-wu-rationale-history.md`

   Each file follows `.specfuse/templates/WU.template.md` and
   the per-WU craft in `.specfuse/skills/authoring-work-units/SKILL.md`:
   - Five required sections.
   - Symbol-existence checks (per §9) for new
     functions/constants.
   - Completeness escalation triggers (per §9).
   - For T04 (driver hook): §10 helper-duplication pre-flight
     enumerating existing close-path / dispatch-loop symbols.
   - For T05 + T06 (skill-side): cross-reference the driver
     contract T02 ships.

2. **`planned_cost_usd` on each new WU** matches PLAN.md's
   planned-cost table.

3. **`PLAN.md` gate-2 `work_units` graph updated** with real
   `depends_on` edges:
   - T04 depends_on: [] (independent surface)
   - T05 depends_on: [] (skill-side, reads what T01 emits)
   - T06 depends_on: [] (skill-side, writes what T02 schema-fies)
   - G2-CLOSE-INTERMEDIATE depends_on: [T04, T05, T06]
   - G2-PLAN depends_on: [G2-CLOSE-INTERMEDIATE]

4. **`GATE-02-REVIEW.md`** written at feature folder root.
   Sections:
   - **Gate-1 summary** — one paragraph: cost actual vs planned,
     T01 bootstrap-gap result, predicate self-check on this
     feature's gate 1.
   - **Gate-2 substantive WUs** — one paragraph per WU.
   - **Open verifications** — pre-arm checks:
     - **Spinning-detection edge cases**: zero-token spin vs
       failure-signature repeat — confirm orthogonality.
     - **`/gate-status` skill discovery**: symlinks from
       `.claude/skills/` per `CLAUDE.md` convention.
     - **`/unblock-wu` re-arm refusal flow**: confirm the
       mandatory-rationale prompt is non-bypassable.
     - **Driver `detect_rearm_dispatch` handshake**: verify
       `/unblock-wu` writes the frontmatter BEFORE the operator
       runs `loop.py`, so the driver detects on first dispatch.
   - **Cross-repo contracts** — invented values:
     - Event reason string `spinning_signature_repeat` (T04)
     - Re-arm history schema fields (T02-shipped, T06-consumed)

5. **Predicate self-check** captured: run
   `python3 .specfuse/scripts/gate_eval.py backtest FEAT-2026-0016
   --gate 1`, paste output into GATE-02-REVIEW.md. This is the
   FIRST run where the predicate has REAL attempt_outcome data
   (T01 produced the events on this gate's own substantive WUs).

6. **Existence check** before declaring complete:

   ```bash
   test -f .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/WU-04-spinning-detector-driver-hook.md
   test -f .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/WU-05-gate-status-per-attempt-surface.md
   test -f .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/WU-06-unblock-wu-rationale-history.md
   test -s .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/GATE-02-REVIEW.md
   grep -A 30 "gate: 2" .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/PLAN.md | grep -qE 'FEAT-2026-0016/T0[4-6]'
   python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/
   grep -q 'predicate=v1' .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/GATE-02-REVIEW.md
   for f in .specfuse/features/FEAT-2026-0016-attempt-outcome-rearm-contract/WU-0[4-6]-*.md; do
     for sec in 'Context\.' 'Acceptance criteria\.' 'Do not touch\.' 'Verification\.' 'Escalation triggers\.'; do
       grep -qE "^\*\*$sec\*\*" "$f" || { echo "missing section $sec in $f"; exit 1; }
     done
   done
   ```

**Do not touch.** Files this WU may edit/create:
- `WU-04-spinning-detector-driver-hook.md` (new)
- `WU-05-gate-status-per-attempt-surface.md` (new)
- `WU-06-unblock-wu-rationale-history.md` (new)
- `GATE-02-REVIEW.md` (new)
- `PLAN.md` (gate-2 `work_units` graph only)

No edits to: `loop.py`, `gate_eval.py`, T01/T02/T03 surfaces,
other features, skills, secrets, `.git/`.

**Verification.** `plannext` gate set + lint_plan.py clean.

**Escalation triggers.**

1. **Gate-1 retrospective evidence reshapes gate 2.** If the
   retrospective revealed an unexpected interaction (e.g.
   spinning-detector edge case T01's emission can't handle),
   emit `status: blocked` naming the finding before drafting.
2. **Cross-WU coordination ambiguity.** If T04/T05/T06 specs
   require precise contracts T01/T02 didn't ship (e.g. the
   `failure_signature` extraction returns a shape T04 can't
   compare on), name the gap and emit `status: blocked`.
3. **Cross-repo contracts.** All invented values (event reason
   strings, frontmatter field names) MUST be checked against
   prior LEARNINGS + existing code. Surface in the review's
   Cross-repo contracts table for operator verification at arm
   time.
