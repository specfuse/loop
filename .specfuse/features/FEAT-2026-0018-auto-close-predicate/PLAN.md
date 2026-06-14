---
feature_id: FEAT-2026-0018
title: Deterministic gate-close predicate + auto-close path
slug: auto-close-predicate
branch: feat/FEAT-2026-0018-auto-close-predicate
roadmap_goal: Replace AI-judgment gate close with deterministic predicate that auto-flips on-plan gates (terminal + intermediate) and skips reflective WUs, preserving full ceremony for off-plan cases.
autonomy_default: review
status: planned
planned_cost_usd: 19.40
---

# Plan: Deterministic gate-close predicate + auto-close path

Today every gate close burns a `close` / `close-intermediate` + `plan-next`
ceremony regardless of whether the gate actually went off-plan. Backtest
of the last 4 completed features shows 50% would have auto-closed under
a strict predicate (0013, 0014) while 50% legitimately needed the full
ceremony (0015, 0017 — both went off-plan). Reflective WUs aren't a
"false good idea" — they're a conditional one. Today's machinery runs
them unconditionally.

This feature lands a deterministic predicate (`gate_eval.py`, hardcoded
v1 constants) that the driver consults at every gate boundary
(intermediate + terminal). On auto-close: stub `RETROSPECTIVE.md`
written, retro+lessons+docs WUs skipped, terminal flips fired or next
gate's `plan-next` runs only (option A — intermediate auto-close still
needs `plan-next` to author the next gate's draft work units; full
retro+lessons+docs is what gets skipped). On non-auto: existing close
path unchanged. `--force-full-close` flag escapes.

Real value isn't AI cost savings (backtest: ~$0.67/feature avg). Real
wins are: (a) operator cycle time — no `/arm-gate` round-trip on
happy paths; (b) brittleness surface area reduction — wiring-race,
hollow-pass, assertion-gap classes all disappear on auto-close path
because no close-WU dispatches; (c) predictability — deterministic
flip > AI judgment, scales to the orchestrator.

This file owns the **shape**. WU files own their own status; GATE files
own gate status.

## Scope OUT

- **Re-architecting close-WU types or templates.** FEAT-2026-0015's
  `close` / `close-intermediate` / `plan-next` contract stays. This
  feature adds a *path* that bypasses them when the predicate fires;
  the types themselves are unchanged.
- **Cross-feature cost analytics.** Aggregating per-WU planned vs
  actual across all features for self-calibrating estimates belongs
  to FEAT-2026-0011 (scoring framework) or its successor. This
  feature reads per-feature evidence only.
- **Re-arm contract changes.** FEAT-2026-0016 owns the cumulative
  cost / re-arm-history surface. This feature reads what 0016 writes
  (when 0016 lands), gracefully degrades when fields are absent.
- **Predicate tuning via `verification.yml` knobs.** v1 hardcodes
  constants in `gate_eval.py`. Project-specific tolerances are a
  future feature once a real project needs them.
- **Removing reflective WUs from existing in-flight feature drafts.**
  `/migrate-to-auto-close` (gate 3) surfaces the capability and
  optionally flags now-redundant drafts; it does NOT auto-rewrite
  existing PLAN.md files. Migration is opt-in per-feature.
- **New WU lifecycle status for auto-skipped close WUs.** When the
  predicate fires and skips a `close-intermediate` / `close` WU's
  dispatch, the driver marks the WU `status: done` with frontmatter
  flag `auto_close: true` (and `auto_close_reasons: [...]`). No new
  status added; no lint changes for status transitions; existing
  tooling continues to read `done` correctly. The frontmatter flag
  is the audit signal.

## Predicate v1 (hardcoded constants)

A gate auto-closes iff ALL hold:

1. **No blocked_human in attempt chain** — no WU in this gate has
   `blocked_human` in its lifecycle events (events.jsonl) for this
   run. (Re-arm history from FEAT-2026-0016, if present, is also
   inspected — any prior `blocked_human` cycle disables auto.)
2. **No replan** — no `replan` event in events.jsonl for this gate's
   WUs.
