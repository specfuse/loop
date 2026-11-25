# Retrospective — FEAT-LOOP-2026-0250 gate 1 close

First and only close of gate 1 (single-gate feature, PLAN decision 3). Four loop-dispatched
implementation units (T01–T04). This session re-ran the oracles fresh, annotated
`GATE-01-CRITERIA.md`, wrote the changelog fragments and this file.

## Measurements

Every command below was run in this session from the repository root, exit codes read
directly. HEAD was `158389e952114613487622605f9b1cf5eef49ad1` plus this close's own
uncommitted edits (`changelog.d/`, this file, `LEARNINGS-pending.md`, `GATE-01-CRITERIA.md`,
the `verdict` field of `WU-90-gate-1-close.md`). The close session may not run git commits.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_gate_timings -v -b` (exit 0): `Ran 13 tests` / `OK`,
every class running, none skipped (the run prints no `skipped` marker).

```
TestAttemptGateEvents            3
TestAttemptSplit                 3
TestBaselineAndBroadPhases       3
TestStatsReport                  2
TestNothingExistingChanges       2
```

### No surviving skip (close criterion 1)

`grep -c "unittest.skip" tests/test_gate_timings.py` prints `0`. A looser `grep -nE "skip|Skip"`
matches only the `skipped` payload key, two test names with `skip` in them, and the docstring line
recording the walking skeleton's history. T01 created the module with clauses 2–4 and clause 5's non-schema half
skipped by owner name; T02, T03 and T04 each removed their own.

### Closing lint (close criterion 5)

`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-LOOP-2026-0250-gate-timings --closing`
is run last, after the verdict field is written; its result is in the RESULT block of this
attempt. The bare `specfuse lint --closing` warns that it measures the pipx-installed build
rather than this checkout, so the checkout's script was run instead.

### Broad run (driver's, not re-run here)

`events.jsonl` records two `broad_run_result` events for gate 1. The first, at
2026-11-25T15:37:40, was `ok: false` (`tests` `(failures=4,`, `coverage` `no_gate_marker`)
and raised `human_escalation` `broad_run_gate_failure`. The second, at 15:49:51, was `ok: true`,
`failing: []`, on the tree in `GATE-01.md`'s `broad_run:` block. `security` and `coverage` are
`tier: broad` and are the driver's.

### Per-criterion oracles (12 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 12

All twelve were `unverified` on entry. Each was run in this session as its own command; each now
records its oracle command, `kind: narrow`, `state: pass`, `attempt: 1` and `proved_at_sha`
`158389e952114613487622605f9b1cf5eef49ad1`, all exit 0.

| criterion | oracle | ran |
| --- | --- | --- |
| T01#1 | `TestAttemptGateEvents` | 3 tests, OK |
| T01#2 | `TestNothingExistingChanges.test_gate_result_in_schema_event_types` | 1 test, OK |
| T01#3 | `tests.test_dispatch_skeleton tests.test_loop_worklist_injection` | 20 tests, OK |
| T02#1 | `TestAttemptSplit` | 3 tests, OK |
| T02#2 | `TestAttemptSplit.test_blocked_records_zero_verify` | 1 test, OK |
| T02#3 | `tests.test_dispatch_skeleton tests.test_files_changed_auto_repair` | 18 tests, OK |
| T03#1 | `TestBaselineAndBroadPhases` | 3 tests, OK |
| T03#2 | same class; asserts the key set of the failing-gate lists, see "did NOT verify" 4 | 3 tests, OK |
| T03#3 | `tests.test_gate_timings tests.test_dispatch_skeleton tests.test_events_stats` | 45 tests, OK |
| T04#1 | `TestStatsReport` | 2 tests, OK |
| T04#2 | `tests.test_events_stats` | 20 tests, OK |
| T04#3 | `grep -c "unittest.skip" tests/test_gate_timings.py` | `0` |

### Definition of done, clause by clause (close criterion 1)

| clause | proven by | result |
| --- | --- | --- |
| 1. one `gate_result` per gate per attempt, `feature_oracle` included; duration at least the sleep; skipped dependent `ok: false`, `skipped: true`, `0` | `TestAttemptGateEvents.test_one_gate_result_per_gate_with_payload`, `test_durations_and_skip_semantics`, `test_stub_verify_without_gate_results_emits_none`; real `sleep` gates, one passing, one failing, one dependent, plus a sleeping `feature_oracle` | proven, positive control present |
| 2. `attempt_outcome` carries `agent_seconds` and `verify_seconds`, sum at most `duration_seconds`; blocked attempt records `verify_seconds: 0` | `TestAttemptSplit.test_split`, `test_blocked_records_zero_verify`, `test_defaults_when_usage_lacks_keys` | proven with a stubbed session that sleeps and a real sleeping gate |
| 3. baseline probe and broad run emit one `gate_result` per gate with `phase: baseline` / `broad`; unchanged-tree broad skip emits none | `TestBaselineAndBroadPhases.test_broad_run_phase`, `test_baseline_phase`, `test_unchanged_tree_broad_skip_emits_none` | proven at the `build_phase_gate_events` seam; the broad half also observed live, 18 `gate_result` events in this feature's `events.jsonl` |
| 4. `specfuse stats` (text and `--json`) reports the split and the slowest gates; an old corpus reads `not recorded`, never zeros | `TestStatsReport.test_new_corpus_reports_split_and_gates`, `test_old_corpus_reads_not_recorded` (positive control: new and old corpus) | proven; also observed live, see Cost analysis |
| 5. nothing existing changes: `duration_seconds` keeps its meaning, `verify_fn` stubs pass unchanged, `gate_result` in the schema and every emitted shape validates | `TestNothingExistingChanges.test_gate_result_in_schema_event_types`, `test_emitted_events_validate`; `tests.test_dispatch_skeleton`, `tests.test_files_changed_auto_repair`, `tests.test_events_stats` pass unedited | proven for the three new or changed shapes; `duration_seconds` meaning has no dedicated assertion, see "did NOT verify" 5 |

No `unittest.skip` survives in `tests/test_gate_timings.py` (grep above prints `0`).

## Cost analysis

Reconciled from `events.jsonl` `attempt_outcome` events and each unit's `planned_cost_usd`.
The unit plans sum to **18.50** (13.50 for T01–T04 plus 5.00 for this close), matching
`PLAN.md`; `GATE-01.md` sets `cost_budget_usd: 22.00`.

| unit | planned (USD) | actual (USD) | attempts (outcomes) | duration (s) |
| --- | --- | --- | --- | --- |
| T01 | 4.00 | 0.7950 | 2 (failed `other`, passed) | 358.3 |
| T02 | 3.00 | 0.3352 | 1 (passed) | 79.8 |
| T03 | 3.50 | 0.2817 | 1 (passed) | 72.0 |
| T04 | 3.00 | 0.2925 | 1 (passed) | 54.1 |
| T01–T04 | 13.50 | 1.7043 | 5 recorded | 564.2 |
| G1-CLOSE (this attempt) | 5.00 | not yet recorded | 1 | — |
| **recorded total** | 18.50 | **1.7043** | 5 recorded | 564.2 |

The five recorded attempts spent $1.70 (12.6% of the $13.50 planned for them, 7.7% of
`cost_budget_usd`). This close's own attempt is written when the driver ends it, so it is not
reconciled and the total excludes it. T01's frontmatter `cost_usd` (0.3842) is its second
dispatch only; `events.jsonl` has both attempts, 0.4108 and 0.3842. The two gate-1 broad runs and
the baseline probe are the driver's with no model session, so they are not charged to a unit.
The two repair commits between T01 and the close (`75c1ace`, `60dc90f`) were made outside the
driver, so `events.jsonl` carries no cost for them.

**T01's two attempts.** The first (291.2 s, $0.4108) failed `roadmap-link-gate`: the drafted
roadmap detail section had no `<a id="feat-loop-2026-0250">` anchor, so the row's detail link did
not resolve. The driver's baseline probe then found `tests` (`(failures=2,`), `coverage`
(`no_gate_marker`) and `roadmap-link-gate` failing on the reset tree, attributed the failure to
the branch rather than to T01, and raised `human_escalation` `preexisting_gate_failure`. Commit
`75c1ace` added the anchor and reopened the gate; the second dispatch passed in 67.1 s.

**What the broad run caught.** Four tests failed in the first broad run that no unit's narrow
tier selected: `TestNothingExistingChanges.test_emitted_events_validate` passed alone and failed
in the full suite (a module-level cache in `validate_event` left empty by an earlier test), and
three docs-sync tests failed because T04 edited `docs/methodology.md` without its packaged copy.
Commit `60dc90f` fixed both and the second broad run was clean.

**What the self-halt cost.** The terminal judge-editing stop fired at 2026-11-25T15:49:51 (PLAN
decision 2) and was acknowledged by the operator at 17:03:29: about 73 minutes of wall-clock, $0.00
driver spend, three acknowledged keys (`produces_driver_helper`,
`specfuse/loop/data/schemas/driver-event.schema.json`, `specfuse/loop/loop.py`).

### This feature's own agent/verify split (close criterion 3)

`python3 -m specfuse.loop.events_stats --roots .` (the module `specfuse stats` calls, run from the
checkout because the installed build is not this tree; exit 0) prints, for the whole repository:

```
agent / verify time per feature
  not recorded
```

and `--json` carries `"time_split": {}`. This feature's split is therefore **not recorded**, and
that is the correct reading, not a defect: all five attempts ran under driver builds pinned before
T01–T03 landed (`driver_build_pinned` and `driver_staleness_detected` with `halted: false` for each
unit in `events.jsonl`), so none of the five `attempt_outcome` events carries `agent_seconds` or
`verify_seconds`. Nothing renders `0` where it should read `not recorded`. No attempt on this
repository carries the split yet.

What this repository does record is the broad phase. `gate_timings` holds 18 `phase: broad` rows
from the clean 15:49:51 run, 351.3 s of gate time in total, of which `tests` is 311.0 s (88.5%),
then `leak-scan` 17.9 s, `sync-scaffold-bats` 10.8 s, `pre-push-hook` 3.6 s, with the other
fourteen gates under 2 s each. The slowest-gates view names real gates, as the plan's post-merge
checklist asks.

### Failure-class breakdown

| class | unit / event | count | cost (USD) | what it was |
| --- | --- | --- | --- | --- |
| `other` | T01 attempt 1 | 1 | 0.4108 | `roadmap-link-gate`: roadmap detail anchor missing (`no_gate_marker` on `coverage` rode along); fixed outside the unit |
| `preexisting_gate_failure` halt | gate 1, 2026-11-25T15:26:26 | 1 | $0.00 | probe attributed the red to the branch, not to T01; operator fixed and reopened |
| `tests` + `other` broad-run failure | gate 1 broad run 1, 15:37:40 | 1 | $0.00 | cache pollution in a new test, and a missing packaged docs copy; fixed outside the unit, second broad run clean |
| `judge_editing_terminal` halt | G1-CLOSE 2026-11-25T15:49:51 | 1 | $0.00 | expected (PLAN decision 2); acknowledged by the operator with a reason |

## Consumer-visible contract changes

Enumerated across T01–T04 for acknowledgment; each is a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0250`, written with `python3 -m specfuse.loop.changelog_fragments add`
(`Added` ×3). `python3 -m specfuse.loop.changelog_fragments check` exits 0.

- **Added — the `gate_result` driver event type**, registered in
  `specfuse/loop/data/schemas/driver-event.schema.json`'s `event_types`. One per gate per run,
  payload `attempt`, `gate`, `ok`, `skipped`, `duration_seconds`, `phase` (`attempt`, `baseline` or
  `broad`); `attempt` is `null` outside an attempt. Consumers that validate events against the
  registry now see a new type.
- **Added — `agent_seconds` and `verify_seconds` on `attempt_outcome` payloads.** `duration_seconds`
  keeps its meaning (the attempt loop's total); an attempt that never reached verification records
  `verify_seconds: 0`. A consumer reading old events finds neither key.
- **Added — the `specfuse stats` agent/verify section and slowest-gates section**, in text and in
  `--json` as `time_split` and `gate_timings`. A corpus with no such events reads `not recorded`.

No removals or renames. `broad_run_result` and `baseline_attribution` payloads are unchanged, and
existing `--json` keys are untouched.

## What the loop did NOT verify

1. **Real agent sessions.** The oracle stubs the agent session, so `agent_seconds` on a real
   dispatch is unchecked: that the timer around `dispatch()` covers a real `claude -p` session, and
   that `agent_seconds + verify_seconds` is close to `duration_seconds` on real attempts (the
   remainder is unnamed driver overhead), has not been observed. All five attempts in this
   feature ran on builds pinned before the change, so this repository holds no real attempt that
   carries the split. `PLAN.md`'s Post-merge checklist, first item, carries it.
2. **The external corpus that motivated the feature.** The report of 184 attempts and about 17.5
   hours of attempt time was not re-read; `specfuse stats` was not run on it, and whether its
   slowest-gates view names that corpus's real gates is unobserved. Backfilling old
   `events.jsonl` files is out of scope, so such a corpus reads `not recorded` until it has run
   attempts on a build that carries this feature. Post-merge checklist, second item.
3. **The `run()` wiring of attempt and baseline events.** The oracle drives
   `execute_unit_attempt()`, `build_attempt_gate_events()` and `build_phase_gate_events()` directly.
   That `run()` resets `wu.last_gate_results`, extends `wu_events` and flushes the events with
   `attempt_outcome` is covered by no test and has no live example; the broad half of the wiring
   was observed live (18 events at 15:49:51), the attempt and baseline halves were not. The
   baseline `gate_result` events are emitted only on the retroactive attribution path, the only
   path that still probes a baseline since FEAT-2026-0109/T01, and no real probe has run on the new
   build.
4. **`broad_run_result` and `baseline_attribution` payloads unchanged.** T03's criterion 2 asks the
   class to assert their keys. `TestBaselineAndBroadPhases` asserts the key set of the failing-gate
   lists those events carry, not the two event payloads themselves; the diff shows neither payload
   was edited.
5. **`duration_seconds` keeps its meaning.** Clause 5 has no dedicated assertion. It rests on
   `test_split` bounding `agent_seconds + verify_seconds` by `duration_seconds`, on the unedited
   existing suites above, and on the driver's clean broad run.
6. **Killed attempts.** Attempt-phase `gate_result` events share `attempt_outcome`'s buffer, so a
   killed attempt loses both; PLAN decision 4 puts changing that out of scope and it is untested.
7. **The "fails on HEAD" halves of the red-first criteria** were claimed by each unit's own attempt and
   not re-observed here; this close re-observed only the passing side.
8. **The `feature_oracle` as a timed gate on a real run.** Clause 1 includes it, and the test
   drives it with a sleeping command; no real attempt on this repository has recorded it.

## Retrospective

**What went well.** Four units, three first-time passes, $1.70 against a $13.50 plan. The walking
skeleton held: T01 created the oracle with later clauses skipped by owner name, each owner removed
its own skip, and none survived to the close. Every clause has a positive control (a passing gate
beside a failing one and a skipped dependent; a fresh broad run beside a tree-unchanged skip; a new
corpus beside an old one). The feature measured itself: the one phase it could observe live, the
broad run, already names `tests` as 88.5% of gate time.

**What didn't.** The feature could not report its own split, since the driver running it was pinned
before the code existed. The first broad run was red on four tests no unit selected, and T01's first
attempt spent 291 s on a roadmap anchor that the draft step should have written.

**Lessons.** Two entries staged to `LEARNINGS-pending.md`: a docs edit needs its packaged copy in the
same unit, and a test that validates events must pin the validator's caches.

**Open follow-ups (not blockers).** The two post-merge checklist items (one real feature checked
for `agent_seconds + verify_seconds` near `duration_seconds`; `specfuse stats` run on the corpus that
motivated this feature), filed at close as `specfuse:post-merge`.
