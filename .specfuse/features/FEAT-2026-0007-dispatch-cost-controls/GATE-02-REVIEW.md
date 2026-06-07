# Gate 2 review — FEAT-2026-0007

Drafted by `FEAT-2026-0007/G1-PLAN` (Opus). Read this before arming.
Weighted toward **DOUBT**: if I had to bet which decision you'll overturn at
review, those calls are in **Flagged for attention** first.

This file is **advisory**. It owns no state. Status lives in WU files; the
graph lives in `PLAN.md`. If you change a decision, edit the WU and the graph
directly.

---

## Headline: a hygiene WU was inserted that you did not ask for

Gate 1's `RETROSPECTIVE.md` documents a CRITICAL FINDING under T04:
T04 reported `status: complete`, the driver committed, verification passed,
but **none of the required code changes (the retry-escalation ladder, the
`effort_for_attempt`/`terseness_for_attempt` helpers, the `dispatch()`
kwargs, the `attempts_usage` extensions) ever landed in the repo.** The
existing tests don't assert the symbols exist, so the driver's verification
saw an unchanged tree and let it through.

T08 in this gate's stated scope is "telemetry extension." T08 cannot extend
fields T04 was supposed to add but did not. So I inserted **T08H** — a
hygiene WU that re-lands T04's contract — ahead of T08 per
`.specfuse/rules/correlation-ids.md` §Hygiene units and LEARNINGS
`[meta/first-live-use]` (the hygiene-WU pattern). The original WU-93 prompt
asked for "three substantive WUs"; this gate now has four (T06, T07, T08H,
T08). I chose hygiene-WU-insertion over the alternatives:

- Re-open T04 (forbidden — it's committed `done`).
- Bundle T04's missing work into T08 (muddies T08's scope; loses the
  audit trail that *says* this was a corrective action).
- Silently ship T08 over absent fields (the original problem, repeated).

**This is your call to validate or overturn.** If you'd rather collapse
T08H into T08 (acceptable; document the bundle in the commit), edit T08's
ACs to include T08H's AC 1-8 and delete WU-08H. If you'd rather defer the
fix to a Gate 3, scope T08 to *only* add `resolved_model` + `cache_hit_rate`
(no per-attempt `effort_used`/`terseness` reads) and accept the gap.

