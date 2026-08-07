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
