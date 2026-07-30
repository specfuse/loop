---
feature_id: FEAT-2026-0053
title: Autonomous feature mode — auto gate-arming with mechanical stop conditions
slug: auto-mode
branch: feat/FEAT-2026-0053-auto-mode
roadmap_goal: Implement the declared-but-dead `auto` autonomy level end to end — the driver arms drafted gates and accepts plan-next's additive plan adjustments on its own, stopping only on mechanical conditions, so a four-gate feature costs one human touch (the PR review) instead of four.
autonomy_default: review
status: active
planned_cost_usd: 54.00
---

# Plan: Autonomous feature mode

The autonomy field (`auto` / `review` / `supervised`) is written to PLAN.md
frontmatter and never read by the run loop — its only consumers are
`gh_features.py` and `adopt_feature.py`, which copy it from labels into
frontmatter. Every feature therefore stops at every gate boundary exactly like a
`review` feature. Operator history shows those gate reviews are near-universal
rubber-stamps whose accepted changes are additive (new WUs at gate check,
occasionally a new gate); the operator's real read happens at PR review, and
merge stays human. This feature makes `auto` real, with the checkpoint value
preserved by construction rather than by judgment.

**The organizing principle, binding on every gate of this feature:**
*model-authored signals may only veto; only mechanical facts and human-authored
constants may approve.* `open_questions`, `human_only`, and `provenance` are
veto channels. The predicate's approval inputs are counters, paths, and
hardcoded constants.

## Decisions taken at drafting

- **All thresholds are hardcoded driver constants v1** (operator decision,
  2026-07-29): `BUDGET_PROJECTION_MULTIPLIER = 2.0`, `DRIFT_CAP_RATIO = 0.5`,
  `ADDED_GATE_CAP = 1`, the judge-editing path set, and the decision-class /
  dependency-manifest path set. The frontmatter dial (`autonomy_default: auto`)
  is pure on/off. Tuning graduates to `agent-policy.yml`
  ([FEAT-2026-0044](../../roadmap.md)) later, tighten-only.
- **No separate shadow mode.** The predicate evaluates and emits an
  `arm_predicate_evaluated` event at every `awaiting_review` flip regardless of
  dial. `review` features generate the shadow trail for free; `auto` features
  (gate 2) act on the verdict. Shadow = the event stream, not a mode.
