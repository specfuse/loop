---
id: FEAT-LOOP-2026-0251/G1-CLOSE
type: close
status: done
verdict: not_met
attempts: 1
oracle_env: macos_local
planned_cost_usd: 5.00
auto_close_disabled: true
model: sonnet
effort: high
judge_edit_acknowledged:
  paths:
    - .specfuse/verification.yml.example
    - produces_driver_helper
    - specfuse/loop/data/verification.yml.example
    - specfuse/loop/lint_plan.py
    - specfuse/loop/loop.py
  reason: "Review fixes tested, full suite green, accept the generator risk"
re_arm_count: 3
re_arm_history:
  -
    timestamp: 2026-11-26T13:30:05+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 0.0
    prior_duration_seconds: 0.0
    reason: "Review fixes tested, full suite green, accept the generator risk"
  -
    timestamp: 2026-11-26T13:50:58+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.69295
    prior_duration_seconds: 291.43
    reason: "A for both, go ahead"
  -
    timestamp: 2026-11-26T15:22:22+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.489002
    prior_duration_seconds: 259.427
    reason: "1, go ahead"
cumulative_cost_usd: 3.181952
cumulative_duration_seconds: 550.857
cumulative_input_tokens: 118
cumulative_output_tokens: 71498
cumulative_attempts: 2
cost_usd: 1.161317
duration_seconds: 379.569
input_tokens: 40
output_tokens: 34180
folded_through_re_arm: 3
gate_set: plannext
driver_version: 0.33.2
started_at: 2026-11-26T15:32:04.468694+00:00
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: the three diff-only deliverable refusals run before
verification (with an opt-out), their retry note lists the changed paths, and `specfuse lint`
warns on a `produces:` path its unit never mentions.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was proven
   and by which test, and that no `unittest.skip` survives in
   `tests/test_fail_fast_deliverables.py`. It lists every pre-existing test that was changed
   (clause 6, as widened for #3609), with why.
2. Each consumer-visible change (the new order, `defaults.fail_fast_deliverables`, the retry
   note's path list, the lint WARN) is written with
   `python3 -m specfuse.loop.changelog_fragments add`, tracing to `FEAT-LOOP-2026-0251`.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and `events.jsonl`, and
   reports T04's measured warning rate.
4. "What the loop did NOT verify" names, at minimum: a real project whose gates write a declared
   deliverable (the opt-out is tested only with stubs), and real refused attempts on the new
   build (every attempt in this feature ran on a build pinned before the change).
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` and `scripts/`. Permitted closing surfaces:
`RETROSPECTIVE.md`, `LEARNINGS-pending.md`, `changelog.d/`, `.specfuse/roadmap.md`.

**Verification.** `specfuse lint --closing`, plus the gate set in `.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or an early refusal whose outcome or failure class
differs from the late one for the same input, other than the precedence `GATE-01.md` states
under "Precedence when two refusals apply" (a deliverable refusal outranks every check that
runs after the agent session, #3608 and #3610): record `not_met` with a follow-up.

**Re-close note (2026-11-26).** The first close recorded `not_met` on #3608 and #3609; the
operator chose to amend the definition of done for both (see `GATE-01.md` clause 6 and
"Precedence when two refusals apply"). That close already wrote `RETROSPECTIVE.md`,
`FOLLOW-UPS.md`, `LEARNINGS-pending.md` and changelog fragments: update them in place, do not
duplicate fragments, and say in `FOLLOW-UPS.md` whether each entry's re-run condition now holds.

**Second re-close note (2026-11-26).** The second close recorded `not_met` on #3610 (cases D to
G: the deliverable refusal also outranks the smoke-import, blocked-verdict and
closing-deliverable checks). The operator chose to state one general precedence rule; it is in
`GATE-01.md`, in the escalation trigger above and in `docs/methodology.md`, together with the
kept-tree side effect. Update `RETROSPECTIVE.md`, `FOLLOW-UPS.md` and the other closing files in
place as before, and say in `FOLLOW-UPS.md` whether #3610's re-run condition now holds.
