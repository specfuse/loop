---
id: FEAT-2026-0109/G1-PLAN
type: plan-next
status: done
attempts: 1
planned_cost_usd: 6.00
oracle_env: macos_local
produces:
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-02-REVIEW.md
  - .specfuse/features/FEAT-2026-0109-tiered-verification/GATE-02.md
  - .specfuse/features/FEAT-2026-0109-tiered-verification/PLAN.md
escalation_reason: deterministic_refusal_repeat
duration_seconds: 984.346
cost_usd: 7.413869
input_tokens: 146
output_tokens: 65957
re_arm_count: 2
re_arm_history:
  -
    timestamp: 2026-09-08T13:54:45+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 3.093962
    prior_duration_seconds: 450.221
    reason: "fix WU-91, plan-next never told to write the task graph"
  -
    timestamp: 2026-09-08T14:09:03+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 2.193218
    prior_duration_seconds: 378.256
    reason: "go with option 2, close the differing-sha gap"
cumulative_cost_usd: 2.193218
cumulative_duration_seconds: 378.256
cumulative_input_tokens: 34
cumulative_output_tokens: 27350
cumulative_attempts: 0
folded_through_re_arm: 2
model: opus
effort: high
gate_set: plannext
driver_version: 0.16.0
started_at: 2026-09-08T14:09:48.245501+00:00
---

# Draft gate 2 — the per-attempt tier — and its own oracle

**Objective.** Forward design: draft gate 2's work units and its
`feature_oracle`, and write the human review summary for gate 1.

**Context.** FEAT-2026-0109/G1-PLAN; read `PLAN.md`, `GATE-01.md`, and gate 1's
`RETROSPECTIVE.md`. Gate 2 is the per-attempt vs per-gate tier split: per
attempt, the unit's declared tests, tests touching changed files, lint, and the
feature oracle; once per gate before the close, the full suite with coverage,
bats, leak-scan and security.

