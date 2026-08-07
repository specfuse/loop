## Gate 1

Gate 1 of FEAT-2026-0056 set out to make per-criterion close state **recorded** and
**linted**, and it did: `specfuse/loop/criteria_state.py` defines the entry schema and
its parser/renderer (T01), `precreate_dispatch_skeleton` seeds `GATE-NN-CRITERIA.md`
on every `close` / `close-intermediate` dispatch through a hoisted
`extract_wu_criteria` shared with `build_autoclose_debt_enumeration` (T02),
`closing_requirements.py` declares `close-l` / `close-intermediate-f` and
`lint_closing.py` implements `check_criteria_state_well_formed` (T03), and
`close-discipline.md` §5 documents the narrow/broad oracle contract while the roadmap's
benefit paragraph was re-baselined to what the design can reach (T04). Four work units,
five attempts, $6.99 against a $12.50 plan for those units.

Every oracle is green. The composite checks this close is here to run are not, and the
two findings below are the substance of this gate's record. Neither is a defect *inside*
a producing unit — each is a gap *between* two of them, which is the class no producing
unit's acceptance criteria can reach.

### Oracle re-runs (close-discipline §1)

Re-run fresh in this session, exit codes read directly. Commands are prefixed with the
project venv's interpreter; the gate declarations in `.specfuse/verification.yml` write
them as bare `python3`.

The full `code` gate set:

```
$ python3 -m unittest discover -s tests -v -b
Ran 2411 tests in 107.185s
OK (skipped=3)
EXIT=0

$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
EXIT=0

$ bandit -r specfuse .specfuse/scripts -ll
	Total issues (by severity):  Undefined: 0  Low: 92  Medium: 0  High: 0
EXIT=0

$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
TOTAL                                               7726    502    94%
EXIT=0

$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
EXIT=0

$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 53 events.jsonl file(s), 1244 event(s) checked
EXIT=0
```

The remaining `code` entries, run for completeness rather than because a producing
unit's criteria named them: `roadmap_link_gate.py` EXIT=0 (0 errors, 8 warnings, none
new), `arm_sweep_gate.py` EXIT=0 (14 evaluable features swept clean),
`lint_monitoring.py` EXIT=0, and all six `bats` suites EXIT=0.

The per-unit oracles named in T01–T04's own acceptance criteria:

```
$ python3 -c "from specfuse.loop.criteria_state import ORACLE_KINDS, CRITERION_STATES, parse_criteria_state, render_criteria_state, criterion_id_for"     # T01 c7
EXIT=0

$ python3 -c "from specfuse.loop.loop import extract_wu_criteria, _precreate_criteria_state_stub"                                                          # T02 c9
EXIT=0

$ python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"                                                                    # T03 c11
EXIT=0

$ python3 -m unittest discover -s tests -v -b -k debt                                                                                                     # T02 c3
Ran 5 tests in 0.007s
OK
EXIT=0

$ bash scripts/sync-scaffold.sh                                                                                                                           # T04 c6
Scaffold data already in sync (26 files checked).
EXIT=0
$ diff specfuse/loop/data/rules/close-discipline.md .specfuse/rules/close-discipline.md          -> EXIT=0
$ diff specfuse/loop/data/templates/GATE.template.md .specfuse/templates/GATE.template.md        -> EXIT=0
$ diff specfuse/loop/data/templates/WU.template.md .specfuse/templates/WU.template.md            -> EXIT=0

$ python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0056-per-criterion-dod-state                                                         # T04 c10
OK — .specfuse/features/FEAT-2026-0056-per-criterion-dod-state is structurally valid.
EXIT=0
```

**T03's corpus sweep had to be re-run with a different command than the one on record,
and that is itself a finding.** `GATE-01.md`'s arming baseline and T03's criterion-10
sweep both invoke the `specfuse-lint` console script from the project venv. That script
resolves `specfuse.loop` from the **installed** distribution in `site-packages`
(version 0.7.1), not from the working tree — it has no `close-l`, no
`close-intermediate-f`, and no `criteria_state` module at all. So the sweep that was
offered as evidence the severity flip is satisfiable never executed the requirement it
was measuring. The shims under `.specfuse/scripts/` path-insert the repo root and do
resolve from source, so the sweep re-run below is against the code under test:

```
$ for d in .specfuse/features/*/; do python3 .specfuse/scripts/lint_plan.py "$d" --closing; done   # non-zero exits only
### .specfuse/features/FEAT-2026-0001-health-endpoint/ (exit 1)
  - plan-next-a: GATE-02-REVIEW.md absent or empty
### .specfuse/features/FEAT-2026-0036-adopt-ruff-016/ (exit 1)
  - close-a: RETROSPECTIVE.md absent or empty in feature dir
  - close-b: no LEARNINGS.md additions and no 'nothing generalizes' note
  - close-d: verdict frontmatter field is absent
### .specfuse/features/FEAT-2026-0056-per-criterion-dod-state/ (exit 1)
  - close-intermediate-b: no LEARNINGS.md additions and no 'nothing generalizes' note
```

The conclusion T03 reached is correct — **zero findings attributable to `close-l` or
`close-intermediate-f` across the corpus** — and it is unchanged from `GATE-01.md`'s
baseline except that this feature's own `close-intermediate-a` is now satisfied. But it
was correct for a reason nobody checked: no feature in `.specfuse/features/` carries a
criteria artifact, so the requirement's `applies_when` gate short-circuits before any
code that could differ between the two package copies is reached. The finding set would
have been identical had T03 shipped nothing at all. See finding 2 for why that premise
expires the moment the driver restarts.

### The feature-level question — does a close dispatched today receive a seeded artifact?

**Answer: no, this close did not. The shipped code does. The two facts are both true and
the gap between them is finding 1.**

This session's own feature folder contains no `GATE-01-CRITERIA.md`. It contains a
`RETROSPECTIVE.md` pre-created at dispatch, so `precreate_dispatch_skeleton` ran — it
ran the retrospective stub and not the criteria stub, which are consecutive statements
in the same function.

Run against a temporary copy of this exact feature folder, through the real entrypoint,
with the real `FEAT-2026-0056/G1-CLOSE-INTERMEDIATE` work unit loaded by `load_wu` from
the `PLAN.md` graph:

```
WU: FEAT-2026-0056/G1-CLOSE-INTERMEDIATE type: close-intermediate
artifact before: False
artifact after : True
entries: 41
ids: ['T01#1', 'T01#2', 'T01#3', 'T01#4', 'T01#5'] ... ['T04#8', 'T04#9', 'T04#10']
states set: ['unverified'] kinds set: ['None']
```

Forty-one entries, seeded from this gate's own four substantive work units, every one
`state: unverified` with `oracle` / `kind` / `proved_at_sha` / `attempt` absent — exactly
T02's criterion 6. So the composite works in the tree. It did not work in this dispatch.

#### Finding 1 — the driver process that dispatched this close predates the code that seeds the artifact

The driver for this feature is `.specfuse/scripts/loop.py --prepare`, and
`ps -eo pid,lstart,etime,command` shows that process started at 23:40:21 UTC — the same
minute as `GATE-01.md`'s `baseline.probed_at` of 23:40:22. T02, which added
`_precreate_criteria_state_stub`, completed at 00:05:04. Python caches modules in
`sys.modules` at first import, so the `precreate_dispatch_skeleton` in that process's
memory is the pre-T02 function object with no criteria-stub call site in it. Every
in-process check — the unit tests, the symbol imports, the composite above — runs in a
fresh interpreter and reports the new behaviour correctly.

This is a **recurrence of an already-promoted lesson**, not a new one:
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]` states the rule, and its rule (b)
— check the driver process's start time against the wiring unit's `started_at` before
writing anything else — is the step that produced this diagnosis in one command. What the
recurrence adds is that the lesson was already in `LEARNINGS.md` when this gate was
planned, and gate 1 was planned anyway with a driver-module `produces:` in T02 and a
close armed to observe it, with no restart step in the gate. The lesson is not missing;
it is not being consumed at plan time. That belongs in gate 2's plan as a step, not in
`LEARNINGS.md` as a second copy of a rule that is already there.

Consequence for the feature: **gate 2's consumer will read an artifact that the same
driver run never wrote.** If gate 2 is planned to be dispatched by the process now
running, its skip policy will find no state to skip on and will silently do nothing —
which looks exactly like "the cache did not help", not like "the cache was never
written". G1-PLAN should treat a driver restart between T02-class wiring and any unit
that observes it as a planned gate step.

#### Finding 2 — a freshly seeded artifact is born failing its own lint, 41 findings deep

The seeded artifact from the composite run above, untouched, linted with the
working-tree lint:

```
$ python3 .specfuse/scripts/lint_plan.py <temp copy of this feature folder> --closing
FAIL — 42 unmet closing requirement(s):
  - close-intermediate-b: no .specfuse/LEARNINGS.md additions ...
  - close-intermediate-f: T01#1: missing kind: — would fail check_criteria_state_well_formed after squash
  - close-intermediate-f: T01#2: missing kind: — would fail check_criteria_state_well_formed after squash
  ... (41 × close-intermediate-f, one per seeded criterion)
