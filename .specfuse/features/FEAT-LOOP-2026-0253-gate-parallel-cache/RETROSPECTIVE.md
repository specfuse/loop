# Retrospective — FEAT-LOOP-2026-0253, parallel gates and the gate result cache

## Gate 1

## Verdict

`met` (advisory; the judge concludes). All nine Definition-of-done clauses are proven by the
runs below, and none of the unit's escalation triggers fired. The probes also found two
limits of the cache that no clause covers. They are listed under "Notes for the human
reviewer".

## Measurements

Everything here ran fresh in this close, unless a line says otherwise. No git command was
typed in this session. Test fixtures and probes ran git inside their own temporary
repositories. Probes and control runs used copies and scripts under `$TMPDIR`.

carried forward: 0 criteria, re-measured: 16

### feature_oracle: PASS

`python3 -m unittest tests.test_gate_parallel_cache -v -b`: exit 0, `Ran 33 tests`, `OK`.
Five more runs of the same command, to look for timing flakes: exit 0 each time.

`grep -nE "skip(Test)?\(" tests/test_gate_parallel_cache.py` finds no `unittest.skip(`. It
finds two `skipIf(sys.platform == "win32", ...)` guards (POSIX process groups, POSIX file
modes). Neither skipped on this macOS run.

### Control: the oracle against the pre-feature driver

The current test file was run against a copy of the pre-feature pinned build (tree
`e362f74e…`, which has no `max_parallel` or `gate_cache` text in `loop.py`): exit 1,
`FAILED (failures=17, errors=14)`. Those counts include subtests. 23 of the 33 tests failed
and 10 passed. The 10 are three `TestDefaultUnchanged` tests, six `TestCacheMiss` tests and
`test_a_gate_run_fresh_carries_no_cached_field`. A driver with no cache that runs one gate
at a time is expected to pass those. This shows the module red before the feature. It does
not show each class red at its own unit's dispatch.

### Control: the default run, old driver against new

One script ran the same four gates (pass, fail, dependency-skipped, pass), with no
`max_parallel` and no `inputs:`, through `_run_gate_set()` and `verify()`. It ran once on
the pre-feature pinned build and once on the working tree. After removing durations and
gate-log paths, the two JSON outputs are byte-identical (`cmp` exit 0). Compared: result
dicts, return codes, the `verify()` verdict and report, `gate_result` payloads, and that no
cache file exists.

### Controls: mutations in temporary copies of the tree

| Edit made to the copy | Tests run | Result |
|---|---|---|
| gates considered in reverse order | `TestDefaultUnchanged` | exit 1, 1 failure |
| cache argument removed from `verify()`'s call | `TestCacheHit` | exit 1, 2 failures |
| the `never_cached` filter disabled | `TestNeverForAVerdict` | exit 1, 2 failures |
| cache passed to `run_gate_broad_set` | `TestNeverForAVerdict.test_the_broad_run` | exit 1, 1 failure |
| cache passed to `probe_baseline` | `TestNeverForAVerdict.test_the_baseline_probe` | exit 1, 1 failure |

### Unit-named modules

`python3 -m unittest tests.test_gate_timings tests.test_run_progress
tests.test_dispatch_skeleton -b` with `HOME` under `$TMPDIR`: exit 0, `Ran 63 tests`, `OK`.
These cover the module lists in T01, T02, T03 and T04. The first try, with the real `HOME`,
exited 1: the sandbox does not allow writing the Claude session directory the driver
checks for.

`cmp` finds `docs/methodology.md` and its packaged copy identical, and both copies of
`verification.yml.example` identical. `scripts/sync-scaffold.sh` itself was not run.
`python3 -m specfuse.loop.changelog_fragments check`: exit 0.

### Probes of paths the oracle does not drive

- **Cross-unit hit (clause 5 as widened).** In a temporary repository, `verify()` for unit
  `T01`, then the driver's ignored-file cleanup (`_clean_attempt_ignored`), then
  `verify()` for unit `T02`: `gate-cache.json` survived the cleanup, the second report
  read `PASS (cached)`, and the command had run once. The oracle's hit tests use one unit
  ID only.
- **A real `verification.yml`.** The oracle passes config as dicts. Two temporary YAML
  files (block-list and inline-list `inputs:`, `max_parallel: 4`) read through
  `load_verification()` both gave limit 4, `inputs` `['src/*', 'docs']` and a cache key.
- **Broad run and baseline probe with bad config.** `max_parallel: 0`, and
  `inputs: "src/"`: both `run_gate_broad_set` and `probe_baseline` returned a
  `CONFIGURATION ERROR` and the gate command ran 0 times. The oracle checks this through
  `verify()` only.
