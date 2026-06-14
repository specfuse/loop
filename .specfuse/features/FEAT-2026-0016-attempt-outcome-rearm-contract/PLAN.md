---
feature_id: FEAT-2026-0016
title: Per-attempt outcome events + re-arm contract + audit trail
slug: attempt-outcome-rearm-contract
branch: feat/FEAT-2026-0016-attempt-outcome-rearm-contract
roadmap_goal: Every dispatched attempt emits one `attempt_outcome` event with structured failure metadata, and re-arm cycles carry cumulative audit fields, so /gate-status, the predicate, the spinning-detector hook, and close-ceremony cost analysis read events.jsonl directly instead of re-parsing driver stdout.
autonomy_default: review
status: done
planned_cost_usd: 20.10
actual_cost_usd: 23.20
verdict: met_locally
---

# Plan: Per-attempt outcome events + re-arm contract + audit trail

Today the driver emits `attempt_outcome` events on SOME failure paths
(`zero_token_skip`, `smoke_import_failed`, `closing_deliverable_missing`,
`files_changed_mismatch`) but NOT on:

- **Successful attempts** — no event, no `outcome: passed`.
- **Generic gate failures** — when `tests: FAIL` / `lint: FAIL` / etc.
  fires, the driver buffers a per-attempt note and resets; no
  `attempt_outcome` event records WHICH gate failed or WHY.
- **Agent-emitted blocked** — agent RESULT `status: blocked` produces
  a `human_escalation` event but not a per-attempt `attempt_outcome`
  capturing the blocked-reason.

Consequences surfaced this session:

- **Predicate v1 check 7** fires `final_attempt_not_passed:
  outcome=no_events` against FEAT-2026-0015 because the events
  predate even the partial emission — a false positive caused by the
  predicate falling back on "no signal = bad signal".
- **Spinning detection** required reading driver stdout (`retry
  reason: ### tests: FAIL`) via Monitor. Non-queryable, lost on
  driver reset, can't drive an active hook.
- **Hollow-pass + wiring-race retros** need attempt-level signal
  (e.g. "attempt 1 wrote frontmatter only, no symbols") to be
  precise. Today the operator reconstructs this from prior_attempts
  notes + commit messages.
- **Re-arm cycles** (FEAT-2026-0013 burned $13.50 across 5
  dispatches) need cumulative audit fields so each cycle's prior
  spend is visible. /unblock-wu mentions the pattern but doesn't
  automate it; cumulative fields were invented ad-hoc per WU.

This feature lands the **data-layer foundation** that closes both
gaps in one ceremony:

1. **Attempt-level signal** — every dispatched attempt emits exactly
   one `attempt_outcome` event with structured payload
   (`outcome`, `failure_class`, `failure_signature`, `failure_excerpt`,
   `model`, `effort`, `files_touched`, `agent_status`,
   `agent_blocked_reason`, cost/duration/tokens). One event per
   attempt, every branch, standardized payload.
2. **Re-arm-level signal** — WU frontmatter gains `re_arm_count`,
   `re_arm_history`, and `cumulative_*` fields. Driver maintains
   them. `/unblock-wu` writes the history entries. `/gate-status`
   and close ceremony read them.
3. **Active consumers** — predicate-v2 candidate consumer deferred
   to a future feature (this feature LANDS the evidence; v2 designs
   against accumulated real data). For now: spinning-detector
   driver hook, `/gate-status` per-attempt surfacing, close-ceremony
   cost-analysis breakdown by failure_class, LEARNINGS
   auto-suggester clustering recurring signatures.

This file owns the **shape**. WU files own their own status; GATE
files own gate status.

## Folded scope — original FEAT-2026-0016 (re-arm contract + audit trail)

