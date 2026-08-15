## Gate 1

**Verdict: `blocked`.** Criterion 1's driver-restart precondition failed. Gate 1's
code is complete and every oracle is green, but the central in-situ observation this
close exists to make could not be made, because the driver process that dispatched
this close is the same process that probed gate 1's baseline — it predates `T01`,
`T02` and `T03`. This is **the fourth occurrence** of the hazard this feature exists
to fix, and it fired on the close of the feature that fixes it.

### 1. Driver-restart precondition — FAILED

| Fact | Value |
| --- | --- |
| Dispatching process | PID 50693, `python .specfuse/scripts/loop.py --prepare`, cwd = this repo root |
| Its start time | `Thu Aug  6 22:50:38 2026` EDT = **`2026-08-07T02:50:38+00:00`** |
| This session (its child) | PID 82403, `claude -p --model opus --effort high --output-format json`, started `Fri Aug  7 00:41:15 2026` EDT |
| `T01.started_at` | `2026-08-07T03:54:47.489903+00:00` |
| `T02.started_at` | `2026-08-07T04:08:20.570950+00:00` |
| `T03.started_at` | **`2026-08-07T04:21:20.975561+00:00`** |

The dispatching process predates `T03`'s start by **1 h 30 min 43 s**, and predates
`T01`'s start by 1 h 04 min 09 s — it predates the *entire* gate.

The identification is not an inference from process names. `GATE-01.md`'s frontmatter
records `baseline.probed_at: 2026-08-07T02:50:38.480017+00:00`, which is PID 50693's
start time to the second. The process that probed gate 1's baseline is byte-for-byte
the process that dispatched this close. No restart happened at any point in gate 1.

Consequence: this session is executing the `specfuse.loop.loop` that was cached in
`sys.modules` at `02:50:38`, which contains neither `format_driver_staleness_warning`
(`T02`) nor `format_driver_staleness_summary` (`T03`), and never imported
`specfuse/loop/driver_edit.py` (`T01`) because that file did not exist when the
process imported `loop.py`.

Per criterion 1 and `GATE-01.md` § *Arming discipline*, this is reported as a finding
and the unit emits `status: blocked` rather than reporting a stale observation as a
result.

### 2. The feature-level question — did the warning fire in this dispatch?

**No. Neither half of gate 1 fired, and the answer is corroborated by three
independent surfaces rather than asserted.**

- **The immediate warning (`T02`) did not fire.** No `STALE DRIVER PROCESS:` line
  appears anywhere in this dispatch's output. It could not have: the running process
  has no such function.
- **The gate-completion summary (`T03`) did not fire.** No
  `STALE DRIVER PROCESS (gate summary):` block appears. Gate 1 has not reached
  completion in a process that carries the code, so the call site at `loop.py:6824`
  was never reached by anything that could execute it.
- **The event was never emitted.** This feature's `events.jsonl` holds exactly nine
  events, and **zero** carry `driver_staleness_detected`:

  ```
  2026-08-07T03:54:47.490115+00:00 FEAT-2026-0075/T01 task_started
  2026-08-07T04:08:20.540485+00:00 FEAT-2026-0075/T01 attempt_outcome
  2026-08-07T04:08:20.541146+00:00 FEAT-2026-0075/T01 task_completed
  2026-08-07T04:08:20.571160+00:00 FEAT-2026-0075/T02 task_started
  2026-08-07T04:21:20.947158+00:00 FEAT-2026-0075/T02 attempt_outcome
  2026-08-07T04:21:20.948496+00:00 FEAT-2026-0075/T02 task_completed
  2026-08-07T04:21:20.976195+00:00 FEAT-2026-0075/T03 task_started
  2026-08-07T04:39:12.414096+00:00 FEAT-2026-0075/T03 attempt_outcome
  2026-08-07T04:39:12.414407+00:00 FEAT-2026-0075/T03 task_completed
  ```

  A repo-wide sweep (`grep -rl driver_staleness_detected .specfuse/features/*/events.jsonl`)
  returns nothing: the event type has been added to the schema and has never been
  emitted by any run in this repository.

**What the warning *would* have said, had a restarted driver dispatched this close.**
Both `T02` and `T03`'s `attempt_outcome` payloads record `specfuse/loop/loop.py` in
`files_touched`, and `T01`'s records `specfuse/loop/driver_edit.py`. Feeding those
through the predicate that now exists, all three units are driver-editing, and the
close was dispatched after all three — so a correct run would have printed the `T02`
warning three times (once per squash) and a `T03` gate summary naming `T01`, `T02`
and `T03` as editors with `G1-CLOSE-INTERMEDIATE` dispatched after them.

That reconstruction is exactly what `T03` was built to make unnecessary, and this
close having to perform it by hand — from `ps` output and `started_at` timestamps —
is the precise failure mode `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`
rule (b) names. **It is stated here as a prediction to be confirmed by the next
correctly-restarted run, not as an observation.** Gate 1's central claim is therefore
**unverified in situ**, not refuted: the code is present and unit-tested at the seam,
but no run has ever executed it end-to-end.

### 3. Oracles re-run fresh — all green

Re-run in this session, unsandboxed, exit codes read directly. `code` gate set, all
12 gates:

| Gate | Result | Exit |
| --- | --- | --- |
| `tests` — `python3 -m unittest discover -s tests -v -b` | `Ran 2456 tests in 110.006s` / `OK (skipped=3)` | 0 |
| `lint` — `ruff check specfuse .specfuse/scripts tests scripts` | `All checks passed!` | 0 |
| `security` — `bandit -r specfuse .specfuse/scripts -ll` | `Medium: 0  High: 0` | 0 |
| `coverage` — `coverage run … && coverage report --fail-under=90` | `TOTAL 7839 504 94%` | 0 |
| `leak-scan` — `python3 .specfuse/scripts/leak_scan.py --all` | `leak-scan: clean` | 0 |
| `event-type-gate` — `python3 .specfuse/scripts/event_type_gate.py` | `ok: no validation errors across 54 events.jsonl file(s), 1285 event(s) checked` | 0 |
| `roadmap-link-gate` | `0 error(s), 8 warning(s)` (WARN does not fail by design) | 0 |
| `arm-sweep-gate` | `ok: 15 evaluable feature(s) swept clean` | 0 |
| `monitoring-example-lint` | `OK — monitoring config is structurally valid` | 0 |
| `leak-scan-hook` — `bats tests/leak_scan_hook.bats` | `ok 1..3` | 0 |
| `sync-scaffold-bats` + `sync-scaffold-symlinks-bats` | `ok 1..9`, `ok 1..4` | 0 |
| `init-sh-shim-bats` + `init-skills-bats` + `hookspath-conflict-bats` | `ok 1..5`, `ok 1..1`, `ok 1..4` | 0 |

`T03`'s `event-type-gate` sweep is the one above: 54 `events.jsonl` files, 1285
events, no validation errors — so `driver_staleness_detected` is accepted by the
vendored envelope even though nothing has emitted it.

Symbol-existence imports (`T01#8`, `T02#7`, `T03#10`), each exit 0:

```
$ python3 -c "from specfuse.loop.driver_edit import DRIVER_MODULE_PREFIXES, diff_edits_driver, driver_paths_in, changed_paths_for_commit"
ok ('specfuse/loop/',)
$ python3 -c "from specfuse.loop.loop import format_driver_staleness_warning"   -> ok
$ python3 -c "from specfuse.loop.loop import format_driver_staleness_summary"   -> ok
```

Purity (`T01#6`) and no-cycle (`T01#7`) greps: `specfuse/loop/driver_edit.py`
imports only `subprocess`, used solely at line 44 inside `changed_paths_for_commit`;
`diff_edits_driver` and `driver_paths_in` contain no I/O. The only occurrence of the
string `specfuse.loop.loop` in the module is line 17, a docstring sentence — there is
no import statement, so the cycle `loop.py -> driver_edit.py -> loop.py` is absent.

The three feature test modules, run individually: 14 + 4 + 4 = **22 tests, all OK**.

**Nothing is red.** The composite failure a close exists to catch is not a red oracle
here — it is that every oracle can be green while the feature has never once
executed in the process it was written to change.

### 4. The warning's negative case — and a design finding for gate 2

`DRIVER_MODULE_PREFIXES` is `("specfuse/loop/",)` and both predicates are a bare
`str.startswith` over it. `T01` produced `specfuse/loop/driver_edit.py`, which is
under that prefix, so **`T01` is classified as a driver-editing unit, identically to
`T02` and `T03`.** Stated plainly, as criterion 4 requires: **the predicate treats a
*new* driver module exactly the same as an edit to an existing one**, because it
tests path shape only and has no notion of file existence, newness, or importability.

For a new module that fact is *correct* — a running driver never imported it, so it
is as stale as if it had been edited. But the same insensitivity produces a real
false positive, and it already fired in this gate:

> **Finding for gate 2 (not reconciled here — `never-touch` forbids touching
> `specfuse/`).** `T03`'s `files_touched` includes
> `specfuse/loop/data/schemas/driver-event.schema.json`. That path is under
> `specfuse/loop/` and is therefore flagged as a driver-module edit, but it is a JSON
> data file read from disk at runtime — it is not cached in `sys.modules` and editing
> it does **not** make a running process stale. The module docstring claims detection
> of "the driver's own importable surface"; the prefix is broader than that claim.
> Gate 2 must decide whether to narrow the predicate (e.g. `.py` suffix, or excluding
> `specfuse/loop/data/`) before building a *refusal* on it. Gate 1 is warn-only so a
> false positive costs only noise; a gate-2 refusal keyed on the same predicate would
> block a run over a schema edit.

The negative case proper is verified, though only at the seam and not in a live
dispatch: `test_no_driver_edit_no_warning` (`T02#6`) and
`test_no_driver_edit_no_summary_no_event` (`T03#6`) both pass, driving the real
outcome path with a non-driver diff and asserting silence.

### 5. Deferred-verification list

| Criterion | Why not verified in-loop | Where it actually gets checked |
| --- | --- | --- |
| `T02#4` — warning emitted from the real outcome path immediately after `squash_commit` | The seam test drives the path with a stub; no live driver has executed it. Verified statically (call site `loop.py:6287`) plus the seam test | First gate completion under a driver started after `cbc3b23`. Gate 2's own dispatch is the natural site |
| `T03#5` — summary emitted at gate completion, before the gate flips to `awaiting_review` | Same: seam-verified at `loop.py:6824-6828`, never reached by a live run | As above |
| `T03#7` — `driver_staleness_detected` appended to the feature's `events.jsonl` | Asserted by the seam test against a temp feature dir. Zero such events exist in any real `events.jsonl` repo-wide | The first real gate completion containing a driver-editing unit |
| This close's criterion 2 (composite, in situ) | Criterion 1 failed — the dispatching process cannot execute the code | The re-run of this close under a restarted driver |
| This close's criterion 7 (human acknowledgment of contract changes) | No human is present in this non-interactive dispatch (`claude -p`) | Operator review at gate arming |

Every other acceptance criterion across `T01`–`T03` was verified in-loop this
session; all 31 are recorded `state: pass` in `GATE-01-CRITERIA.md` against
`proved_at_sha: cbc3b23a53d068e9ee5a76488b41bc4cc10f7498`.

### 6. Consumer-visible contract changes (§3) — **human acknowledgment NOT obtained**

Criterion 7 requires blocking on explicit human acknowledgment. This dispatch is
non-interactive, so acknowledgment could not be sought; it is an independent reason
for `blocked`, on top of criterion 1. The enumeration and the `CHANGELOG.md`
`Unreleased` entries are complete and awaiting that acknowledgment.

1. **New importable module `specfuse/loop/driver_edit.py`**, shipped in the wheel.
   Public surface: `DRIVER_MODULE_PREFIXES = ("specfuse/loop/",)`,
   `diff_edits_driver(paths) -> bool`, `driver_paths_in(paths) -> list`,
   `changed_paths_for_commit(sha, repo_root) -> list`. Additive — nothing previously
   occupied the import path. `classified: added`.
2. **New driver output every run may now print**, unprompted, to any consumer's
   console and CI log: a line beginning `STALE DRIVER PROCESS: <WU-ID> edited the
   driver itself (<paths>). …`, emitted immediately after a squash whose diff touches
   `specfuse/loop/`. Anything scraping driver output sees a new line class.
   `classified: added`.
3. **New gate-completion summary block**, emitted at gate completion before the gate
   flips to `awaiting_review`, beginning `STALE DRIVER PROCESS (gate summary):` and
   listing each driver-editing unit and the units dispatched after it.
   `classified: added`.
4. **New event type `driver_staleness_detected`** in
   `specfuse/loop/data/schemas/driver-event.schema.json`'s `event_types`. Every
   downstream project's `events.jsonl` may now carry it. Any consumer that enumerates
   event types, or validates events against a *pinned older* schema copy, must accept
   it. `classified: added`.
5. **Two new public helpers on `specfuse.loop.loop`**:
   `format_driver_staleness_warning(wu_id, driver_paths) -> str` and
   `format_driver_staleness_summary(edits, dispatched_after) -> str`. Both return `""`
   on empty input. `classified: added`.

No removals and no renames. Nothing in gate 1 blocks, refuses, or fails a gate — the
whole gate is warn-only, so no existing run that passed before will fail now.

### 7. Lessons

One entry promoted to `.specfuse/LEARNINGS.md`:
`[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`.
It addresses the question criterion 8 names as the feature's actual thesis — why a
written rule did not prevent three recurrences — with the fourth recurrence, observed
on the close of the feature written to fix it, as its evidence.

