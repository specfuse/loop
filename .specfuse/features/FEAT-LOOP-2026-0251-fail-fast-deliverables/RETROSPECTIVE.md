# Retrospective — FEAT-LOOP-2026-0251, refuse a missing deliverable before verification

## Gate 1

## Verdict

`not_met` (advisory; the judge concludes). The early refusals work and every oracle is green.
Two things do not hold as written:

1. For one input, the early refusal records a different outcome and failure class than the
   late order records. This is the close unit's escalation trigger.
2. Two edits to pre-existing tests are not assertions on the order of verify and guard, so
   clause 6 does not hold literally.

Both may be acceptable as designed. That is an operator decision, and `FOLLOW-UPS.md` states it.

## Measurements

All commands ran fresh in this session on the working tree. Runs that drive `loop.run()` used
`HOME` under `$TMPDIR`, because the sandbox blocks writes to the real session directory.

### feature_oracle: PASS

`python3 -m unittest tests.test_fail_fast_deliverables -v -b`: exit 0, `Ran 29 tests`, `OK`,
no skips. `grep -c "unittest.skip" tests/test_fail_fast_deliverables.py` prints `0`, and a
search for `skipIf`, `skipUnless`, `skipTest` and `@skip` in that file finds nothing.

### Other oracles

| Check | Result |
|---|---|
| `python3 -m unittest tests.test_dispatch_skeleton tests.test_gate_timings -b` | 25 tests, OK |
| `python3 -m unittest tests.test_lint_plan -b` (named by T04) | **error: no such module** (`ModuleNotFoundError`) |
| the six `tests/test_lint_plan*.py` modules that do exist | 46 tests, OK |
| the ten changed pre-existing test modules | 68 tests, OK |
| `.specfuse/scripts/lint_plan.py` over every feature folder with a `PLAN.md` | 97 linted, 0 non-zero exits |
| `diff` of `verification.yml.example` against its packaged copy | empty |
| `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` | empty |
| `python3 -m specfuse.loop.changelog_fragments check` | exit 0 |

The full suite and coverage were not re-run by this session. The driver's broad run at
2026-11-26T13:36:49Z recorded `ok: true`; its tests log shows `Ran 5143 tests`,
`OK (skipped=4)`, and its coverage log shows 92% total.

### Mutation control

