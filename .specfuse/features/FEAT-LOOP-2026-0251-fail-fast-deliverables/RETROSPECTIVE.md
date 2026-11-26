# Retrospective — FEAT-LOOP-2026-0251, refuse a missing deliverable before verification

## Gate 1

## Verdict

`not_met` (advisory; the judge concludes). This is the second close of the gate. The two
`not_met` findings of the first close (#3608, #3609) are settled by the operator's amendment
to the definition of done. The close unit's escalation trigger still fires on inputs the
amendment does not name: four probed inputs get a different early and late refusal outcome,
and none of them involves `files_changed_mismatch`. `FOLLOW-UPS.md` states the decision.

## Measurements

All commands ran fresh in this session on the working tree. Runs that drive `loop.run()` used
`HOME` under `$TMPDIR`, because the sandbox blocks writes to the real session directory.

### feature_oracle: PASS

`python3 -m unittest tests.test_fail_fast_deliverables -v -b`: exit 0, `Ran 30 tests`, `OK`,
no skips. `grep -c "unittest.skip" tests/test_fail_fast_deliverables.py` prints `0`. A search
of that file for `unittest.skip`, `skipIf`, `skipUnless`, `skipTest` and `@skip` finds nothing.

### Other oracles

| Check | Result |
|---|---|
| `python3 -m unittest tests.test_dispatch_skeleton tests.test_gate_timings -b` | exit 0, 25 tests |
| `python3 -m unittest tests.test_lint_plan -b` (named by T04) | **error: no such module** |
| the six `tests/test_lint_plan*.py` modules that do exist | exit 0, 46 tests |
| the ten changed pre-existing test modules | exit 0, 68 tests |
| `.specfuse/scripts/lint_plan.py` over every feature folder with a `PLAN.md` | 97 linted, 0 non-zero exits |
| `diff` of `verification.yml.example` against its packaged copy | exit 0, empty |
| `diff docs/methodology.md specfuse/loop/data/docs/methodology.md` | exit 0, empty |
| `python3 -m specfuse.loop.changelog_fragments check` | exit 0 |

This session did not run the full suite or coverage. The driver's broad run recorded at
2026-11-26T13:59:19Z has `ok: true` and no failing gate. The newest tests log in
`work/gate-logs/` (stamp `20261126T135837`) shows `Ran 5144 tests`, `OK (skipped=4)`. The
coverage log of the same run shows 92% total.

### Mutation control

With `resolve_fail_fast_deliverables` forced to return `False`, 13 of the 30 oracle tests
fail, with no errors: `TestOptOut` (4, including the resolver's own default test),
`TestPresenceEarly` (3), `TestProducesNotInDiffEarly` (3), `TestTreeAndNote` (2) and
`TestEarlyRefusalRecovery` (1). So these classes observe the new order.
`TestArmTimeWarning` was not part of this control. No unit's "fails on HEAD" claim was
re-run against a pre-feature tree.

### Early against late, same input

A throwaway probe drove `loop.run()` over the oracle's fixture and read the first
`attempt_outcome` for T01, once with `fail_fast_deliverables` `true` and once `false`.
Verification is a stub. The unit declares `src/rule.py`. Unless the row says otherwise, the
attempt writes only `docs/notes.md`, the RESULT is plain and the stub passes. Each cell is
outcome / failure class. Every `true` run had `verify_seconds: 0`.

| Case | `true` | `false` | Same | Named precedence |
|---|---|---|---|---|
| A: RESULT claims `src/rule.py` in `files_changed` | `produces_not_in_diff` / `produces_not_in_diff` | `files_changed_mismatch` / `files_changed_mismatch` | no | yes (#3608) |
| B: the verify stub fails | `produces_not_in_diff` / `produces_not_in_diff` | `failed` / `other` | no | no |
| C: control | `produces_not_in_diff` / `produces_not_in_diff` | same | yes | — |
| D: unit body has a failing smoke-import line | `produces_not_in_diff` / `produces_not_in_diff` | `smoke_import_failed` / `smoke_import_failed` | **no** | **no** |
| E: also declares `docs/report.md`; attempt writes it with a `BLOCKED` verdict heading | `produces_not_in_diff` / `produces_not_in_diff` | `failed` / `guard_refusal` | **no** | **no** |
| F: the same unit typed `close` | `produces_not_in_diff` / `produces_not_in_diff` | `closing_deliverable_missing` / `guard_refusal` | **no** | **no** |
| G: attempt empties `src/rule.py`; failing smoke-import line | `deliverable_missing` / `guard_refusal` | `smoke_import_failed` / `smoke_import_failed` | **no** | **no** |

Positive controls with `fail_fast` `true` and every declared path changed: the D unit gets
`smoke_import_failed`, and the E unit gets `failed` / `guard_refusal`. So the second check
in D and E fires on its own. F has no separate control; its `false` run shows the closing
guard firing. F needs a `close` unit that declares `produces:`.

A, D, E, F and G are each refused under both orders. Only the reported refusal differs.
B is not a second refusal guard: a gate that never runs cannot report a failure, which is
what the feature is for. D to G each trip two refusals. `GATE-01.md` limits clause 3 to
inputs that trip one, so clause 3 is not contradicted. The same file names a precedence only
over `files_changed_mismatch`, and the close unit's trigger exempts only that one.

Read in `loop.py`, not measured: the late smoke-import and closing-deliverable refusals call
`reset_preserving_events` without consulting `retain_on_guard_refusal`. The early refusal
follows that key, which defaults to keeping the tree. So for D, F and G the tree handling
should differ too.

### Per-criterion results

All 13 criteria were re-measured. `GATE-01-CRITERIA.md` is left as the driver seeded it,
because it is not one of this unit's permitted closing surfaces.

| Criterion | Result | Evidence |
|---|---|---|
| T01#1 | passes now | `TestProducesNotInDiffEarly`, in the oracle run; "fails on HEAD" not re-run |
| T01#2 | passes | `test_early_record_equals_late_record` (plain RESULT, passing stub) |
| T01#3 | passes | 25 tests, exit 0 |
| T02#1 | passes now | `TestPresenceEarly`; "fails on HEAD" not re-run |
| T02#2 | passes now | `TestOptOut`; "fails on HEAD" not re-run |
| T02#3 | passes | empty diff |
| T03#1 | passes now | `TestTreeAndNote`; "fails on HEAD" not re-run |
| T03#2 | passes | `test_list_is_capped_at_twenty` |
| T04#1 | passes now | `TestArmTimeWarning`; "fails on HEAD" not re-run |
| T04#2 | passes with the repository script | 97 folders, 0 non-zero exits; the installed `specfuse` command was not used |
| T04#3 | not observed | this session did not see T04's RESULT; the count is re-measured below |
| T04#4 | passes | empty diff |
| T04#5 | passes | prints `0` |

carried forward: 0 criteria, re-measured: 13

## Definition of done, clause by clause

| Clause | Proven | By |
|---|---|---|
| 1. `produces_not_in_diff` early | Refused with 0 `verify_fn` calls, `verify_seconds` 0, no attempt-phase `gate_result`; a changed path verifies once and passes; a justified path still verifies; class, signature and summary equal the late site's | `TestProducesNotInDiffEarly` (6 tests) |
| 2. Presence early | Absent, empty and bookkeeping-only diffs are refused with 0 calls | `TestPresenceEarly` (3) |
| 3. Opt-out | With the key `false`, each of the three cases verifies once; outcome, class, signature and summary equal the default's, for inputs that trip one refusal | `TestOptOut` (4), on plain-RESULT, passing-stub inputs |
| 4. Tree and note | Note says verification did not run and lists changed paths or says none; cap of 20 plus a count; tree kept or reset | `TestTreeAndNote` (6). The kept/reset assertions use `produces_not_in_diff` only; no test asserts tree handling for an early presence refusal |
| 5. Arm-time WARN | Warns on an unmentioned path; silent on full path, file name or parent directory, and on `done` / `abandoned`; `lint()` calls it | `TestArmTimeWarning` (6) |
| 6. Nothing else changes | Holds as widened for #3609. See the list below | `diff -ru` of `tests/` against the recorded base; the ten modules pass |
| Precedence over `files_changed_mismatch` | Both sides asserted | `test_deliverable_refusal_outranks_files_changed_mismatch`; probe case A |

Three review fixes made before the first close, outside any work unit, are covered by
`TestEarlyRefusalRecovery` (3: re-plan still fires; uncommitted tracked edits count as a
moved tree; an untouched tree still halts) and `TestEarlyRetainedNoteWording` (2).

## Pre-existing tests changed

Compared against the public tarball of `a89373d119f8e2d8003a8956dbd4bd27dde8057f`, the
merge base recorded on the first close's `judged` event, and against public `main` as
fetched in this session. No git command was run. Against `main`, besides the new oracle
file, exactly ten test modules differ. Against the older base the same ten differ; three
further test files absent from that base are identical to `main`. The `.claude` directory
under `tests/` was left out of the comparison.

Changed because of the order of verify and guard:

| Test module | Change | Why |
|---|---|---|
| `test_files_changed_auto_repair` | `test_untouched_deliverable_still_refuses` now expects `produces_not_in_diff`, not `files_changed_mismatch`, and reads `payload["remaining"]` | The early check pre-empts the post-verify guard. The expected outcome changed; this is the stated precedence (#3608) |
| `test_guard_repair_e2e` | Patches `early_produces_refusal` to return `None` in one test | The absent `src/extra.py` would be refused early, so the guard under test would never run. The test now exercises the late order only |
| `test_arm_wiring` | Two dispatch stubs wrapped in `with_deliverable` | The stubs wrote nothing and relied on `verify` failing first |
| `test_loop_files_changed_guard` | One stub wrapped in `with_deliverable` | Same: it must get past the presence refusal to reach `verify` |
| `test_replan_end_to_end` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_event_emission` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_note_collision` | Stub wrapped in `with_deliverable` | Same |
| `test_replan_trigger` | One stub writes `deliverable.txt`; one comment rewritten | Attempts must reach `verify`; the comment's claim that the re-plan trigger is never consulted became false |

Forced by the shared helper or the new lint wording (the widened clause 6):

| Test module | Change | Why |
|---|---|---|
| `test_deterministic_refusal_repeat` | The source-text anchor moved from `"deliverable_missing",` to `if not deliv_ok:` | The emit call moved into the shared `refuse_deliverable_missing` helper. Both assertions are unchanged. They cover the late branch only |
| `test_produces_shape` | Two negative tests filter findings on `assert_declared_deliverables`, not `directory` | The new WARN text contains "directory". `lint_plan.py` puts the new marker in the shape ERROR, and the two positive tests are unchanged, so the negative tests still catch a shape ERROR on a file or glob |

## What happened

T01 to T04 each passed on the first attempt. The gate's first broad run
(2026-11-25T23:44Z) failed: `tests` with 5125 tests and 2 failures, both in
`test_produces_shape`, and `coverage` with `no_gate_marker`. The T04 WARN text caused the
two test failures. No unit's narrow tier selected that module. A later broad run was clean.
The terminal judge-editing stop then fired, as `GATE-01.md` expected. An independent review
found three behaviour changes, fixed test-first on the branch, and the operator
acknowledged the judge edits and re-armed this unit.

The first close (2026-11-26T13:42Z) and the judge both recorded `not_met`, and the driver
filed #3608 and #3609. The operator amended `GATE-01.md` for both (precedence over
`files_changed_mismatch`; a wider clause 6), added a test for the precedence, and re-armed
this unit. The first close had noted the other overtaken checks from reading the code but
did not probe them or put them in a follow-up entry, so the amendment named only one. This
close probed them (cases D to G).

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
| G1-CLOSE, first close | 5.00 | 1.69 | 34% | 1 |
| G1-CLOSE, this re-close | (same plan line) | not yet recorded | — | in progress |

Recorded unit spend is 4.37 USD. The first close's `judged` event also records a judge cost
of 0.44 USD; the events do not say whether the close's 1.69 includes it. The plan total is
11.00 and the gate budget 14.00. This session's cost and its judge's are written later. The
earlier `blocked_human` stop of this unit recorded 0.00. The review, its fixes and the
amendment happened outside the loop, so `events.jsonl` has no cost for them.

**T04's warning rate.** Re-measured this session over `done` units with `produces:`: the
shipped rule (path, file name or parent directory) would fire on 35 of 402, **8.7%** (same as the first close), under
the 10% limit. Path or file name alone would fire on 81 of 402, 20.1%. T04 recorded 81 and
35 of 401 in the check's docstring; the population has since grown by one. T04's progress
note does not carry the count that its criterion 3 asked for in the RESULT notes, and this
session did not see that RESULT. The parent-directory match is a plain substring test, so a
short directory such as `tests` is satisfied by almost any body. The WARN is weak for such
paths.

## Consumer-visible contract changes

Pending human acknowledgment. Each has a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0251`. This re-close added no fragment; it extended the first one in place
with the overtaken checks measured in cases D to G.

1. **Changed:** the three deliverable refusals run before verification. An attempt that
   would also have failed a gate, `files_changed_mismatch`, the smoke-import check, a
   closing-deliverable guard or the blocked-verdict check is reported as the deliverable
   refusal.
2. **Added:** `defaults.fail_fast_deliverables`, default `true`.
3. **Changed:** the retry note for the three refusals lists the changed paths, at most 20
   plus a count.
4. **Added:** a `specfuse lint` WARN for a `produces:` path the unit's body never mentions.

## What the loop did NOT verify

- **A real project whose gates write a declared deliverable.** The opt-out is tested only
  with stubs. With the default, such a unit is refused early on every attempt.
- **Real refused attempts on the new build.** T01 to T04 ran on a build pinned before the
  change (`bd7e508`). `events.jsonl` shows three later pins (`cddc418`, `eb30755`,
  `b2513b4`), and both closes were dispatched after a later pin, so "every attempt ran on
  the old build" holds for T01 to T04 and is not established for the closes. No event in
  this feature shows a real early refusal, so no real saving in gate time is measured.
- Tree handling for early `deliverable_missing` and `no_deliverable_files` refusals.
- Tree handling in probe cases D, F and G; the difference stated above is from the code.
- The probe used a stubbed `verify`. `no_deliverable_files` was not paired with any
  overtaken check.
- That cases A to G are the whole list of overtaken checks. The list comes from reading
  `execute_unit_attempt()` and the post-squash guards in `run()`; a squash-commit failure,
  for one, was not probed.
- Any unit's "fails on HEAD" claim, against a pre-feature tree.
- Whether the pending-diff computation matches the squash diff for renames, submodules or
  ignored files. Only the oracle's simple cases were run.
- `specfuse lint` as the installed command. The installed build differs from this tree, so
  the repository scripts were used.
- `docs/methodology.md` states the early order but names no precedence; this unit may not
  edit it. Its line "What is refused does not change, only when" was not checked beyond
  the probe cases.
