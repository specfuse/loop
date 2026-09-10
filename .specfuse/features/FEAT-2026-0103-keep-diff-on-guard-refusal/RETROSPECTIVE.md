<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0103, keep the diff on guard refusals

Single-gate feature. Gate 1 is terminal, so this close records what was
measured and the terminal verdict is written by a separate judge session.

## Gate 1 — a guard refusal keeps the tree and the next attempt repairs it

Five work units landed: T01 (retain the tree at the four guard sites, behind
`defaults.retain_on_guard_refusal`), T02 (the repair-turn note leads with the
guard's complaint), T03 (a RESULT naming an untouched non-deliverable is
auto-repaired without a dispatch), T04 (document the contract), and T04H, a
hygiene unit the gate's broad run forced after T04 wrote its two documentation
edits on opposite sides of the canonical/mirror split.

## Measurements

Every oracle below was re-run in this close session, on the working tree at
`126e7c661a036ea9039a96cb4e6ff7f03966fab8`, exit codes read directly. None is
inherited from a producing unit's self-report.

### feature_oracle: PASS

`GATE-01.md` declares `feature_oracle: python3 -m unittest
tests.test_guard_repair_e2e -v`. Re-run in this session (with `-b`, which
changes buffering only):

```
$ python3 -m unittest tests.test_guard_repair_e2e -v -b
test_retain_disabled_falls_back_to_todays_reset ... ok
test_retained_tree_lets_attempt_2_finish_the_job ... ok
Ran 2 tests in 0.995s
OK
EXIT=0
```

Both halves of the gate's claim are in that module: the retained-tree case
drives `loop.run()` through a `files_changed_mismatch` refusal on attempt 1 and
asserts the deliverable is still on disk when attempt 2 starts, and the
kill-switch case asserts today's reset is byte-for-byte restored when
`defaults: retain_on_guard_refusal: false` is set.

### Per-criterion oracles