This feature **absorbs the entire scope of the originally-planned
FEAT-2026-0016** (re-arm contract + audit trail). The original 0016
row's WU frontmatter additions (`re_arm_count`, `re_arm_history`,
`cumulative_*`), driver cumulative-fold logic, `/unblock-wu`
mandatory-rationale, and `/gate-status` re-arm surfacing are all
in scope here. The merger preserves the original 0016 ID so the
roadmap row's planning history stays attached to the work that
ships under it — mirrors the FEAT-2026-0012 → FEAT-2026-0015
folding pattern.

Rationale for the merger: attempt-level events and re-arm cumulative
fields are at different granularities of the **same audit signal**.
Designing them in isolation is the documented failure mode (every
prior split in this surface — 0012/0015, 0007/0008 — eventually
re-converged). Re-arm history aggregates attempt_outcome data;
attempt_outcome data only makes sense in the context of a re-arm
lifecycle. Ship together.

## Scope OUT

- **Predicate v2.** This feature creates the evidence (attempt_outcome
  history per WU + re-arm cumulative data). Predicate v2 (relaxed
  check 1, structured check 7) ships in a future feature once the
  evidence exists to inform its design. Designing v2 simultaneously
  with the data feature = guessing.
- **Re-architecting result-contract.** Failure metadata is
  driver-observed (parsed from gate stdout), not RESULT-block-claimed.
  The agent's RESULT contract stays unchanged.
- **events.jsonl rotation / compression.** File-size concern, not in
  scope.
- **Cross-feature analytics.** Aggregating attempt_outcome history
  across all features for cost-calibration or estimation belongs to
  FEAT-2026-0011 (scoring framework) or a successor.
- **Validate-event.py extension.** Loop-driver events are validated
  in unit tests inside this feature; `validate-event.py` continues
  to validate orchestrator events only (its current scope).
- **Backfill of historical features.** Predicate gracefully
  degrades when `attempt_outcome` events are absent for a WU
  (legacy features) — treats final attempt as `passed` if WU
  `status == done`. No backfill skill / migration in this feature.

## Event payload shape — `attempt_outcome` v1

```json
{
  "event_type": "attempt_outcome",
  "correlation_id": "FEAT-YYYY-NNNN/TNN",
  "payload": {
    "attempt": 1,
    "outcome": "passed | failed | blocked | zero_token | files_changed_mismatch | post_pass_invariant_failed | closing_deliverable_missing | smoke_import_failed",
    "duration_seconds": 0.000,
    "cost_usd": 0.000,
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
    "model": "sonnet | opus | haiku-...",
    "effort": "low | medium | high | xhigh | max",
    "failure_class": "tests | lint | security | coverage | symbol_existence | bandit | other | null",
    "failure_signature": "<short stable string; null when outcome=passed>",
    "failure_excerpt": "<≤500 chars verbatim from gate stdout; null when outcome=passed>",
    "files_touched": ["<path>", ...],
    "agent_status": "complete | blocked | null",
    "agent_blocked_reason": "<from RESULT block; null otherwise>",
    "re_arm_count": 0
  }
}
```

`outcome` taxonomy locked at v1: extending requires a deliberate
revision (and the consumers — predicate, /gate-status, spinning-
detector — must update in lock-step). `null` is permitted for
`failure_class`, `failure_signature`, `failure_excerpt`,
`agent_status`, `agent_blocked_reason` when the outcome doesn't
have one. `failure_class: other` is the explicit bucket for
unclassified failures.

## Re-arm contract — WU frontmatter additions

```text
# WU frontmatter additions (issue: original FEAT-2026-0016 scope)
re_arm_count: 0                           # int, default 0; incremented by driver
re_arm_history: []                        # list of dicts:
                                          #   {timestamp, prior_status, prior_attempts,
                                          #    prior_cost_usd, prior_duration_seconds, reason}
cumulative_cost_usd: 0.0                  # float, sum across all attempts + re-arms
cumulative_duration_seconds: 0.0          # float, ditto
cumulative_input_tokens: 0                # int, ditto
cumulative_output_tokens: 0               # int, ditto
```