With `resolve_fail_fast_deliverables` forced to return `False`, 12 of the 29 oracle tests
fail, with no errors. They are in `TestProducesNotInDiffEarly` (2), `TestPresenceEarly` (3),
`TestOptOut` (4, including the resolver's own default test), `TestTreeAndNote` (2) and
`TestEarlyRefusalRecovery` (1). So these classes observe the new order.
`TestArmTimeWarning` calls `check_produces_mentioned`, which does not exist on `main`.
No unit's "fails on HEAD" claim was re-run against a pre-feature tree.

### Early against late, same input

A throwaway probe drove `loop.run()` over the oracle's fixture and read the first
`attempt_outcome` for T01. The unit declares `src/rule.py`; the attempt writes only
`docs/notes.md`.

| Case | `fail_fast` true | `fail_fast` false | Same |
|---|---|---|---|
| A: RESULT lists `src/rule.py` in `files_changed`, gates green | `produces_not_in_diff` / `produces_not_in_diff`, 0 verify calls | `files_changed_mismatch` / `files_changed_mismatch`, 1 call | **no** |
| B: plain RESULT, gates red | `produces_not_in_diff`, 0 calls | `failed` / `other`, 1 call | no (see below) |
| C: control, plain RESULT, gates green | `produces_not_in_diff`, 0 calls | `produces_not_in_diff`, 1 call | yes |

B follows from the feature's purpose: a gate that never runs cannot report a failure.
A does not follow from it. `files_changed_mismatch` needs no gate result, and `PLAN.md`
decision 4 says that guard stays where it is. The early produces check now pre-empts it.
The pre-existing test `test_untouched_deliverable_still_refuses` shows the same change.

By reading the code only, not measured: the early check also runs before the smoke-import
guard, the closing-deliverable guards and the produced-verdict contradiction check. An
attempt that would trip one of those and also misses a deliverable is now reported as the
deliverable refusal.

carried forward: 0 criteria, re-measured: 13

## Definition of done, clause by clause

| Clause | Proven | By |
|---|---|---|
| 1. `produces_not_in_diff` early | Refused with 0 `verify_fn` calls, `verify_seconds` 0, no attempt-phase `gate_result`; a changed path verifies once and passes; a justified path still verifies; class, signature and summary equal the late site's | `TestProducesNotInDiffEarly` (5 tests). Case A above is an input where the late order never reaches that late site |
| 2. Presence early | Absent, empty and bookkeeping-only diffs are refused with 0 calls | `TestPresenceEarly` |
| 3. Opt-out | With the key `false`, each of the three cases verifies once; outcome, class, signature and summary equal the default's | `TestOptOut`, on plain-RESULT, green-gate inputs only |
| 4. Tree and note | Note says verification did not run and lists changed paths or says none; cap of 20 plus a count; tree kept or reset | `TestTreeAndNote`. The kept/reset assertions use `produces_not_in_diff` only; no test asserts tree handling for an early presence refusal |
| 5. Arm-time WARN | Warns on an unmentioned path; silent on full path, file name or parent directory, and on `done` / `abandoned`; `lint()` calls it | `TestArmTimeWarning` |
| 6. Nothing else changes | **Not literally.** See the list below | diff of `tests/` against a snapshot of public `main`, fetched this session |

Three review fixes made before this close, outside any work unit, are covered by
`TestEarlyRefusalRecovery` (re-plan still fires; uncommitted tracked edits count as a moved
tree; an untouched tree still halts) and `TestEarlyRetainedNoteWording`.

## Pre-existing tests changed

The comparison is against `main` as fetched during this close, not against the recorded
merge base, because this session runs no git command. Besides the new oracle file, ten
test modules differ.

Changed because of the order of verify and guard:

| Test module | Change | Why |
|---|---|---|
| `test_files_changed_auto_repair` | `test_untouched_deliverable_still_refuses` now expects `produces_not_in_diff`, not `files_changed_mismatch` | The early check pre-empts the post-verify guard. This changes the expected **outcome**, not only the order (case A) |
| `test_guard_repair_e2e` | Patches `early_produces_refusal` to return `None` in one test | The absent `src/extra.py` would be refused early, so the guard under test would never run. The test now exercises the late order only |
| `test_arm_wiring` | Two dispatch stubs wrapped in `with_deliverable` | The stubs wrote nothing and relied on `verify` failing first |
| `test_loop_files_changed_guard` | One stub wrapped in `with_deliverable` | Same: it must get past the presence refusal to reach `verify` |
| `test_replan_end_to_end` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_event_emission` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_note_collision` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_trigger` | One stub writes `deliverable.txt`; one comment rewritten | Attempts must reach `verify`; the comment's claim that the re-plan trigger is never consulted became false |

Not an assertion on order:

| Test module | Change | Why |
|---|---|---|
| `test_deterministic_refusal_repeat` | The source-text anchor moved from `"deliverable_missing",` to `if not deliv_ok:` | The emit call moved into the shared `refuse_deliverable_missing` helper. The two assertions are unchanged. They cover the late branch only |
| `test_produces_shape` | Two negative tests filter findings on `assert_declared_deliverables`, not `directory` | The new WARN text contains "directory". The shape check's ERROR still carries the new marker, so the filter can still catch it |

## What happened

T01 to T04 each passed on the first attempt. The gate's first broad run
(2026-11-25T23:44Z) failed: `tests` with 5125 tests and 2 failures, both in
`test_produces_shape`, and `coverage` with `no_gate_marker`. The T04 WARN text caused the
two test failures. No unit's narrow tier selected that module. A later broad run was clean.
The terminal judge-editing stop then fired, as `GATE-01.md` expected. An independent review
found three behaviour changes, fixed test-first on the branch, and the operator
acknowledged the judge edits and re-armed this unit.

T04 passed although its Verification section names `tests.test_lint_plan`, which does not
exist.

## Cost analysis

Unit costs are from the `task_completed` events in `events.jsonl`.

| Unit | Planned USD | Actual USD | Actual / planned | Attempts |
|---|---|---|---|---|
| T01 | 2.00 | 0.88 | 44% | 1 |
| T02 | 1.50 | 0.77 | 51% | 1 |
| T03 | 1.00 | 0.55 | 55% | 1 |
| T04 | 1.50 | 0.47 | 32% | 1 |
| Substantive total | 6.00 | 2.67 | 45% | 4 |
| G1-CLOSE | 5.00 | not yet recorded | — | in progress |

The plan total is 11.00 and the gate budget 14.00. The close's own cost and the judge's are
written after this session. The earlier `blocked_human` stop of this unit recorded 0.00.
The review and its fixes happened outside the loop, so `events.jsonl` has no cost for them.

**T04's warning rate.** Re-measured this session over `done` units with `produces:`: the
shipped rule (path, file name or parent directory) would fire on 35 of 402, **8.7%**, under
the 10% limit. Path or file name alone would fire on 81 of 402, 20.1%. T04 recorded 81 and
35 of 401 in the check's docstring; the population has since grown by one. T04's progress
note does not carry the count that its criterion 3 asked for in the RESULT notes, and this
session did not see that RESULT. The parent-directory match is a plain substring test, so a
short directory such as `tests` is satisfied by almost any body. The WARN is weak for such
paths.

## Consumer-visible contract changes

Pending human acknowledgment. Each has a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0251`.

1. **Changed:** the three deliverable refusals run before verification. An attempt that
   would also have failed a gate or `files_changed_mismatch` is reported as the deliverable
   refusal.
2. **Added:** `defaults.fail_fast_deliverables`, default `true`.
3. **Changed:** the retry note for the three refusals lists the changed paths, at most 20
   plus a count.
4. **Added:** a `specfuse lint` WARN for a `produces:` path the unit's body never mentions.

## What the loop did NOT verify

- **A real project whose gates write a declared deliverable.** The opt-out is tested only
  with stubs. With the default, such a unit is refused early on every attempt.
- **Real refused attempts on the new build.** T01 to T04 ran on a build pinned before the
  change (`bd7e508`). `events.jsonl` shows later pins (`cddc418`, `eb30755`), and this
  close was dispatched after the last one, so "every attempt ran on the old build" is not
  established for the close. No event in this feature shows a real early refusal, so no
  real saving in gate time is measured.
- Tree handling for early `deliverable_missing` and `no_deliverable_files` refusals.
- The precedence over the smoke-import, closing-deliverable and contradiction checks.
- Whether the pending-diff computation matches the squash diff for renames, submodules or
  ignored files. Only the oracle's simple cases were run.
- `specfuse lint` as the installed command. The pipx build differs from this tree, so the
  repository scripts were used.
