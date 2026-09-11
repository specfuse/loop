---
id: FEAT-2026-0104/G2-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: not_met
model: opus
effort: high
gate_set: plannext
driver_version: 0.19.0
started_at: 2026-09-11T03:12:25.674221+00:00
duration_seconds: 863.799
cost_usd: 7.952012
input_tokens: 132
output_tokens: 63788
---

# Close the feature — re-plan replaces the third identical attempt

**Objective.** Terminal close for FEAT-2026-0104: fold retrospective, lessons
and docs into one session and record what the feature did and did not prove.

**Context.** FEAT-2026-0104/G2-CLOSE. Sharpened by `G1-PLAN` against what
gate 2 actually builds. Close obligations bind by reference
(`.specfuse/rules/close-discipline.md` §§1–5). On a terminal gate the
**judge** writes the verdict from evidence, so this unit says what to measure
and never what verdict to reach. Two things gate 1's retrospective asks this
close to carry forward: the feature is proven **runnable**, not **useful**,
and the reverted first run's spend is unrecoverable from `events.jsonl`, so
gate 1's recorded $8.76 understates it by roughly half.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries a `## Cost analysis` section —
  `assert_cost_analysis_section_when_met` checks that heading after dispatch
  on a `met` verdict, so a missing one costs a full re-attempt.
- Under that heading, cost is reconciled across both gates against `PLAN.md`'s
  `planned_cost_usd` **as revised by `G1-PLAN` to 39.50**, with the variance
  explained per gate and gate 1's discarded run named rather than netted out.
- The feature's own claim is measured, not asserted: how many attempts across
  both gates were re-plans, and whether the units that re-planned then
  passed. Gate 1's answer was zero and n/a; if gate 2's is the same, say so
  and say what that leaves unproven.
- The execute-versus-recommend decision recorded in `GATE-02.md` is re-read
  against what gate 2 built, and the close states whether any gate-2 evidence
  would change it — the decision was made on gate-1 evidence and is due a
  second look, not a re-affirmation by default.
- The deferred-verification list names every acceptance criterion not
  verified in-loop with its reason and where it is actually checked, or
  carries the explicit nothing-deferred line. Gate 1's four deferred items
  are carried forward or discharged, not silently dropped.
- The metric that motivated the feature is re-read, not assumed — human waits
  per feature on drivers running this code, against the 2.09 baseline
  recorded in `PLAN.md`. One feature is not a trend and the close should say
  so rather than claim a win the sample cannot support.
- `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` — `fire_terminal_flips` owns the
terminal flip to `done`, on both the dispatched-close and auto-close paths. A
manual flip is redundant. `GATE-01.md` and gate 1's WU files: the record
stands as it was written.

**Verification.** Narrow tier for `close`, plus `specfuse lint --closing`.

**Escalation triggers.** Stop with `status: blocked` if the re-plan count
cannot be recovered from the event record — a feature that built an event
specifically so this could be measured, and then cannot measure it, has found
a real defect in its own emit path.
