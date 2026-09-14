---
id: FEAT-2026-0106/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
verdict: met
model: opus
effort: high
gate_set: plannext
driver_version: 0.19.0
started_at: 2026-09-14T01:44:51.329316+00:00
duration_seconds: 530.494
cost_usd: 3.361594
input_tokens: 482
output_tokens: 41118
---

# Close the feature — progress lines and conditional reflection

**Objective.** Terminal close: fold retrospective, lessons and docs
reconciliation into one session, and record whether the thing this feature
built is any good.

**Context.** FEAT-2026-0106/G1-CLOSE. Close obligations bind by reference
(`.specfuse/rules/close-discipline.md` §§1–5); required sections are
scaffolded at dispatch, so write their substance, not their headings. On a
terminal gate the **judge** writes the verdict from evidence, so this unit
says what to measure and never what verdict to reach.

This close is the first one to run under T03's rule, and if this gate stayed
on-plan it is the first close the feature suppresses reflection for. That is
the intended behaviour and the sharpest available test of it.

**Acceptance criteria.**

- `RETROSPECTIVE.md` carries a `## Cost analysis` section — the heading
  `assert_cost_analysis_section_when_met` checks after dispatch on a `met`
  verdict — reconciling both the per-WU figures and the $16.50 plan against
  what `events.jsonl` recorded, with the variance explained rather than noted.
- The deferred-verification list names every acceptance criterion not verified
  in-loop with its reason and where it is actually checked, or carries the
  explicit nothing-deferred line.
- **Whether reflection was suppressed for this gate is stated plainly**, with
  the off-plan signal's own verdict quoted. If it was suppressed, the close
  says whether `PROGRESS.md` carried enough for this session to do its job
  without it — the only first-hand evidence anyone will have on that question.
- The `summary` emission rate T01 recorded is carried forward against T02's
  outcome: how often a real agent filled the forward-looking field, and
  whether the optional-field bet paid.
- `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** `PLAN.md`'s `status` — `fire_terminal_flips` owns the
terminal flip to `done` on both the dispatched-close and auto-close paths, and
a manual flip is redundant.

**Verification.** Narrow tier for `close`, plus `specfuse lint --closing`.

**Escalation triggers.** Stop with `status: blocked` if the cost
reconciliation cannot be built because `events.jsonl` and the committed WU
frontmatter disagree — that disagreement is itself the finding (#3296 is the
precedent for taking it seriously rather than papering over it).
