---
feature_id: FEAT-2026-0062
title: Lifetime-cost reads for budget_projection and the per-gate brake
slug: lifetime-cost-reads
branch: feat/FEAT-2026-0062-lifetime-cost-reads
roadmap_goal: Make both cost consumers — the budget_projection arm-predicate class and the per-gate budget brake — read a work unit's lifetime spend rather than its current dispatch cycle, and make the brake able to see an overrun that happens inside a gate's final work unit.
autonomy_default: review
status: done
planned_cost_usd: 16.00
---

# Plan: Lifetime-cost reads for `budget_projection` and the per-gate brake

Two consumers gate real driver behaviour on a work unit's cost. `budget_projection`
(`arm_eval.py`) is the arm-predicate class that stops a feature heading past 2× its
baseline; `gate_spent_usd` (`loop.py`) drives the per-gate budget brake. Both are
mechanical brakes, and under `auto` they are among the few things standing between a
stuck feature and an unbounded spend.

## What the roadmap got wrong, and what is actually broken

The roadmap detail section states that neither consumer reads `cumulative_cost_usd`
or `re_arm_history[].prior_cost_usd`. **That is half stale.** `gate_spent_usd`
(`loop.py:1782`) already sums `cost_usd + cumulative_cost_usd` — it was fixed for the
driver's fold path in #199/#219, and its docstring says so. Only
`budget_projection` (`arm_eval.py:266`) still reads `cost_usd` alone.

The remaining hole is narrower and was found by reading real data rather than the
code. A re-arm folds the prior cycle's spend into `cumulative_cost_usd` **only when
`detect_rearm_dispatch` fires**, and that helper requires `cost_usd > 0` at dispatch
time. Re-armed work units in this repository therefore exist in two shapes:

```
WU-02 (FEAT-2026-0020)  cost=0.539  cum=0.473  priors=[0.473]   fold ran
WU-03 (FEAT-2026-0069)  cost=2.384  cum=5.261  priors=[5.261]   fold ran
WU-07 (FEAT-2026-0053)  cost=4.282  cum=—      priors=[5.01]    fold never ran
WU-04 (FEAT-2026-0020)  cost=0.163  cum=—      priors=[0.163]   fold never ran
```

On the fold-never-ran shape the prior cycle's spend survives **only** in
`re_arm_history[].prior_cost_usd`, which neither consumer reads. For
`FEAT-2026-0053/WU-07` the true lifetime is $9.29 and `gate_spent_usd` reads
**$4.28** — the missing $5.01 is exactly the gate-spend under-read the roadmap
cites, arriving by a different route than the roadmap describes.

**The trap.** The obvious fix — sum all three fields — is wrong. On the fold-ran
shape `cumulative_cost_usd` and `prior_cost_usd` are *the same money*, so naive
summing double-counts $0.47 on WU-02 and $5.26 on WU-03. Double-counting brakes
healthy features, which is the opposite failure but not a better one.

## The decisions this feature settles

**Canonical source: `events.jsonl`, with a frontmatter fallback.** Every attempt
emits one `attempt_outcome` event carrying `cost_usd`. Summing those events for
`FEAT-2026-0053/WU-07` reconstructs **$9.29 exactly**, with no fold-shape reasoning
at all — the event log is the one surface that never loses a cycle, which is what
`LEARNINGS [FEAT-2026-0053/G2-CLOSE]` recommends in as many words. It is also
already inside `feature_dir`, so `arm_eval` gains no new coupling.

An events-only read was rejected: **12 of 44 features have no usable cost events**
(3 carry no `events.jsonl`, 9 have one with no `attempt_outcome`), and on those an
events-only sum returns $0.00 — a false `clean` on a budget brake, which fails open.
The fallback to `cost_usd + cumulative_cost_usd` keeps those features at today's
behaviour rather than worse than today.

A shape-aware frontmatter reconstruction was also rejected. Deciding "did the fold
run" is a heuristic recovery of a past code path, and that exact class of guard is
what produced the two shapes in the first place.

**Helper location: a new `specfuse/loop/cost.py`.** `arm_eval.py`'s module docstring
records that the dependency runs `loop.py → arm_eval`, so `arm_eval` cannot import
`loop`. Without a third module the fix is duplicated in two places, which is how the
two aggregates acquired *different* blind spots in the first place.