- **A close unit's own verify can reuse a result.** A `close` unit with `inputs:` on a
  `plannext` gate, and `extra_gates: [code]` with `inputs:` on the code gate, was verified
  twice. The second report read `PASS (cached)` for both, and each command had run once.
- **A pathspec that matches nothing stays cached.** A gate with `inputs: ["scr/*"]` (a
  mistyped `src/*`) passed, then `src/a.txt` was edited. The next `verify()` read
  `PASS (cached)`, and the command had run once.

### This attempt, on the new driver

This close runs on a build pinned after the four units. `work/STATUS.json`, read during the
session, held `"gates_running": []` with `phase: agent`. This repository's
`verification.yml` sets neither `max_parallel` nor `inputs:`.

### Broad run (the driver's, not re-run here)

`GATE-01.md` records `broad_run.ok: true` with `failing: []` at 04:59:00Z, and
`events.jsonl` has 18 `gate_result` events with `phase: broad`, all `ok: true`, including
`tests` (431.6 s) and `coverage`. `find specfuse tests scripts docs -type f -newer` a
marker stamped at that time, leaving out `__pycache__`, lists nothing. This unit does not
run the broad tier.

### Per-criterion results

All 16 unit criteria pass on the runs above; the entries are in `GATE-01-CRITERIA.md`. The
"fails on HEAD" half of T01#1, T02#1, T03#1 and T04#1 rests on the whole-module control
against the pre-feature build.

## Definition of done, clause by clause

Tests are in `tests/test_gate_parallel_cache.py`.

| Clause | Result | Proved by |
|---|---|---|
| 1 default unchanged | proven | `TestDefaultUnchanged` (four tests); the old-against-new comparison; the reverse-order control |
| 2 parallel | proven | `TestParallel`: overlap at 2, none at 1, a peak of exactly 2 with three gates, a `needs` gate starting after its dependency ends, failed dependencies skipped and never started, and all three callers applying the limit. Overlap is read from intervals the stubs record |
| 3 result order | proven | `TestResultOrder`: `test_a_later_gate_finishing_first_keeps_declared_order` (results, joined report, failure signature) and `test_gate_result_events_are_in_declared_order`. The second drives the broad-phase event builder; the per-attempt builder reads the same ordered list |
| 4 parallel safety | proven | `TestParallelSafety` (four tests): a timeout kills its process group while two gates pass; four gates write each event once on whole lines, with a flush that deliberately splits lines; `STATUS.json` names both running gates |
| 5 cache hit | proven | `TestCacheHit` (four tests); the cross-unit probe; the cache-argument control |
| 6 cache miss | proven | `TestCacheMiss` (seven tests): edit, add, delete, mode change, command change, a failure not stored, no `inputs:`. Each hit has a miss that differs by one input |
| 7 never for a verdict | proven for the four named runs | `TestNeverForAVerdict`: broad run, baseline probe, `feature_oracle`, and a gate another gate needs (narrow and broad dependents), each counted by command runs; the three matching controls. See the note below on a close unit's own verify |
| 8 configuration errors | proven | `TestConfigurationErrors` (bad `max_parallel` and `inputs:` values, no command run); the broad-run, baseline and YAML probes |
| 9 nothing else changes | proven | no pre-existing test changed (next section); the driver's broad run |

**No `unittest.skip` survives** in `tests/test_gate_parallel_cache.py`.

**Clause 5 was widened during the feature.** `GATE-01.md` records that on 2026-11-27,
before the close, "an earlier attempt of the same unit" became "an earlier attempt in this
feature (of the same unit or an earlier one)". The edit is on the operator's standing
instruction. Review it as a change to the definition of done.

## Pre-existing tests changed

None. The four units' `attempt_outcome.files_touched` name one file under `tests/`,
`tests/test_gate_parallel_cache.py`, which this feature created. `find tests -type f
-newer` a marker stamped at the first unit's start, leaving out `__pycache__`, lists only
that file. So clause 9's allowance for forced edits was not used, and there is no edit to
explain.

## What happened

T01 to T04 each passed on the first attempt, and the gate's broad run was clean. The driver
then stopped on `judge_editing_terminal`, as `PLAN.md` decision 6 expected. The operator
acknowledged it ("Driver changes reviewed"), widened clause 5, and re-armed the close. The
pinned build stayed pre-feature for T01 to T04 (`driver_staleness_detected`,
`halted: false`).

## Cost analysis

Actual figures are `cost_usd` from each unit's `task_completed` event in `events.jsonl`.

| Unit | Planned USD | Actual USD | Actual / planned | Attempts |
|---|---|---|---|---|
| T01 | 2.50 | 0.57 | 23% | 1 |
| T02 | 2.50 | 0.42 | 17% | 1 |
| T03 | 3.00 | 0.54 | 18% | 1 |
| T04 | 2.00 | 0.37 | 19% | 1 |
| Substantive total | 10.00 | 1.90 | 19% | 4 |
| G1-CLOSE (and its judge) | 5.00 | not yet recorded | — | in progress |
| Feature | 15.00 | 1.90 recorded | 13% so far | — |

