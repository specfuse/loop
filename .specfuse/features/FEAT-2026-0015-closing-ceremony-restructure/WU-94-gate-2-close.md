---
id: FEAT-2026-0015/G2-CLOSE
type: close
model: claude-opus-4-7
effort: high
status: done
attempts: 1
planned_cost_usd: 1.50
oracle_env: macos_local
verdict: met
duration_seconds: 385.52
cost_usd: 2.854313
input_tokens: 37
output_tokens: 21872
---

# Gate 2 close — terminal close ceremony (NEW contract; recursive dogfood)

**Objective.** Close this feature's terminal gate in a single
session using the NEW `type: close` contract that T01–T08 just
shipped. Produce RETROSPECTIVE.md Gate 2 section, append durable
LEARNINGS, reconcile docs/roadmap, write the feature-arc verdict,
include a `## Cost analysis` section, and fire the consolidated
terminal state-flips (per T06). Run T07's hollow-pass guard
recursively against THIS WU's own deliverables — per
`[FEAT-2026-0008/G1-CLOSE]`, the close ceremony of an anti-
hollow-pass feature MUST audit itself.

**Context.** This is `FEAT-2026-0015/G2-CLOSE`. The first
production exercise of the new `close` contract — every prior
feature on this branch used the 4-WU legacy sequence
(grandfathered with WARN). Gate 1 itself paid the legacy tax;
gate 2 closes with the new shape. This is the load-bearing
dogfood that proves the contract works end-to-end.

Read at session start:

- `.specfuse/features/FEAT-2026-0015-closing-ceremony-restructure/`
  RETROSPECTIVE.md (already contains Gate 1 section from
  G1-RETRO), PLAN.md, GATE-01-REVIEW.md (the gate-1 plan-next
  output), events.jsonl (full slice — T04 through T08 attempts).
- `.specfuse/LEARNINGS.md` (read before appending; deduplicate).
- `.specfuse/roadmap.md` (this feature's row + the detail
  section; reconcile).
- This feature's git diff against the gate-1-close commit
  (everything T04–T08 produced).

Reference binding rules under `.specfuse/rules/` (`result-
contract.md`, `never-touch.md`, `security-boundaries.md`,
`correlation-ids.md`). Driver owns all git.

**Cross-repo contracts (this WU reads / writes load-bearing
strings; verify the lexicon before completing).**

- `verdict:` frontmatter field — one of `met`, `met_locally`,
  `partially_met`, `not_met` (per T04 `VERDICT_VALUES`).
  Write into THIS WU's own frontmatter before declaring
  `status: complete`.
- `oracle_env:` frontmatter — already declared as `macos_local`
  in this WU's frontmatter. If you determine at close time
  that the goal env should be different (e.g. CI), update the
  declared field AND escalate per Escalation Trigger 4.
- `## Cost analysis` section heading — exact bytes, used by
  T07's `assert_cost_analysis_section_when_met`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` Gate 2 section appended (do NOT overwrite
   the existing Gate 1 section). Use heading `## Gate 2
   retrospective — <short title>`. Per-WU analysis (T04, T05,
   T06, T07, T08) including: what worked, what failed and why,
   attempt count, cost vs plan, rule/template/boundary gaps.
   Cite specific events.jsonl evidence per WU.

2. **Cost analysis section.** Append `## Cost analysis` to
   `RETROSPECTIVE.md` with a table covering Gate 2's WUs:
   `| WU | type | effort | planned_cost_usd | actual_cost_usd
   | delta $ | delta % |`. Sum to gate total and to feature
   total (Gate 1 + Gate 2 across the whole feature). For any
   WU with |delta| > 50%, write a one-paragraph rationale
   per `[FEAT-2026-0015/G1]` calibration entry.

3. **Durable lessons** appended to `.specfuse/LEARNINGS.md`,
   tagged `[FEAT-2026-0015/G2-CLOSE]`. Candidate categories:
   verdict-coupling ergonomics, oracle-env lint false-positive
   rate, state-flip consolidation surface area, hollow-pass
   guard coverage gaps, planned-cost calibration delta on a
   feature that dogfooded the field from draft time. If
   nothing generalizes, append nothing and say so explicitly
   in `RETROSPECTIVE.md`.

4. **Docs and roadmap reconciled.**
   - `.specfuse/roadmap.md` row for FEAT-2026-0015: status
     reflects the verdict (see AC6). If `verdict: met`, flip
     to `done` (the driver's `fire_terminal_flips` does this
     post-verify per T06 — but the AC verifies the post-state).
   - If any `.specfuse/skills/*/SKILL.md` documents legacy
     closing behavior that T01–T08 invalidated, reconcile
     here (or note as a follow-on hygiene WU if scope is too
     large for the close session).

5. **Feature-arc verdict** appended to RETROSPECTIVE.md as
   `# Feature-arc verdict`. State whether `PLAN.md.roadmap_goal`
   was met. Quote the roadmap goal verbatim. Reference T04
   `VERDICT_VALUES`. Set this WU's frontmatter `verdict:` to
   the matching enum value.

6. **State flips (driver-side per T06; this AC verifies
   post-state).** After this WU is dispatched, when verify+
   squash succeeds AND `verdict == "met"`:
   - GATE-02.md `status: awaiting_review → passed`
   - Roadmap row status: `active → done`
   - PLAN.md `status: active → done` (WU body writes; driver
     gates per T04 verdict-coupling)
   - `auto_archive_feature` invoked.
   If verdict is hedged (`met_locally` / `partially_met`),
   PLAN.md stays `active` and the gate stays
   `awaiting_review` per T04/T06 contract.
   The WU's responsibility is to WRITE the verdict accurately;
   the driver enforces the consequences.