**Brake evaluation: add a post-dispatch breach report, keep the pre-dispatch halt.**
`_should_halt_for_budget` is evaluated only before each dispatch (`loop.py:5142`),
so an overrun inside a gate's final work unit cannot be seen — FEAT-2026-0053's
gate 2 closed **$4.94 over** its $31.50 brake without the brake firing. The
alternative, a projected-cost pre-check that refuses to dispatch a unit whose
`planned_cost_usd` would breach, was rejected for this feature: it brakes on an
*estimate*, and refusing real work on a guess is a larger behaviour change than
reporting a breach that has already happened.

## Scope boundary

**IN.** The lifetime-cost helper and its two consumers; the post-dispatch brake
breach report; their tests.

**OUT — the `detect_rearm_dispatch` fold divergence itself.** The two shapes above
come from that guard's `cost_usd > 0` condition. Under the chosen design the
consumers become shape-independent, so the divergence stops affecting any decision
the driver makes. Fixing the fold changes what is *written* to frontmatter for every
future work unit — a different blast radius, and not required for this feature to be
correct. It needs its own roadmap row.

**OUT — token and duration aggregates.** `cumulative_duration_seconds`,
`cumulative_input_tokens`, and `cumulative_output_tokens` have the same shape, but
no consumer gates behaviour on them and no impact has been measured.

**OUT — backfilling cost events** for the 12 features that lack them.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  `grep -n "def gate_spent_usd\|def _should_halt_for_budget" specfuse/loop/loop.py`
  and `grep -rn "def .*lifetime\|def .*cumulative\|def .*total_cost\|def .*spend" specfuse/loop/*.py`
- **Verdict:** `found gate_spent_usd, extending it`

`gate_spent_usd` already exists and already does most of this job — its docstring
opens *"Sum lifetime recorded cost across ALL of the gate's WUs"* and it was
corrected for the driver fold path in #199 and for non-`done` work units in #219.
This feature extends that existing aggregate to the one path it still misses and
routes the second consumer through the same code, rather than building a parallel
mechanism beside it. The second grep returns only `fold_cumulative_on_rearm`, which
*writes* the cumulative fields rather than reading them, so there is no existing
reader to reuse.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature makes two existing brakes fire in cases where they previously stayed
silent, so the check applies.

- **What does the rule report on an input already in its intended final state?**
  **Unchanged from today.** A work unit that was never re-armed has no
  `cumulative_cost_usd` and no `re_arm_history`, so its lifetime cost equals its
  `cost_usd` and both consumers produce exactly the number they produce now. A gate
  that stays within budget still reports no breach.

The verdicts that change are precisely the ones that are wrong today: a re-armed
work unit's spend stops being under-counted, and a gate that overran on its final
work unit stops reporting silence. Neither brake becomes stricter on a feature that
is genuinely within budget.

**The residual risk runs the other way and T02 carries it explicitly:**
double-counting on the fold-ran shape would brake a healthy feature. That is the one
regression this design can introduce, and it has a named acceptance criterion.

## Task graph

```yaml
# Single terminal gate: 3 substantive WUs, under the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0062/T01
        file: WU-01-lifetime-cost-helper.md
        depends_on: []
      - id: FEAT-2026-0062/T02
        file: WU-02-wire-both-consumers.md
        depends_on: [FEAT-2026-0062/T01]
      - id: FEAT-2026-0062/T03
        file: WU-03-post-dispatch-brake-check.md
        depends_on: []
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0062/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0062/T01
          - FEAT-2026-0062/T02
          - FEAT-2026-0062/T03
```

T03 is independent of T01 and T02: the brake's *evaluation point* is a separate
defect from what it *reads*, and fixing where the check runs needs nothing from the
lifetime helper. T02 depends on T01 because it wires consumers to a function T01
creates.

## Notes

- **The close reconciles against the surface this feature makes canonical.** Every
  close ceremony already computes actual spend from `events.jsonl`; this feature
  makes that the driver's source too. The close is therefore exercising its own
  deliverable, which is a genuine verification and worth stating rather than a
  coincidence to leave implicit.
- **`autonomy_default: review` is structural.** `specfuse/loop/` is a `JUDGE_PATHS`
  prefix (`arm_eval.py:57`), so every gate of this feature fires `judge_editing` and
  `auto` is unreachable regardless of what this field says.
- This feature modifies the arm predicate that would evaluate its own successor
  gates. Gate 1 is terminal, so there is no successor gate and no bootstrap problem
  — the same note FEAT-2026-0061 recorded, and for the same reason.