**Gate 2 must declare its own `feature_oracle` (#3262).** A gate with no
substantive units carries no oracle requirement, which is why gate 2 has none
today — the moment you give it work units, the requirement lands and
`specfuse lint` will ERROR without one. Draft the oracle in the same pass as
the units, and state in the review summary **how gate 2's oracle advances
gate 1's**, per the `plan-next` obligation FEAT-2026-0101/T04 added. Nothing
can decide mechanically whether one shell command is a stronger proof than
another; that judgement is yours to write down.

**§ Operator decision — answered, proceed.** The previous attempt blocked
correctly: gate 1's retrospective records that attribution fired **zero** times,
so the failure path that makes narrowing safe is covered by T01's tests and by
no live run. The operator has answered that question and chosen to proceed
**with the gap closed** — gate 2 is drafted, and it carries one extra unit for
the differing-sha gap below. Do not re-litigate this; it is decided.

**The gap that extra unit must close.** Gate 1's `GATE-01.md` claims
"Attribution runs at most once per gate", but the implementation — the
tree/sha dedup in `gate_baseline_check` — actually guarantees *at most once per
tree state per gate*. Two units failing at **different** shas, separated by a
landed unit, would legitimately re-probe. The covering test
(`AttributionDedup.test_attribution_runs_at_most_once_per_gate`) exercises the
same-sha case only; the differing-sha case has no test anywhere.

This matters now because gate 2's per-attempt narrowing makes multi-unit failure
within one gate more likely — the exact condition under which the two readings
diverge. The unit you draft must **decide which side moves**: either the claim
is reworded to "once per tree state per gate", matching what the mechanism does
and what is arguably correct (a genuinely different tree deserves a fresh
measurement), or the mechanism is changed to hold the stronger bound. Whichever
you choose, the differing-sha case gets a test. Say which you chose and why in
`GATE-02-REVIEW.md` — the retrospective explicitly deferred this decision to
you, and picking silently would waste that deferral.

**The open design question gate 1 was sequenced to inform.** "Tests touching
changed files" needs a concrete rule — import graph, path convention, a
declared mapping, or the unit's own `produces:` list. Gate 1 makes the driver's
failure path explicit, which is the context that should decide it. Surface the
options and your recommendation in the review summary rather than settling it
silently in a WU body.

**Do not draft gate 3.** The installed-copy driver is deliberately alone in its
own gate — `[FEAT-2026-0019/G1]` records that a harness migration cannot be
decomposed into separately-gated units, and the last attempt cost $5.63 and 49
minutes of thrash. Gate 2's own `plan-next` drafts it, with the same atomicity
constraint restated there.

**Drafting a gate means editing `PLAN.md`'s task graph, not only writing files
— read this before starting.** Two earlier attempts wrote `GATE-02.md` and were
refused by the same deterministic guard, which is why this unit escalated
`deterministic_refusal_repeat`:

```
assert_next_gate_drafted_or_terminal: gate 2 has no drafted work_units in
PLAN.md and neither PLAN.md nor roadmap marks done
```

The guard reads **`PLAN.md`'s `gates:` graph**, where gate 2 currently has
`work_units: []`. Creating `WU-*.md` files and a `GATE-02.md` does not satisfy
it and never will. `PLAN.md` is in this unit's `produces:` for that reason:
insert one graph entry per drafted unit — `id`, `file`, `depends_on` — under
gate 2, matching the shape gate 1's entries already have, and leave gate 3's
entry untouched. Do this **before** reporting, and re-read the graph afterwards
to confirm the entries are actually there.

**Acceptance criteria.**

- **The guard's own precondition, checked directly:** `PLAN.md`'s gate 2 entry has a non-empty `work_units` list, one entry per drafted unit, each naming a `file` that exists on disk. This is what `assert_next_gate_drafted_or_terminal` reads; two attempts failed it.
- `GATE-02.md` carries a definition of done, substantive work units drafted at `status: draft`, and a non-empty `feature_oracle` — `grep -n "feature_oracle" GATE-02.md` returns it.
- Each drafted unit carries the five mandatory sections and a `planned_cost_usd`; `specfuse lint .specfuse/features/FEAT-2026-0109-tiered-verification` reports zero ERROR.
- `GATE-02-REVIEW.md` carries the decisions and their rationale, an explicit "if you check only three things, check these" list, a roadmap-anchor check against `PLAN.md`'s `roadmap_goal`, and open questions each mapped to the draft WU it affects.
- The review summary states how gate 2's `feature_oracle` advances gate 1's, and names the chosen rule for "tests touching changed files" with the alternatives considered.
- **Gate 2 includes one unit closing the differing-sha gap**, drafted like any other: it states which side moved (the `GATE-01.md` wording, or `gate_baseline_check`'s bound), and its acceptance requires a test covering two units failing at **different** shas within one gate — the case that has no test today. `GATE-02-REVIEW.md` records which side was chosen and why.
- The drafted units are left `draft` — arming is the human's act.

**Do not touch.** Source, tests, rules, templates; gate 1's WUs or its
`RETROSPECTIVE.md`; `GATE-03.md` and gate 3's entry in the task graph;
`.git/`, secrets. **`PLAN.md` is explicitly IN scope** for gate 2's graph
entries only — edit that one list and nothing else in the file.

**Verification.** The `plannext` gate set.

**Escalation triggers.** Emit `status: blocked` if the differing-sha decision
below cannot be made from gate 1's code and retrospective alone — if answering
"does the wording move or does the mechanism move" needs a behavioural change
outside `gate_baseline_check`, that is a design decision for an operator, not a
drafting judgement. Also block if drafting gate 2 would require editing gate 1's
completed units.

**Do NOT block again on "attribution never fired."** That trigger fired on the
previous attempt and has been answered — see § Operator decision above. The
condition still holds and is expected to; it is no longer a reason to withhold
drafting.
</content>
