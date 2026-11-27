# Retrospective — FEAT-LOOP-2026-0252, run progress and stop notification

## Gate 1

## Verdict

`not_met` (advisory; the judge concludes). One Definition-of-done clause fails a probe run in
this session: clause 6. When `run()` switches to the feature branch and that branch holds a
different `events.jsonl`, the stop reason is worked out from the wrong lines. The probe got
`halted` from a run that wrote no `human_escalation`, and `stopped` from a run that did write
one. See `FOLLOW-UPS.md`. All 36 oracle tests and all 17 unit criteria pass. No test
exercises a log that changes during `run()`.

## Measurements

Everything here ran fresh in this close, unless a line says otherwise. Test runs and probes
used `HOME` under `$TMPDIR`. With the real `HOME` the sandbox blocks the driver's
`session-env` preflight: the first run of the oracle and of the named modules both exited 1
(named modules: 153 tests, 34 errors; the traceback shown was that `SystemExit`).

carried forward: 0 criteria, re-measured: 17

One breach of this unit's own rule: an early inspection command in this session included one
read-only `git ls-files` on the feature folder. No other git command was typed. The test and
probe fixtures run git inside their own temporary repositories.

### feature_oracle: PASS

`python3 -m unittest tests.test_run_progress -v -b`: exit 0, `Ran 36 tests`, `OK`, no skips.
A search of the file for `unittest.skip`, `skipTest`, `@skip`, `SkipTest` and
`expectedFailure` finds nothing (grep exit 1).

**Control: the oracle goes red without the feature.** The current `tests/` was run against a
copy of the pre-feature driver (the build pinned at 03:04:41Z, before T01 started): exit 1,
`ImportError: cannot import name 'progress' from 'specfuse.loop'`. This shows the whole
module is red there. It does not show each class going red at its own unit's dispatch.

### Unit-named modules

`python3 -m unittest tests.test_judge_path_registry
tests.test_driver_event_registry_covers_emitters tests.test_validate_event_driver_types
tests.test_gate_timings tests.test_dispatch_skeleton tests.test_fail_fast_deliverables
tests.test_agent_policy_schema tests.test_notify tests.test_notify_escalation
tests.test_scaffold_data_in_sync -b`: exit 0, `Ran 153 tests`, `OK`.

### Probe: the log changes while `run()` is running (clause 6 fails)

`remember_run` stores the byte size of `events.jsonl` early in `run()` (`loop.py`, before
the lock). `ensure_feature_branch` runs later and can check out an existing feature branch.
`notify_stop` then reads from the stored offset in whatever file is there.

Both probes drive `loop.main()` through the oracle's `_Notified` helper. They wrap
`ensure_feature_branch` so that, after it returns, the log holds what a checkout would bring
in. **The checkout is simulated by rewriting the file; no real branch with a different log
was used.**

| Probe | Run | Control reason | Reason after the log changes |
|---|---|---|---|
| `probe_offset.py` | passing session; the log gains an older run's `human_escalation` | `awaiting_review` | `halted` |
| `probe_converse.py` | blocked session; the starting log is long, the new one is empty | `halted`, unit `…/T01` | `stopped`, unit empty |

`PYTHONPATH=. python3 <scratchpad>/probe_offset.py` and `…/probe_converse.py`: exit 0; each
run made exactly one command call.

**Reachability, from reading the code.** The two pre-flight guards before the checkout,
`require_feature_folder_committed` and `require_feature_folder_unmodified`, look only at
untracked and uncommitted files. Neither compares the log with the feature branch's copy.
So a run started on another branch that holds the feature folder, with the feature branch
already there, reaches this path. A branch with no `events.jsonl` gives offset 0, so every
older escalation on the feature branch counts. This feature's own log already holds one
(`judge_editing_terminal`).

### Clause 7: what changed outside the new code

Compared with the pre-feature pinned build, using `diff` and `ast`:

