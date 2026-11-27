# Retrospective — FEAT-LOOP-2026-0252, run progress and stop notification

## Gate 1

## Verdict

`met` (advisory; the judge concludes). This is the second close of gate 1. The first
recorded `not_met` on clause 6 (#3626). The fix is on the branch, and the re-run condition
in `FOLLOW-UPS.md` holds. All seven Definition-of-done clauses are proven by the runs below.

## Measurements

Everything here ran fresh in this re-close, unless a line says otherwise. Test runs and the
watcher used `HOME` under `$TMPDIR`. No git command was typed in this re-close; the test
fixtures run git inside their own temporary repositories.

carried forward: 0 criteria, re-measured: 17

One breach in this re-close: the final check also ran
`python3 .specfuse/scripts/leak_scan.py --all` (exit 0), a `tier: broad` gate that this
unit was told not to run.

(The first close ran one read-only `git ls-files` on the feature folder, against its own
rule.)

### feature_oracle: PASS

`python3 -m unittest tests.test_run_progress -v -b`: exit 0, `Ran 38 tests`, `OK`, no skips.
`grep -nE "unittest\.skip|skipTest|@skip|SkipTest|expectedFailure" tests/test_run_progress.py`:
exit 1, no match.

**Control from the first close, not re-run here:** the then-current `tests/` against the
pre-feature pinned driver gave exit 1, `ImportError: cannot import name 'progress' from
'specfuse.loop'`. This shows the whole module red there. It does not show each class going
red at its own unit's dispatch.

### Unit-named modules

`python3 -m unittest tests.test_judge_path_registry
tests.test_driver_event_registry_covers_emitters tests.test_validate_event_driver_types
tests.test_gate_timings tests.test_dispatch_skeleton tests.test_fail_fast_deliverables
tests.test_agent_policy_schema tests.test_notify tests.test_notify_escalation
tests.test_scaffold_data_in_sync -b`: exit 0, `Ran 153 tests`, `OK`.

### #3626: the two real-checkout tests, and their control

`TestStopNotification.test_checkout_bringing_an_older_escalation_is_not_read` and
`test_checkout_to_a_shorter_log_still_reads_this_runs_events` drive `loop.main()`. The run
starts off the feature branch, and the driver's own checkout switches `events.jsonl`. Both
pass in the oracle run above.

**Control.** In a copy of the tree under `$TMPDIR`, `progress.py` was edited back to read
from a byte offset taken in `remember_run`, with no timestamp filter.
`python3 -m unittest tests.test_run_progress.TestStopNotification -b` there:
`Ran 14 tests`, `FAILED (failures=2)`. The two failures were those two tests, with
`'halted' != 'awaiting_review'` and `'stopped' != 'halted'`. These are the two wrong
results the first close's probes found. So both tests detect the defect, and the checkout
in them really changes the log.

### Clause 7: what changed outside the new code

`ast` comparison of `loop.py` with the pre-feature pinned build (tree `f903f872…`):

- `dispatch()` and `parse_claude_json_output()`: identical syntax trees.
- The 2 syntax nodes that name `attempt_outcome` (calls and builder functions): identical.
- Functions changed: `_paths_differing_from`, `_run_gate_set`,
  `capture_working_tree_diff`, `execute_unit_attempt`, `main`, `run`. Added:
  `heartbeat_files_touched`, `resolve_heartbeat_seconds`. None removed.

A byte comparison of the files under `specfuse/loop/` with the first close's pinned build
(tree `e9e8ef33…`) names one differing file, `progress.py`.

From the first close's reading of the `loop.py` diff, not repeated here: the one changed
input to the `attempt_outcome` payload is `_refusal_touched`, which now leaves out
`events.jsonl`, so the driver's mid-attempt lines stay out of a refused attempt's
`files_touched`.

### Live observation: this attempt

- `events.jsonl` held `agent_session_started` (`attempt: 1`, 04:17:54Z) while the session
  was running.
- `work/STATUS.json` read `phase: agent` with `elapsed_seconds` 90.131
  (`updated_at` 04:19:24Z), then 150.326 (04:20:24Z). `files_touched` was `[]` on both,
  taken before this session had written any file.
- `python3 -u -m specfuse.loop.loop --watch --feature FEAT-LOOP-2026-0252`, run for 35 s
  with output piped: printed one line (`FEAT-LOOP-2026-0252/G1-CLOSE  attempt 1/3  phase
  agent  gate -  elapsed 90s`) and was still watching when the probe killed it.

### Other oracles

- `validate_agent_policy` on three temporary policy files: a string `notify_command` gives
  no finding about the key; `["a", "b"]` and `5` each give
  `ERROR: 'escalation.notify_command' must be a string`.
- `resolve_heartbeat_seconds`: `[30, 30, 30, 30, 7]` for missing, `"x"`, `0`, `-5`, `7`.
- `cmp` finds both copies of `verification.yml.example` identical, and both copies of
  `docs/getting-started.md` identical.
- `python3 -m specfuse.loop.changelog_fragments check`: exit 0.

### Broad run (the driver's, not re-run here)

`GATE-01.md` records `broad_run.ok: true` at 04:17:54Z, after the #3626 fix. Its logs read
`Ran 5201 tests`, `OK (skipped=4)`, and total coverage 92% (`progress.py` 92%). This unit
does not run the broad tier.

### Per-criterion results

All 17 unit criteria pass on the oracle, named-module and validator runs above; the entries
are in `GATE-01-CRITERIA.md`. "Fails on HEAD" rests only on the first close's whole-module
control.

## Definition of done, clause by clause

| Clause | Result | Proved by (all in `tests/test_run_progress.py` unless named) |
|---|---|---|
| 1 phase events | proven | `TestPhaseEvents`: `test_order_and_payloads`, `test_events_validate_against_the_packaged_schemas`, `test_session_start_is_on_disk_while_the_session_runs`, `test_gate_start_is_on_disk_while_the_gate_runs`; plus the live observation |
| 2 status file | proven, with the note below on `stop_reason` | `TestStatusFile` (four tests); `TestStopNotification._assert_notified` for `stop_reason` |
| 3 heartbeat | proven | `TestHeartbeat` (four tests); `updated_at` advances at least twice, `notes/a.txt` listed, no thread left after return or raise |
| 4 driver lines | proven | `TestDriverLines` (two tests) |
| 5 watcher | proven | `TestWatch` (eight tests) |
| 6 stop notification | proven | `TestStopNotification` (14 tests): five reasons, each with one post and one command call; failing commands; nothing configured; `--dry-run`; no shell; the two real-checkout tests for #3626. Validator check above |
| 7 nothing else changes | proven | no pre-existing test changed (next section); syntax-tree comparison above; the driver's broad run |

**No `unittest.skip` survives** in `tests/test_run_progress.py`.

**Notification count.** `_assert_notified` asserts one post and one command call for each
stop it checks. No test run here showed a stop that sent more or fewer where a channel was
configured.

**Clause 2.** The clause is stated for runs driven through `loop.run()`. `stop_reason` is
set by `notify_stop`, which `main()` calls. After a direct `loop.run()` it stays `null`, and
`TestStatusFile.test_stopped_after_run_returns` asserts that `null`. The set value is proven
through `loop.main()` only. At the first close, `pyproject.toml` pointed `specfuse-loop` at
`main`, and a search of `specfuse/` found no other caller of `run()`. T04's body told it to
make the call from `main()`. The same applies to clause 6's "each return from `run()`".

**Clause 5.** An elapsed-only change prints nothing, as T03's AC1 says. The clause's "prints
a line only when one of those changes" limits when a line may be printed, so this stays
within it, although the list it refers to includes elapsed time. The watcher also prints
once when the file goes stale, which the clause's next sentence asks for.

## Pre-existing tests changed

None. The four units' `attempt_outcome.files_touched` name one file under `tests/`,
`tests/test_run_progress.py`, which this feature created. `find tests -type f -newermt`
from the feature's start, leaving out `__pycache__`, run again after the #3626 fix, lists
only that file. So clause 7's allowance for edits forced by the new driver lines was not
used.

## What happened

T01 to T04 each passed on the first attempt. The gate's broad run was clean. The driver then
stopped on `judge_editing_terminal`, as `PLAN.md` decision 6 expected. The operator
acknowledged it ("Driver changes reviewed and sound, accept them") and re-armed the close.
The pinned build stayed pre-feature for T01 to T04 (`driver_staleness_detected`,
`halted: false`), so their events carry no phase lines.

The first close passed its guards and recorded `not_met`; the judge agreed. `remember_run`
had stored the byte size of `events.jsonl` before `run()` checked out the feature branch, so
`notify_stop` could read the wrong lines. The earlier-run test kept one file for the whole
run and could not see this. The driver filed #3626. The fix selects events stamped at or
after the run's start time and adds two real-checkout tests. The operator re-armed the close
("Fixed the stop-reason offset, re-close it"), and the driver ran the broad tier again.

## Cost analysis

Actual figures are `cost_usd` from each unit's `task_completed` event in `events.jsonl`.

| Unit | Planned USD | Actual USD | Actual / planned | Attempts |
|---|---|---|---|---|
| T01 | 2.50 | 1.27 | 51% | 1 |
| T02 | 2.50 | 0.45 | 18% | 1 |
| T03 | 2.00 | 0.45 | 22% | 1 |
| T04 | 2.50 | 0.72 | 29% | 1 |
| Substantive total | 9.50 | 2.89 | 30% | 4 |
| G1-CLOSE, first close (includes its 0.42 judge) | 5.00 | 1.89 | 38% | 1 |
| G1-CLOSE, this re-close | (same 5.00) | not yet recorded | — | in progress |
| Feature | 14.50 | 4.78 recorded | 33% so far | — |

The gate budget is 18.00 USD. The judge-editing stop before the first close recorded 0.00
cost and 0 attempts (`re_arm_history`). The #3626 fix has no work unit and no
`task_completed` event, so its cost is not in these figures.

## Consumer-visible contract changes

Pending human acknowledgment. Each item has a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0252`. The first close wrote the four fragments; they still describe the
behaviour, so none was added or changed here. The operator's judge-edit acknowledgment
covers driver paths, not this list.

1. **Added:** one plain driver line per phase change, and the event types
   `agent_session_started`, `agent_session_finished`, `gate_started` and `gate_finished`.
   Gates run outside a unit carry `attempt: null`, from the code. `events.jsonl` order is no
   longer timestamp order.
2. **Added:** `<feature>/work/STATUS.json` (with a `work/.gitignore` the driver writes if
   absent) and `defaults.heartbeat_seconds`, default 30.
3. **Added:** `specfuse-loop --watch [--feature F]`.
4. **Added:** one stop notification through the escalation webhook, and the key
   `escalation.notify_command`. A project that already has a webhook configured now gets a
   message at the end of every non-dry-run run.

## Notes for the human reviewer

- From T04's note and the code: `--prepare-only` and a refused lock also notify. A refused
  lock leaves the other driver's status file alone. `quiet_hours` holds back the webhook
  (through `notify.post_notification`), not `notify_command`.
- A killed driver sends nothing and leaves the status file at its last phase. `--watch`
  then shows `no update for Ns` and keeps waiting.
- From the code, untested: "this run's events" now means events stamped at or after the
  run's start by the wall clock. A clock stepped backwards during a run could drop the
  run's own lines. A line written elsewhere with a later stamp, and brought in by the
  run's checkout or base merge, would count as this run's.
- `PLAN.md`'s post-merge checklist has no line for a real driver crash. This unit may not
  edit `PLAN.md`; add one.
- The driver files the post-merge issue only on a `met` close.

## What the loop did NOT verify

- **Real desktop and chat delivery.** Only a counting stub poster and a stub command ran.
  See `PLAN.md` "Post-merge checklist", second line (desktop notifier) and third (chat
  webhook).
- **A real multi-minute attempt watched live.** The observation above is from inside this
  attempt, with piped output, for 35 s. Nobody watched from a second terminal, saw the
  in-place redraw on a real terminal, or saw the watcher follow a gate change. See
  the checklist's first line.
- **A real driver crash.** Exceptions are simulated by a stub session that raises. No
  process was killed. The post-merge checklist is the place for this check, but none of its
  three lines covers it (see the reviewer note).
- **A stop notification from a real run of this feature.** The checkout tests use real
  branches in temporary repositories, not a live feature run.
- **The 30 s command timeout in real time.** The test patches it to 1 s and asserts the
  constant is 30.

## Lessons

Staged in `LEARNINGS-pending.md`.
