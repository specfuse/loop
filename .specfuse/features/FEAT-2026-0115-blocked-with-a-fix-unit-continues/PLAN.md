---
feature_id: FEAT-2026-0115
title: A block that names its fix unit continues the gate — the driver inserts the draft instead of waiting for a human
slug: blocked-with-a-fix-unit-continues
branch: feat/FEAT-2026-0115-blocked-with-a-fix-unit-continues
roadmap_goal: When a session reports `status: blocked` and hands the driver a drafted fix unit, the driver validates the draft, inserts it ahead of the blocked unit and keeps the gate running, so a defect the session already diagnosed costs no human wait.
autonomy_default: auto
status: planned
planned_cost_usd: 23.00
---

# Plan: a block that names its fix unit continues the gate

Agent-reported blocks are the largest class of human wait in the post-review
corpus: 34 of 76 escalations on driver >= 0.19 (45%), and 48% of all idle time
that follows an escalation (`reviews/2026-09-26-impact-assessment/`, private).
Thirty of the thirty-four came from one consumer repository, seventeen from one
feature whose QA unit carried the trigger "if a finding is a generator defect,
record it and block: the fix is a new unit before T18". The session did exactly
that, ten times: it diagnosed the defect, drafted the fix unit, and stopped. Each
stop waited for a human to flip the draft to `pending`, re-arm the blocked unit,
and restart the driver — median hours, sometimes a day. The escalation brief
does not even offer re-planning for this reason (`REPLAN_OPTION_SCOPE` marks
`agent_reported_blocked` as "the session named a boundary; its own
`blocked_reason` is the better lead"), which is right when the boundary is a
human decision and wrong when the session has already written the fix.

FEAT-2026-0104 built the mid-flight recovery this needs, for a different
trigger: a re-plan turn rewrites a unit's body before its last attempt. It may
not author new units or touch `depends_on`. This feature is the other half: a
blocked RESULT may carry `blocked_next:` naming a drafted fix unit; the driver
validates the draft with the same checks a plan-next draft gets and the same
stop classes the arm predicate applies, inserts it into the gate ahead of the
blocked unit, re-arms the blocked unit behind it, records the insertion, and
continues — under `autonomy_default: auto`. Under `review` the escalation
happens as today, but the brief says the fix is drafted and one command arms it.

**What this is not.** It is not a way for a session to grow its own gate
without bound. Two insertions per blocked unit, the arm predicate's
`drift_caps` (50% churn of the baseline), the gate's `cost_budget_usd`, and the
veto classes (`judge_editing`, `decision_class_paths`, `missing_provenance`)
all refuse the insertion and fall back to today's escalation, naming the class.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "def agent_reported_blocked\|REPLAN_OPTION_SCOPE\|def run_replan_turn\|def lint_plan_next_draft\|def evaluate_arm_predicate\|def apply_arm_transaction\|def reload_unit_after_replan\|detect_rearm_dispatch" specfuse/loop/loop.py specfuse/loop/lint_plan.py specfuse/loop/arm_eval.py specfuse/loop/arm_txn.py`
- **Verdict:** found the re-plan turn (FEAT-2026-0104), the plan-next draft lint, the arm predicate's stop classes and the arm transaction; reusing all four, building the insertion path new.
- **Detail.** `run_replan_turn` rewrites a body in place and is forbidden from
  authoring units — the wrong tool for a fix that is a new unit.
  `lint_plan_next_draft` already validates a drafted unit's five sections and
  `provenance`; `evaluate_arm_predicate` already classifies an added unit
  (`drift_caps`, `missing_provenance`, `judge_editing`, `decision_class_paths`);
  `apply_arm_transaction` already flips `draft → pending` in one bookkeeping
  commit. None of them runs mid-gate today: the live arm is gate-end only, and a
  gate holding a `draft` unit at start exits 2. `reload_unit_after_replan`
  shows how the in-memory `units` snapshot is refreshed mid-run.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero. A blocked RESULT without `blocked_next:` escalates exactly as today. A
  RESULT with it either inserts (no escalation) or escalates with the refusing
  class named — never a new block. With `verification.yml`
  `defaults: fix_unit_insertion: false` the key is ignored.

## Assumptions taken by default (answers-supplied drafting, 2026-09-26)

- **Autonomy `auto`.** Single gate; the judge writes the terminal verdict.
- **The session drafts the unit file; the driver inserts it.** The alternative
  (the driver dispatches a separate drafting session from `blocked_reason`) costs
  a second dispatch and loses the diagnosing session's context. The consumer
  runs in the evidence already drafted the units themselves.
- **Insertion is `draft → pending` immediately, not `draft` awaiting arm.** The
  point is no wait; the stop classes are the review.
- **Caps:** two insertions per blocked unit, `drift_caps` unchanged at 50%.

## Task graph

```yaml
# Single gate, single terminal close: 4 substantive WUs is under the ceremony
# proportionality threshold (docs/methodology.md §6).
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0115/T01
        file: WU-01-insert-the-named-fix-unit.md
        depends_on: []
      - id: FEAT-2026-0115/T02
        file: WU-02-stop-classes-and-caps.md
        depends_on: [FEAT-2026-0115/T01]
      - id: FEAT-2026-0115/T03
        file: WU-03-auto-close-and-brief.md
        depends_on: [FEAT-2026-0115/T01]
      - id: FEAT-2026-0115/T04
        file: WU-04-document-the-contract.md
        depends_on: [FEAT-2026-0115/T02, FEAT-2026-0115/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0115/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0115/T01, FEAT-2026-0115/T02, FEAT-2026-0115/T03, FEAT-2026-0115/T04]
```

## Scope boundary — explicitly OUT

- **Blocks that name no fix.** A `blocked_reason` without `blocked_next:` is a
  human decision and escalates as today. No parsing of free text for unit ids.
- **The re-plan turn (FEAT-2026-0104).** Untouched; different trigger.
- **Gate-end arming and `plan-next`.** The inserted unit lives in the current
  gate; the next gate's drafts and their arm are unchanged.
- **Parallel dispatch (FEAT-2026-0105).** Insertion assumes serial dispatch.
- **No consumer repository is edited.**

## Post-merge checklist

Observable only across repositories and over time (`close-discipline.md` §2).

- [ ] Over the next ten features closed in this repo and the generator, count
      `human_escalation` events with `reason: agent_reported_blocked` per
      feature (baseline 1.21 per feature on driver >= 0.19, 3.26 in the
      generator) and `fix_unit_inserted` events, and the share of blocks that
      carried `blocked_next:`.
- [ ] For every insertion, whether the terminal close or judge found the
      inserted unit's work wanting (a finding naming its id).

## Notes

- Dependencies live here, not in WU frontmatter.
- T02 and T03 are independent once T01 lands.