- `dispatch()` and `parse_claude_json_output()`: identical syntax trees.
- The 2 syntax nodes that name `attempt_outcome` (calls and builder functions): identical.
  The full `loop.py` diff shows no change to how the payload is built. One input changed:
  `_refusal_touched` now excludes `events.jsonl`, which keeps the driver's new mid-attempt
  lines out of a refused attempt's `files_touched`.
- Functions changed in `loop.py`: `_paths_differing_from`, `_run_gate_set`,
  `capture_working_tree_diff`, `execute_unit_attempt`, `main`, `run`. Added:
  `heartbeat_files_touched`, `resolve_heartbeat_seconds`. None removed.
- `assert_implementation_touched_files` already ignores any `events.jsonl`, so the new
  mid-attempt lines cannot count as a deliverable.

### Live observation: this close attempt

The driver that dispatched this close runs the feature's own code.

- `events.jsonl` held `agent_session_started` (`attempt: 1`, 03:36:06Z) while the session
  was running. No `task_started` for `G1-CLOSE` was in the file at that point: that event is
  still buffered, so file order is not timestamp order.
- `work/STATUS.json` read `phase: agent`, with `elapsed_seconds` 150.4, 180.4, 210.5 and
  270.6 on successive reads, each a multiple of the 30 s beat.
- `python3 -m specfuse.loop.loop --watch --feature FEAT-LOOP-2026-0252`, run for 35 s from
  inside the session with output piped: printed one line
  (`… attempt 1/3  phase agent  gate -  elapsed 180s`), printed nothing for the next
  elapsed-only rewrite, and was still watching when the probe killed it.
- `files_touched` was `[]` on those reads, taken before a beat had seen any write by this
  session. The read at 331.3 s, after this session added the changelog fragments, listed all
  four of them, and left out `events.jsonl` and the close's unit file, both modified.

### Other oracles

- `validate_agent_policy`: a string `notify_command` gives no finding about the key; `["a",
  "b"]` and `5` each give `ERROR: 'escalation.notify_command' must be a string`.
- `cmp` finds both copies of `verification.yml.example` identical, and both copies of
  `docs/getting-started.md` identical.
- `python3 -m specfuse.loop.changelog_fragments check`: exit 0.

### Broad run (the driver's, not re-run here)

`GATE-01.md` records `broad_run.ok: true` at 03:34:05Z. Its logs read `Ran 5199 tests`,
`OK (skipped=4)`, and total coverage 92% (`progress.py` 92%). This unit does not run the
broad tier.

### Per-criterion results

All 17 unit criteria pass on the oracle and named-module runs above; the entries are in
`GATE-01-CRITERIA.md`. "Fails on HEAD" is covered only by the whole-module control above.
The clause 6 failure is a gate-level case that no unit criterion states.

## Definition of done, clause by clause

| Clause | Result | Proved by (all in `tests/test_run_progress.py` unless named) |
|---|---|---|
| 1 phase events | proven | `TestPhaseEvents`: `test_order_and_payloads`, `test_events_validate_against_the_packaged_schemas`, `test_session_start_is_on_disk_while_the_session_runs`, `test_gate_start_is_on_disk_while_the_gate_runs`; plus the live observation |
| 2 status file | proven, with the note below on `stop_reason` | `TestStatusFile` (four tests); `TestStopNotification._assert_notified` for `stop_reason` |
| 3 heartbeat | proven | `TestHeartbeat` (four tests); `updated_at` advances at least twice, `notes/a.txt` listed, no thread left after return or raise |
| 4 driver lines | proven | `TestDriverLines` (two tests) |
| 5 watcher | proven, under the reading below | `TestWatch` (eight tests) |
| 6 stop notification | **not met** | `TestStopNotification` passes, including exactly-once counts, five reasons, failing commands, nothing configured, `--dry-run`, no shell. The probe above breaks the reason rule |
| 7 nothing else changes | proven | no pre-existing test changed (next section); syntax-tree comparison above; the driver's broad run |

**No `unittest.skip` survives** in `tests/test_run_progress.py`.