The gate budget is 19.00 USD. `events.jsonl` has no `task_completed` event for the close
yet. The judge-editing stop recorded 0.00 cost and 0 attempts (`re_arm_history`). The
substantive units came in at about a fifth of plan.

### Failure-class breakdown

No attempt failed: each of T01 to T04 has one `attempt_outcome`, `passed`, with
`failure_class: null`. The only halt was `judge_editing_terminal`, a planned stop for a
person and not a work-unit failure.

## Consumer-visible contract changes

Pending human acknowledgment. Each item has a new `changelog.d/` fragment tracing to
`FEAT-LOOP-2026-0253`. The operator's judge-edit acknowledgment covers driver paths, not
this list.

1. **Added:** `defaults.max_parallel` (integer of 1 or more, default 1). Any other value is
   now a `CONFIGURATION ERROR`.
2. **Added:** per-gate `inputs:` and the report line `PASS (cached)`, stored in
   `<feature>/work/gate-cache.json`. A value that is not a non-empty list of non-empty
   strings is now a `CONFIGURATION ERROR`. A project that already carried either key for
   another purpose would now be refused or get new behaviour.
3. **Added:** `cached: true` (with `duration_seconds: 0`) on the `gate_result` event of a
   reused result. The field is absent otherwise.
4. **Added:** `gates_running` in `work/STATUS.json`. With parallel gates, `gate` names the
   most recently started gate still running.

## Notes for the human reviewer

- **A mistyped `inputs:` pathspec hides later changes.** If the pathspecs match no file,
  the key depends on the command alone, so after one `PASS` the per-attempt verify reuses
  it for the rest of the feature. T03's notes raised this; T04 did not add a check or a
  specific warning. The example file says to list every file that can change the verdict.
  The broad run still runs the gate fresh, so the error would show there, at the end of
  the gate. No clause covers it. Suggested follow-up: treat zero matches as "never
  cached".
- **A close unit's own verify can reuse a result.** It is a per-attempt `verify()`, which
  clause 5 and the first sentence of decision 4 allow. Decision 4 also says that "any run
  a close or judge reads" runs fresh. The code of `build_judge_bundle` takes no gate
  result or verify report, so I found no path from a reused result to the judge. A close
  can still pass its own exit check on one, if its `plannext` or `extra_gates` gates
  declare `inputs:`. If decision 4 was meant to include that check, `verify()` should pass
  no cache for close-type units. The same holds for the sentence in `docs/methodology.md`
  that no terminal verdict rests on a reused result.
- From the code, untested: a broad run that fails a gate does not remove that gate's cache
  entry. With `inputs:` that leave a file out, the repair attempt could report
  `PASS (cached)` for the gate the broad run just failed.
- From the code, untested: `gate-cache.json` is an ordinary file in the work tree, which an
  agent session can write. A forged entry would affect the per-attempt verify only.
- From the code: the pre-dispatch `prep` and `oracles` runs (`prerun.py`) ignore
  `max_parallel` and run one gate at a time.
- The driver writes `work/.gitignore` for the status file only. The cache stays out of
  commits through the scaffold's `.specfuse/**/work/` ignore line.

## What the loop did NOT verify

- **Wall-clock savings on a real project.** Only stub gates that sleep ran. No timing of a
  real gate set at `max_parallel` above 1, and no real cache hit in a live feature run. See
  `PLAN.md` "Post-merge checklist", first line (parallel timing) and second (cache hit on
  a retry).
- **Gates that interfere in one tree.** `max_parallel` lets two gates share output files,
  ports, caches or coverage data at once. The example file says such gates must be safe to
  run together; the driver does not check it, and no test runs gates that interfere.
  Follow-up: while doing the checklist's first line, record any failure that appears only
  above 1.
- **The Windows Git-Bash path under threads.** All runs were on macOS. The `taskkill`
  timeout branch and `bash.exe` spawning from worker threads did not run, and the timeout
  and file-mode tests skip on Windows. `PLAN.md`'s checklist has no Windows line. Follow-up:
  add one, or run the oracle on a Windows host, before recommending `max_parallel` there.
- **Interrupting a parallel run.** No test sends Ctrl-C or kills the driver while several
  gates run. This has no checklist line; it belongs with the Windows follow-up as a manual
  check.
- **Large input sets.** The key reads every matched file on each attempt. The cost on a
  large tree was not measured; the checklist's second line is the place to compare.

## Lessons

Staged in `LEARNINGS-pending.md`.