- **No terminal-gate floor, no consecutive-auto-gate cap** (operator decision):
  the stop conditions are the budget projection, the objective-at-risk proxies,
  the drift caps, the judge-editing and decision-class floors, and the
  model-veto channels. The PR read is fed by accumulated per-gate doubt
  summaries (gate 2's FEATURE-REVIEW.md accumulation).
- **Doubt prose stays decoupled from the arming signal.** The review file's
  doubt section remains mandatory and is never read by the predicate; only the
  narrow `open_questions` enumeration is. Being doubtful in prose must stay
  free, or the drafting model learns hedging is expensive and stops hedging
  everywhere.
- **This feature runs `autonomy_default: review`.** Per
  `[FEAT-2026-0007/G2-LESSONS]`, an enforcement mechanism cannot be exercised by
  the gate that builds it. The shadow event fires passively from gate 1's own
  close onward (T04 lands mid-gate-1), but the first live `auto` ride belongs to
  a successor feature.
- **Honest v1 limit, recorded up front:** weakening an *existing* test is
  mechanically undetectable in v1. The judge-editing class catches edits to
  verification config, hooks, CI, rules, and the driver; it does not catch a
  draft that rewrites an existing test's assertions. Out of scope, named here so
  nobody believes otherwise.

## Scope boundary

**IN.** The plan baseline snapshot; the machine-readable plan-next contract
fields (`open_questions`, `human_only`, `provenance`) with warn-only lint; the
arm predicate module (seven stop classes, hardcoded constants); shadow event
emission at every gate close (gate 1). Live arming behind the dial, the atomic
arm transaction with tag-before-arm, lint warns flipping to blocking under
`auto`, FEATURE-REVIEW.md accumulation, LEARNINGS staged to a pending file
(gate 2, drafted by G1-PLAN). Docs and methodology rewrite (gate 3).

**OUT, each with a home.** Outbound notifications are
[FEAT-2026-0047](../../roadmap.md); the policy file owning tunable dials is
[FEAT-2026-0044](../../roadmap.md); the run-to-drain runner is
[FEAT-2026-0049](../../roadmap.md); auto-merge is
[FEAT-2026-0048](../../roadmap.md) and merge stays human here without
exception. Remote arm (approve from phone via issue comment) has no roadmap
home yet — deliberately unplanned, noted for a future `/roadmap-add`.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

Four searches, four verdicts — three reuse, one gap confirmed.

- **Command:** `grep -n 'gate_budget_usd\|gate_spent_usd\|_should_halt_for_budget' specfuse/loop/loop.py`
- **Verdict:** found `gate_budget_usd` (loop.py:1711), `gate_spent_usd`
  (loop.py:1730, counts every WU status including blocked burn — the #221 fix),
  `_should_halt_for_budget` (loop.py:1769). **Reusing:** the budget-projection
  stop class extends this plumbing to feature level (spent + planned-remaining
  vs 2× baseline total); it does not replace the per-gate brake.

- **Command:** `grep -n '^def ' specfuse/loop/gate_eval.py`
- **Verdict:** found `evaluate_auto_close(feature_dir, gate_id) -> AutoCloseDecision`
  — a pure, structured, side-effect-free predicate with `_format_decision` for
  the event trail. **Reusing the shape, not the code:** `arm_eval.py` mirrors
  it in a separate module because arming and closing are different decisions
  with different inputs; folding both into one predicate would couple their
  failure modes.

- **Command:** `grep -n 'lint_plan_next_draft' specfuse/loop/lint_plan.py`
- **Verdict:** found `lint_plan_next_draft(feature_dir, just_closed_gate)`
  (lint_plan.py:932) — the warn-only pass over plan-next drafts.
  **Extending:** T02 adds the contract-field warns there; gate 2 flips them to
  blocking under `auto` only.

- **Command:** `grep -rn 'autonomy' specfuse/loop/*.py`
- **Verdict:** only `gh_features.py:78` (label extraction) and
  `adopt_feature.py:30,41` (frontmatter write). **Zero run-loop consumers —
  no existing mechanism; building new.** This is the gap the feature closes.

Cost capture needs no building: `attempt_outcome` events already carry
`cost_usd` in their payload and WU frontmatter carries lifetime totals
(FEAT-2026-0016, PR #204).

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero — for everything gate 1 introduces.

Gate 1 introduces no severity flip: T02's lint checks are WARN-only, and T04's
wiring is passive (evaluate, emit, halt as today). The shadow predicate on a
clean on-plan feature with complete contract fields reports `would_arm: true`
and stops nothing. **Gate 2 is a different matter and must answer this section
again when G1-PLAN drafts it:** flipping the contract-field warns to blocking
under `auto` is a severity flip, and the §4 runtime probe at arming (run the
lint over every shipped feature fixture, paste the finding list into
`GATE-02-REVIEW.md`) is mandatory there.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0053/T01
        file: WU-01-plan-baseline-snapshot.md
        depends_on: []
      - id: FEAT-2026-0053/T02
        file: WU-02-plannext-contract-fields.md
        depends_on: []
      - id: FEAT-2026-0053/T03
        file: WU-03-arm-predicate-module.md
        depends_on: [FEAT-2026-0053/T01, FEAT-2026-0053/T02]
      - id: FEAT-2026-0053/T04
        file: WU-04-shadow-eval-wiring.md
        depends_on: [FEAT-2026-0053/T03]
      # --- closing sequence: non-terminal gate ---
      - id: FEAT-2026-0053/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0053/T01
          - FEAT-2026-0053/T02
          - FEAT-2026-0053/T03
          - FEAT-2026-0053/T04
      - id: FEAT-2026-0053/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0053/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0053/T05
        file: WU-05-arm-transaction-module.md
        depends_on: []
      - id: FEAT-2026-0053/T06
        file: WU-06-dial-and-verdict-wiring.md
        depends_on: [FEAT-2026-0053/T05]
      - id: FEAT-2026-0053/T07
        file: WU-07-lint-blocking-under-auto.md
        depends_on: [FEAT-2026-0053/T06]
      - id: FEAT-2026-0053/T08
        file: WU-08-feature-review-accumulation.md
        depends_on: [FEAT-2026-0053/T06]
      - id: FEAT-2026-0053/T09
        file: WU-09-learnings-staging.md
        depends_on: [FEAT-2026-0053/T06]
      # --- closing sequence: non-terminal gate ---
      - id: FEAT-2026-0053/G2-CLOSE-INTERMEDIATE
        file: WU-90-gate-2-close-intermediate.md
        depends_on:
          - FEAT-2026-0053/T05
          - FEAT-2026-0053/T06
          - FEAT-2026-0053/T07
          - FEAT-2026-0053/T08
          - FEAT-2026-0053/T09
      - id: FEAT-2026-0053/G2-PLAN
        file: WU-91-gate-2-plan-next.md
        depends_on: [FEAT-2026-0053/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      # --- closing sequence: terminal gate ---
      # G2-PLAN inserts gate 3's substantive WUs (docs/methodology rewrite,
      # migration guidance, whatever gate 2's retro surfaces) BEFORE this entry.
      - id: FEAT-2026-0053/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on: []   # G2-PLAN sets real depends_on when it drafts gate 3
```

T01 and T02 are independent (baseline vs contract fields); T03 needs both
(reads the baseline, tolerates but records the fields); T04 wires T03 into the
close path.

Gate 2 repeats gate 1's module-then-wiring shape: T05 is the pure arm
transaction, T06 wires the dial and the verdict into the one flip site that can
arm. T07, T08 and T09 all hang off T06 and are independent of each other — the
severity flip, the doubt accumulation, and the LEARNINGS staging touch
different surfaces and can be re-ordered or dropped individually at arming
without stranding the others.

## Notes

- `planned_cost_usd` covers the **drafted** work only. Re-baselined by G1-PLAN
  at the gate-1 → gate-2 boundary: gate 1's six units ($23.50) plus gate 2's
  seven drafted units ($25.50) plus gate 3's close placeholder ($5.00) =
  **$54.00**, a **+$25.50** delta against the original $28.50. Gate 3's
  substantive units are still undrafted, so this figure will move again when
  G2-PLAN re-baselines; the delta is stated in `GATE-02-REVIEW.md`.
- The shadow predicate fires for the first time at **this feature's own gate-1
  close** (T04 lands mid-gate). That is passive logging, so the
  `[FEAT-2026-0007/G2-LESSONS]` self-exercise trap does not bite — but the
  first *live* arming (dial `auto`, verdict acted on) must happen on a
  successor feature, and `GATE-02.md` carries the reminder to set its
  `cost_budget_usd` so the brake interplay is exercised too.
- Templates are duplicated: canonical scaffold copies live in
  `specfuse/loop/data/templates/` and the working copies in
  `.specfuse/templates/`, with `test_scaffold_data_in_sync.py` as drift guard.
  T02 edits **both** or the `tests` gate fails.