The cumulative fields differ from existing `cost_usd` / `duration_seconds`
/ `input_tokens` / `output_tokens` which the driver writes per
DISPATCH cycle. After `/unblock-wu` re-arms a `blocked_human` WU,
the cumulative fields preserve the prior cycle's spend so
`/gate-status` and close ceremony see the true total.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0016/T01
        file: WU-01-attempt-outcome-emission.md
        depends_on: []
      - id: FEAT-2026-0016/T02
        file: WU-02-rearm-frontmatter-contract.md
        depends_on: []
      - id: FEAT-2026-0016/T03
        file: WU-03-data-layer-tests.md
        depends_on:
          - FEAT-2026-0016/T01
          - FEAT-2026-0016/T02
      - id: FEAT-2026-0016/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0016/T01
          - FEAT-2026-0016/T02
          - FEAT-2026-0016/T03
      - id: FEAT-2026-0016/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0016/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0016/T04
        file: WU-04-spinning-detector-driver-hook.md
        depends_on: []
      - id: FEAT-2026-0016/T05
        file: WU-05-gate-status-per-attempt-surface.md
        depends_on: []
      - id: FEAT-2026-0016/T06
        file: WU-06-unblock-wu-rationale-history.md
        depends_on: []
      - id: FEAT-2026-0016/G2-CLOSE-INTERMEDIATE
        file: WU-90-gate-2-close-intermediate.md
        depends_on:
          - FEAT-2026-0016/T04
          - FEAT-2026-0016/T05
          - FEAT-2026-0016/T06
      - id: FEAT-2026-0016/G2-PLAN
        file: WU-91-gate-2-plan-next.md
        depends_on: [FEAT-2026-0016/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      - id: FEAT-2026-0016/T07
        file: WU-07-close-ceremony-cost-analysis.md
        depends_on: []
      - id: FEAT-2026-0016/T08
        file: WU-08-learnings-suggest-skill.md
        depends_on: []
      - id: FEAT-2026-0016/T09
        file: WU-09-docs-and-roadmap-archive.md
        depends_on: []
      - id: FEAT-2026-0016/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on:
          - FEAT-2026-0016/T07
          - FEAT-2026-0016/T08
          - FEAT-2026-0016/T09
```

## Notes

- Dependencies live here, not in WU frontmatter.
- WU file numbers track the correlation sub-ID; closing WUs use the
  reserved 90+ range.
- **Recursive dogfood.** This feature's own gate closes evaluate
  predicate v1 — which means T01's attempt_outcome emission will
  produce real evidence for the predicate to consume on this very
  feature's gate closes. If the data layer works, predicate-v2
  design has live data within this feature's lifecycle.
- **Bootstrap gap** (per `[FEAT-2026-0006/G1-CLOSE]`). T01's own
  attempt records will lack the standardized payload fields it
  adds (the driver dispatching T01 runs OLD code, before the
  commit lands). First WU with the full new shape is T02. T01's
  spec must call this out so retros don't flag the gap.

## Planned-cost table

| Gate | WU | type | effort | planned_cost_usd |
|------|----|------|--------|------------------|
| 1 | T01 | implementation | xhigh | 2.50 |
| 1 | T02 | implementation | high | 1.80 |
| 1 | T03 | implementation | high | 1.50 |
| 1 | G1-CLOSE-INTERMEDIATE | close-intermediate | medium | 1.20 |
| 1 | G1-PLAN | plan-next | high | 1.50 |
| 2 | T04 | implementation | high | 2.00 |
| 2 | T05 | implementation | medium | 1.20 |
| 2 | T06 | implementation | high | 1.50 |
| 2 | G2-CLOSE-INTERMEDIATE | close-intermediate | medium | 1.20 |
| 2 | G2-PLAN | plan-next | high | 1.50 |
| 3 | T07 | implementation | medium | 1.00 |
| 3 | T08 | implementation | medium | 1.20 |
| 3 | T09 | docs | low | 0.50 |
| 3 | G3-CLOSE | close | high | 1.50 |
| **Total** | | | | **20.10** |