```

T02's criterion 6 requires every seeded entry to omit `kind:`. T03's criterion 6 requires
a missing `kind:` to be exactly one blocking finding. Each unit is right in isolation and
each shipped its own passing test. Composed, they mean: **from the instant the driver is
restarted, every `close` and `close-intermediate` dispatch in this repo starts with a red
`specfuse-lint --closing` and stays red until the close session hand-annotates a `kind:`
and a `state:` for every acceptance criterion of every substantive work unit in its
gate** — 41 of them for this gate. Gate 1 shipped no mechanism to fill them in, because
filling them in is a close-session behaviour and no unit in gate 1 owned it.

`PLAN.md`'s escalation-predicate analysis asked the right question ("what does the rule
report on an input already in its intended final state? **Zero**") and answered it for
the *final* state. Nothing asked what it reports on the *initial* state the driver itself
creates, and that is the state every close now begins in. `GATE-01.md`'s arming
condition — "the finding set is unchanged from the baseline" — was satisfiable only
because the stale driver never produced an artifact for the sweep to find.

This is a design question for the operator and for gate 2, and it is deliberately not
fixed here: `specfuse/` is outside this work unit's boundary, and a fix nobody reviewed
is worse than a finding somebody reads. Three shapes are available to gate 2 and the
choice is not this session's to make — seed entries with a `kind` the close may correct;
narrow `applies_when` so the requirement fires only once a close has begun recording; or
give the close a helper that fills the artifact from the oracles it already ran.

**This close did not create `GATE-01-CRITERIA.md` in this feature folder.** No acceptance
criterion asks it to, creating one would be simulating a driver action rather than
observing it, and the observation above is precisely that doing so turns criterion 10
(`specfuse-lint --closing` exits 0) red. The absence is reported, not papered over.

### The re-arm property, observed rather than asserted

`tests/test_loop_criteria_skeleton.py::test_criteria_artifact_survives_rearm_fold`
exercises **the real fold path**: it calls `loop.fold_cumulative_on_rearm(close_wu,
loop.Backend())` — the production function at `specfuse/loop/loop.py:1829` with the
production backend, no stub, no stand-in — after seeding through the real
`precreate_dispatch_skeleton`, and asserts the parsed entries are identical across it.
The driver's only call site for that function is `loop.py:5893`, on the re-arm branch of
the dispatch loop. So the property T02 claims is the property T02 tests.

**The property is true and it is not the one that protects the artifact.** The fold
rewrites work-unit frontmatter; the artifact is a separate file, so no frontmatter
operation could ever have touched it — the test can only pass. The path that *does*
destroy it is the per-attempt reset. `untracked_before` is snapshotted once per work
unit at `loop.py:5890`, outside the attempt loop that begins at `loop.py:5952`;
`precreate_dispatch_skeleton` runs inside each attempt, at `loop.py:3357`. So on attempt
1 the artifact is created *after* the snapshot, and a failing attempt's
`reset_preserving_events(head_before, events_path, untracked_before)` hands it to
`_clean_attempt_untracked` as a file that appeared since the snapshot. Executing that
function's real decision rule and unlink loop against a real filesystem:

```
criteria artifact still present after attempt reset: False
events.jsonl still present after attempt reset:      True
```

`events.jsonl` is preserved by an explicit carve-out. The criteria artifact has none. It
is untracked until the close's own passing attempt commits it, so through every failed
attempt of a close — which is the entire scenario this feature exists to make cheaper —
the recorded state is deleted and re-seeded blank. `[FEAT-2026-0053/G2-CLOSE]` is the
precedent the plan cited, and it applies more exactly than the plan expected: the guard
was keyed on the wrong path, and the wrong path was the one that could not fail.

This is a third finding for gate 2 to design against, alongside finding 2. It does not
change any gate 1 acceptance criterion's verdict — T02's criterion 8 asks for the fold
test and got a correct one.

### Failure-class breakdown

| failure_class | count | work units | attempt cost |
| --- | --- | --- | --- |
| `produces_not_in_diff` | 1 | `FEAT-2026-0056/T04` (attempt 1) | $0.94 |

One non-passing attempt in the gate, excluding this close's own. T04 spent attempt 1
editing `.specfuse/roadmap.md` and its own work-unit file while leaving all three paths
in its `produces:` list — the canonical `close-discipline.md` and the two templates —
untouched. The driver's produces-vs-diff guard refused it, and attempt 2 made the
declared edits and passed. The work unit's body warned about exactly this ("**Canonical
copy first, then propagate**", with the reason spelled out), which is worth noting: the
prose was there, correct, and did not prevent the failure. The guard did. $0.94 of the
gate's $6.99 — 13.5% — went to the refused attempt, and it bought the correct file set on
the retry.

### What gate 1 did for cost: nothing, by design

**Gate 1 shipped no cost saving, and none was expected.** Nothing reads the recorded
state to skip work until gate 2; the artifact is written and linted, and no close is
cheaper for it. This gate's own spend must not be read as evidence for or against the
feature's savings claim in either direction — the mechanism that saves money has not
shipped. `GATE-01.md` says this ("Gate 1 makes no close cheaper — that is the intended
shape, not an omission") and it is repeated here because a cost table in a retrospective
invites exactly that misreading.

Separately, and more consequentially: **the roadmap's benefit paragraph was re-baselined
by T04 because the original claim assumed a mechanism `PLAN.md` rejects.** The row
claimed the feature "roughly halves close cost on multi-attempt gates". That number was
reachable only through diff-derived test selection, which `PLAN.md` rejected on the
grounds that it builds a second, weaker definition of the tests gate alongside
`verification.yml`. This repository's `tests` gate is
`python3 -m unittest discover -s tests -v -b` — 2411 tests, one command, no diff
awareness. It is a `broad` oracle by the contract this gate just documented, so it
re-runs on every close attempt and is excluded from the saving by construction. What
oracle-kind invalidation can actually save is the per-criterion agent reasoning, the
regeneration, and the scenario matrix. T04 rewrote the paragraph to say that and to name
the suite as the excluded oracle. The claim is now smaller and true.

## Gate 2

Gate 2 set out to make gate 1's recorded state **consumed**, and it did: `T05` gives
`_clean_attempt_untracked` a `CRITERIA_FILENAME_RE` carve-out and gives the artifact
filename one home (`criteria_state.criteria_filename`), `T06` narrows
`check_criteria_state_well_formed` so a pristine seeded entry is not a finding, `T07`
adds `build_reverification_worklist` partitioning entries into `carry_forward` /
`reverify` / `oracle_groups`, and `T08` renders that partition into the close
session's prompt at dispatch. Four work units, four attempts, no non-passing producing
attempt, $6.43 against a $13.00 plan for those units.

**The restart precondition held, and this is the first observation in this feature
made against the code it is about.** Gate 1's finding 1 was that the dispatching
driver predated the unit it was armed to observe. Checked first, before anything was
written:

```
$ ps -eo pid,lstart,etime,command
25213 Wed Aug  5 23:09:26 2026  ... python3 -u .specfuse/scripts/loop.py --feature FEAT-2026-0056
```

The dispatching driver started **2026-08-06T03:09:26Z** (23:09:26 EDT). `T08`'s
frontmatter `started_at` is **2026-08-06T02:36:22Z**, and it completed at
02:49:38Z. The driver postdates `T08`'s start by 33 minutes and its completion by 20,
so `specfuse.loop.loop` in that process's `sys.modules` is the post-`T05`/`T08`
module. Criterion 2 passes and this close proceeds.

### Oracle re-runs (close-discipline §1)

Re-run fresh in this session, exit codes read directly, commands prefixed with the
project venv's interpreter. **Every lint/sweep below was run through the
`.specfuse/scripts/` shims, which path-insert the repo root and resolve from the
working tree — not through the installed `specfuse-lint` console script, which
resolves from `site-packages`
(`[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/console-script-is-not-the-tree]`).**

The full `code` gate set, all 14 gates:

```
$ python3 -m unittest discover -s tests -v -b
Ran 2432 tests in 103.504s
OK (skipped=3)
EXIT=0

$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
EXIT=0

$ bandit -r specfuse .specfuse/scripts -ll
	Total issues (by severity):  Undefined: 0  Low: 92  Medium: 0  High: 0
EXIT=0

$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
TOTAL                                               7787    502    94%
EXIT=0

$ python3 .specfuse/scripts/leak_scan.py --all          -> leak-scan: clean            EXIT=0
$ python3 .specfuse/scripts/event_type_gate.py          -> 53 files, 1271 events, ok   EXIT=0
$ python3 .specfuse/scripts/roadmap_link_gate.py        -> 0 error(s), 8 warning(s)    EXIT=0
$ python3 .specfuse/scripts/arm_sweep_gate.py           -> 14 evaluable, swept clean   EXIT=0
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example        EXIT=0
$ bats tests/leak_scan_hook.bats                                                       EXIT=0
$ bats tests/sync_scaffold.bats                                                        EXIT=0
$ bats tests/sync_scaffold_symlinks.bats                                               EXIT=0
$ bats tests/init_sh_shim.bats                                                         EXIT=0
$ bats tests/init_skills_idempotent.bats                                               EXIT=0
$ bats tests/hookspath_conflict.bats                                                   EXIT=0
```

The suite grew from 2411 to 2432 tests across gate 2 — 21 new tests from `T05`–`T08`.
The 8 `roadmap_link_gate.py` warnings are pre-existing tidiness findings on unrelated
features (`FEAT-2026-0050`, `FEAT-2026-0052`, …), unchanged from gate 1, and that gate
deliberately does not fail on WARN.

The per-unit oracles named in `T01`–`T08`'s own acceptance criteria:

```
$ python3 -c "from specfuse.loop.criteria_state import ORACLE_KINDS, CRITERION_STATES, parse_criteria_state, render_criteria_state, criterion_id_for"   # T01 c7   EXIT=0
$ python3 -c "from specfuse.loop.loop import extract_wu_criteria, _precreate_criteria_state_stub"                                                        # T02 c9   EXIT=0
$ python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"                                                                  # T03 c11 / T06 c11  EXIT=0
$ python3 -c "from specfuse.loop.criteria_state import criteria_filename, CRITERIA_FILENAME_RE"                                                         # T05 c8   EXIT=0
$ python3 -c "from specfuse.loop.criteria_state import build_reverification_worklist"                                                                   # T07 c11  EXIT=0
$ python3 -c "from specfuse.loop.loop import format_reverification_worklist"                                                                            # T08 c9   EXIT=0

