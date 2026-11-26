---
id: FEAT-LOOP-2026-0251/G1-CLOSE
type: close
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 5.00
verdict: met
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
re_arm_count: 7
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
  -
    timestamp: 2026-11-26T16:08:13+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.733084
    prior_duration_seconds: 379.569
    reason: "Trying to fix the last issue"
  -
    timestamp: 2026-11-26T16:44:22+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.435437
    prior_duration_seconds: 478.949
    reason: "Fixed the deleted-file edge case, re-close it"
  -
    timestamp: 2026-11-26T17:35:20+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.347591
    prior_duration_seconds: 616.642
    reason: "Fixed renames, modes and non-ASCII names, re-close it"
  -
    timestamp: 2026-11-26T21:34:17+00:00
    prior_status: done
    prior_attempts: 1
    prior_cost_usd: 1.657563
    prior_duration_seconds: 747.309
    reason: "Amend both as recommended, fixed bookkeeping paths, re-close it"
cumulative_cost_usd: 9.355627
cumulative_duration_seconds: 2773.326
cumulative_input_tokens: 344
cumulative_output_tokens: 223290
cumulative_attempts: 6
cost_usd: 0.975064
duration_seconds: 415.272
input_tokens: 42
output_tokens: 25318
folded_through_re_arm: 7
gate_set: plannext
driver_version: 0.33.2
started_at: 2026-11-26T21:46:35.862369+00:00
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

**Third re-close note (2026-11-26).** The third close's judge recorded `not_met` on #3612: with
the tree kept, a later attempt's retry note listed the earlier attempt's kept edits as its own
(clause 4). Fixed on the branch (`snapshot_dirty_tree`, `attempt_own_paths` in `loop.py`; tests
in `TestTreeAndNote`; see `PLAN.md` Notes). Update the closing files in place as before, and say
in `FOLLOW-UPS.md` whether #3612's re-run condition now holds.

**Fourth re-close note (2026-11-26).** The fourth close recorded `not_met` on #3613: a kept file
the attempt deleted or reverted was missing from its retry note. Fixed on the branch
(`attempt_own_paths` in `loop.py`; tests in `TestTreeAndNote`; see `PLAN.md` Notes). Update the
closing files in place as before, and say in `FOLLOW-UPS.md` whether #3613's re-run condition
now holds.

**Fifth re-close note (2026-11-26).** The fifth close recorded `not_met` on #3614: the retry
note's path list missed renames, mode-only changes and non-ASCII names. Fixed on the branch by
comparing each path's state at the start and end of the attempt (`snapshot_dirty_tree`,
`attempt_own_paths` in `loop.py`; tests in `TestTreeAndNote`; see `PLAN.md` Notes). The
`git add -N` crash on a new non-ASCII file predates this feature and is outside clause 4. Update
the closing files in place as before, and say in `FOLLOW-UPS.md` whether #3614's re-run
condition now holds.

**Sixth re-close note (2026-11-26).** The sixth close recorded `not_met` on #3617, #3618 and
#3619. #3618 (the retry note dropped an agent's own `docs/events.jsonl` or `docs/PROGRESS.md`
because it matched driver bookkeeping by base name) is fixed on the branch: it now matches the
unit file, `events.jsonl` and `PROGRESS.md` by full path in the unit's feature folder (tests in
`TestTreeAndNote`; see `PLAN.md` Notes). For #3617 and #3619 the operator amended `GATE-01.md`
clause 5: the warning stays silent when the body names the path's parent directory (narrowed
under `PLAN.md` decision 7), and T04's measurement is recorded there with its evidence. Update
the closing files in place as before, and say in `FOLLOW-UPS.md` whether each of #3617, #3618
and #3619's re-run conditions now holds.
