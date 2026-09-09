# Follow-ups — FEAT-2026-0109

> **Both entries below are closed.** `FEAT-2026-0109/T09` was drafted from this
> file and landed on 2026-09-09; the re-armed `G3-CLOSE` re-ran both probes in
> its own session and both re-run conditions are satisfied — the evidence is in
> `RETROSPECTIVE.md` § *The two bullets T09 moved, against `FOLLOW-UPS.md`'s
> re-run conditions*, and each entry carries a **Closed by** line below. The
> entries and their `### ` headings are left verbatim: they are what issues
> **#3270** and **#3271** were filed from, and rewriting a heading would break
> the driver's deduplication against those issues.

Written by `FEAT-2026-0109/G3-CLOSE`, attempt 1, per `close-discipline.md` §2.
That attempt's verdict was `not_met`; two of `GATE-03.md`'s seven
definition-of-done bullets were not satisfied. One entry per failed criterion,
each carrying the criterion verbatim, the command run and its exit code, and the
condition whose re-run would satisfy it. The driver files one tracked
`specfuse:follow-up` issue per entry.

### A pinned run prints the pre-T08 halt text at the point it declines to halt

**Criterion (verbatim, `GATE-03.md` § Definition of done):** "**The cost is
stated at the moment it is incurred.** A driver change landed by a unit takes
effect at the **next run**, not at this gate's close. The driver says so, in
words, at the point where it declines to halt — an operator must never have to
infer from silence which build verified their gate."

**Command run, and its result.** Drove the gate oracle's own pinned-driver
scenario as a subprocess and read its stdout — the surface no test in the gate
reads, because `GATE-03.md` binds the oracle to assert only on the exit code and
`events.jsonl`:

```
python3 - <<'EOF'          # exit 0
import sys; sys.path.insert(0, ".")
from tests import test_installed_copy_driver_e2e as m
C = m.PinnedRunRecordsAndSurvivesDriverEdits
C.setUpClass()
print("RETURNCODE:", C.proc.returncode)      # -> 0
print(C.proc.stdout)
C.tearDownClass()
EOF
```

Observed on stdout of the **pinned** run, at the squash seam:

```
STALE DRIVER PROCESS: FEAT-2026-8801/T01 edited the driver itself
(specfuse/loop/loop.py). This process cached the pre-edit versions of those
modules at import time, so every work unit dispatched next in this process —
including any close — will execute the OLD code, not what FEAT-2026-8801/T01
just wrote. A fresh driver process is required before any close can verify this
change: stop this driver now and start a new one before dispatching the next
work unit.
```

and, at gate completion:

```
STALE DRIVER PROCESS (gate summary):
  - FEAT-2026-8801/T01 edited the driver: specfuse/loop/loop.py
  Dispatched after the edit above in this same process: FEAT-2026-8801/T02 —
  each executed the pre-edit module(s), not what the edit(s) wrote. A fresh
  driver process is required before any of these can be trusted as a
  verification of the change.
```

The driver then did **not** halt, and dispatched `T02` in the same process.
Case-insensitive occurrences of `pin` in that stdout: **2**, both the feature
slug in the branch name. `format_driver_staleness_warning(wu_id, driver_paths)`
takes no pin argument, so one string serves both branches, and the
gate-completion summary has the same shape. The operator is not left inferring
from silence — they are told the opposite of what the process does.

**Re-run condition that would satisfy it.** The pinned branch prints its own
text, naming the pin's tree hash, the tree the edit will take effect in
(`next_pin_tree`, already computed at the seam and written to the event), and
the fact that this process continues against its snapshot. The unpinned branch
keeps today's wording byte-for-byte. Satisfied when the probe above shows a
pin-aware sentence at both the per-unit seam and the gate summary, and
`UnpinnedRunStillHalts` still passes unchanged. Because the gate's oracle is
bound to `events.jsonl` and the exit code, the covering assertion needs a
separate test that reads the subprocess's stdout.