**Clause 2.** The clause is stated for runs driven through `loop.run()`. `stop_reason` is
set by `notify_stop`, which `main()` calls. After a direct `loop.run()` it stays `null`, and
`TestStatusFile.test_stopped_after_run_returns` asserts that `null`. The set value is proven
through `loop.main()` only. `pyproject.toml` points `specfuse-loop` at `main`, and a search
of `specfuse/` found no other caller of `run()`. T04's body told it to make the call from
`main()`. The same applies to clause 6's "each return from `run()`".

**Clause 5.** "Prints a line only when one of those changes" follows a list that includes
elapsed time. T03 followed its own AC1 instead: an elapsed-only change prints nothing. T03
said so in its progress note and did not block, although `GATE-01.md` asks a unit to block
on an ambiguous clause. The watcher also prints once when the file goes stale.

## Pre-existing tests changed

None. The four units' `attempt_outcome.files_touched` name one file under `tests/`,
`tests/test_run_progress.py`, which this feature created. `find tests -newermt` from the
feature's start, leaving out `__pycache__`, lists only that file. So clause 7's allowance
for edits forced by the new driver lines was not used.

## What happened

T01 to T04 each passed on the first attempt. The gate's broad run was clean. The driver then
stopped on `judge_editing_terminal`, as `PLAN.md` decision 6 expected. The operator
acknowledged it ("Driver changes reviewed and sound, accept them") and re-armed this close.
The pinned build stayed pre-feature for T01 to T04 (`driver_staleness_detected`,
`halted: false`), so their events carry no phase lines. This close is the first unit run by
the new code.

The probe result comes from where the offset is taken. The oracle's earlier-run test
(`test_events_of_an_earlier_run_are_not_read`) keeps one file for the whole run, so it
cannot see this.

## Cost analysis

Actual figures are `cost_usd` from each unit's `task_completed` event in `events.jsonl`.

| Unit | Planned USD | Actual USD | Actual / planned | Attempts |
|---|---|---|---|---|
| T01 | 2.50 | 1.27 | 51% | 1 |
| T02 | 2.50 | 0.45 | 18% | 1 |
| T03 | 2.00 | 0.45 | 22% | 1 |
| T04 | 2.50 | 0.72 | 29% | 1 |
| Substantive total | 9.50 | 2.89 | 30% | 4 |
| G1-CLOSE (this attempt, with its judge) | 5.00 | not yet recorded | — | in progress |
| Feature | 14.50 | 2.89 recorded | 20% so far | — |

The gate budget is 18.00 USD. The judge-editing stop before this close recorded 0.00 cost
and 0 attempts (`re_arm_history`).

## Consumer-visible contract changes

Pending human acknowledgment. Each item has a `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0252`. The operator's judge-edit acknowledgment covers driver paths, not
this list.

1. **Added:** one plain driver line per phase change, and the event types
   `agent_session_started`, `agent_session_finished`, `gate_started` and `gate_finished`.
   Gates run outside a unit carry `attempt: null`, from the code. `events.jsonl` order is no
   longer timestamp order.
2. **Added:** `<feature>/work/STATUS.json` (with a `work/.gitignore` the driver writes if
   absent) and `defaults.heartbeat_seconds`, default 30.
3. **Added:** `specfuse-loop --watch [--feature F]`.
4. **Added:** one stop notification through the escalation webhook, and the key
   `escalation.notify_command`. A project that already has a webhook configured now gets a
   message at the end of every non-dry-run run. The stop reason can be wrong in the case in
   `FOLLOW-UPS.md`.

## Notes for the human reviewer

- From T04's note and the code: `--prepare-only` and a refused lock also notify. A refused
  lock leaves the other driver's status file alone. `quiet_hours` holds back the webhook
  (through `notify.post_notification`), not `notify_command`.
- A killed driver sends nothing and leaves the status file at its last phase. `--watch`
  then shows `no update for Ns` and keeps waiting.
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
- **A real branch checkout with a different log.** Both clause 6 probes simulate it.
- **The 30 s command timeout in real time.** The test patches it to 1 s and asserts the
  constant is 30.

## Lessons

Staged in `LEARNINGS-pending.md`.