7. **Recursive hollow-pass audit (per
   `[FEAT-2026-0008/G1-CLOSE]`).** Before declaring
   `status: complete`, run T07's guard manually against this
   WU's own deliverables. Specifically run:
   - `grep -c "^## Gate 2 retrospective" RETROSPECTIVE.md`
     returns ≥1.
   - `grep -c "^## Cost analysis" RETROSPECTIVE.md` returns
     ≥1.
   - `grep -c "^# Feature-arc verdict" RETROSPECTIVE.md`
     returns ≥1.
   - `grep -c "FEAT-2026-0015/G2-CLOSE" .specfuse/LEARNINGS.md`
     returns ≥1 OR RETROSPECTIVE.md states "nothing
     generalizes for this gate."
   - `grep -E "^\| FEAT-2026-0015 \|" .specfuse/roadmap.md`
     shows the correct status column for the chosen verdict.
   - This WU's frontmatter `verdict` field is set and in
     `VERDICT_VALUES`.
   If any of these recursive checks fails, emit
   `status: blocked` — per Escalation Trigger 3 below.

8. **T07 driver-side guard MUST fire on this WU.** Confirm in
   the RETROSPECTIVE Gate 2 section that
   `CLOSING_ASSERTIONS_BY_TYPE["close"]` was exercised against
   this WU's own commit. If the guard was SKIPPED for the
   currently-executing WU (T07 escalation trigger 4 explicitly
   forbids this), emit `status: blocked`.

**Do not touch.** Source code (`loop.py`, `lint_plan.py`,
templates) — this is a closing WU, it does not change
behavior. T01–T08 already shipped the code. Other features'
WU files, generated dirs, secrets, `.git/`. You write:
RETROSPECTIVE.md (Gate 2 section + Cost analysis + Feature-arc
verdict), append LEARNINGS.md, update roadmap.md row, write
this WU's frontmatter `verdict:` field, flip PLAN.md status
(conditional on verdict per T04). Nothing else.

The driver-side state flips (GATE-02.md status, roadmap row
status, auto_archive) are owned by `fire_terminal_flips` per
T06; you DO NOT touch GATE-02.md directly. PLAN.md `status`
IS written by this WU's body, conditional on verdict.

See `.specfuse/rules/never-touch.md`.

**Verification.** `plannext` gate set in
`.specfuse/verification.yml` (`lint_plan.py` on this feature —
structural validity preserved). Plus AC7 recursive grep
audit. Plus driver-side T07 guard runs against this commit
post-squash.

**Escalation triggers.**

1. **Audit reveals hollow-pass on this very feature's
   anti-hollow-pass deliverable.** Per
   `[FEAT-2026-0008/G1-CLOSE]`: if T07's guard does not exist
   in `loop.py` at this WU's run time (recursive missing-
   guard scenario), emit `status: blocked`. The whole point
   of this feature is the guard; closing without it is the
   worst-case recursive failure.
2. **Verdict honesty.** If you cannot truthfully write
   `verdict: met` — e.g. T07's guard fires on this WU's own
   deliverables and you cannot fix the gap within the
   session — write `verdict: met_locally` or
   `partially_met` with the hedge cited in the verdict
   section. Do NOT inflate the verdict to permit the flips.
   Per `[FEAT-2026-0013/G1-CLOSE]` v1 incident: a falsely-
   met verdict that flips PLAN.md `done` is harder to
   recover than an honest hedge.
3. **Recursive AC7 grep failure.** If any of the AC7 grep
   commands return 0 / wrong status after your writes, emit
   `status: blocked` and name the failing grep. Do NOT write
   the missing section and re-run silently — the gap is
   evidence that something else upstream (T01–T08
   deliverables themselves, or this WU's draft authoring)
   missed a contract surface.
4. **Oracle env mismatch with goal env.** PLAN.md
   `roadmap_goal` does NOT name a CI-only environment, so
   `oracle_env: macos_local` is acceptable for the audit-of-
   methodology that constitutes this close. If during close
   you discover this feature's goal SHOULD have been
   audited under `linux_docker` / `github_actions_ci`,
   update the frontmatter, write the gap into RETROSPECTIVE,
   and write `verdict: met_locally` (not `met`). Per
   `[FEAT-2026-0013/G1-CLOSE/oracle-environment]`.
5. **Legacy contract drift / fall-back temptation.** If you
   are tempted to fall back to the legacy 4-WU close shape
   ("to be safe") — STOP. Per
   `[FEAT-2026-0003/G3-LESSONS/multi-gate]` and this very
   feature's PLAN.md: the recursive dogfood is the load-
   bearing test that the new contract works. Falling back
   invalidates the whole feature's claim. Emit
   `status: blocked` rather than reshape this WU into a
   4-WU sequence.
6. **Cross-surface mismatch.** If `verdict_permits_terminal_
   flips` is missing from `loop.py` at run time (T04 didn't
   ship), the driver-side flip logic (T06) can't fire, and
   AC6's post-state will not hold. Emit `status: blocked`.
   The same holds for T07's `assert_closing_deliverables`,
   T08's lint surface, etc.