The escalation trigger in WU-93 covered this exact case ("if Gate 1's
retrospective surfaces a fundamental flaw … draft what is coherent and
flag the ordering question loudly"). T08H is the "what is coherent" call.

---

## Decisions & rationale

### Substantive WUs — count and shape

| WU | Title | Model | Effort | Type |
|---|---|---|---|---|
| T06 | Defaults-by-WU-type policy + Haiku guidance | sonnet | high | implementation |
| T07 | Per-gate cost budget with `blocked_human` halt | opus | high | implementation |
| T08H | Hygiene: re-land T04's retry-ladder code | opus | high | implementation |
| T08 | Telemetry extension (resolved_model, cache_hit_rate, gate summary) | sonnet | medium | implementation |

T06 carries `MODEL_BY_TYPE` + `EFFORT_BY_TYPE` tables, a `load_wu` change to
default-when-absent, a `lint_plan.py` change to accept absent `model:`, a
template note edit, and a Haiku policy section. Five files; design surface
is in the table values. Sonnet because the shape is bounded by ACs.

T07 carries `gate_budget_usd` / `gate_spent_usd` helpers, a halt branch at
the top of the per-WU iteration in `run()`, a GATE.template.md note, a
`lint_plan.py` validator entry. Four files; design surface is in the halt
placement (see Flagged #1). Opus because it edits `run()`'s control flow
and the budget-vs-closing-sequence interaction (Escalation trigger 3 in
WU-07) needs forward design that Sonnet would underweight.

T08H is the hygiene re-land of T04. The ACs are T04's original ACs
verbatim, plus the existence-smoke-check that was missing
(`[FEAT-2026-0007/G1-LESSONS]`). Opus because T04 itself was Opus —
matching the original control-flow-editing call.

T08 carries `cache_hit_rate`, `gate_summary`, the per-attempt
`resolved_model` field, and the `task_completed` payload extension. Two
files; design surface is the cache_hit_rate denominator (see Flagged #2).
Sonnet because the shape is mechanical once T08H lands.

### Defaults tables (T06)

| Type | Model default | Effort default |
|---|---|---|
| implementation | sonnet | medium |
| retrospective | sonnet | low |
| lessons | sonnet | low |
| docs | sonnet | low |
| plan-next | opus | high |
| close | opus | high |

Source: Gate 1's per-WU cost table in `RETROSPECTIVE.md`. T01–T03
(implementation, sonnet, medium-ish work) completed in 1 attempt for
\$0.40–\$0.82 each. T04 (implementation, opus) cost \$1.26 — and didn't
actually land its code, weakening the "opus for control-flow edits"
justification mildly, but the per-attempt rules suggest the opus failure
mode was an instruction-following gap, not a reasoning gap. Closing WUs
(retrospective \$0.49, lessons \$0.20, docs \$0.69) on sonnet at what
was effectively `low` (single-purpose synthesis) confirm cheap defaults.
Plan-next is the only WU where forward design matters — opus + high.

Haiku policy: opt-in only via explicit `model: haiku`; recommended for
`docs` (small reconciliation) and `lessons` (≤5-entry append). Discouraged
for implementation/plan-next/close, where Gate 1's costs were already
modest and the regression risk on Haiku outweighs the saving. (T06 AC 6.)

### Budget brake semantics (T07): halt **between** WUs

`MAX_ATTEMPTS` halts mid-WU after attempt 3 fails. A budget brake could
analogously halt mid-attempt when running total exceeds budget. I chose
**halt between WUs** instead:

- The squash-commit contract assumes a WU runs to a terminal outcome
  before the next begins. Mid-attempt halt would leave an in-progress
  WU with no terminal artifact.
- The driver's `IN_PROGRESS → DONE | blocked_human` state machine has
  no "interrupted" leaf today. Adding one is gate-3 scope, not gate-2.
- Cost overshoot of one WU is a bounded leak — the next WU might cost
  \$0.50 — vs the much larger correctness risk of a half-completed
  WU's diff.

**This is the Flagged #1 call.** A reviewer who weighs cost-overrun
more highly than diff-cleanliness can flip it; see WU-07 AC 4 and
trigger 2.

### Cache hit rate denominator (T08)

T08 AC 1 chose `cache_read / (cache_read + cache_creation + input_tokens)`
— total cached share of all input the model saw. The alternative is
`cache_read / (cache_read + input_tokens)` — share of cacheable input
that hit cache, ignoring creations. The methodology has no prior art
here. I picked the first because creations are a real cost component
the user pays for; rolling them into the denominator makes the metric
worse when the loop pays to write cache that doesn't pay back. Without
first telemetry I can't confirm the formula produces sensible values
in [0,1] — flagged as Open Question Q2.

### Dependency edges

```
T06 ─┐
     ├─→ T08 ─→ G2-RETRO ─→ G2-LESSONS ─→ G2-DOCS ─→ G2-PLAN
T08H ┘            ▲
T07 ──────────────┘
```

T06 must land before T08 because T08 reads `wu.model` post-`load_wu` and
T06 changes what `wu.model` resolves to when absent. T08H must land
before T08 because T08's tests assert the schema T08H lands. T07 is
independent of all three substantive WUs (its halt logic doesn't touch
the WU's own dispatch).

### Closing-WU file numbering 94–97

Continues Gate 1's `WU-90`..`WU-93`. The convention (90+ range sorts
last) is documented in LEARNINGS `[FEAT-2026-0003/G1-LESSONS]` but still
not promoted to a binding rule — see Q3.

### Existence smoke checks on every implementation WU

Every implementation WU in this gate (T06, T07, T08H, T08) includes an
explicit `python3 -c "from loop import <symbol>"` smoke check in its
Verification section and a completeness escalation trigger ("if the
symbol is absent, emit `status: blocked`"). This is the
`[FEAT-2026-0007/G1-LESSONS]` rule applied uniformly — the rule the
T04 failure surfaced.

---

## Flagged for attention — check these three first

### (1) Budget brake halts **between WUs**, not mid-attempt — is that what you want?

WU-07 AC 4 commits to halting before the next WU's
`set_wu(IN_PROGRESS)`. Rationale above. **The risk shape**: a single
expensive WU can overrun the budget by ~\$1–\$2 (one Opus implementation
WU's worth) before the brake fires. If the budget is \$3.00 and the
running total is \$2.95 when WU N starts, WU N runs to completion at,
say, \$1.25, total ends at \$4.20, *then* the brake fires for WU N+1.

**Resolution options at review:**
- **Accept** (recommended for v0.1): the simplest, atomic-with-squash
  semantics; matches the natural granularity of the loop. Mention the
  overrun caveat in T07's GATE.template.md note.
- **Tighten:** add a pre-dispatch check in `execute_unit_attempt` that
  halts when `spent + estimated_max_cost > budget`. Requires an
  estimator (per-WU type? from history?) — non-trivial; rolls into
  gate-3.
- **Loosen:** make the brake advisory only (log + warn, don't halt).
  Rejected because it doesn't mirror `MAX_ATTEMPTS`' shape.

### (2) Cache hit rate denominator is a guess — Q2 below depends on Gate 2 telemetry

T08 AC 1 picks `cache_read / (cache_read + cache_creation + input)`.
**Sample-check the math** against the Gate 1 events for sanity before
arming. From events.jsonl tail: G1-LESSONS attempt had
`cache_read_input_tokens=203587, cache_creation_input_tokens=24439,
input_tokens=8`. By chosen formula: `203587 / (203587 + 24439 + 8) =
0.893`. By the alternative: `203587 / (203587 + 8) ≈ 1.000`. The
alternative degenerates to ~1 on every Gate 1 attempt (input_tokens
were 8–30 across the gate; cache_creation was the only meaningful
non-read input). The chosen formula gives a useful range. So the
**math validates the chosen denominator**, but I haven't confirmed it
on a gate where creation-vs-read balance is different. Open Question
Q2 keeps this honest.

### (3) Assumption made to proceed: T08H will land cleanly

T08H repeats T04's contract with the missing completeness trigger
added. If T08H *also* fails to land its code — the same instruction-
following gap that bit T04 — Gate 2 ends in the same failure mode,
this time with a `status: done` T08H whose symbols don't import. The
new triggers (T08H AC 9 smoke check, trigger 1 completeness, trigger
2 diff-sanity check) are designed to catch it, but they live inside
the agent's RESULT block — the same surface T04 lied through.

**Mitigation at arming time:** consider running the smoke check
yourself after T08H's commit lands, before letting the driver move
on to T08. (You can `python3 -c "from loop import EFFORT_LADDER"`
from your shell.) If T08H is the same lie, halt and escalate before
T08 builds on a phantom schema.

**Alternative:** add T08H smoke-check to `verification.yml`'s `code`
gate as a temporary check (`python3 -c "..."` listed as a `name: smoke`
command). This makes the gate the oracle, not the agent's RESULT block.
I did not include this edit in T08H's ACs because modifying
`verification.yml` from a substantive WU is scope creep — it belongs
in a dedicated WU. If you want belt-and-suspenders, add it as a
prerequisite hand-edit before arming.

---

## Roadmap anchor

`roadmap_goal`: *Cut loop dispatch cost via per-WU model alias, effort
tier, terseness, and per-gate budget.* Mapping:

| Lever | Mechanism shipped in | Status |
|---|---|---|
| per-WU model alias | T01 (Gate 1) | landed |
| effort tier | T02 (Gate 1) | landed |
| terseness directive | T03 (Gate 1) | landed |
| retry escalation | T04 (Gate 1) | **claimed-done, not landed** — T08H corrects |
| failure-note cap | T05 (Gate 1) | landed |
| per-gate budget | T07 (Gate 2) | drafted |
| defaults policy | T06 (Gate 2) | drafted (not in original goal text, but a force-multiplier on the four levers) |
| telemetry | T08 (Gate 2) | drafted (observation only; how we *know* the goal was met) |

Gate 2 closes the goal — assuming T08H actually lands T04's code. If
T08H also fails to land, the feature did not deliver retry escalation
and the goal is not met; G2-PLAN should write that finding into the
terminal verdict and propose a Gate 3 (or, more honestly, a new
feature) to fix it.

**Goal-change escalation?** The retrospective does not imply the
roadmap_goal should change. The text is fine; what's broken is one of
its levers, and the fix is T08H, not a goal rewrite.

---

## Open questions (mapped to WUs)

### Q1. Should T08H be collapsed into T08 (or T08H smoke-check promoted into `verification.yml`)? (affects T08H, T08)

The hygiene-WU split adds one more squash commit and one more
plan-status flip vs bundling. The split's value is audit clarity ("this
is a corrective WU because T04 lied"); the bundle's value is fewer
moving parts. If you'd prefer the bundle, fold T08H's ACs 1-8 into
T08, delete WU-08H, and update PLAN.md's graph.

### Q2. Cache hit rate denominator — does the chosen formula produce useful values on Gate 2 telemetry? (affects T08)

The chosen `cache_read / (reads + creations + input)` gave 0.893 on a
Gate 1 sample. If Gate 2's WUs all have similar cache-creation
patterns, the metric will sit near 1.0 and lose discrimination.
G2-RETRO is the natural place to verify this empirically; the formula
itself may need a second pass in a future feature if the metric is
not actionable.

### Q3. Closing-WU 90+ numbering convention — promoted to a binding rule before Gate 3 plan-next? (affects G2-PLAN's drafting if Gate 3 happens)

Same question as gate 2 review of FEAT-2026-0003 raised; still
unpromoted. If you do not promote it before G2-PLAN fires (and Gate 3
gets drafted), G2-PLAN will continue the convention by hand with
WU-98..WU-101. If you do promote it, the rule's wording should match
what's been done de facto across FEAT-2026-0003 and FEAT-2026-0007.

### Q4. Budget halt during the closing sequence — should it fire? (affects T07)

WU-07 trigger 3 anticipates: substantive WUs done; gate over budget;
G2-RETRO about to dispatch. Fire the halt and the gate closes mid-
ceremony with no retrospective — making the next cycle's plan-next
harder. Don't fire it and the budget brake's "atomic with the gate
boundary" semantics break. I picked "do fire it" (the brake fires,
the gate halts to `awaiting_review` with no retrospective). The human
can decide to flip back to `open` and pay the remaining cost, or to
manually write the retrospective. This is uncomfortable but
consistent. If you'd rather guarantee the closing sequence always
completes, edit T07 AC 3 to skip the brake when the next WU's type is
in `{retrospective, lessons, docs, plan-next, close}`.

### Q5. Defaults table values — sonnet for `implementation`, opus for `plan-next`. Is that what we want? (affects T06)

This is the policy heart of T06. The table reflects Gate 1's
observed costs; the alternative is "opus for everything" (safer,
\$3.81 → ~\$8 per gate at Gate 1 sizes) or "haiku for closing-WUs"
(cheaper, untested on this loop). If your priors point a different
direction, edit T06 AC 1's table before arming; the constants need
to match policy intent, not just my reading of Gate 1.

---

## Summary

Four substantive WUs (T06 defaults / T07 budget / T08H retry-ladder
re-land / T08 telemetry) + standard closing sequence, total eight WUs
in Gate 2. T08H is the call to validate first — if you reject the
hygiene-WU shape, you must pick one of the alternatives in the
Headline section before arming. T07's halt placement and T08's
denominator choice are the two pieces of forward design most likely
to want a review tweak. Models hold sonnet for synthesis and opus for
forward design / control-flow editing, matching Gate 1's grain. The
T08H smoke check is the single most important post-T08H verification
to run by hand — if it fails, halt before T08 dispatches.