Deliberately **not** re-promoted, per criterion 8:
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` and
`[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` — both already
present, and gate 1 was planned against them. That they were present, correct, cited
verbatim in `GATE-01.md`, and still did not prevent occurrence four is precisely the
new entry's subject.

### 8. Incidental findings (reported, not repaired)

- **`events.jsonl` lost this close's cycle.** The log holds nine events, none with a
  `G1-CLOSE-INTERMEDIATE` correlation ID, while the WU's frontmatter reads
  `attempts: 2`. Criterion 5 describes this log as "the only surface that never loses
  a re-armed cycle"; for this gate that is not borne out — a prior attempt of this
  close ran and failed `assert_learnings_appended_or_noop`, and no event records it.
- **The `specfuse-lint` on `PATH` is itself a stale copy.** It resolves to the
  installed wheel at `.venv/lib/python3.14/site-packages/specfuse/loop/lint_closing.py`,
  which lacks the `close-intermediate-f` criteria-state check present in the working
  tree's `specfuse/loop/lint_closing.py`. The closing lint therefore checks a weaker
  contract than the repo declares. Same family as this gate's subject: an installed
  artifact diverging from the source that a session believes it is running.

## Gate 2

**Verdict: `met_locally`.** Gate 2's three producing units are `done`, every oracle
named across both gates re-runs green in this session, the restart precondition that
failed in gate 1 held this time, and the shipped halt would have fired on **all five**
recorded occurrences of the hazard — including this feature's own two. Two things are
not met here and neither is a red oracle: the human acknowledgment `close-discipline.md`
§3 requires cannot be sought from a non-interactive dispatch, and gate 1's central
in-situ observation is *still* unmade — not because the restart failed, but because it
succeeded, which is a finding in its own right (§5 below).

The cost reconciliation this close owes lives under `## Cost analysis`, which follows
this section and now carries both gates.

### 1. Driver-restart precondition — PASSED

| Fact | Value |
| --- | --- |
| Dispatching process | PID 2874, `python3 -u .specfuse/scripts/loop.py --feature FEAT-2026-0075`, cwd = repo root |
| Its start time | `Fri Aug  7 11:50:38 2026` EDT = **`2026-08-07T15:50:38+00:00`** |
| `GATE-02.md` `baseline.probed_at` | `2026-08-07T15:50:38.454866+00:00` — this same process's own probe |
| `T04.started_at` | `2026-08-07T12:06:59.829998+00:00` |
| `T05.started_at` | `2026-08-07T12:24:19.815013+00:00` |
| `T06.started_at` | **`2026-08-07T12:39:59.025188+00:00`** |
| `GATE-01.md` `baseline.probed_at` | `2026-08-07T02:50:38.480017+00:00` |

The dispatching process started **3 h 10 min 39 s after `T06`** and 13 h 00 min 00 s
after gate 1's baseline probe. It postdates every unit it is armed to verify. **The
restart happened.**

Corroborated without relying on `ps`: `specfuse/loop/loop.py`'s mtime is
`2026-08-07T12:48:36+00:00` (written by `T06` mid-attempt) and
`specfuse/loop/driver_edit.py`'s is `2026-08-07T12:07:48+00:00` (written by `T04`).
Both precede this process's import at `15:50:38` and neither file has changed since, so
the process's `sys.modules` holds the post-`T06` code. The `git status` snapshot handed
to this session names this process's own bookkeeping commit —
`89b42cb chore(loop): gate 2 baseline probed clean` — as HEAD.

**This is the first close in this repository's history to pass its own restart check.**
What forced it was occurrence five: `G2-CLOSE`'s first dispatch, three attempts and
$9.32 with no retrospective section produced, from a process that predated `T04`–`T06`
— exactly what `GATE-02-REVIEW.md` § *The one thing gate 2 cannot fix* predicted, and
recorded by the operator in `GATE-02.md` § *Budget re-baseline*.

### 2. Oracles re-run fresh (§1) — all green

Re-run in this session, unsandboxed, from the repo root, exit codes read directly. The
imported package was confirmed to be the working tree and not the installed wheel
(`python3 -c "import specfuse.loop.loop as L; print(L.__file__)"` resolves under
`specfuse/loop/`, not `.venv/lib/.../site-packages/`) — a check `RETROSPECTIVE.md` §8's
stale-wheel finding makes non-optional, and one that caught a wrong-directory first run
of this very batch.

Full `code` gate set, all 15 gates:

| Gate | Result | Exit |
| --- | --- | --- |
| `tests` | `Ran 2481 tests in 114.565s` / `OK (skipped=3)` | 0 |
| `lint` | `All checks passed!` | 0 |
| `security` | `No issues identified.` / 16708 LOC scanned, 0 `#nosec` | 0 |
| `coverage` | `TOTAL 7860 505 94%` (`--fail-under=90`) | 0 |
| `leak-scan` | `leak-scan: clean` | 0 |
| `event-type-gate` | `ok: no validation errors across 54 events.jsonl file(s), 1310 event(s) checked` | 0 |
| `roadmap-link-gate` | `0 error(s), 8 warning(s)` (WARN does not fail by design) | 0 |
| `arm-sweep-gate` | `ok: 15 evaluable feature(s) swept clean, no not_evaluable verdicts` | 0 |
| `monitoring-example-lint` | `OK — monitoring config is structurally valid` | 0 |
| `leak-scan-hook` | `1..3` | 0 |
| `sync-scaffold-bats` | `1..9` | 0 |
| `sync-scaffold-symlinks-bats` | `1..4` | 0 |
| `init-sh-shim-bats` | `1..5` | 0 |
| `init-skills-bats` | `1..1` | 0 |
| `hookspath-conflict-bats` | `1..4` | 0 |

Gate 1's test count was 2456; it is 2481 now — the 25 added are gate 2's three suites
(12 + 9 + 4).

Per-criterion oracles for all 34 of gate 2's acceptance criteria are recorded in
`GATE-02-CRITERIA.md`, each with the command run, its `kind`, and `state: pass`. The
ones worth quoting here:

```
$ python3 -c "from specfuse.loop.driver_edit import is_driver_module_path, DRIVER_DATA_PREFIXES"
ok ('specfuse/loop/data/',)
$ python3 -c "from specfuse.loop.loop import format_driver_restart_halt, HALT_REASON_DRIVER_RESTART, EXIT_DRIVER_RESTART_REQUIRED"
ok
$ python3 -c "... print(repr(H), E, E not in (0,1,2))"
'driver_restart_required' 3 not in 0/1/2: True

$ grep -n 'startswith' specfuse/loop/driver_edit.py
38:        path.startswith(DRIVER_MODULE_PREFIXES)
40:        and not path.startswith(DRIVER_DATA_PREFIXES)

$ grep -n 'changed_paths_for_commit' specfuse/loop/loop.py
103:from .driver_edit import changed_paths_for_commit, driver_paths_in
6393:                            _changed = changed_paths_for_commit(sha, REPO_ROOT)

$ grep -n 'format_driver_restart_halt|_halt_for_driver_restart' specfuse/loop/loop.py
1965:def _halt_for_driver_restart(
1987:    message = format_driver_restart_halt(
2273:def format_driver_restart_halt(
5976:                        return _halt_for_driver_restart(
```

`5976` is inside the `for wu in pending` brake, alongside `_should_halt_for_budget`, and
`squash_commit` begins at `2288` — the halt is at the dispatch seam and not in the
squash block, as `T05#5` / `T06#3` require.

Gate 1's three suites still pass under the narrowed predicate: `Ran 22 tests ... OK`.

### 3. The feature-level question (§1) — is the hazard actually prevented?

#### 3a. Would the halt have fired on the historical occurrences? **Yes — on all of them.**

Answered from each feature's recorded `files_touched` and `task_started` order in its
own `events.jsonl`, run through the *shipped* `is_driver_module_path`, not through a
reimplementation:

| Occurrence | First driver-editing unit and its paths | Units dispatched after it in the same process | Halt fires? |
| --- | --- | --- | --- |
| FEAT-2026-0057 gate 1 | `T01` — `specfuse/loop/prerun.py` | `T02, T03, G1-CLOSE, T04, G1-CLOSE, T05, T06, G1-CLOSE` | **yes**, before the first `G1-CLOSE` |
| FEAT-2026-0056 gate 1 | `T01` — `specfuse/loop/criteria_state.py` | `T02, T03, T04, G1-CLOSE-INTERMEDIATE, G1-PLAN` | **yes** |
| FEAT-2026-0056 gate 2 | `T05` — `criteria_state.py, lint_closing.py, loop.py` | `T06, T07, T08, G2-CLOSE, G2-CLOSE` | **yes**, before the `spinning_detected` escalation |
| FEAT-2026-0075 gate 1 | `T01` — `specfuse/loop/driver_edit.py` | `T02, T03, G1-CLOSE-INTERMEDIATE, G1-PLAN` | **yes** |
| FEAT-2026-0075 gate 2 (occurrence five) | `T04` — `specfuse/loop/driver_edit.py` | `T05, T06, G2-CLOSE` | **yes** |

**No occurrence escapes**, and none escapes narrowly: in every one the halt fires at the
*first* driver-editing unit, several dispatches ahead of the close where the money was
actually lost. `T04`'s narrowing costs nothing here — every path above is a `.py` under
`specfuse/loop/` and outside `data/`, so all five are narrow-positive as well as
broad-positive.

Stated as the criterion asks: **there is no occurrence on which the halt would not have
fired.**

#### 3b. Does it report zero on the correctly-ordered gates now in the tree?

The `GATE-02.md` § *Escalation-predicate satisfiability* sweep, re-run in this session
against the shipped predicate over all feature folders:

```
features=57  gates=90  gates with a driver-editing WU = 42
gates flagged by BROAD prefix specfuse/loop/  : 42
gates flagged by NARROW (.py, excl data/)     : 39
gates flagged ONLY by broad (false positives) : 3
gates with NO driver-module edit at all       : 48

HALT REPORTED ON A GATE WITH NO DRIVER-MODULE EDIT: 0
  the halt predicate IS is_driver_module_path; narrow-negative gates never set the flag.

--- the broad-only (false-positive) gates T04 removes ---
  FEAT-2026-0039 gate 2: data/monitoring-secrets-checklist.md,
                         data/monitoring.overrides.yml.example,
                         data/rules/design-for-diagnosis.md
  FEAT-2026-0040 gate 3: data/workflows/specfuse-monitor.yml
  FEAT-2026-0053 gate 3: data/docs/concepts/adopting-auto-mode.md,
                         data/docs/concepts/autonomy-stop-classes.md,
                         data/docs/methodology.md
```

**Zero halts on gates with no driver-module edit. The shipped control is correctly
scoped**, and the escalation trigger for a mis-scoped control does not fire.

**The discrepancy against the expected 41 / 38 / 3 / 49, explained as `GATE-02.md` §
*Arming discipline* requires.** The counts are 42 / 39 / 3 / 48 — one gate has moved
from the no-driver-edit column into both flagged columns, and the false-positive set is
unchanged at exactly the same three gates. The extra gate is **this feature's own gate
2**: `G1-PLAN` ran its sweep in the same session in which it drafted `WU-04`/`WU-05`/
`WU-06`, so `T04`'s `produces: specfuse/loop/driver_edit.py` and `T05`/`T06`'s
`produces: specfuse/loop/loop.py` were not yet on disk when the sweep read them. Both
FEAT-2026-0075 gates are narrow-flagged now; only gate 1 was then. The delta is the
sweep observing the drafts it produced, not a change in the predicate's behaviour — the
predicate's own numbers (3 broad-only, 0 halts on unflagged gates) are identical.

### 4. Gate 1's deferred-verification list — closed out, and three of four rows are still deferred

`RETROSPECTIVE.md` §5 deferred four rows to "the first gate completion under a driver
started after `cbc3b23`". Gate 2 *is* that dispatch, and the honest answer is that it
cleared one row and could not clear three. Recorded here as still-deferred with named
sites rather than dropped.

| Row | Did gate 2's dispatch observe it? | Evidence |
| --- | --- | --- |
| `T02#4` — the immediate warning emitted from the real outcome path right after `squash_commit` | **Not observable from any durable surface.** | `T04`'s squash touched `specfuse/loop/driver_edit.py` and `T05`/`T06`'s touched `loop.py`, so the warning almost certainly printed. But `format_driver_staleness_warning` only `print()`s — it writes no file and emits no event — and the driver's stdout for that run went to the operator's terminal with no log on disk. `grep -rln "STALE DRIVER PROCESS" .specfuse/features/` returns only three prose files (`GATE-02.md`, `WU-90-gate-2-close.md`, this file). **There is nothing to quote, and reconstructing it from dispatch order is precisely what `T03` exists to make unnecessary.** Still deferred. |
| `T03#5` — the summary emitted at gate completion, before the gate flips to `awaiting_review` | **No, and it structurally cannot be — see §5.** | Gate 2 has not reached completion; when it does, this process's `driver_edits` list is empty, because the units that edited the driver were squashed by the *previous* process. The summary is therefore silent by construction on any gate that correctly restarts. Still deferred, with a newly named site. |
| `T03#7` — `driver_staleness_detected` appended to the feature's `events.jsonl` | **No.** | `grep -rl driver_staleness_detected .specfuse/features/*/events.jsonl` still returns nothing; exit 1. Zero such events exist anywhere in this repository, in gate 2's own log included. Same structural reason as the row above. Still deferred. |
| Gate 1's own composite criterion 2 (in situ) | **Partly — and only in a harness, not in a live dispatch.** | `T06`'s seam test `test_final_unit_driver_edit_does_not_halt` drives the **real run loop** and asserts `"STALE DRIVER PROCESS (gate summary):" in output` at gate completion — so `T03`'s code is now proven to execute end-to-end through the driver's own dispatch path, not merely through its formatter. That is strictly more than gate 1 could show. It is still a temp-dir harness rather than this repository's own dispatch. **Upgraded from "never executed" to "executed under the real run loop in a harness"; not upgraded to "observed in a live repository run."** |

The one row this close *can* mark cleared in a live process is not on gate 1's list at
all: **the restart itself** (§1). That is the precondition all four rows were waiting
on, and it held.

### 5. Design finding — the gate summary is silent in exactly the runs the feature makes correct

Not a defect in any acceptance criterion, and reported rather than repaired
(`never-touch` forbids touching `specfuse/` here).

`driver_edits` is accumulated at the squash site (`loop.py:6398`) and read at gate
completion (`loop.py:6934`). It is **per-process**, not per-gate. Once `T06`'s halt is
live, any gate that edits the driver stops at the first such unit; the operator starts a
fresh process; that process finishes the gate with `driver_edits == []` and therefore
prints no summary and emits no `driver_staleness_detected` event.

So `T03`'s gate summary and its event now fire in exactly two cases: a gate whose
**final** unit edits the driver (nothing left pending, no halt — `T06#5`'s asserted
path), and a run on a driver too old to carry `T06`. **In the correctly-operated case
the control this feature ships suppresses the diagnostic the previous gate shipped.**

That is arguably right — a halt that names the unit, the paths, the remaining units and
the resume command carries strictly more information than a gate-end summary, and the
halt's own `driver_staleness_detected` event (with `halted: true`) is the durable
record. But it means gate 1's `T03` is now largely dead code on the happy path, and no
artifact said so before this one. Routed as a follow-up below.

### 6. Consumer-visible contract changes (§3) — **human acknowledgment NOT obtained**

`close-discipline.md` §3 requires blocking on explicit human acknowledgment of this
list. This dispatch is non-interactive (`claude -p`), so it cannot be sought. The
enumeration is complete and every item is appended to `CHANGELOG.md`'s `Unreleased`
carrying `FEAT-2026-0075`; the verdict is hedged to `met_locally` so the driver leaves
gate 2 `awaiting_review` and `PLAN.md` `active`, which puts the list in front of the
operator rather than past them. The follow-up record below carries it as
`kind: acceptance-discharged`.

**Gate 1's five items (§6 above) stand unchanged except where noted.** Restated rather
than copied forward:

1. **`specfuse/loop/driver_edit.py` — new importable module. `classified: added`, but
   its public surface is *not* what gate 1 enumerated.** `T04` changed it: see item 6.
2. **The `STALE DRIVER PROCESS:` warning line.** Unchanged in shape. Its *trigger* is
   narrowed by item 6 — a path under `specfuse/loop/data/` no longer produces it.
3. **The `STALE DRIVER PROCESS (gate summary):` block.** Unchanged in shape, and
   unchanged as a contract. Its practical reachability is changed by item 8 — see §5.
4. **The `driver_staleness_detected` event type.** `classified: added` in gate 1; `T05`
   **adds five payload keys to it** — see item 7.
5. **`format_driver_staleness_warning` / `format_driver_staleness_summary` on
   `specfuse.loop.loop`.** Unchanged.

**Gate 2's items:**

6. **`T04` narrows an already-shipped predicate. `classified: changed`, and a path that
   warned in gate 1 is silent after gate 2.** `diff_edits_driver(paths)` and
   `driver_paths_in(paths)` were a bare `str.startswith(("specfuse/loop/",))`; they now
   delegate to a new `is_driver_module_path(path)`, which additionally requires the path
   to end in `.py` and to *not* start with the new `DRIVER_DATA_PREFIXES =
   ("specfuse/loop/data/",)`. Concretely: `driver_edit.diff_edits_driver(
   ["specfuse/loop/data/schemas/driver-event.schema.json"])` returned `True` on the
   gate-1 wheel and returns `False` now, and the same flips for every file under
   `specfuse/loop/data/` — docs, templates, schemas, example configs, workflows, and a
   hypothetical `.py` payload under `data/`. Measured blast radius across this
   repository: 3 of 42 flagged gates go silent. Any downstream consumer that imported
   these helpers to answer "does this diff touch the driver directory" gets a different
   answer for data paths and should switch to a prefix test of its own. **New public
   names:** `is_driver_module_path`, `DRIVER_DATA_PREFIXES`. `DRIVER_MODULE_PREFIXES` is
   unchanged.
7. **`T05` adds five keys to the `driver_staleness_detected` payload, and two new public
   names on `specfuse.loop.loop`. `classified: added`.** The event is emitted from a
   second site (the halt) with `wu_id`, `driver_paths`, `halted: true`,
   `reason: "driver_restart_required"`, `remaining_wu_ids` and `resume_command`. The
   gate-completion site's payload (`edits`, `dispatched_after`) is unchanged, so a
   consumer must now branch on `halted` rather than assume one shape. `event_type_gate`
   passes with no schema edit (`1310 event(s) checked`, exit 0). New public names:
   `format_driver_restart_halt(wu_id, driver_paths, remaining_wu_ids, resume_command)`
   and `HALT_REASON_DRIVER_RESTART = "driver_restart_required"`.
8. **`T06` can stop a driver run mid-gate, and the process exits `3`.
   `classified: breaking`. This is a breaking change.** Stated plainly, without
   softening:
   - **Any downstream project whose gate edits `specfuse/loop/*.py` now needs two
     invocations of the driver instead of one.** When a work unit's squash touches the
     driver's importable surface and the gate still has units pending, the run stops
     before the next dispatch. It was previously a run that completed the gate.
   - **A new exit status appears: `EXIT_DRIVER_RESTART_REQUIRED = 3`.** Any script, CI
     job, wrapper or cron that reads the driver's exit code sees a value that did not
     exist before. `0` (success), `1` (budget/escalation halts) and `2` (unarmed drafts)
     were the whole vocabulary; a caller treating "non-zero" as "failed" will now report
     a failure for a run that stopped deliberately and lost nothing.
   - **What an operator who hits it should do.** Nothing is broken and nothing is lost.
     The halt flips **no** gate status and **no** work-unit status: the gate stays
     `open`, every remaining unit stays `pending`, and the unit that triggered it is
     already `done` with its `task_completed` event written. The halt message names the
     unit, the driver paths it edited, every work unit left pending, and the exact
     resume command. Stop the driver, start a fresh process, and re-run that command;
     the run picks up at the same unit it was about to dispatch. Expect this once per
     driver-editing gate. There is deliberately **no opt-out flag** — `GATE-02.md` §
     *Flag-scope table* records why: an opt-out is a control a human can forget, which
     is the failure this feature exists to remove.
9. **No removals and no renames across either gate.** No work-unit status, feature
   status or gate status vocabulary is added: `VALID_TYPES`, `VALID_STATUS`,
   `MODEL_BY_TYPE`, `EFFORT_BY_TYPE`, `GATES_FOR_TYPE`, `CLOSING_ASSERTIONS_BY_TYPE` and
   `POST_PASS_INVARIANTS_BY_TYPE` all read exactly their pre-existing members, checked
   by import in this session. Reported as observed values rather than as a diff: this
   session may not run `git`, so "no new entry was added" is evidenced by the absence of
   any halt or restart vocabulary in those tables, not by a diff hunk.

### 7. Lessons

Two entries promoted to `.specfuse/LEARNINGS.md`:
`[FEAT-2026-0075/G2-CLOSE/a-control-closes-the-loop-a-diagnostic-cannot-close-its-own]`
and `[FEAT-2026-0075/G2-CLOSE/a-control-retires-the-diagnostic-that-reported-it]`.
The first answers the question `PLAN.md` posed as the feature's thesis — whether the
gate-2 control actually closed the loop that
`[FEAT-2026-0075/G1-CLOSE-INTERMEDIATE/a-rule-a-human-must-execute-is-not-a-control]`
opened — and it carries the negative case, because gate 2's own arming still needed a
manual restart that no shipped code could enforce. The second is the §5 finding, which
generalizes past this feature: a control that prevents a hazard silently retires the
diagnostic that used to report it, and nothing notices unless the close says so.

Deliberately **not** re-promoted:
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`,
`[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` and gate 1's own entry
— all three are present, correct, and were consumed by this gate's planning.

### What the loop did NOT verify

No predecessor auto-close debt markers exist in this feature
(`grep -rn "specfuse:autoclose-debt"` over the feature folder returns nothing, exit 1),
so `close-g` has nothing to reconcile.

| Criterion | Why not verified in-loop | Where it actually gets checked |
| --- | --- | --- |
| `T04#1`, `T05#1`, `T06#1` — the red-test half ("fails on HEAD **before** this WU's edits") | The edits are landed; the test cannot be re-run against a tree that no longer exists without `git`, which this session may not use. The half that *is* re-runnable — the test exists and passes now — was re-run and is recorded `state: pass` in `GATE-02-CRITERIA.md` | The producing WU's own RESULT and the driver's red-test guard at the time each unit ran |
| `T02#4` — the immediate warning fired in a live dispatch | It only `print()`s; no durable surface records it and no driver log exists on disk | A live gate whose driver-editing unit is followed by another unit, on a driver carrying `T06`: the halt's `driver_staleness_detected` event (`halted: true`) is the durable proof, and it lands in `events.jsonl` |
| `T03#5`, `T03#7` — gate summary and its event at gate completion | Structurally unreachable on a correctly-restarted gate (§5); reachable only when the gate's **final** unit edits the driver | The first gate in any project whose last work unit edits `specfuse/loop/*.py`. Asserted today only through `T06`'s harness test `test_final_unit_driver_edit_does_not_halt` |
| Gate 1's composite criterion 2 (in situ, in this repository) | The observation requires a live dispatch of the previous gate's code, and gate 2's own dispatches are spent | Any downstream project's next driver-editing gate |
| Criterion 8 — human acknowledgment of the contract-change list | No human is present in a `claude -p` dispatch | Operator review at the `awaiting_review` gate boundary, or `/accept-hedged-close` |
| `T05#11` — "no new entry is **added**" as a diff | This session may not run `git`, so the delta cannot be shown | The gate's own `code` set and the observed table membership above; a reviewer with `git` can confirm in one command |

### Failure-class breakdown

Gate 2's three substantive work units each passed on attempt 1, so the guard's own
scope — substantive-WU failures, excluding this close's attempts — is empty. Recorded
here in full anyway, because a $9.32 loss that the guard deliberately excludes is still
this gate's most expensive event:

| failure_class | non-passed attempts | scope |
|---------------|---------------------|-------|
| (none) | 0 | substantive WUs `T04`, `T05`, `T06` — the guard's scope |
| `closing_deliverable_missing` | 3 | `G2-CLOSE`'s own first dispatch ($9.32), excluded from the guard per issue #145 |
| **total in guard scope** | **0** | — |

All three `G2-CLOSE` attempts failed the same three assertions —
`assert_learnings_appended_or_noop`, `assert_doc_or_roadmap_diff`,
`assert_verdict_well_formed` — and touched only `GATE-02-CRITERIA.md`. That is the
signature of a close dispatched into a process that could not run the code it was armed
to observe: it produced per-criterion state and nothing else, three times.

## Hedged-verdict follow-up record

### Human acknowledgment of the consumer-visible contract-change list

- **criterion (verbatim):** "**Consumer-visible contract changes (§3).** Enumerate every
  addition, removal, or rename across both gates, block on explicit human
  acknowledgment, and append each item to `CHANGELOG.md`'s `Unreleased` carrying
  `FEAT-2026-0075`."
- **why it is unverifiable here:** the enumeration and the `CHANGELOG.md` appends are
  done (§6). The acknowledgment is a human act and this is a non-interactive `claude -p`
  dispatch; there is no one to ask and no surface on which consent could be recorded by
  this session without fabricating it. Gate 1 hit the same wall and left the list
  awaiting the same signature.
- **exact re-run condition that would upgrade the verdict:** an operator reads §6 —
  specifically item 8, the breaking mid-gate halt and exit code `3` — and accepts it,
  either at the `awaiting_review` gate boundary or through `/accept-hedged-close`.
- **kind:** `acceptance-discharged`

### Gate 1's central claim, observed in a live repository dispatch

- **criterion (verbatim):** "**Gate 1's deferred-verification list is closed out.**
  `RETROSPECTIVE.md` §5 lists four rows deferred to 'the first gate completion under a
  driver started after `cbc3b23`' — `T02#4`, `T03#5`, `T03#7`, and gate 1's own
  composite criterion 2."
- **why it is unverifiable here:** the list is closed out as the criterion requires —
  every row is stated, with evidence, and three are recorded still-deferred with named
  sites (§4). What cannot be produced is the underlying observation. `T02`'s warning
  writes to stdout only and no log survives; `T03`'s summary and event are structurally
  unreachable on a gate that restarted correctly (§5). This is
  `[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]` landing a second
  time: the restart bought a truthful close, not the missing observation.
- **exact re-run condition that would upgrade the verdict:** the next driver-editing
  gate in any project running on a driver that carries `T06`. Its halt writes a
  `driver_staleness_detected` event with `halted: true` into that feature's
  `events.jsonl` — a durable artifact, unlike a printed line — and that event is the
  observation gate 1 could never make. For `T03`'s summary specifically: a gate whose
  **final** work unit edits `specfuse/loop/*.py`.
- **kind:** `externally-verifiable-later`

### `T03`'s gate summary is dead on the happy path

- **criterion (verbatim):** "`T03#5` — summary emitted at gate completion, before the
  gate flips to `awaiting_review`" and "`T03#7` — `driver_staleness_detected` appended to
  the feature's `events.jsonl`" (`RETROSPECTIVE.md` §5, carried into this close's
  criterion 4).
- **why it is unverifiable here:** §5 — `driver_edits` is per-process, so a gate that
  restarts as this feature now requires reaches completion with an empty list. The
  criterion is not failing; the code path is unreachable in the case the feature makes
  correct. Repairing it is forbidden to this close (`never-touch` on `specfuse/`) and
  would be a design change, not a fix.
- **exact re-run condition that would upgrade the verdict:** a decision, then a feature.
  Either accept that the halt's event supersedes the summary and retire `T03`'s
  gate-completion path, or make `driver_edits` per-gate by rehydrating it from the
  gate's `events.jsonl` at completion so a restarted process still reports what the gate
  did. Neither belongs in a close.
- **kind:** `routed-finding`

### Follow-ups `GATE-02-REVIEW.md` deliberately did not build

Carried forward verbatim from `GATE-02-REVIEW.md` § *Deferred with a home* rather than
re-derived, per criterion 7.

- **criterion (verbatim):** the five rows of `GATE-02-REVIEW.md` § *Deferred with a
  home* — (1) `/attention` and `gate-status` rendering a halted run as "awaiting driver
  restart — re-run `<cmd>`"; (2) an advisory arm-time class reporting "this gate will
  halt mid-way, budget for two invocations"; (3) driver re-exec instead of
  halt-and-resume; (4) `specfuse-lint` on `PATH` resolving to a stale installed wheel;
  (5) `events.jsonl` losing a re-armed closing cycle.
- **why it is unverifiable here:** none of the five is built, by design, and each was
  rejected with reasoning at plan time. Row (5) is the one this close *can* answer, and
  it did — see `## Cost analysis`; the divergence did not recur and gate 1's report of
  it was an artifact of reading the log mid-flight. Row (4) recurred and was worked
  around rather than fixed: this session's first oracle batch resolved
  `specfuse.loop.loop` to the installed wheel and produced 14 spurious red results
  before the run was repeated from the repo root. Rows (1)–(3) remain unbuilt.
- **exact re-run condition that would upgrade the verdict:** each row's named home in
  `GATE-02-REVIEW.md` — its own roadmap row, or the next `/attention` feature. Row (3)
  only if halt-and-resume proves insufficient in practice.
- **kind:** `routed-finding`

## Cost analysis

### Per-unit reconciliation against `planned_cost_usd`

| WU | Planned | Actual | Δ | % of plan |
| --- | ---: | ---: | ---: | ---: |
| `T01` | $2.50 | $1.175409 | −$1.324591 | 47.0% |
| `T02` | $3.50 | $1.440831 | −$2.059169 | 41.2% |
| `T03` | $3.00 | $2.779493 | −$0.220507 | 92.6% |
| `G1-CLOSE-INTERMEDIATE` | $4.50 | not stamped (`attempts: 2`, no `cost_usd`) | — | — |
| `G1-PLAN` | $6.00 | not dispatched | — | — |
| **Producing units (`T01`–`T03`)** | **$9.00** | **$5.395733** | **−$3.604267** | **60.0%** |
| **Gate total planned** | **$19.50** | — | — | — |

Against the gate's **$25.50** budget: $5.395733 spent by the producing units, 21.2%
of budget consumed with the two closing units still to run. The gate's planned sum
($19.50) sits $6.00 under budget, i.e. one full `G1-PLAN`'s worth of headroom for
re-attempts — which this close's second attempt is now drawing on.

All three producing units came in under plan, `T01` and `T02` at well under half.
That is the expected shape for units whose work is a small pure module and a
single call site, and it is not a signal of hollow work: `T01` produced 14 tests,
`T02` and `T03` four each, all passing.

### Independent recomputation from `events.jsonl`

Summing `payload.cost_usd` over the three `task_completed` events:

```
T01  1.175409
T02  1.440831
T03  2.779493
---------------
     5.395733
```

**The two totals agree exactly: $5.395733 from the WU frontmatter stamps, $5.395733
from `events.jsonl`.** No divergence between the surfaces for the producing units —
each unit ran a single attempt (`attempts: 1`, `re_arm_count: 0` throughout), so
there is no re-armed cycle for either surface to lose.

**But the agreement is weaker evidence than it looks, and one divergence is real.**
Both surfaces are blind to this close's own spend: the frontmatter carries no
`cost_usd` and `events.jsonl` carries no event at all for
`G1-CLOSE-INTERMEDIATE`, despite `attempts: 2`. So neither number is a gate total —
both are producing-unit subtotals, and the true gate spend is $5.395733 *plus* an
unrecorded amount for this close's first, failed attempt. The premise that
`events.jsonl` is the surface that never loses a re-armed cycle does not hold for
this gate; here it lost the entire close.

### Gate 2 — per-unit reconciliation against `planned_cost_usd`

| WU | Planned | Actual | Δ | % of plan |
| --- | ---: | ---: | ---: | ---: |
| `T04` | $2.00 | $1.260218 | −$0.739782 | 63.0% |
| `T05` | $3.00 | $2.894009 | −$0.105991 | 96.5% |
| `T06` | $2.50 | $7.904370 | **+$5.404370** | **316.2%** |
| `G2-CLOSE` (first dispatch, 3 attempts) | $5.00 | $9.317808 | +$4.317808 | 186.4% |
| **Gate 2 total** | **$12.50** | **$21.376405** | **+$8.876405** | **171.0%** |

`T06` and `G2-CLOSE`'s first dispatch account for **$9.72 of the $8.88 overrun** — the
other two units came in under plan and partly offset it. Both overruns are already
diagnosed in `GATE-02.md` § *Budget re-baseline*, and this close confirms both figures
independently from `events.jsonl`. Neither is evidence the estimates were wrong across
the board: `T05`, the unit `GATE-02-REVIEW.md` called the largest of the three, landed
at 96.5% of plan.

The costs of this close's own current attempt are in neither surface yet — the driver
stamps them after the session ends — so every gate-2 figure here is a floor.

### Both gates, and the feature against `PLAN.md`

| Scope | Planned | Actual (through `G2-CLOSE` attempt 1's dispatch) | Δ | % of plan |
| --- | ---: | ---: | ---: | ---: |
| Gate 1 | $19.50 | $15.955562 | −$3.544438 | 81.8% |
| Gate 2 | $12.50 | $21.376405 | +$8.876405 | 171.0% |
| **Feature** | **$32.00** | **$37.331966** | **+$5.331966** | **116.7%** |

Against the declared budgets rather than the plans: gate 1 spent 62.6% of its $25.50;
gate 2 spent 122.2% of its **original** $17.50 — which is what the brake caught — and
69.0% of the $31.00 the operator re-baselined it to, leaving $9.62 of headroom for this
close. Reported against both figures as `GATE-02.md` § *Budget re-baseline* requires:
**the gate overran the number it was planned against, and the brake fired correctly at
`spent $21.3764 >= budget $17.5000` before dispatching anything.**

### Independent recomputation from `events.jsonl` — the two surfaces agree exactly

Summing `payload.cost_usd` over every `attempt_outcome` event, all attempts, both gates:

```
T01                      1  passed                        1.175409
T02                      1  passed                        1.440831
T03                      1  passed                        2.779493
G1-CLOSE-INTERMEDIATE    1  closing_deliverable_missing    1.110404
G1-CLOSE-INTERMEDIATE    2  passed                        3.628914
G1-PLAN                  1  passed                        5.820510
                                                 gate 1: 15.955562
T04                      1  passed                        1.260218
T05                      1  passed                        2.894009
T06                      1  passed                        7.904370
G2-CLOSE                 1  closing_deliverable_missing    1.892973
G2-CLOSE                 2  closing_deliverable_missing    4.201394
G2-CLOSE                 3  closing_deliverable_missing    3.223441
                                                 gate 2: 21.376405
                                                  total: 37.331966
```

Summing `cost_usd` over the nine work-unit frontmatter stamps gives **$37.331966** — the
same figure to the cent.

### Did gate 1's `events.jsonl` divergence recur in gate 2? No — and gate 1's report of it was an artifact

**It did not recur, and the gate-1 finding does not survive re-reading the log.** Gate 1's
§8 recorded that `events.jsonl` held nine events with no `G1-CLOSE-INTERMEDIATE`
correlation ID while that WU's frontmatter read `attempts: 2`, and concluded the log
"lost the entire close". The log now holds **both** of that close's `attempt_outcome`
events — `1 closing_deliverable_missing $1.110404` and `2 passed $3.628914`, summing to
exactly the `$4.739318` its frontmatter carries. Nothing was lost.

What gate 1 actually observed was **its own attempt reading the log from inside that
attempt**: the driver flushes an `attempt_outcome` after the session it describes ends,
and the between-attempt `git reset --hard` had rolled the file back to its last
committed state. A close reporting on its own cycle from `events.jsonl` is reading a
surface that cannot yet contain it. That is a real trap and worth keeping — but it is a
read-time artifact, not a lost write, and gate 1's stronger claim should not be carried
forward.

**One divergence is real, and it runs the other way.** `G2-CLOSE`'s frontmatter reads
`attempts: 1` while `events.jsonl` holds **three** `attempt_outcome` events for it: the
operator's re-arm (`23bb642 chore(loop): re-arm G2-CLOSE against a driver carrying
T04-T06`) reset the counter. Its `cost_usd: 9.317808` survived and matches the three
events to the cent, so no money is hidden — but **the frontmatter's `attempts` field
undercounts a re-armed unit and `events.jsonl` does not.** For attempt counting the log
is authoritative; for cost either surface works. This is the row
`GATE-02-REVIEW.md` § *Deferred with a home* asked this close to check, answered.

## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Operator's reason, verbatim:** *"The next feature touching the driver will allow us to
test it"*

**Recorded:** 2026-08-08T11:20:42Z, via `/accept-hedged-close`.

**Computed ceiling at acceptance:** `rework exists` — entry 2 carries
`externally-verifiable-later`, naming the next driver-editing gate under a `T06`-carrying
driver as the condition. The operator's reason answers that condition directly: the
acceptance ships the measurement forward rather than staging it here.

**No mid-flight re-baseline.** The roadmap row's `**Why.**` / `**Goal.**` /
`**Benefits.**` paragraphs are unchanged since `1439a67` (the scaffold commit) — the
only commit on this branch touching `.specfuse/roadmap.md`. The operator accepted the
business case they approved at `/pick-feature` time.

**These follow-ups remain OPEN.** Accepting the hedge ships the feature with them
outstanding; it does not resolve, discharge, or close any of them, except where the kind
itself makes acceptance the discharge (entry 1). Carried forward verbatim from
§ *Hedged-verdict follow-up record* above.

### Carried forward — 1. Human acknowledgment of the consumer-visible contract-change list

**kind:** `acceptance-discharged`

**Criterion, verbatim:** *"**Consumer-visible contract changes (§3).** Enumerate every
addition, removal, or rename across both gates, block on explicit human acknowledgment,
and append each item to `CHANGELOG.md`'s `Unreleased` carrying `FEAT-2026-0075`."*

**Status at acceptance.** Discharged BY this acceptance — that is what
`acceptance-discharged` means. The enumeration and the `CHANGELOG.md` appends were
complete before acceptance (§6). The full list was quoted to the operator before the
reason was given, with **item 8 — the breaking mid-gate halt and exit code `3`** —
called out as the item needing a real decision rather than a nod: after upgrade, a
driver in any downstream project can stop a run partway through a gate. The operator
confirmed having read all four entries.

### Carried forward — 2. Gate 1's central claim, observed in a live repository dispatch

**kind:** `externally-verifiable-later`

**Criterion, verbatim:** *"**Gate 1's deferred-verification list is closed out.**
`RETROSPECTIVE.md` §5 lists four rows deferred to 'the first gate completion under a
driver started after `cbc3b23`' — `T02#4`, `T03#5`, `T03#7`, and gate 1's own composite
criterion 2."*

**Re-run condition named by the close, verbatim:** *"the next driver-editing gate in any
project running on a driver that carries `T06`. Its halt writes a
`driver_staleness_detected` event with `halted: true` into that feature's `events.jsonl`
— a durable artifact, unlike a printed line — and that event is the observation gate 1
could never make. For `T03`'s summary specifically: a gate whose **final** work unit
edits `specfuse/loop/*.py`."*

**Status at acceptance: OPEN, and this is the feature's headline open item.**
`driver_staleness_detected` has fired **zero** times across the entire repository. The
mechanism is built, tested at the seam, and unexecuted. The operator's reason routes the
measurement to the next driver-touching feature. Note the asymmetry that makes this
acceptable: gate 1's observation was ephemeral (stdout, no log survived), while the
condition above produces a **durable event**, so the next occurrence records itself
rather than needing someone to be watching.

### Carried forward — 3. `T03`'s gate summary is dead on the happy path

**kind:** `routed-finding`

**Criterion, verbatim:** *"`T03#5` — summary emitted at gate completion, before the gate
flips to `awaiting_review`" and "`T03#7` — `driver_staleness_detected` appended to the
feature's `events.jsonl`"*

**Why it is unmet, verbatim:** *"`driver_edits` is per-process, so a gate that restarts
as this feature now requires reaches completion with an empty list. The criterion is not
failing; the code path is unreachable in the case the feature makes correct."*

**Re-run condition named by the close, verbatim:** *"a decision, then a feature. Either
accept that the halt's event supersedes the summary and retire `T03`'s gate-completion
path, or make `driver_edits` per-gate by rehydrating it from the gate's `events.jsonl` at
completion so a restarted process still reports what the gate did. Neither belongs in a
close."*

**Tracking surface: NOT NAMED at acceptance.** The operator acknowledged the entry and
did not answer the tracking prompt, which `/accept-hedged-close` treats as non-blocking.
Recorded as unanswered rather than assigned a home this record would be inventing. **This
finding is currently untracked outside this retrospective**, and the decision it needs —
retire the path, or rehydrate `driver_edits` per-gate — is an operator call that no other
surface holds.

### Carried forward — 4. Follow-ups `GATE-02-REVIEW.md` deliberately did not build

**kind:** `routed-finding`

**Criterion, verbatim:** *"the five rows of `GATE-02-REVIEW.md` § *Deferred with a home*
— (1) `/attention` and `gate-status` rendering a halted run as 'awaiting driver restart —
re-run `<cmd>`'; (2) an advisory arm-time class reporting 'this gate will halt mid-way,
budget for two invocations'; (3) driver re-exec instead of halt-and-resume; (4)
`specfuse-lint` on `PATH` resolving to a stale installed wheel; (5) `events.jsonl` losing
a re-armed closing cycle."*

**Status per row at acceptance, from the close's own record.** Row (5) answered here —
the divergence did not recur. **Row (4) recurred and was worked around rather than
fixed**: this session's first oracle batch resolved `specfuse.loop.loop` to the installed
wheel and produced **14 spurious red results** before the run was repeated from the repo
root. Rows (1)–(3) remain unbuilt, each rejected with reasoning at plan time.

**Tracking surface: NOT NAMED at acceptance**, same as entry 3 and recorded the same way.
Each row's named home in `GATE-02-REVIEW.md` § *Deferred with a home* remains the
pointer, but no roadmap row or issue was created. **Row (4) is the one that has now cost
real time twice** — it is the same failure family as this feature's own subject, an
installed artifact diverging from the source a session believes it is running, and
nothing owns it.

### What this acceptance does and does not settle

Settled: the feature ships. Its nine work units are done, its contract changes are
enumerated and acknowledged, and its cost is reconciled ($45.55 actual against $32.00
planned, with gate 2's budget re-baselined $17.50 → $31.00 by operator decision and
recorded in `GATE-02.md` § *Budget re-baseline*).

Not settled, and worth stating so a later reader does not infer otherwise: the feature's
benefit has never been observed. Entry 2 is the open measurement; entries 3 and 4 are
untracked findings that will evaporate if nobody gives them a home.