3. **Per-WU cost ≤ 1.5× planned** — every substantive WU's
   `cost_usd` ≤ `planned_cost_usd × 1.5`. If `planned_cost_usd`
   absent: skip this check for that WU (graceful degrade — emits a
   warning reason in the decision but doesn't disable auto).
4. **No WU > 2× planned** — even one substantive WU exceeding
   plan by > 2× disables auto regardless of others. Catches
   estimation drift like FEAT-2026-0015/G1-PLAN (3.8× over).
5. **Plan-next ≤ 1.5× planned** — plan-next type specifically held
   to same 1.5× ceiling (separately enforced so plan-next overrun
   is a visible reason in the decision).
6. **Gate total ≤ `cost_budget_usd`** — if GATE-NN.md declares a
   budget, sum of all WU `cost_usd` in the gate must be ≤ budget.
   Absent budget: skip this check.
7. **No test/lint/security failures in attempt notes** — every
   substantive WU's final attempt's `attempt_outcome` must be
   `passed`. Earlier attempts may have failed (covered by check 1
   already if blocked), but the FINAL outcome on each WU must be
   clean. (Effectively: WUs that passed-after-retry are eligible
   only if check 1's "no blocked_human" holds.)

Edge case — **single-attempt-after-failure**: check 1 governs. A
WU that had 2 attempts (one fail, one pass) and no blocked_human
escalation is auto-eligible. A WU that escalated to blocked_human
and was re-armed is NOT auto-eligible even if eventually passed.
Rationale: re-arm cycles signal substantive operator intervention
worth a retrospective.

## Task graph

```yaml
# Closing shape (FEAT-2026-0015):
#   Gates 1 & 2 (non-terminal): 2-WU each → close-intermediate + plan-next.
#   Gate 3 (terminal): 1-WU → close.
#   Gates 2 & 3 work_units scaffolded so lint identifies gate position;
#   substantive WU bodies drafted by prior gate's plan-next at arm time.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0018/T01
        file: WU-01-gate-eval-module.md
        depends_on: []
      - id: FEAT-2026-0018/T02
        file: WU-02-gate-eval-tests.md
        depends_on: [FEAT-2026-0018/T01]
      - id: FEAT-2026-0018/T03
        file: WU-03-gate-eval-cli.md
        depends_on: [FEAT-2026-0018/T01, FEAT-2026-0018/T02]
      - id: FEAT-2026-0018/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0018/T01
          - FEAT-2026-0018/T02
          - FEAT-2026-0018/T03
      - id: FEAT-2026-0018/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0018/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # Substantive WUs drafted by G1-PLAN at gate-1 close.
      # Closing sequence scaffolded so lint can identify gate 2 as non-terminal.
      - id: FEAT-2026-0018/G2-CLOSE-INTERMEDIATE
        file: WU-90-gate-2-close-intermediate.md
        depends_on: []   # G1-PLAN sets real depends_on
      - id: FEAT-2026-0018/G2-PLAN
        file: WU-91-gate-2-plan-next.md
        depends_on: [FEAT-2026-0018/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      # Substantive WUs drafted by G2-PLAN at gate-2 close.
      # Single close WU scaffolded so lint identifies gate 3 as terminal.
      - id: FEAT-2026-0018/G3-CLOSE
        file: WU-90-gate-3-close.md
        depends_on: []   # G2-PLAN sets real depends_on
```

## Notes

- Dependencies live here, not in WU frontmatter.
- WU file numbers track the correlation sub-ID; closing WUs use the
  reserved 90+ range so they sort last.
- **Recursive dogfood.** Gate 1's close runs through the OLD path
  (driver not yet wired). Gate 2's close-intermediate dispatches via
  the new wiring but gate 2 IS the hot-path rework — attempts likely
  > 1, predicate likely refuses auto. Gate 3 (lint + skill + docs)
  is the only realistic self-test: if G3 goes on-plan, G3-CLOSE
  auto-fires, $0 close-WU cost, and the close-WU bypass exercises
  itself end-to-end against the terminal-flip path. Documented in
  G3-CLOSE's verdict regardless of outcome.
- **Wiring race recursion.** FEAT-2026-0017's
  `assert_terminal_flips_fired` invariant guard MUST still fire on
  auto-close terminal paths — the driver still calls
  `fire_terminal_flips` after the stub retro is written. If the
  guard somehow misses the auto-close path, that's a new wiring
  hole this feature created. T04's body names this as an explicit
  invariant.

## Planned-cost table

| Gate | WU | type | effort | planned_cost_usd |
|------|----|------|--------|------------------|
| 1 | T01 | implementation | high | 1.80 |
| 1 | T02 | implementation | high | 1.50 |
| 1 | T03 | implementation | medium | 0.80 |
| 1 | G1-CLOSE-INTERMEDIATE | close-intermediate | medium | 1.20 |
| 1 | G1-PLAN | plan-next | high | 1.50 |
| 2 | T04 | implementation | xhigh | 2.50 |
| 2 | T05 | implementation | xhigh | 2.20 |
| 2 | T06 | implementation | medium | 0.80 |
| 2 | G2-CLOSE-INTERMEDIATE | close-intermediate | medium | 1.20 |
| 2 | G2-PLAN | plan-next | high | 1.50 |
| 3 | T07 | implementation | medium | 1.00 |
| 3 | T08 | implementation | low | 0.40 |
| 3 | T09 | implementation | medium | 1.20 |
| 3 | T10 | docs | low | 0.30 |
| 3 | G3-CLOSE | close | high | 1.50 |
| **Total** | | | | **19.40** |
