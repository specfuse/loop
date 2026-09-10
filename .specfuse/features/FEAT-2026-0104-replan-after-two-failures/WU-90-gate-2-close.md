---
id: FEAT-2026-0104/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
---

# Close the feature — re-plan replaces the third identical attempt

**Objective.** Terminal close for FEAT-2026-0104: fold retrospective, lessons
and docs into one session and record what the feature did and did not prove.

**Context.** FEAT-2026-0104/G2-CLOSE. **Placeholder, drafted at feature
planning time so the linter reads gate 1 as non-terminal.** `G1-PLAN` rewrites
this unit when it drafts gate 2 — it sets the real `depends_on` in `PLAN.md`
and sharpens the criteria below against what gate 2 actually builds. The
criteria here are the floor every terminal close owes, not this gate's final
list.

Close obligations bind by reference (`.specfuse/rules/close-discipline.md`
§§1–5). On a terminal gate the **judge** writes the verdict from evidence, so
this unit says what to measure and never what verdict to reach.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries a `## Cost analysis` section — `assert_cost_analysis_section_when_met` checks that heading after dispatch on a `met` verdict, so a missing one costs a full re-attempt.
- Under that heading, cost is reconciled across both gates against `PLAN.md`'s
  `planned_cost_usd: 30.00` and what `events.jsonl` recorded, with the
  variance explained per gate.
- The deferred-verification list names every acceptance criterion not verified
  in-loop with its reason and where it is actually checked, or carries the
  explicit nothing-deferred line.
- The feature's own claim is measured, not asserted: how many attempts across
  both gates were re-plans, and whether the units that re-planned then passed.
- The metric that motivated the feature is re-read, not assumed — human waits
  per feature on drivers running this code, against the 2.09 baseline recorded
  in `PLAN.md`. One feature is not a trend and the close should say so rather
  than claim a win the sample cannot support.
- `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` — `fire_terminal_flips` owns the
terminal flip to `done`, on both the dispatched-close and auto-close paths. A
manual flip is redundant.

**Verification.** Narrow tier for `close`, plus `specfuse lint --closing`.

**Escalation triggers.** Stop with `status: blocked` if the re-plan count
cannot be recovered from the event record — a feature that built an event
specifically so this could be measured, and then cannot measure it, has found
a real defect in its own emit path.
