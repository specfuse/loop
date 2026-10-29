---
id: FEAT-LOOP-2026-0204/G1-CLOSE
type: close
status: done
attempts: 1
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
model: sonnet
effort: high
gate_set: plannext
verdict: met
driver_version: 0.28.2
started_at: 2026-10-17T16:43:33.017235+00:00
duration_seconds: 153.218
cost_usd: 1.284495
input_tokens: 76
output_tokens: 20812
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: a finding's lifecycle is correct (T01–T04) and a
finding carries what a diagnosis needs (T05–T08). This unit folds the retrospective,
lessons, documentation and the terminal verdict into one session.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was
   proven and by which test, and states that `grep -n 'unittest.skip'` over both
   oracle modules reports nothing — a surviving skip is a hollow oracle and makes the
   verdict `not_met`. For each check type it lists the body sections a rendered
   fixture finding carries against `PLAN.md`'s "Diagnostic context" section.
2. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and
   `events.jsonl`, not estimated.
3. The deferred-verification list names the live run on the first consumer (`PLAN.md`'s
   Post-merge checklist) and anything else not verified in-loop, each with its reason
   and where it actually gets checked.
4. The documentation pass updates `docs/concepts/monitoring-to-fix.md` (or
   `docs/concepts/monitoring-runners.md` if it does not exist at this tree) so it
   describes reopen-not-refile with the "reopens, never closes" boundary, `dlq`
   acknowledgement, heartbeat grace, and what a finding contains per check type;
   shipped copies under `specfuse/loop/data/docs/` stay byte-identical
   (`tests.test_scaffold_data_in_sync`), and `CHANGELOG.md`'s Unreleased section
   carries the user-visible changes.
5. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` other than the docs in criterion 4.
Other features.

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** If any check type's rendered finding lacks a section the plan
names and no unit records why, record `not_met` with a follow-up rather than closing
green.