**Closed by `FEAT-2026-0109/T09` (issue #3270).** Re-ran the same probe in the
re-armed close's session, returncode 0. The per-unit seam now prints `DRIVER
EDIT RECORDED (pinned build <tree>)` naming `next_pin_tree` and "This process
continues dispatching against its own pinned snapshot; no restart is required.";
the gate summary prints `DRIVER EDITS RECORDED (gate summary, pinned build
<tree>)` and "No restart was required." Neither `STALE DRIVER PROCESS:` nor
"stop this driver now and start a new one" nor "A fresh driver process is
required" appears anywhere on that stdout. Case-insensitive `pin` occurrences:
**11**, against the 2 recorded above. `UnpinnedRunStillHalts` passes unchanged,
and `tests/test_pin_honesty_and_integrity.py::UnpinnedTextIsByteIdentical`
compares the unpinned strings against HEAD's wording directly. The covering
assertion this condition asked for is
`tests/test_pin_honesty_and_integrity.py::PinnedSeamTextIsPinAware`, which reads
the subprocess's stdout rather than `events.jsonl`.

### A materialized pin can lose its files and still be reported as the running build

**Criterion (verbatim, `GATE-03.md` § Definition of done):** "**The pin is
transparent to the operator's command.** `specfuse run --feature X` and `python3
-m specfuse.loop.loop --feature X` both still work and both reach the pinned
execution; no new command is required to get it, and `resume_command_for`
returns a command that reproduces the same pinned execution rather than one that
silently escapes it."

**Commands run, and their results.**

The half that holds — `resume_command_for` returns the module form, and the
console script's dispatch table routes `run` to the same `main()`:

```
python3 -c "from specfuse.loop.loop import resume_command_for; print(resume_command_for('FEAT-2026-0109'))"
  -> python3 -m specfuse.loop.loop --feature FEAT-2026-0109            # exit 0
grep -n '"run"' <site-packages>/specfuse/cli.py
  -> "run": ("specfuse.loop.loop:main", "specfuse-loop", ...)          # exit 0
```

The half that does not. `materialize_pin` reuses a pin whenever
`.specfuse-pin-tree` matches the directory name, checking nothing else, and
writes pins into `tempfile.gettempdir()` with `shutil.copytree`, which preserves
source mtimes — so a freshly written pin already looks days old to an age-based
tmp reaper. This feature's own recorded pin has been reaped:

```
find $TMPDIR/specfuse-pins/021342f2e43375cf6c598f9c67de095cc1f60fe1/specfuse -type f | wc -l
  -> 40                       # 131 when materialized; ls -ldT on its
                              # subdirectories reads 2026-09-09T08:03Z
```

`021342f2…` is the build `events.jsonl` records the driver executing at
2026-09-08T20:30:25Z. `specfuse/loop/__init__.py` is among the 91 files gone.
Reproduced directly, exit 0 on each:

```
python3 - <<'EOF'
# fresh pin, then remove one aged file, then re-ask materialize_pin
pin = materialize_pin(repo_root, head_tree_hash(repo_root))   # 133 files
(pin/"specfuse"/"loop"/"driver_edit.py").unlink()
materialize_pin(repo_root, same_hash)
#  -> same dir returned: True
#  -> files before: 133   after reuse: 132
#  -> driver_edit.py restored by the reuse? False
EOF

python3 - <<'EOF'
# with specfuse/loop/__init__.py removed and the marker intact, run the
# launcher's own import shape from inside the pin, cwd = repo root
sys.path.insert(0, str(pin)); import specfuse.loop.loop as L; print(L.__file__)
#  -> RESOLVED: <REPO_ROOT>/specfuse/loop/loop.py
#  -> marker still valid? True
EOF
```

`specfuse` is a namespace package (no `specfuse/__init__.py`), and the working
tree is on `sys.path`, so a pin missing `specfuse/loop/__init__.py` resolves the
whole `specfuse.loop` package from the tree. The process still sets
`SPECFUSE_LOOP_PINNED_TREE`, still emits `driver_build_pinned` naming a build it
is not executing, and still takes the pinned "record, do not halt" branch while
running code that can go stale under it — #1040's failure mode, reintroduced by
the mechanism built to retire it.

**Re-run condition that would satisfy it.** `materialize_pin`'s reuse check
validates the pin's **content**, not only its marker — a manifest written
alongside `.specfuse-pin-tree`, or a re-materialize when the tree does not match
— so a partially reaped pin is rebuilt rather than reused; and/or pins move out
of the OS-reaped `tempfile.gettempdir()` into a cache directory with a retention
policy the driver controls. Satisfied when a test materializes a pin, deletes
`specfuse/loop/__init__.py` (or any other file) behind its back, calls
`materialize_pin` again, and asserts the returned pin is complete — and when the
launcher-shaped import inside a reused pin resolves `specfuse.loop.loop` to the
pin, never to the working tree.

**Closed by `FEAT-2026-0109/T09` (issue #3271).** T09 took the first of the two
options this condition offered — a manifest — and did **not** relocate the cache
out of `tempfile.gettempdir()`, which was offered as an "and/or" and is an
operator decision. `materialize_pin` now writes a `.specfuse-pin-manifest`
alongside `.specfuse-pin-tree` at materialize time and `_pin_is_complete`
requires every manifested file to still be present. Re-probed in the re-armed
close's session, exit 0 on each:

```
real reaped pin 021342f2… : 40 of 131 files, marker present, manifest absent
                            _pin_is_complete -> False      # refused, would rebuild
fresh pin, 131 files, manifest 131 lines
  delete specfuse/loop/__init__.py + build_provenance.py behind its back -> 129
  marker still matches: True ;  _pin_is_complete -> False
  materialize_pin() again -> same dir, 131 files, both deleted files restored
launcher-shaped import inside the reused pin, cwd = repo root
  RESOLVED: <cache>/<tree>/specfuse/loop/loop.py
  resolves to the PIN: True ;  resolves to WORKING TREE: False
```

Both clauses of the condition hold. What T09 did not change: pins still live in
`tempfile.gettempdir()` and `shutil.copytree` still preserves source mtimes, so
a pin is still born looking days old to an age-based reaper — losing files is
now loud (one re-copy) instead of silent (a hybrid of pin and working tree).
Recorded in `RETROSPECTIVE.md` § *What the loop did NOT verify* item 1.

## Noted, not filed

`PLAN.md`'s `planned_cost_usd` is **$26.00**. At the time this was written the
WU sum was **$56.00** and actual spend **$50.34** across 16 attempts; with T09
and T10 added the WU sum is **$62.50** and actual spend **$67.77** across 21
attempts, a delta of **+160.7%** against the plan figure and **+8.4%** against
the WU sum. `GATE-02-REVIEW.md` Q4 and `GATE-03-REVIEW.md` Q3 both flagged it
and both left it to the operator; it was not corrected, and the re-armed close
did not correct it either. It is not an acceptance criterion of any work unit
and the driver owns `PLAN.md`, so it is recorded here rather than filed as a
follow-up. The arithmetic is in `RETROSPECTIVE.md` § Cost analysis.

### T08#1

Recorded path for pin identity is not under pin cache — points at working tree's `specfuse/loop`, not the materialized build. Identity is not actually recorded correctly on the run.

- command: `python3 -m unittest tests.test_installed_copy_driver_e2e -q`
- exit: 1

### T08#2

`UnpinnedRunStillHalts.test_halt_event_and_exit_code_are_unchanged` fails: unpinned run now returns exit 0 instead of 3 — "unpinned run keeps today's behaviour byte-identically" is false.

- command: `python3 -m unittest tests.test_installed_copy_driver_e2e -q`
- exit: 1

### T08#4

Same suite this criterion cites reports 3 failures, not `OK`.

- command: `python3 -m unittest tests.test_installed_copy_driver_e2e tests.test_pin_honesty_and_integrity -q`
- exit: 1

### T08#6

`ProjectWithoutDriverSourceIsUnaffected.test_no_pin_materialized_no_new_event` fails: a `driver_build_pinned` event IS emitted for a project with no `specfuse/loop/` in its working tree — contradicts "no new event".

- command: `python3 -m unittest tests.test_installed_copy_driver_e2e -q`
- exit: 1

### G3-CLOSE#4

`tests.test_installed_copy_driver_e2e` (one of the three gates' `feature_oracle` commands) does not report `OK` — 3 failures.

- command: `python3 -m unittest tests.test_installed_copy_driver_e2e -q`
- exit: 1