All 20 acceptance criteria across T01–T04H were re-verified this attempt (0
carried forward — this is the gate's first close). Per-criterion oracle,
`kind`, `state`, exit code and proving SHA are recorded in
`GATE-01-CRITERIA.md`. Every entry reads `state: pass`, `kind: narrow`.
Two entries carry a substituted oracle, disclosed here rather than silently:

**T03#4 — the criterion names a module that does not exist.** WU-03's
criterion 4 is `python3 -m unittest tests.test_files_changed_guard
tests.test_attempt_outcome_contract tests.test_guard_repair_e2e -v` exits 0.
Run literally, it exits 1:

```
$ python3 -m unittest tests.test_files_changed_guard tests.test_attempt_outcome_contract tests.test_guard_repair_e2e -v -b
ERROR: test_files_changed_guard (unittest.loader._FailedTest.test_files_changed_guard)
ModuleNotFoundError: No module named 'tests.test_files_changed_guard'
Ran 8 tests in 0.993s
FAILED (errors=1)
EXIT=1
```

The other seven tests in that run pass; the single error is the import. There
is no file named `test_files_changed_guard*` anywhere in the tree
(`find . -name "test_files_changed_guard*" -not -path "./.git/*"` prints
nothing), so this is not a module the feature deleted — it is a misspelling of
`tests.test_loop_files_changed_guard`, the files-changed guard suite, which
T01#4 names correctly in the same gate and whose docstring reads
"files_changed diff guard — FEAT-2026-0008/T02". With the corrected spelling:

```
$ python3 -m unittest tests.test_loop_files_changed_guard tests.test_attempt_outcome_contract tests.test_guard_repair_e2e -v -b
Ran 24 tests in 3.776s
OK
EXIT=0
```

The regression the criterion was written to make — T03's auto-repair breaks
neither the files-changed guard, nor the outcome-contract doc test, nor the
gate's own oracle — is green. The literal command is not, and cannot be, on
any tree. `GATE-01-CRITERIA.md` records the substituted oracle with the
substitution spelled out in the `oracle:` field.

**T04H#3 — a close session runs no git.** WU-04H's criterion 3 asks what
`git diff --stat` for that unit touched. A dispatched work-unit session runs no
git command (`.specfuse/rules/result-contract.md` §1), so the measurement was
taken from the driver's own record instead: the `attempt_outcome` event for
`FEAT-2026-0103/T04H` at `2026-09-10T10:48:11Z`, `outcome: passed`, carries

```
files_touched: [".specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md",
                ".specfuse/verification.yml.example",
                "specfuse/loop/data/docs/methodology.md"]
```

— exactly the two produced paths plus the WU file the driver itself flips, and
neither `specfuse/loop/data/verification.yml.example` nor `docs/methodology.md`
appears, which is the criterion's "byte-identical to HEAD" half. The mirror
halves were checked directly and both diffs print nothing (T04H#2, exit 0
each).

One further limitation, recorded for honesty rather than substituted: T01#1,
T04#1 and T04H#1 each assert a *red-before* state ("fails on HEAD before this
unit's edits"). A close runs after those edits landed and cannot re-observe the
red half without reverting the tree. This close verified the green half of each
by re-running the named command; the red half rests on the producing attempt's
report and, for T04H#1, on the gate's own broad-run record — the 2026-09-10T02:32Z
`broad_run_result` and the `human_escalation` it raised both name
`test_package_data_matches_canonical` as failing, which is that criterion's
red-before observation made by the driver rather than by an agent.

### Guard-refusal outcomes measured in this gate

Criterion 2 asks for every `attempt_outcome` in this feature's `events.jsonl`
whose `failure_class` is `guard_refusal`, `files_changed_mismatch` or
`produces_not_in_diff`, with its `tree_retained` value and whether the
following attempt passed. Reading all 8 `attempt_outcome` events in
`.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/events.jsonl`:

```
no guard refused an attempt in this gate
```

All three non-passing attempts (all `FEAT-2026-0103/T04H`) carry
`failure_class: tests`, signature `test_package_docs_match_canonical`. No event
in this feature carries an `extras` payload at all, so no `tree_retained` value
was emitted and the feature's first live measurement of itself is empty.

**This is a real result, not a gap in the measurement.** The retain path fires
only on the four bookkeeping guards, and no work unit in this gate tripped one:
every unit that failed, failed its `tests` gate, which keeps today's reset by
design (PLAN.md § *Scope boundary — explicitly OUT*). The feature therefore
ships with its behaviour proved by `tests/test_guard_repair_e2e.py` driving
`loop.run()` end to end, and with zero production observations of itself. The
first of those is a post-merge item, below.

## Cost analysis

Per-WU `planned_cost_usd` from each WU's frontmatter, against the sum of
`cost_usd` over that WU's `attempt_outcome` events in `events.jsonl`.

| WU | planned | actual (events) | delta | attempts |
| --- | ---: | ---: | ---: | --- |
| T01 | 5.00 | 2.593358 | −2.406642 | 1, passed |
| T02 | 3.00 | 1.194540 | −1.805460 | 1, passed |
| T03 | 4.00 | 1.736334 | −2.263666 | 1, passed |
| T04 | 3.00 | 0.591725 | −2.408275 | 1, passed |
| T04H | 1.00 | 1.612077 | +0.612077 | 4 outcomes over 3 dispatches, passed on the last |
| G1-CLOSE | 8.00 | (not yet emitted) | — | this attempt, in flight |
| **substantive total** | **16.00** | **7.728034** | **−8.271966** | |

Feature `planned_cost_usd` is 24.00 (16.00 substantive + 8.00 close); gate
`cost_budget_usd` is 40.00. The close's own `attempt_outcome` is written by the
driver after this session ends, so its actual is not reconcilable from inside
it; that is the one row the reconciliation cannot close, and it is stated
rather than estimated.

**T04H's four outcomes over three dispatches, and why the frontmatter
under-reports it.** T04H is the only WU that cost more than planned. Its
`cumulative_cost_usd` frontmatter field reads 0.998202, but `events.jsonl`
carries 1.612077 across four `attempt_outcome` events:

| when | attempt | outcome | cost | what followed |
| --- | --- | --- | ---: | --- |
| 02:53:52Z | 1 | failed (tests) | 0.241148 | `baseline_attribution`, then `human_escalation: preexisting_gate_failure` |
| 03:15:08Z | 1 | failed (tests) | 0.777625 | attempt counter had restarted after the escalation |
| 03:19:21Z | 2 | failed (tests) | 0.220577 | `human_escalation: spinning_signature_repeat`, `blocked_human` |
| 10:48:11Z | 1 | passed | 0.372726 | after `re_arm_dispatched` ("go, try again") |

`cumulative_cost_usd` is the sum of the second and third rows only — the
02:53Z attempt was dropped when the `preexisting_gate_failure` escalation reset
the unit's attempt counter. The events ledger is the fuller record of what the
unit cost, and the reconciliation above uses it. T04H's 1.00 plan was written
for a mechanical copy-and-sync; it was overspent because its first body named
only one of the two drifts T04 had created (see the failure-class breakdown).

### Failure-class breakdown

Three non-passing attempts, all in `FEAT-2026-0103/T04H`, all one class:

| failure_class | count | failure_signature | cost |
| --- | ---: | --- | ---: |
| `tests` | 3 | `test_package_docs_match_canonical` | 1.239351 |

No `guard_refusal`, `files_changed_mismatch` or `produces_not_in_diff` outcome
occurred (see § *Guard-refusal outcomes measured in this gate*).

Root cause of all three: T04's `produces:` named the package mirror
`specfuse/loop/data/verification.yml.example` rather than the canonical
`.specfuse/verification.yml.example`, so its two documentation edits landed on
opposite sides of the canonical/mirror split. The gate's broad run caught it as
`test_package_data_matches_canonical`. T04H was armed to fix it, but its first
body named only the `verification.yml.example` drift; the *docs* drift
(`test_package_docs_match_canonical`) was invisible to the session, which
repaired what it was told about and was refused by a test it had never been
shown — twice, identically, which is exactly what
`detect_deterministic_refusal_repeat` escalates on. The re-arm that passed did
so because the body was rewritten to name both drifts and both mirrors.

## Consumer-visible contract changes

Four, enumerated for human acknowledgment and appended to `CHANGELOG.md`'s
`Unreleased` section:

1. **added** — `verification.yml` gains an optional `defaults:
   retain_on_guard_refusal` key (default `true`). Setting it `false` restores
   the previous reset at all four guard sites, byte-identically.
2. **changed** — a `deliverable_missing`, `no_deliverable_files`,
   `produces_not_in_diff` or `files_changed_mismatch` refusal now uncommits the
   squash and *keeps* the working tree; the next attempt is dispatched with the
   guard's complaint and the retained diff and asked to repair in place.
3. **added** — `attempt_outcome` events may carry `extras.tree_retained` (on a
   retained guard refusal) and `extras.auto_repaired_files_changed` (on a
   `passed` outcome that dropped untouched non-deliverable paths). Consumers
   that parse `events.jsonl` see two new optional `extras` keys; no outcome
   string was added or removed (`tests/test_attempt_outcome_contract.py`, exit 0).
4. **changed** — a RESULT block naming an untouched path that is *not* in the
   unit's `produces:` no longer costs a dispatch: the driver drops the path,
   records it, and the attempt proceeds as `passed`.

## What the loop did NOT verify

Two items, both `PLAN.md` § *Post-merge checklist* lines, both filed as
post-merge observations rather than acceptance criteria under
`close-discipline.md` §2 because neither is observable inside this gate.

1. **Cross-repository spend share of guard-refusal outcomes.**
   *Criterion:* over the next five features closed in this repo and in the
   generator, count `attempt_outcome` events with `failure_class` in
   `guard_refusal`, `files_changed_mismatch`, `produces_not_in_diff`, sum their
   `cost_usd`, and record the share of feature spend against the review's
   baseline (10% of spend, 323 attempts corpus-wide) plus the mean attempts a
   refused unit needed to pass.
   *Reason not verified in-loop:* it is a measurement over features that do not
   exist yet, in two repositories, and this gate produced zero events of the
   classes being counted — the § *Guard-refusal outcomes* section above is the
   empty first data point, not the measurement.
   *Where it actually gets checked:* the `specfuse:post-merge` issue the driver
   files from this checklist at close, read against `events.jsonl` in this repo
   and in the generator after five more features close.

2. **One real refusal in the generator survives the driver's own bookkeeping
   commit.**
   *Criterion:* confirm on a live refusal in the generator that the retained
   tree survived the driver's bookkeeping commit and that the repair attempt's
   squash carried both the original work and the repair.
   *Reason not verified in-loop:* it requires a genuine guard refusal in
   another repository running this driver build. `tests/test_guard_repair_e2e.py`
   proves the mechanism against a stubbed dispatch and asserts exactly this
   (one squash commit whose diff carries attempt 1's file), but a stub is not a
   live refusal, and PLAN.md § *Scope boundary* puts consumer repositories
   explicitly out of scope for this feature.
   *Where it actually gets checked:* the same `specfuse:post-merge` issue, on
   the first generator run after this release that trips one of the four
   guards.

## Durable lessons

Two, staged to `LEARNINGS-pending.md` in this feature directory rather than
appended to `.specfuse/LEARNINGS.md` — this feature runs
`autonomy_default: auto`, where `assert_learnings_staged_under_auto` forbids
writing the shared file directly:

- A `produces:` naming the mirror side of a canonical/mirror split.
- An arming body that names one drift when the broad run found two.

Both are written out in full in `LEARNINGS-pending.md`.