$ python3 -m unittest discover -s tests -v -b -k debt          # T02 c3    Ran 5 tests   OK  EXIT=0
$ python3 -m unittest tests.test_loop_criteria_survival        # T05 c9    Ran 1 test    OK  EXIT=0
$ python3 -m unittest tests.test_lint_closing_criteria_pristine # T06 c12  Ran 4 tests   OK  EXIT=0
$ python3 -m unittest tests.test_lint_closing_criteria         # T06 c6    Ran 11 tests  OK  EXIT=0
$ python3 -m unittest tests.test_criteria_worklist             # T07 c12   Ran 8 tests   OK  EXIT=0
$ python3 -m unittest tests.test_loop_worklist_injection       # T08 c10   Ran 8 tests   OK  EXIT=0

$ bash scripts/sync-scaffold.sh                                # T04 c6    26 files in sync  EXIT=0
$ diff specfuse/loop/data/rules/close-discipline.md .specfuse/rules/close-discipline.md      EXIT=0
$ diff specfuse/loop/data/templates/GATE.template.md .specfuse/templates/GATE.template.md    EXIT=0
$ diff specfuse/loop/data/templates/WU.template.md .specfuse/templates/WU.template.md        EXIT=0
$ python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0056-per-criterion-dod-state   # T04 c10  EXIT=0

$ grep -rnE 'GATE-\{[a-z_]+[^}]*\}-CRITERIA\.md' specfuse/     # T05 c3
specfuse/loop/criteria_state.py:67:    return f"GATE-{gate_n:02d}-CRITERIA.md"    (one match, in criteria_state.py)  EXIT=0

$ grep -n 'untracked_before = untracked_paths()' specfuse/loop/loop.py   # T05 c7
5963:                untracked_before = untracked_paths()   (exactly one; 16-space indent, in the
                                                             per-WU block before the attempt loop)  EXIT=0
