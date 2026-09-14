---
id: FEAT-2026-0111/G1-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 6.00
auto_close_disabled: true
---

# Close the feature — bounded LEARNINGS on the dispatch path

**Objective.** Terminal close: fold retrospective, lessons and docs into one
session, and measure what this feature actually changed.

**Context.** FEAT-2026-0111/G1-CLOSE. Close obligations bind by reference
(`.specfuse/rules/close-discipline.md` §§1–5); required sections are
scaffolded at dispatch, so write their substance, not their headings. On a
terminal gate the **judge** writes the verdict from evidence, so this unit says
what to measure and never what verdict to reach.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries a `## Cost analysis` section reconciling the
  per-WU figures and the $28.00 plan against `events.jsonl`, with the variance
  explained. Note for the reconciliation: the driver-touching units were priced
  at $5–6 deliberately, correcting FEAT-2026-0106's $3.50 estimates that came
  in at $9.13 and $6.13. Whether that correction was enough is the question.
- The deferred-verification list names every criterion not verified in-loop
  with its reason and where it is actually checked, or the explicit
  nothing-deferred line.
- **The binding block's before and after word counts are stated**, with what
  was trimmed and what the distilled file cost — the feature's own claim,
  measured rather than asserted.
- **Whether this gate stayed on-plan is stated, and what that means for
  FEAT-2026-0106.** That feature's conditional reflection has never fired
  because its own gate went off-plan on cost; this is the first gate planned
  with corrected estimates, so it is the first real test of that mechanism.
  Say whether reflection was suppressed here and, if so, whether
  `PROGRESS.md` carried enough.
- `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` — `fire_terminal_flips` owns the
terminal flip on both the dispatched-close and auto-close paths.

**Verification.** Narrow tier for `close`, plus `specfuse lint --closing`.

**Escalation triggers.** Stop with `status: blocked` if the before/after word
counts cannot be recovered — a feature that built a word-budget lint and cannot
report the number it moved has found a defect in its own instrument.