```

**T06's corpus sweep, and why this time it measured something.** Gate 1's sweep
reported "zero findings attributable to `close-l` / `close-intermediate-f`" and was
correct for a reason nobody had checked: no feature carried a criteria artifact, so
`applies_when` short-circuited and the sweep would have reported zero had `T03`
shipped nothing. This gate's sweep is not vacuous — `FEAT-2026-0056` now carries a
44-entry `GATE-02-CRITERIA.md`, so the requirement actually evaluates:

```
$ for d in .specfuse/features/*/; do python3 .specfuse/scripts/lint_plan.py "$d" --closing; done   # non-zero exits only
### .specfuse/features/FEAT-2026-0001-health-endpoint/ (exit 1)
  - plan-next-a: GATE-02-REVIEW.md absent or empty
### .specfuse/features/FEAT-2026-0036-adopt-ruff-016/ (exit 1)
  - close-a: RETROSPECTIVE.md absent or empty in feature dir
  - close-b: no LEARNINGS.md additions and no 'nothing generalizes' note
  - close-c: no docs/, roadmap.md, LEARNINGS.md, or RETROSPECTIVE.md file in the working tree
  - close-d: verdict frontmatter field is absent
### .specfuse/features/FEAT-2026-0056-per-criterion-dod-state/ (exit 1)
  - close-c: (this close's own, satisfied by this edit)
  - close-d: (this close's own, satisfied by the verdict below)
```

Zero `close-l` / `close-intermediate-f` findings across the corpus, against 41 on the
same input before `T06`. And the sweep is carrying a positive control, per rule (b) of
the lesson above — a scratch copy of this feature folder seeded through the real
`loop._precreate_criteria_state_stub`, then annotated with one bad entry:

```
$ python3 .specfuse/scripts/lint_plan.py <scratch copy> --closing        # T06 c7, initial state
close-l findings: 0

$ (annotate T05#1 with `- **kind:** `bogus``, re-lint)                    # T06 c8, positive control
  - close-l: T05#1: kind 'bogus' not one of ['broad', 'narrow']
```

Exactly one finding, naming the entry. The check is silent because it is correct, not
because it is not running.

**The `T06` narrowing, probed at every boundary it claims.** Driving
`check_criteria_state_well_formed` directly against five synthetic artifacts:

```
state: pass, no kind:                       -> ['X#1: missing kind:']                       (c3, exactly one)
state: unverified, oracle: present, no kind -> ['X#1: missing kind:']                       (c4, exactly one)
kind: broad, state: pass, attempt: 0 (cur=1)-> ["X#1: broad entry reads state: pass but
                                                 attempt '0' != current attempt '1'"]       (c5, exactly one)
two pristine entries                        -> []                                           (c2, zero)
kind: broad, state: pass, attempt: 1 (cur=1)-> []                                           (control, correctly silent)
```

The soundness contract `T03` shipped is intact: the narrowing skips only the
never-touched entry, and a `broad` green from a prior attempt is still a blocking
finding.

**`T05`'s carve-out, driven against a real filesystem rather than a re-implementation.**
A temporary git working tree, `untracked_before` snapshotted before any of the three
files exist, then the real `loop._clean_attempt_untracked`:

```
events.jsonl survives        : True     (T05 c6, behaviour)
GATE-02-CRITERIA.md survives : True     (T05 c4)
unrelated junk.txt deleted   : True     (T05 c5 — the carve-out did not widen)
```

**`T07`'s partition, driven over nine synthetic entries covering every kind/state
combination:**

```
carry_forward: ['A#1']                                                       (c4)
reverify     : ['A#2','A#3','A#4','A#5','A#6','A#7','A#8','A#9']
               A#2/A#3 broad+pass at and below current attempt               (c5, the soundness contract)
               A#4 narrow+fail (c6); A#5/A#6 unverified (c7);
               A#7 kind absent, A#8 kind 'bogus' (c8, fail-safe, no raise)
partition exact: True | disjoint: True | document order preserved: True      (c9)
oracle_groups: [('cmd-y', ['A#2','A#3','A#4']), ('cmd-z', ['A#5','A#6','A#7','A#8'])]
               A#9 carries no oracle: contributes no group, still in reverify (c10)
no broad entry in carry_forward: True
$ grep -E 'open\(|Path\(|subprocess|os\.' over the function body -> 0 matches (c3, pure)
```

Three criteria sharing `cmd-y` collapse to one line of work. That is the mechanism the
feature exists for, working on synthetic input.

### The feature-level question — did this close's own dispatch carry a real worklist?

**Answer: yes, the section was there and it was correct. The carried-forward set was
empty, and that is the honest result of a first attempt against a pristine artifact —
not a failure of the mechanism.**

This is the question no producing unit's criteria asked, and it is answerable only
from what this session actually received. Quoted verbatim from the tail of this work
unit's own dispatched body:

```
## Re-verification worklist (gate 2)

0 criterion/criteria carried forward from a prior attempt; 44 require re-verification this attempt.

This worklist bounds per-criterion re-verification only. The close's own feature-level
question (close-discipline.md §1's fresh, feature-level re-run) is never carried forward
by this worklist and runs this attempt regardless of the above.
```

And the artifact it was rendered from, `GATE-02-CRITERIA.md` as this session received
it — 44 entries, every one of this shape:

```
### T05#1

- **criterion:** `tests/test_loop_criteria_survival.py::test_criteria_artifact_survives_attempt_reset`
- **state:** `unverified`
```

Every entry pristine: `state: unverified`, no `kind:`, no `oracle:`. Taking the three
sub-questions in order:

- **Did the prompt carry a re-verification worklist?** **Yes.** `T08`'s section is
  present, appended by `execute_unit_attempt` after the oracle-capture section
  (`loop.py:3428-3430`) — which is `T08` criterion 7 observed in situ rather than
  through a harness, and `T08` criterion 5's unconditional feature-level line
  observed in the only place it matters.
- **Was the carried-forward set non-empty and strictly smaller than the full
  criterion set?** **No — it was empty (0 of 44).** The reason is mechanical and is
  not a defect: `build_reverification_worklist` carries an entry forward only when
  `kind == "narrow"` **and** `state == "pass"` **and** `oracle` and `attempt` are
  non-empty. `_precreate_criteria_state_stub` seeds every entry with `state:
  unverified` and none of the other three fields, so a first attempt against a
  freshly seeded artifact carries nothing forward **by construction**. There is no
  input on which it could have been otherwise.
- **Was every carried-forward entry `kind: narrow`?** **Vacuously yes**, and the
  soundness contract is separately confirmed non-vacuously by the `T07` probe above:
  a `broad` entry reading `state: pass` lands in `reverify` whether its `attempt`
  matches the current one or not. No `broad` entry carried forward, so the escalation
  trigger on a leaked soundness contract did not fire.

**Why the set was empty is worth being precise about, because there were three prior
attempts and they did not help.** `GATE-02.md` § *Arming discipline* records that the
first `G2-CLOSE` dispatch was voided: the driver that ran it started at 21:57, before
`T05` landed, so it executed pre-`T05` code and `_clean_attempt_untracked` deleted
`GATE-02-CRITERIA.md` between each of those three attempts. Each attempt annotated the
artifact from scratch and each reset threw the annotations away. So the state that
would have made this attempt's worklist non-empty was written three times and
destroyed three times — by exactly the defect `T05` exists to fix, in the window
before `T05` was running. `[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]`
predicted this outcome and `GATE-02.md` budgeted for it in advance: *"the restart buys
a truthful observation, not a working one — budget for the honest answer being 'the
worklist was empty'."* It was.

**What this close leaves behind is the first non-empty input the mechanism has ever
had.** `GATE-02-CRITERIA.md` now carries 40 annotated entries. Re-partitioning it for
a hypothetical attempt 2:

```
carry_forward: 37   reverify: 7   oracle_groups: 3
```

37 of 44 criteria carried forward; the 7 re-verified are the 4 that stayed pristine
(the red-before-green criteria, D1), the 1 recorded `fail` (`T05#6`, finding 3), and
the 2 `broad` entries that can never carry forward by design. That is a concrete,
checkable prediction and the cheapest possible way to falsify this feature: if a
second attempt of this close is ever dispatched, its prompt must say `37 criterion/criteria
carried forward ... 7 require re-verification`.

#### Finding 3 — `T05` criterion 6's assertion is absent from the module that criterion names

`T05` criterion 6 reads: *"`_clean_attempt_untracked` still never unlinks
`events_path` — the existing carve-out is intact, asserted in the same test module."*

The **behaviour** is intact and is verified above by a direct probe against a real
git working tree. The **assertion** is not there:

```
$ grep -n 'def test_' tests/test_loop_criteria_survival.py
57:    def test_criteria_artifact_survives_attempt_reset(self)

$ grep -n 'events' tests/test_loop_criteria_survival.py
12:  (docstring)
59:            events_path = root / "events.jsonl"
75:            loop._clean_attempt_untracked(untracked_before, events_path)
```

The module holds exactly one test. It constructs `events_path`, passes it to the real
function, and never asserts on it — the file is never even created, so no assertion
about its survival could have been made. The nearest real coverage lives in
`tests/test_loop_reset_preserving_events.py`, which exercises the carve-out through
`reset_preserving_events` rather than `_clean_attempt_untracked`, and which predates
this feature. So `T05` did not weaken the carve-out and did not test that it hadn't.

Recorded as `T05#6` `state: fail` in `GATE-02-CRITERIA.md`, and carried into the
hedged-verdict record below. This is the class of gap only a close finds: the unit's
own oracle (its named test module) passed, because a module with no assertion about X
passes whether or not X holds.

#### Finding 4 — the dispatch skeleton does not pre-create `## Gate N` for a terminal `close`

This work unit's body states that *"the required artifacts and headings are pre-created
in this session's skeleton"* and criterion 11 says both `## Gate 2` and
`## Cost analysis` *"are in the pre-created skeleton"*. Neither was:

- `_precreate_retrospective_stub` gates the `## Gate {gate_n}` stub on
  `wu.type == "close-intermediate"` (`loop.py:2358`). A terminal `close` gets no gate
  section. This is consistent with the requirement registry — `close-intermediate-a`
  requires a `Gate N` heading and there is no `close-*` counterpart — so the driver
  is behaving as specified and the WU body's expectation was wrong, not the code.
- `## Cost analysis` is explicitly never touched by the skeleton, by design:
  `precreate_dispatch_skeleton`'s own docstring says it *"never touches
  verdict-conditional headings such as '## Cost analysis' (owned by the lint once the
  agent writes its verdict)"*. It exists here only because gate 1's close wrote it.

Both headings were written by hand in this session. No escalation: nothing under
`specfuse/` is broken and no acceptance criterion is unmet by it. It is recorded
because a close WU body that promises a skeleton the driver does not produce is a
plan-time defect that will recur in every terminal close drafted from this one, and
because the honest reading of criterion 11 is "these headings must exist when you are
done", which they now do.

### The close-cost delta, honestly

**This close skipped nothing, and the number it exists to move did not move on this
run.** Stated plainly rather than framed:

- **Criteria skipped: 0 of 44.** The worklist carried nothing forward, for the
  by-construction reason above.
- **Oracle invocations skipped: 0.** Every oracle named across `T01`–`T08` was
  re-run in this session, plus the full 14-gate `code` set, plus the corpus sweep,
  plus five in-session probes the criteria did not name but honesty required.
- **What could not have been skipped even with a full worklist:** the `code` gate set
  (`T05#10`) and the corpus sweep (`T06#9`) are `broad` — they re-run every attempt by
  design, and together they are the dominant wall-clock cost of this close (~104s for
  the suite, ~110s again for the coverage re-run of the same suite). And the
  feature-level question above is excluded from the cache by construction
  (`PLAN.md` § *Notes*, `[FEAT-2026-0057/G1-CLOSE]`), which `T08`'s rendered section
  states unconditionally in every close prompt from here on.

**What the run does establish**, which is weaker than a saving and stronger than
nothing: the mechanism is wired end-to-end and produced a correct section from a real
artifact in a real dispatch, and it leaves behind a 37-of-44 carry-forward set for the
next attempt to consume. The saving remains **unmeasured, not disproven**.

`T04` already re-baselined the roadmap's benefit paragraph to what oracle-kind
invalidation can actually reach — per-criterion agent reasoning, regeneration, and the
scenario matrix, with this repo's diff-unaware `tests` gate named as the excluded
`broad` oracle. Nothing this close observed argues with that paragraph, and nothing
here restates the retired headline.

**This is a sample of one, and a first attempt at that.** A first attempt is the one
case where the worklist is guaranteed to be empty; the feature's entire value lives in
attempts 2..N, and no attempt 2 has ever run against a driver carrying `T05`. One run
is not evidence of a saving in either direction, and reading it as such in either
direction would be the mistake.

### Failure-class breakdown (gate 2)

| failure_class | count | work units | attempt cost |
| --- | --- | --- | --- |
| `guard_refusal` (`assert_doc_or_roadmap_diff`) | 3 | `FEAT-2026-0056/G2-CLOSE` (voided dispatch, attempts 1–3) | $3.66 |

**No producing unit in gate 2 had a non-passing attempt.** `T05`, `T06`, `T07`, and
`T08` each passed on attempt 1 — four units, four attempts, four passes, which is the
first gate in this feature with a clean producing run.

Every non-passing attempt in the gate belongs to this close's own voided dispatch,
under the driver that predated `T05`. All three failed the same guard
(`closing_deliverable_missing` / `assert_doc_or_roadmap_diff`) and the driver escalated
`spinning_detected` at attempt 3. The cost — $0.90 + $1.29 + $1.46 = **$3.66, 36% of
gate 2's spend to date** — bought nothing except the evidence in `GATE-02.md` §
*Arming discipline* that the restart precondition is real. It is the price of the
operator step this gate was planned around, paid once, in the gate designed to prevent
exactly that class of loss. The re-arm reset `attempts` to 1 while `events.jsonl` kept
all three records; see the cost reconciliation below, where that asymmetry is the whole
story.

## Cost analysis

Two independent totals, computed separately and compared:

| work unit | planned | actual | attempts | delta |
| --- | --- | --- | --- | --- |
| `T01` criteria-state schema | $3.00 | $0.599546 | 1 | −$2.40 (−80%) |
| `T02` pre-create the artifact | $4.00 | $2.093737 | 1 | −$1.91 (−48%) |
| `T03` criteria-state lint | $3.00 | $2.313287 | 1 | −$0.69 (−23%) |
| `T04` rules, templates, re-baseline | $2.50 | $1.983739 | 2 | −$0.52 (−21%) |
| **producing units** | **$12.50** | **$6.990309** | 5 | **−$5.51 (−44%)** |
| `G1-CLOSE-INTERMEDIATE` (this unit) | $4.50 | not yet stamped | 1 in progress | — |
| `G1-PLAN` | $6.00 | not dispatched | — | — |
| **gate plan / budget** | **$23.00** / $29.00 | **$6.99 to date** | | |

**Frontmatter total: $6.990309.** Summing `cost_usd` across the four `done` work units'
frontmatter.

**`events.jsonl` total: $6.990309.** Summing `cost_usd` across every `attempt_outcome`
payload in the feature's event log — five attempts, including T04's refused attempt 1 at
$0.943193. Summing the four `task_completed` payloads instead gives the same
$6.990309.

**Divergence: $0.000000 (0.00%).** The two surfaces agree exactly, and they agree for a
checkable reason rather than by luck: `re_arm_count` is 0 on every unit in this gate, so
no cycle was ever folded into a `cumulative_*` accumulator and the per-cycle frontmatter
field is still the whole story. `events.jsonl` is the only surface that survives a
re-arm — that property was not exercised here, so this gate's agreement is not evidence
the reconciliation would hold on a re-armed unit. T04's two attempts do exercise the
weaker property: its frontmatter `cost_usd` of $1.983739 and `duration_seconds` of
1191.003 are the sums across both attempts, not attempt 2 alone.

Against the $29.00 gate budget: $6.99 spent, 24% consumed, with $10.50 of planned close
spend still ahead. Projected gate total is roughly $17.49 — about 60% of budget — and
even a three-attempt close would land inside it. The producing units came in 44% under
plan, which is a plan-side signal worth carrying to G1-PLAN: the two units estimated
highest (T02 at $4.00, T03 at $3.00) were the two that actually did structural work, and
they were the closest to their estimates. T01 at 20% of plan was a pure-data module with
no wiring, and it was over-estimated by the same reasoning that over-estimated the rest.

### Both gates — actual against planned (acceptance criterion 5)

| work unit | gate | planned | actual | attempts | delta |
| --- | --- | --- | --- | --- | --- |
| `T01` criteria-state schema | 1 | $3.00 | $0.599546 | 1 | −$2.40 (−80%) |
| `T02` pre-create the artifact | 1 | $4.00 | $2.093737 | 1 | −$1.91 (−48%) |
| `T03` criteria-state lint | 1 | $3.00 | $2.313287 | 1 | −$0.69 (−23%) |
| `T04` rules, templates, re-baseline | 1 | $2.50 | $1.983739 | 2 | −$0.52 (−21%) |
| `G1-CLOSE-INTERMEDIATE` | 1 | $4.50 | $8.293007 | 1 | **+$3.79 (+84%)** |
| `G1-PLAN` | 1 | $6.00 | $6.413651 | 1 | +$0.41 (+7%) |
| **gate 1 total** | | **$23.00** | **$21.696967** | 7 | −$1.30 (−6%) |
| `T05` artifact survives attempt reset | 2 | $3.00 | $1.320755 | 1 | −$1.68 (−56%) |
| `T06` pristine entries are not findings | 2 | $3.00 | $2.205899 | 1 | −$0.79 (−26%) |
| `T07` re-verification worklist | 2 | $3.00 | $0.873341 | 1 | −$2.13 (−71%) |
| `T08` worklist reaches the close session | 2 | $4.00 | $2.027098 | 1 | −$1.97 (−49%) |
| **gate 2 producing units** | | **$13.00** | **$6.427093** | 4 | **−$6.57 (−51%)** |
| `G2-CLOSE` (this unit, to date) | 2 | $5.00 | $3.658889 | 1 recorded / 3 spent | — |
| **gate 2 total to date** | | **$18.00** | **$10.085982** | | −$7.91 (−44%) |
| **both gates** | | **$41.00** | **$31.782949** | | **−$9.22 (−22%)** |

**Frontmatter total: $31.782949.** Summing `cost_usd` across all eleven work-unit
files' frontmatter.

**`events.jsonl` total: $31.782948.** Summing `cost_usd` across every
`attempt_outcome` payload in the feature's event log — fifteen attempts, including
`T04`'s refused attempt 1 and this close's three voided attempts.

**Divergence: $0.000001 (0.000003%),** which is float accumulation order, not a
bookkeeping disagreement: the events log sums fifteen per-attempt values and the
frontmatter sums eleven already-aggregated ones.

**The two surfaces do NOT agree on attempt count, and that is the interesting
number.** Summing `task_completed` payloads instead gives **$28.124060** — short by
exactly $3.658889, this close's own spend, because `G2-CLOSE` has no `task_completed`
event: its voided dispatch ended in a `human_escalation` (`spinning_detected`), not a
completion. And this unit's frontmatter reads `attempts: 1` while `events.jsonl` holds
three `attempt_outcome` records for it, because the operator's re-arm reset the
counter without deleting history. Cost reconciles across the re-arm; attempts do not.
`PLAN.md` § *Notes* cited `[FEAT-2026-0053/G2-CLOSE]` — *"an aggregate reading a
per-cycle field silently under-counts every re-armed unit"* — as the reason
per-criterion state had to be a standalone artifact rather than close-WU frontmatter.
This gate produced a live instance of that exact shape in its own bookkeeping: a
reader taking `attempts` from frontmatter under-counts this close by 2 of 3, and only
`events.jsonl` carries the whole run. **The design decision the plan made on
borrowed evidence is now supported by evidence from this feature.**

**The planned-figure discrepancy criterion 5 names has already been fixed, and the
criterion is the stale surface.** This work unit's criterion 5 says *"`PLAN.md`'s
frontmatter `planned_cost_usd: 28.00` predates gate 2's draft and is below the two
gates' WU estimates ($23.00 + $18.00)"*. `PLAN.md` frontmatter actually reads:

```
planned_cost_usd: 41.00   # re-derived by G1-PLAN once gate 2 had work units; see GATE-02-REVIEW.md
```

$41.00 = $23.00 + $18.00 exactly, so the feature figure and the sum of the two gates'
work-unit estimates now agree to the cent. `G1-PLAN` corrected it when it drafted gate
2, between this work unit being authored and being dispatched. Reported as required
against the two gates' own numbers rather than against the feature figure — and the
answer is that on this feature there is no longer a gap between them.

**Against the gate budgets** (the `cost_budget_usd` frontmatter values, which are
larger than the WU sums by design, as headroom for close re-attempts): gate 1 spent
$21.70 of $29.00 (75%); gate 2 has spent $10.09 of $23.00 (44%) with this close's
final attempt still to be stamped; both gates together, $31.78 of $52.00 (61%).
Nothing is near its ceiling, and that is true even carrying the $3.66 of voided
close spend.

**One plan-side signal worth carrying forward.** Producing units came in 51% under
plan in gate 2 and 44% under in gate 1, while the two closing units in gate 1 came in
*over* ($8.29 against $4.50, and $6.41 against $6.00). The estimate error is not
uniform — it is concentrated, with the same sign every time, in the closing sequence.
Gate 1's retrospective read its producing-unit underspend as a plan-side signal;
across both gates the sharper reading is that **implementation work is being
over-estimated and close work under-estimated**, which is consistent with
`PLAN.md`'s own opening — close attempts are the costliest attempt type
portfolio-wide. `G2-CLOSE` at $5.00 planned is on track to overrun once this attempt
is stamped, for the third closing unit in a row.

## What the loop did NOT verify

Deferred-verification list, per acceptance criterion 5. Every criterion across T01–T04
was re-verified in this session except the four below.

**D1 — T01 c1, T02 c1, T03 c1: the red-test-first observation.**
*Criteria, in substance:* the named test "exists and **fails on HEAD before this WU's
edits**", with the failing output recorded.
*Why not verified here:* the property is historical. It is a claim about the tree as it
stood before each unit's edits, and it is unobservable from a tree in which those edits
have landed. Reproducing it would require reverting the source, which this unit may not
do — `specfuse/` is outside its boundary and it may not run git.
*Where it actually gets checked:* each producing unit's own attempt, whose RESULT block
recorded the failing output, and the driver's produces-vs-diff guard, which independently
refuses a unit whose declared source went untouched. The post-condition half of each
criterion — that the test passes now — is verified here: all 2411 tests pass.

**D2 — T04 c8 and c9: the roadmap edit is confined to FEAT-2026-0056's section.**
*Criteria, verbatim:* the `**Why.**` and `**Goal.**` paragraphs "are byte-identical to
their state before this WU — verified with `git diff .specfuse/roadmap.md`", and
"`git diff --stat .specfuse/roadmap.md` shows changes confined to the FEAT-2026-0056
section".
*Why not verified here:* both oracles are `git` invocations, and this work unit is
forbidden from running any git command — the driver owns that surface. There is no
non-git substitute: the property is a diff against a commit.
*Where it actually gets checked:* T04's own attempt-2 RESULT block, and the squash commit
for T04, which a reviewer can read directly. `roadmap_link_gate.py` passes here with 0
errors, which confirms the roadmap's link graph is intact but says nothing about which
section changed.

**D3 — the seeded-artifact-to-lint interaction over more than one gate shape.**
*Criterion:* none — this is a gap in the criteria, recorded because finding 2 exists.
*Why not verified here:* the 41-finding observation was made against one gate of one
feature. Whether the count and shape hold for a gate with a different substantive-unit
mix, or for a `close` rather than a `close-intermediate`, is unmeasured.
*Where it actually gets checked:* gate 2, which must design against finding 2 and will
need the measurement to choose between the three remedies named above.

**D4 — the artifact's survival across a genuine multi-attempt close.**
*Criterion:* T02 c8 asks for survival across `fold_cumulative_on_rearm`, and that is
verified. The broader property — that recorded state survives a *failed attempt* — is
not asserted by any criterion in gate 1.
*Why not verified here:* observing it end-to-end requires a close that actually fails an
attempt with state already recorded, which cannot be staged from inside a close session
that may not run git or drive the driver. The deletion rule itself **was** observed (see
the re-arm section); what is unobserved is the full driver loop reaching it.
*Where it actually gets checked:* the first real multi-attempt close after the driver is
restarted — or, better, a gate 2 test that drives `reset_preserving_events` with a
dispatch-time snapshot and asserts the artifact survives.

### Gate 2 — disposition of `D1`–`D4`, plus what gate 2 could not verify

Every acceptance criterion across `T05`–`T08` was re-verified in this session except
where noted below. No predecessor gate auto-closed, so there is no auto-close debt to
reconcile in this section.

**`D1` — the red-test-first observation. Carried forward, and now wider.** It covered
`T01 c1`, `T02 c1`, `T03 c1`; it now also covers `T05 c1`, `T06 c1`, `T07 c1`, and
`T08 c1`, each of which asserts its named test *"exists and fails on HEAD before this
WU's edits."* Still historical and still unobservable from a tree in which those edits
have landed; reverting the source is outside this unit's boundary and it may not run
git. Those four entries are the ones left **pristine** in `GATE-02-CRITERIA.md` — not
annotated to make a lint green. The post-condition half is verified here: all four
modules pass (1, 4, 8, and 8 tests respectively) and the full suite is green at 2432.
*Where it actually gets checked:* each producing unit's own attempt, and the driver's
produces-vs-diff guard, which independently refuses a unit whose declared source went
untouched.

**`D2` — `T04 c8`/`c9`, the roadmap edit confined to this feature's section. Carried
forward unchanged.** Both oracles are `git` invocations and this unit may not run git;
there is no non-git substitute for a diff against a commit. *Where it actually gets
checked:* `T04`'s attempt-2 RESULT block and `T04`'s squash commit.
`roadmap_link_gate.py` is green here (0 errors), which confirms the link graph is
intact but says nothing about which section changed.

**`D3` — the seeded-artifact-to-lint interaction over more than one gate shape.
RESOLVED here.** Gate 1 deferred this because its 41-finding observation came from one
gate of one feature and it was unmeasured whether the count and shape held *"for a
gate with a different substantive-unit mix, or for a `close` rather than a
`close-intermediate`."* Both variables changed in this session: this is a terminal
`close` (not `close-intermediate`), on a different gate, with a different unit mix
producing 44 criteria rather than 41. The seeded artifact linted at **0**
`close-l` findings, and the positive control fired exactly once on the same input. The
narrowing holds across both shapes measured so far. It remains true that only two gate
shapes in one repository have been measured.

**`D4` — the artifact's survival across a genuine multi-attempt close. RE-DEFERRED,
with sharper evidence in both directions.** The negative half is now observed in
production rather than inferred: the voided `G2-CLOSE` dispatch ran three real attempts
under a driver that predated `T05`, and `GATE-02-CRITERIA.md` was deleted and re-seeded
blank between each — the exact failure gate 1 predicted from reading the cleanup
function, reproduced by the driver itself three times at a cost of $3.66. The positive
half is verified against the real function on a real filesystem (the probe above:
artifact survives, `events.jsonl` survives, unrelated leftovers deleted) and by
`tests/test_loop_criteria_survival.py`.
*Why it is still deferred:* what remains unobserved is the full driver loop reaching
that carve-out — a close that fails an attempt **while a T05-carrying driver is
running**, with state already recorded. This dispatch is attempt 1 of a re-armed unit
and has not failed an attempt, so the end-to-end path has still never executed with the
fix in place. It cannot be staged from inside a close session that may not run git or
drive the driver.
*Where it actually gets checked:* the next close in this repository that fails an
attempt after this feature merges — its second attempt's prompt must report a non-empty
carried-forward set. For this unit specifically, the falsifiable prediction is on
record above: `37 carried forward / 7 re-verify / 3 oracle groups`.

**`D5` — the carry-forward path against a non-empty artifact, in a real dispatch.**
*Criterion:* acceptance criterion 3's second sub-question — was the carried-forward set
non-empty and strictly smaller than the full criterion set.
*Why not verified here:* it was empty, by construction rather than by defect, and the
reason is set out in full in § *The feature-level question* above. A first attempt
against a freshly seeded artifact can carry nothing forward under any implementation,
because every seeded entry lacks the `kind`/`oracle`/`attempt` fields the partition
requires. Reported as a legitimate empty result, not as a failure of the run.
*Where it actually gets checked:* the same place as `D4` — any attempt 2 of any close
dispatched after this feature merges. The rendering path for a non-empty set is
verified here on synthetic input (`T08` probe: 1 carried forward, 2 re-verified, the
shared oracle collapsed to one line, no `broad` entry in the carried-forward list); what
is unverified is that path running on state a *real prior attempt* wrote.

**`D6` — `T05 c6`'s in-module assertion.** Recorded as `T05#6` `state: fail` and
carried in the hedged-verdict record below rather than here, because it is an unmet
criterion with a known fix rather than something this environment cannot observe — the
behaviour it asserts was verified in this session.

## Consumer-visible contract changes — awaiting operator acknowledgment

Enumerated per `close-discipline.md` §3 across **both gates** — `T01`–`T08` — as one
combined list, per `GATE-02.md` § *Arming discipline*, which records that the operator
deferred acknowledgment of gate 1's list to this close rather than acknowledging it at
the gate boundary. Ten items. This is a real enumeration; the exemption wording is
deliberately absent from it, and item 1's behaviour is restated below rather than
copied forward, because `T06` changed it. Each item is appended to `CHANGELOG.md`'s
`Unreleased` section, classified and traced to `FEAT-2026-0056`.

> **Wording hazard, and why this section reads the way it does.**
> `closing_requirements.consumer_visible_section_is_na` classifies a §3 section by
> substring: it treats the section as exempt if the body contains both a certain
> two-character abbreviation and a certain seven-word phrase, in any context. A close
> that writes "this section is **not** *(exemption wording)*" — the natural way to say
> it, and the phrasing at least one prior close in this repo used — is therefore read
> as an exempt close. For a terminal `close` that suppresses `close-k`, which is the
> requirement that a real enumeration must reach `CHANGELOG.md`, and the lint stays
> green while a contract change ships unlisted. Gate 1 tripped this on its first draft
> and escaped only because a line wrap split the phrase; this section avoids both
> substrings outright rather than relying on where the text happens to wrap. Not fixed
> here — `specfuse/` is outside this unit's boundary and the code belongs to
> FEAT-2026-0064 — and recorded again for whoever owns that surface. Verified in this
> session: `consumer_visible_section_is_na` returns `False` for this section, so
> `close-k` is live and the changelog requirement applies.

**1. A new blocking `specfuse-lint --closing` finding: `close-l` /
`close-intermediate-f` (breaking, headline) — RESTATED, because `T06` changed what it
does.** A close whose gate carries a `GATE-NN-CRITERIA.md` fails the closing lint for
every entry with a missing or unrecognized `kind:`, a missing or unrecognized `state:`,
or a `broad` entry reading `state: pass` with an `attempt:` that is not the current one.
The requirement is still gated on `applies_when="criteria_artifact_present"` and is
still enforced by `check_criteria_state_well_formed`; the narrowing lives in the check,
not in the registry (verified by import this session).

**What changed between gate 1 and gate 2, and it is the difference between a shippable
item and an unshippable one.** As gate 1 shipped it, a **pristine** seeded entry —
`state: unverified`, no `kind:`, no `oracle:`, exactly and only what
`_precreate_criteria_state_stub` writes — was a finding. Since the driver seeds one
entry per acceptance criterion of every substantive unit in the gate, that meant every
`close` and `close-intermediate` dispatch in every downstream project would begin with a
red closing lint from the moment a driver carrying gate 1 was running: 41 findings for
this feature's gate 1, and nothing in gate 1 filled them in. `T06` narrows the check so
a pristine entry is not this requirement's concern — nobody has annotated it, so there
is nothing to have gotten wrong. **Any deviation re-enters scope immediately:** a
`state` other than `unverified`, or an `oracle` recorded, means a close has begun
touching the entry and every original rule applies to it again. The soundness contract
is untouched — a `broad` entry carrying a green from a prior attempt is still a blocking
finding, confirmed here by direct probe.

**What an operator is actually acknowledging on this item.** After `T06`, a close is
free to leave an entry unannotated and still lint clean, and this close does exactly
that for four entries (see `D1`). The lint therefore no longer enforces "every criterion
was verified" — it enforces "everything you claimed about a criterion is well-formed."
That is a deliberate weakening of the gate-1 rule and it is the reviewable decision in
this list: the alternative shapes gate 1 named (seed entries with a correctable `kind`,
or narrow `applies_when` so the requirement fires only once a close has begun recording)
were rejected in `WU-06`'s Context, and the operator accepted the pristine-entry skip at
arming time. The consequence is that a close's honesty about what it did not verify now
rests on the deferred-verification list and this retrospective, not on the linter.

**2. `GATE-NN-CRITERIA.md` appears in close and close-intermediate sessions
(added, behavioural).** `precreate_dispatch_skeleton` now writes a new file into the
feature folder at dispatch for `close` and `close-intermediate` work units, seeded from
the gate's substantive units' acceptance criteria and additive across re-dispatches — an
existing entry is never rewritten, a new criterion is appended `unverified`, and a
criterion that has disappeared is left in place rather than deleted. It remains a no-op
for `plan-next` and every other work-unit type. Anything that enumerates a feature
folder's contents, or asserts on its file list, will see the new file.

**3. A new `applies_when` value, `criteria_artifact_present`
(added, registry contract).** `closing_requirements.Requirement` accepts a sixth
`applies_when` value alongside `always`, `verdict_met`, `verdict_hedged`,
`failures_present`, and `autoclose_debt_marker`, and its docstring enumerates it. Any
downstream consumer that switches exhaustively on `applies_when` — a custom lint, a
reporting script — gains a case it does not handle.

**4. `specfuse/loop/criteria_state.py`, a new importable module shipped in the wheel
(added).** Public surface: `ORACLE_KINDS` (`narrow`, `broad`), `CRITERION_STATES`
(`pass`, `fail`, `unverified`), `CriterionStateEntry`, `parse_criteria_state`,
`render_criteria_state`, and `criterion_id_for`. Additive as an import path; nothing
previously occupied it.

**5. `close-discipline.md` §5, and the two templates that point at it
(changed, vendored documentation).** The rule gains
`## 5. Per-criterion state and the narrow/broad oracle contract`, placed between §4 and
the project-local split, and `GATE.template.md` and `WU.template.md` each carry a
one-line pointer to it. All three files are vendored: `specfuse upgrade` overwrites the
`.specfuse/` copy in every downstream project, so the new section arrives without any
consumer action. Documentation only — no behaviour rides on it.

**6. `criteria_state.criteria_filename(gate_n)` and `criteria_state.CRITERIA_FILENAME_RE`
(added, gate 2).** The artifact's basename was an f-string literal in three places
(`loop.py`, and twice in `lint_closing.py`); it now has one home.
`criteria_filename(1)` returns `GATE-01-CRITERIA.md` and `criteria_filename(12)` returns
`GATE-12-CRITERIA.md`; `CRITERIA_FILENAME_RE` matches those basenames and does not match
`GATE-NN.md`, `GATE-NN-REVIEW.md`, or `RETROSPECTIVE.md`. Additive to a module that
already shipped. Any downstream consumer constructing the filename by hand should switch
to the helper, and any consumer matching it by hand should use the pattern — the literal
was never a documented contract, but it is one now.

**7. `criteria_state.build_reverification_worklist` and the `ReverificationWorklist`
dataclass (added, gate 2).** `build_reverification_worklist(entries, current_attempt)`
returns a frozen dataclass with `carry_forward`, `reverify`, and `oracle_groups`. It is
pure — no file, process, or environment access — and it is where this feature's central
policy lives, so it is the surface a downstream project would read to answer "what is my
close allowed to skip?" **The policy it encodes is the reviewable part:** an entry
carries forward only when `kind == "narrow"` **and** `state == "pass"` **and** `oracle`
and `attempt` are both non-empty; everything else re-verifies, and unclassifiable
entries fail safe into `reverify`. A `broad` entry never carries forward regardless of
its recorded attempt.

**8. `loop.format_reverification_worklist(wu, feature_dir)` (added, gate 2).** Renders
the partition into a prompt section. Returns `""` for any work-unit type other than
`close`/`close-intermediate`, when the artifact is absent, and when it parses to zero
entries. Importable from `specfuse.loop.loop` alongside the other dispatch helpers.

**9. `_clean_attempt_untracked` gains a permanent, driver-wide carve-out
(changed, behavioural — the widest-blast-radius item in this list).** The per-attempt
cleanup that deletes untracked files appearing since the dispatch-time snapshot now
never unlinks a file whose basename matches `CRITERIA_FILENAME_RE`, joining the single
pre-existing carve-out for `events.jsonl`. **This applies to every feature in every
downstream project after upgrade, not only to features using this artifact** — any file
named `GATE-NN-CRITERIA.md` anywhere in the tree now survives a failed attempt's
cleanup. `GATE-02-REVIEW.md` open question 4 put this blast radius to the operator
explicitly, against the narrower parameter-threading alternative and its ~15 call-site
edits, and the broad carve-out was accepted at arming time. The bound is real and was
asserted: an unrelated untracked file created after the snapshot in the same feature
folder is still deleted.

**10. Every `close` and `close-intermediate` session now receives a new prompt section
(changed, behavioural).** `execute_unit_attempt` appends a
`## Re-verification worklist (gate N)` section to the work-unit body at dispatch, after
the pre-dispatch oracle-capture section and before the agent session starts. It states
the carried-forward and re-verify counts, lists each carried-forward criterion with its
oracle and the attempt it was proved on, lists the grouped re-verification commands one
line per distinct oracle, and always ends with an unconditional statement that the
close's own `close-discipline.md` §1 feature-level question is never carried forward.
Consumer-visible in the literal sense: **the prompt every close agent reads has
changed**, in every downstream project, on every close dispatch, whether or not that
project ever annotates an entry. `plan-next` and all other work-unit types are
unaffected.

Not contract changes, and named here so the absences are on record rather than assumed:
`extract_wu_criteria` was hoisted out of `build_autoclose_debt_enumeration` in gate 1
and that function's output is unchanged (its five scoped regression tests pass
unmodified); `parse_criteria_state`, `render_criteria_state`, and `criterion_id_for`
are unchanged by gate 2; and the `close-l` / `close-intermediate-f` registry records
still carry the same `applies_when` and `enforced_by` values gate 1 gave them.

**Human acknowledgment of this list has not been obtained, and this close does not
claim otherwise.** `close-discipline.md` §3 requires explicit human acknowledgment; a
dispatched work-unit session has no human to ask, and `operator-escalation.md` is
explicit that an agent drafting the acknowledgment has removed the signature it was
collecting. The enumeration is complete for both gates and the changelog entries are
written, so the acknowledgment is the only outstanding act on this surface.

**How this close discharges that requirement rather than spinning on it.** The verdict
below is `met_locally`, and the acknowledgment is carried as an
`acceptance-discharged` entry in the hedged-verdict record — the classification
`close-discipline.md` §2 defines as *"needs a human signature; accepting IS the
discharge."* On a hedged verdict the driver leaves the terminal gate `awaiting_review`,
the roadmap row `active`, and `PLAN.md` `active`; **nothing flips until a human accepts,
which is exactly the block §3 asks for, expressed in the mechanism built for it.**
Emitting `status: blocked` instead would produce no retrospective, no changelog entry
and no enumeration to acknowledge, and would burn three attempts before escalating —
which this unit's voided dispatch already demonstrated at a cost of $3.66. The operator
path is `/accept-hedged-close`, which records the reason and re-checks the verdict
through the driver's `--recheck-verdict` primitive so the terminal flips fire through
their single owner.

**Two items need a real decision rather than a nod:** item 1, because it weakens what
the closing lint enforces, and item 9, because it is a permanent driver-wide behaviour
change affecting every downstream project.

## Hedged-verdict follow-up record

The terminal verdict is **`met_locally`**. Every acceptance criterion of `T05`–`T08`
was delivered and every oracle across both gates is green; three criteria are unmet or
unverifiable in this environment, one per entry below. Per `close-discipline.md` §2 each
entry carries the criterion verbatim, why it is not `met` here, the exact re-run
condition that would upgrade it, and a `kind:` written by this close.

One entry is `externally-verifiable-later`, so the verdict ceiling is **`met`**: real
rework exists, and the operator has a genuine choice between accepting the hedge now and
waiting for that condition.

### Human acknowledgment of the consumer-visible contract-change list

**Criterion, verbatim (acceptance criterion 9):** *"Enumerate every addition, removal,
or rename across both gates, block on explicit human acknowledgment, and append each
item to `CHANGELOG.md`'s `Unreleased` section carrying `FEAT-2026-0056`."*

**Why it is not `met` here.** The enumeration and the changelog append are done — ten
items across both gates, restated where `T06` changed gate 1's behaviour, appended to
`Unreleased` and traced to this feature. The acknowledgment is not, and cannot be: a
dispatched work-unit session has no human to ask, and `operator-escalation.md` is
explicit that an agent that drafts the acknowledgment has destroyed the signature it was
collecting. `GATE-02.md` § *Arming discipline* records that the operator deliberately
deferred gate 1's list to this combined enumeration, so this single acknowledgment
covers both gates.

**Re-run condition that upgrades this to `met`.** A human reads
§ *Consumer-visible contract changes* above — items 1 and 9 in particular, being the
weakening of the closing lint and the permanent driver-wide cleanup carve-out — and
accepts, via `/accept-hedged-close`, which records the reason and re-checks the verdict
through the driver's `--recheck-verdict` primitive so the terminal flips fire through
their single owner.

**kind:** `acceptance-discharged`

### `T05` criterion 6 — the `events.jsonl` carve-out is not asserted in the module its criterion names

**Criterion, verbatim:** *"`_clean_attempt_untracked` still never unlinks `events_path`
— the existing carve-out is intact, asserted in the same test module."*

**Why it is not `met` here.** Two clauses, and they came apart. The behaviour clause
holds and was verified in this session against the real function on a real git working
tree (`events.jsonl survives: True`). The evidence clause does not:
`tests/test_loop_criteria_survival.py` contains exactly one test, which builds an
`events_path`, passes it to `_clean_attempt_untracked`, never creates the file and never
asserts on it. This is not an environment limitation — it is an unmet coverage
requirement that this close found precisely because it re-ran the oracle rather than
inheriting `T05`'s self-report, and it is the reason `T05#6` is recorded `state: fail`
in `GATE-02-CRITERIA.md`. `specfuse/` and `tests/` are outside this unit's boundary, and
`close-discipline.md` §1 plus this unit's *Do not touch* both say a close records what it
found rather than repairing it.

**Re-run condition that upgrades this to `met`.** A work unit adds an assertion to
`tests/test_loop_criteria_survival.py` that creates `events_path` before the
`_clean_attempt_untracked` call and asserts it still exists after — the probe in
§ *Oracle re-runs* above is the assertion, one line of it — and
`python3 -m unittest tests.test_loop_criteria_survival` then reports at least 2 tests,
OK. At that point `T05#6` flips to `state: pass` and this entry is discharged.

**kind:** `externally-verifiable-later`

### The red-before-green observation for `T05 c1`, `T06 c1`, `T07 c1`, `T08 c1`

**Criteria, in substance (identical across all four, quoting `T07 c1`):**
*"`tests/test_criteria_worklist.py::test_broad_pass_never_carries_forward` exists and
**fails on HEAD before this WU's edits**. Record the failing output in the RESULT block
before editing production code."*

**Why it is not `met` here.** The property is historical: it is a claim about the tree as
it stood before each unit's edits, and it is not observable from a tree in which those
edits have landed. Reproducing it would require reverting `specfuse/`, which is outside
this unit's boundary, and comparing against a commit, which requires git — the driver
owns that surface and this session may not run it. These are the four entries left
**pristine** in `GATE-02-CRITERIA.md`; annotating them to make the closing lint green
would be exactly the inference `close-discipline.md` §5 forbids. The post-condition half
is verified: all four modules pass in this session and the suite is green at 2432.

**Re-run condition that upgrades this to `met`.** None from within a close. The
observation is only ever available to the producing unit's own attempt, whose RESULT
block recorded it, and to the driver's produces-vs-diff guard, which independently
refuses a unit whose declared source went untouched. A close can verify that the
recording exists; it can never re-derive the observation. This is the same entry gate 1
deferred as `D1`, and it is inherent to the position a close occupies in the loop rather
than to this environment.

**kind:** `inherent`

## Lessons

Two lessons are promoted to `.specfuse/LEARNINGS.md`, and two further candidates were
considered and deliberately not promoted.

**Promoted.** *State designed to outlive a retry must be tested against every path that
destroys it, and the path named in the plan is rarely the dangerous one.* Written up in
`LEARNINGS.md` under `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/survival-needs-the-whole-path-set]`.
It generalizes past this feature: any artifact whose value is that it persists across
attempts has a set of destroyers — a fold, a reset, a clean, a regeneration — and a test
that covers one of them reads as coverage of all of them.

**Promoted.** *A console-script entry point and a source checkout are two different
programs; a sweep that measures "the corpus is clean" must name which one it ran.*
Written up as `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/console-script-is-not-the-tree]`.
This is not specific to this feature or this repo — it applies to any project that both
ships a CLI and dogfoods it from source.

**Not promoted — already in `LEARNINGS.md`.** The stale-driver-module finding is
`[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`, entry and rules intact, and its
diagnostic rule (b) is what produced finding 1 in a single command. Adding a second entry
saying the same thing would dilute a file that is loaded whole into every planning
session. The recurrence is recorded in finding 1 instead, where it belongs — as evidence
that the gap is at plan time, not in the rule.

**Not promoted — restates this feature's design.** "A close should record which oracle
proved which criterion" is what FEAT-2026-0056 *is*. A lesson that only names the
feature's own thesis teaches a future work unit nothing it would not read in the plan.

### Gate 2

Two further lessons are promoted, and three candidates were deliberately not.

**Promoted.** *When a criterion names both a property and the place that must assert it,
the oracle that runs that place cannot detect a missing assertion — the evidence clause
needs an oracle of its own.* Written up as
`[FEAT-2026-0056/G2-CLOSE/evidence-clause-needs-its-own-oracle]`, from finding 3. It
generalizes well past this feature: every "still works / unchanged / still intact"
criterion in the corpus has this shape, and each is satisfied by the absence of a
regression — which is also what a missing test looks like.

**Promoted.** *A feature whose value is that the second run is cheaper cannot be
demonstrated by its own terminal close, because that close is a first run; measure the
wiring and close with a falsifiable prediction instead.* Written up as
`[FEAT-2026-0056/G2-CLOSE/a-cache-cannot-prove-itself-on-attempt-one]`. This is the
lesson this gate paid for most directly — acceptance criterion 3 asked for a non-empty
carried-forward set from a dispatch that could not produce one under any implementation
— and it applies to memoization, incremental regeneration, warm caches, and skip
policies alike, none of which are specific to Specfuse.

**Not promoted — already in `LEARNINGS.md` and explicitly excluded by this unit's
criterion 10.** `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/survival-needs-the-whole-path-set]`
and `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`. Both were consumed at plan
time by gate 2 rather than rediscovered: the first produced `T05`, and the second became
an explicit operator step in `GATE-02.md` and criterion 2 of this unit. **That is the
outcome gate 1's finding 1 asked for** — it observed that the restart lesson was already
in `LEARNINGS.md` when gate 1 was planned and simply was not consumed, and named the gap
as plan-time rather than in the rule. Gate 2 consumed it, the check fired, and this close
is the first observation in the feature made against the code it is about. Re-promoting
either would dilute a file loaded whole into every planning session.

**Not promoted — a recurrence, recorded where it belongs.** The
`consumer_visible_section_is_na` substring hazard bit this close for the second time in
two gates, and gate 1 already routed it to FEAT-2026-0064. A second `LEARNINGS.md` entry
would not change what any future work unit does; the durable fix is the code change
FEAT-2026-0064 owns. Recorded again in § *Consumer-visible contract changes* with the
detail that gate 1 escaped it only because a line wrap split the phrase, which is a
fragile reason to be green.

**Not promoted — plan-time estimation, too thin on evidence.** Across both gates,
implementation units came in 44–51% under plan while every closing unit came in over.
Three closing units is not a portfolio, and `PLAN.md` already opens with the
corpus-level version of this claim. Recorded in § *Cost analysis* as a signal for the
next plan rather than promoted as a rule.

## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Operator's reason, verbatim:** *"The next feature will exercise the worklist on
repeat closes; accepting now"*

**Recorded:** 2026-08-07T01:15:49Z, via `/accept-hedged-close`.

**Computed ceiling at acceptance:** `rework exists` — one entry carried
`externally-verifiable-later`. See the note on entry 2 below: that entry's named
re-run condition had already been met by the time of acceptance, so the computed
ceiling reflects the record as the close wrote it rather than the state of the
tree at acceptance. No entry was rewritten to change the computed value.

**These follow-ups remain OPEN.** Accepting the hedge ships the feature with them
outstanding; it does not resolve, discharge, or close any of them, except where
the kind itself makes acceptance the discharge (entry 1). They are carried forward
here verbatim from § *Hedged-verdict follow-up record* above.

### Carried forward — 1. Human acknowledgment of the consumer-visible contract-change list

**kind:** `acceptance-discharged`

**Criterion, verbatim:** *"Enumerate every addition, removal, or rename across both
gates, block on explicit human acknowledgment, and append each item to
`CHANGELOG.md`'s `Unreleased` section carrying `FEAT-2026-0056`."*

**Status at acceptance.** The enumeration (ten items, both gates) and the changelog
append were complete before acceptance. The acknowledgment is discharged BY this
acceptance — that is what `acceptance-discharged` means. The full list was quoted to
the operator in full before the reason was given, with the two items flagged by the
close as needing a real decision rather than a nod: **item 1**, the new blocking
closing-lint finding, whose narrowing by `T06` means a close may now leave a
criterion unannotated and still lint clean — so the lint enforces "everything you
claimed is well-formed", not "everything was verified"; and **item 9**, the permanent
driver-wide `_clean_attempt_untracked` carve-out, which applies to every feature in
every downstream project after upgrade, not only to features using this artifact.

### Carried forward — 2. `T05` criterion 6, the `events.jsonl` carve-out assertion

**kind:** `externally-verifiable-later`

**Criterion, verbatim:** *"`_clean_attempt_untracked` still never unlinks
`events_path` — the existing carve-out is intact, asserted in the same test module."*

**Re-run condition named by the close, verbatim:** *"A work unit adds an assertion to
`tests/test_loop_criteria_survival.py` that creates `events_path` before the
`_clean_attempt_untracked` call and asserts it still exists after … and
`python3 -m unittest tests.test_loop_criteria_survival` then reports at least 2
tests, OK. At that point `T05#6` flips to `state: pass` and this entry is
discharged."*

**Status at acceptance — this condition was MET post-close, before acceptance.**
`test_events_jsonl_carve_out_is_intact` was added at `04fbc80`; the module reports 2
tests, OK. The assertion was mutation-verified: replacing `keep =
events_path.resolve()` with `keep = None` in `_clean_attempt_untracked` fails that
test and only that test. `GATE-02-CRITERIA.md`'s `T05#6` was flipped `fail` → `pass`
at `3ebb913` with a provenance line recording that the flip was made post-close by an
operator-directed session rather than by the close WU, per `close-discipline.md` §5.
The entry is retained verbatim above rather than deleted, because the close wrote it
correctly for the tree it saw.

### Carried forward — 3. The red-before-green observation for `T05 c1`, `T06 c1`, `T07 c1`, `T08 c1`

**kind:** `inherent`

**Criterion, in substance (identical across all four, quoting `T07 c1`):**
*"`tests/test_criteria_worklist.py::test_broad_pass_never_carries_forward` exists and
**fails on HEAD before this WU's edits**. Record the failing output in the RESULT
block before editing production code."*

**Re-run condition named by the close, verbatim:** *"None from within a close."* The
observation is only ever available to the producing unit's own attempt, whose RESULT
block recorded it, and to the driver's produces-vs-diff guard. A close can verify the
recording exists; it can never re-derive the observation. These are the four entries
left pristine in `GATE-02-CRITERIA.md` — annotating them to green the lint would be
the inference `close-discipline.md` §5 forbids.

**No `routed-finding` entries**, so no tracking surface was collected for any entry.

### What the operator's reason commits to, and where it gets checked

The reason names the next feature as the place the worklist gets exercised on repeat
closes. That is the feature's central unmeasured claim: `RETROSPECTIVE.md`
§ *The close-cost delta, honestly* records 0 of 44 criteria and 0 oracle invocations
skipped on this run, because a first attempt has an empty carry-forward set by
construction, and states that the saving remains **unmeasured, not disproven**. This
acceptance ships that measurement forward rather than staging it here.
