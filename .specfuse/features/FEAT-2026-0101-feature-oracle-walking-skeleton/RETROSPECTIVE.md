# Retrospective — FEAT-2026-0101, the feature oracle and the walking skeleton

## Gate 1

A gate's definition of done is now an executable command. `GATE-NN.md`
frontmatter carries one `feature_oracle`; `verify()` reads it, appends it to
the gate list the unit was already going to run, and hands the whole list to
the existing `_run_gate_set`. The close re-runs it and records the verdict
where the judge reads. A lint rule refuses a gate that declares none once its
feature goes `active`.

Five substantive units (T01 tracer bullet, T02 close requirement, T03 lint
rule, T04 authoring surfaces, T05 unrunnable-oracle attribution), one terminal
close closed twice. One unit spun three attempts and was re-armed.

T05 and this second close exist because the judge lowered attempt 1's `met` to
`not_met` (issue #3260): a declared oracle naming a command the shell cannot run
was reported as an ordinary gate `FAIL`, so a typo'd declaration read as the
unit's defect. T05 adds run-time attribution by exit status 127, and the gate's
definition of done was **narrowed** — pre-flight resolution of an arbitrary
shell string is now explicitly out of scope, because it is not reliably
decidable and the judge was right to refuse a `met` against the original
wording. The measurements below are against the narrowed wording; the narrowing
is stated in the section itself rather than left for a reader to infer.

## Measurements

Every command below was run in this close session — attempt 2 — in this working
tree, on branch `feat/FEAT-2026-0101-feature-oracle-walking-skeleton`. Exit
statuses are the shell's, read directly. Nothing here is carried forward from
attempt 1; every number was re-measured after T05 landed.

### feature_oracle: PASS

```
$ python3 -m unittest tests.test_feature_oracle_e2e -q
Ran 4 tests in 0.075s
OK
exit 0
```

This is the gate's declared `feature_oracle`, re-run fresh. It is the
feature-level question the five units were each too small to ask: it builds a
temp feature folder whose `GATE-01.md` declares an oracle, drives a real
`WorkUnit` through `verify()`, and asserts the oracle command *executed* —
proven by a marker file the command itself writes — not that a helper returned
the right value.

This verdict is *not* the guard-wiring audit. It proves the mechanism runs in
this session against a synthetic feature folder. It says nothing about whether
the lint rule, the closing requirement, or the authoring surfaces are reachable
from the paths they were meant to intercept. Those are audited separately,
below, and the two must not be read as one result.

### The bar was narrowed, not met as originally written

Read the numbers below against the definition of done as it now reads. Attempt 1
recorded `met`; the judge lowered it to `not_met` and filed issue #3260. The bar
for the unrunnable-oracle bullet was subsequently narrowed — the original
wording demanded a CONFIGURATION ERROR "before any unit dispatches" for a
command that "cannot be resolved", and pre-flight resolution of an arbitrary
shell string (pipes, `&&`, environment-dependent lookup) is not reliably
decidable. `GATE-01.md` now puts pre-flight resolution explicitly out of scope
and asks for run-time attribution by exit status instead. Bullet 5 below is
measured against the narrowed wording and is green; it would still be red
against the original wording. The narrowing itself is the thing to weigh, not
only the measurement.

### Definition of done, bullet by bullet

| # | `GATE-01.md` definition-of-done bullet | Command run in this session | Exit |
|---|---|---|---|
| 1 | Gate declares `feature_oracle`; driver reads it, synthesizes a one-element gate list, runs it through the existing `_run_gate_set`; no second execution path | `python3 -m unittest tests.test_feature_oracle_e2e -q` plus `grep -n "_run_gate_set(" specfuse/loop/*.py` | 0 / 0 |
| 2 | The oracle runs as part of **every unit's verification** in that gate | `python3 -m unittest tests.test_feature_oracle_e2e -q` + the call-chain audit below | 0 |
| 3 | The close re-runs it and records the verdict in `## Measurements`; `specfuse lint --closing` fails a close that omits it | `python3 -m unittest tests.test_close_records_feature_oracle -q`; live negative observation below | 0 |
| 4 | A declared oracle that is empty or whitespace-only is a CONFIGURATION ERROR before any unit dispatches | `python3 -m unittest tests.test_feature_oracle_e2e -q` + live probe below | 0 |
| 5 | **(narrowed)** An oracle whose command the shell cannot run (exit 127) is reported as a configuration problem naming the gate file, not an ordinary `FAIL` | `python3 -m unittest tests.test_oracle_unrunnable_attribution -q` + the issue #3260 probe below | 0 |
| 6 | No-oracle gate: ERROR when `active`, WARN when `planned`/`blocked`/`deferred`, skipped when gate `passed` or feature `done`/`abandoned`; sweep zero ERRORs, exactly four WARNs | `python3 -m unittest tests.test_lint_feature_oracle_declared -q`; sweep + six-branch negative observation below | 0 |
| 7 | `GATE.template.md` carries the key; `/draft-feature` refuses a gate without one; `plan-next` states how the drafted oracle advances the prior gate's; `methodology.md` documents it in one home | five greps + four mirror `diff`s below, plus `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_scaffold_resources -q` | 0 |
| 8 | Per-criterion state and the narrow/broad oracle contract (`close-discipline.md` §5) | `specfuse lint --closing` from the checkout — `close-l` reported not-applicable | see §8 note |

**Bullet 1's second command, verbatim:**

```
$ grep -n "_run_gate_set(" specfuse/loop/*.py
specfuse/loop/loop.py:4067:def _run_gate_set(
specfuse/loop/loop.py:4280:    gate_results = _run_gate_set(gate_set, feature_dir, _capture_returncodes=returncodes)
specfuse/loop/loop.py:4331:    gate_results = _run_gate_set(gate_set, feature_dir)
specfuse/loop/prerun.py:120:        result = _run_gate_set([gate], feature_dir)[0]
specfuse/loop/prerun.py:132:    oracle_results = _run_gate_set(oracle_gates, feature_dir) if oracle_gates else []
exit 0
```

One definition and four call sites, all pre-existing: `4280` is `verify()`,
`4331` is `probe_baseline()`, and `prerun.py`'s two are the pre-dispatch input
oracles. The feature oracle is appended to the list `verify()` was already
building and goes through `4280` with everything else — no fifth call site, no
`subprocess` of its own, no second execution path. T05 added an **optional
out-parameter** (`_capture_returncodes`) to that one runner rather than a second
path; see the guard-wiring audit for why that is the narrow change.

**Bullets 4 and 5 — live probes, run in this session.** Four calls into the real
`loop.verify()` against a temp feature folder, one per branch. The first is the
judge's own reproduction from issue #3260:

```
--- issue #3260: nonexistent binary        oracle: "totally-nonexistent-command-zzz"
    ok=False   report names gate file: True
    | CONFIGURATION ERROR: /tmp/.../GATE-01.md declares `feature_oracle:
      'totally-nonexistent-command-zzz'` but that command could not be run
      (exit 127 — command not found). This is not a work-unit failure — fix
      GATE-01.md and re-run.

--- boundary: oracle runs, genuinely fails  oracle: python3 -c 'import sys; sys.exit(1)'
    ok=False   report names gate file: False
    | ### feature_oracle: FAIL

--- boundary: failing test PRINTS 'command not found'
    ok=False   report names gate file: False
    | ### feature_oracle: FAIL

--- T01 path: empty declaration             oracle: ""
    ok=False   report names gate file: True
    | CONFIGURATION ERROR: /tmp/.../GATE-01.md declares `feature_oracle` but its
      value is empty (or not a string). This is not a work-unit failure — fix
      GATE-01.md and re-run.
exit 0
```

This is the negative observation bullet 5 needs, in both directions. The exact
scenario that produced the judge's `not_met` now reports a configuration problem
naming the gate file. Both boundary cases stay ordinary `FAIL`s — including an
oracle that **prints the words `command not found` while failing for a real
reason**, which proves the classification keys on exit status and not on message
text. Nothing passes silently in any of the four; `ok=False` throughout. Bullet
4's empty-declaration path is unchanged in shape by T05.

**Bullet 7's five greps, verbatim results:**

```
$ grep -n "feature_oracle" .specfuse/templates/GATE.template.md
4:# feature_oracle: "<command>"   # REQUIRED for a drafted gate. The executable proof of
exit 0

$ grep -c "feature_oracle" plugins/specfuse/skills/draft-feature/SKILL.md
4                                          (lines 53, 54, 247, 276)
exit 0

$ grep -n "Tracer bullet" plugins/specfuse/skills/authoring-work-units/SKILL.md
179:## 14. Tracer bullet — stubs permitted only in the unit that turns the oracle green
exit 0

$ grep -rn "advances the prior gate" docs/ plugins/
docs/methodology.md:570:advances the prior gate's oracle — in prose, as a judgment call, not as a
exit 0

$ grep -n "feature_oracle" docs/methodology.md
89:- `feature_oracle` — GATE-level, not WU-level: lives in `GATE-NN.md`
569:`feature_oracle`, and its review summary must state how the drafted oracle
exit 0
```

Line 89 is the frontmatter reference (the key's one home, beside `oracle_env`);
line 569 is §7's `plan-next` obligation, which points at it rather than
redefining it. Two mentions, one definition.

Mirror sync, all four `diff`s clean:

```
$ diff -r plugins/specfuse/skills/draft-feature .specfuse/skills/draft-feature              -> exit 0
$ diff -r plugins/specfuse/skills/authoring-work-units .specfuse/skills/authoring-work-units -> exit 0
$ diff .specfuse/rules/close-discipline.md specfuse/loop/data/rules/close-discipline.md     -> exit 0
$ diff .specfuse/templates/GATE.template.md specfuse/loop/data/templates/GATE.template.md   -> exit 0
```

**§8 note.** `GATE-01-CRITERIA.md` does not exist for this gate, so `close-l`
(`check_criteria_state_well_formed`, `applies_when=criteria_artifact_present`)
never applied and no `kind`/`state` entries were written. The artifact was not
skipped by choice — the driver's own seeder produced nothing. See the
guard-wiring lesson: this is one of two guards found inert on this repo's
artifacts, and neither is a symbol this feature introduced.

### Satisfiability sweep — re-run fresh, with counts

`lint_feature_oracle_declared` applied to every feature folder under
`.specfuse/features/` carrying a `PLAN.md`, each with its own `PLAN.md`
frontmatter as the status input, ERRORs collected from the return value and
WARNs captured from stdout:

```
features swept: 76
ERROR count: 0
WARN count: 4
  WARN: FEAT-2026-0052/GATE-01: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
  WARN: FEAT-2026-0081/GATE-01: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
  WARN: FEAT-2026-0081/GATE-02: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
  WARN: FEAT-2026-0082/GATE-01: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
exit 0
```

**76 folders swept, 0 ERRORs, 4 WARNs.** The four are exactly the four
`GATE-01.md` § Definition of done names: `FEAT-2026-0052/GATE-01`,
`FEAT-2026-0081/GATE-01`, `FEAT-2026-0081/GATE-02`, `FEAT-2026-0082/GATE-01`.
No fifth WARN, no ERROR, no missing entry — so the escalation trigger on a sweep
disagreeing with the four recorded WARNs did not fire. FEAT-2026-0011 has no
gate files and therefore produces no finding of either severity, which is what
`PLAN.md` predicted.

**Negative observation — the rule seen rejecting a purpose-built bad input.** A
green sweep proves the rule is quiet; it does not prove the rule fires. Six
synthetic one-gate feature folders built in a temp directory, one per branch of
the graduation:

```
[ERROR expected (active, no oracle)]        ERRORs=1 WARNs=0
   ERROR: FEAT-9999-9999/GATE-01: gate declares no `feature_oracle` in an active feature — see .specfuse/roadmap.md's oracle contract and declare one before the next dispatch.
[WARN expected (planned, no oracle)]        ERRORs=0 WARNs=1
   WARN: FEAT-9999-9999/GATE-01: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
[WARN expected (blocked, no oracle)]        ERRORs=0 WARNs=1
   WARN: FEAT-9999-9999/GATE-01: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
[clean expected (active, oracle declared)]  ERRORs=0 WARNs=0
[skip expected (feature done)]              ERRORs=0 WARNs=0
[skip expected (gate passed)]               ERRORs=0 WARNs=0
exit 0
```

All six branches behave as specified. The rule is not a rule that fires on
nothing.

**A fixture trap found while building that observation, recorded because it is
the same failure class this feature exists to catch.** The first version of
these six fixtures wrote a `PLAN.md` with frontmatter but **no task-graph
block**, and every branch — including the one built to trip the ERROR —
returned `ERRORs=0 WARNs=0`. The rule was not broken. `_gate_files_from_plan`
resolves gate files from the PLAN graph's `file:` entries and returns nothing
for a PLAN with no readable graph (deliberately, per #2907), so the rule had no
gates to examine and reported clean. A guard reporting "nothing to check" is
indistinguishable from "checked and clean" in a transcript — which is why a
green result from a hand-built fixture is worth nothing until the fixture is
shown capable of producing a finding at all. The counts above are from fixtures
carrying a real graph.

**Negative observation — `close-n` seen rejecting a close that omits the
verdict.** Run live against this feature folder, from the checkout, with the
`### feature_oracle: PASS` line temporarily removed from this document and then
restored. The exact transcript is reproduced under "Oracles re-run fresh" below.

**A trap worth re-recording.** `specfuse lint --closing` invoked as the
installed console script runs the **pipx-installed build**, which predates
`close-n`. Every closing-lint result in this document is from
`python3 -m specfuse.loop.lint_plan ... --closing` in the checkout.

**A second trap, hit while writing this section, and the same class as the
fixture trap above.** `close-n` failed on a draft of this document that *did*
carry `### feature_oracle: PASS` in its `## Measurements` section. The verdict
line was real and correctly formatted; the guard could not see it.
`slice_wu_section` ends an ATX section at the next heading of the same or
shallower level **or at the next line beginning with `**`** — the bold-preamble
form a WU body uses for its sections. A wrapped sentence had left
`**as it now reads**.` at the start of a line above the verdict, which closed
the slice early, so `check_feature_oracle_verdict_recorded` searched 376
characters of a 4131-character section and found nothing. The fix was to put
`### feature_oracle: PASS` directly under the `## Measurements` heading, ahead
of all narrative. Recorded because the failure mode is this feature's own
subject seen from the other side: the guard fired correctly on a document that
satisfied the requirement, because the *slice* it was handed did not contain
the evidence. A guard is only as scoped as the text it is given, and in a
retrospective — prose, hand-wrapped, mixing ATX and bold-preamble headings — a
line-initial `**` is an invisible section terminator.

### Failure-class breakdown

| failure_class | non-passed attempts | dominant signature |
|---------------|---------------------|--------------------|
| tests | 3 | test_package_data_matches_canonical |
| **total** | **3** | — |

All three belong to T02, before its re-arm, and are unchanged from attempt 1:
two were `test_package_data_matches_canonical` (the `.specfuse/rules/` →
`specfuse/loop/data/rules/` mirror left stale) and one was
`test_every_requirement_names_a_real_guard_function` (a registry entry naming a
guard function that did not exist). T05 added no failed attempts — it passed at
attempt 1. The close itself has one non-passing outcome that does **not** appear
in this table: attempt 1's `met` was lowered to `not_met` by the judge, which
`events.jsonl` records as a `judged` event (`lowered: true`, `disagreed: true`,
`findings: 1`) rather than as a failed `attempt_outcome`.

This table was produced by `summarize_attempt_failure_classes(feature_dir, None,
exclude_correlation_id="FEAT-2026-0101/G1-CLOSE")`. Called the way the driver
calls it — with `gate_n=1` — the same function returns `(no non-passing attempts
in scope)`. See the guard-wiring lesson.

### Oracles re-run fresh for this close

```
$ python3 -m unittest discover -s tests -q
Ran 3772 tests in 171.716s
OK (skipped=3)
exit 0

$ bash scripts/smoke-test.sh
16 gates; 26 TAP assertions, 0 failures
smoke test: OK
exit 0

$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
exit 0

$ python3 .specfuse/scripts/lint_plan.py <this feature dir>      # the `plannext` gate set
WARN: WU-04-authoring-surfaces.md: implementation WU mentions driver wiring (['loop.py']) but `produces_driver_helper` frontmatter is empty.
WARN: WU-05-unrunnable-oracle-attribution.md: implementation WU mentions driver wiring (['loop.py']) but `produces_driver_helper` frontmatter is empty.
OK — <this feature dir> is structurally valid.
exit 0

$ python3 -m unittest tests.test_feature_oracle_e2e -q             # the gate's feature_oracle
Ran 4 tests in 0.075s / OK / exit 0

$ python3 -m unittest tests.test_oracle_unrunnable_attribution -q   # T05
Ran 4 tests in 0.101s / OK / exit 0

$ python3 -m unittest tests.test_close_records_feature_oracle -q
Ran 3 tests in 0.293s / OK / exit 0

$ python3 -m unittest tests.test_lint_feature_oracle_declared -q
Ran 6 tests in 0.010s / OK / exit 0

$ python3 -m unittest tests.test_scaffold_data_in_sync tests.test_scaffold_resources -q
Ran 9 tests in 0.017s / OK / exit 0

$ for d in .specfuse/features/*/; do python3 -m specfuse.loop.lint_plan "$d"; done
feature folders linted: 76
folders with ERROR: 0
```

`specfuse lint` over every feature folder: **76 linted, 0 with any ERROR.**

Both the full suite and the smoke script were run twice: once before this
document, `CHANGELOG.md` and `.specfuse/LEARNINGS.md` were written (3772 tests,
189.210s, `OK`; 26 TAP assertions, 0 failures, exit 0) and once after (the
transcript above). The gate's `feature_oracle`, the 76-folder `specfuse lint`,
the leak scan and the `plannext` set were likewise re-run after the edits with
identical results.

**Deltas from attempt 1, stated rather than glossed.** The suite grew from 3768
to **3772 tests** — T05's four. The `plannext` lint now reports **two** WARNs
rather than one: T05 also edits `specfuse/loop/loop.py` and also declares an
empty `produces_driver_helper`. That is arguably correct for T05, which adds an
inline branch inside `verify()` and no new named driver helper, but the WARN is
real, it is on this feature's own work unit, and it is reported rather than
explained away. Neither WARN is an ERROR and neither affects the gate's exit
status.

The `close-n` negative observation, in full:

```
$ python3 -m specfuse.loop.lint_plan <this feature dir> --closing    # verdict line removed
FAIL — 1 unmet closing requirement(s):
  - close-n: gate 1 declares feature_oracle but RETROSPECTIVE.md's 'Measurements' section records no 'feature_oracle' PASS/FAIL verdict — would fail check_feature_oracle_verdict_recorded after squash
exit 1

$ python3 -m specfuse.loop.lint_plan <this feature dir> --closing    # verdict line restored
CLOSING-READY
exit 0
```

## Guard-wiring audit

`[FEAT-2026-0008/G1-CLOSE]`: a feature that fixes a methodology failure mode
must verify at close that its guards **landed and are wired into the path they
were meant to intercept**. A definition is not evidence; a call site is. An
unwired helper is a hollow pass with extra steps, and hollow-passing the close
of an anti-hollow-pass feature is the worst-case recursive failure — so this
audit, not the gate's own green oracle, is what the escalation trigger watches.

Four items, each audited for a definition **and** a caller in the named path.

### 1. `read_gate_feature_oracle` (T01) — wired into `verify()`

```
$ grep -n "def read_gate_feature_oracle" specfuse/loop/loop.py
4521:def read_gate_feature_oracle(gate_file: Path) -> "str | None":

$ grep -n "read_gate_feature_oracle(" specfuse/loop/loop.py
4267:        oracle_command = read_gate_feature_oracle(Path(gate_file))
4521:def read_gate_feature_oracle(gate_file: Path) -> "str | None":
```

DEFINITION at `loop.py:4521`. CALL SITE at `loop.py:4267`. `verify()` spans
`loop.py:4206` to `loop.py:4306` (the next top-level `def` is `probe_baseline`
at `4307`), so `4267` is inside `verify()`. The call is followed at `4275` by
`gate_set = gate_set + [{"name": "feature_oracle", "command": oracle_command}]`
and at `4280` by the single pre-existing `_run_gate_set(...)`.

The chain from the driver's real dispatch path, so the wiring is not merely
test-visible:

```
run()                       loop.py:7980  execute_unit_attempt(..., gate_file=gate.file)
execute_unit_attempt()      loop.py:4769  verify_fn(wu, feature_dir, gate_file=gate_file)
verify()                    loop.py:4267  read_gate_feature_oracle(Path(gate_file))
verify()                    loop.py:4280  _run_gate_set(gate_set, feature_dir, ...)
```

`gate.file` is a real path to the WU's own `GATE-NN.md`, passed unconditionally
for every unit in the gate, not only closing ones. `_accepts_gate_file(verify_fn)`
at `4768` is a compatibility branch for test doubles whose signature predates the
parameter; the production `verify` accepts it and takes the `4769` branch.

**Verdict: wired.** Definition and call site both present, call site inside
`verify()`, and `verify()` reached from `run()` with a non-`None` `gate_file`.

### 2. `lint_feature_oracle_declared` (T03) — wired into the plan-lint entry point

```
$ grep -n "lint_feature_oracle_declared" specfuse/loop/lint_plan.py
971:def lint_feature_oracle_declared(feature_dir: Path, plan_fm: dict) -> list[str]:
2055:    errs.extend(lint_feature_oracle_declared(feature_dir, fm))
```

DEFINITION at `lint_plan.py:971`. CALL SITE at `lint_plan.py:2055`, inside
`_lint_impl()` (`1675`–`2093`), alongside its sibling rules `lint_ac_observable`
and `lint_close_verdict_not_predecided`. `lint()` (`lint_plan.py:1660`) delegates
to `_lint_impl`, and `main()` (`2199`) calls `lint()` — the path
`specfuse lint <feature-dir>` actually takes.

**Verdict: wired.** Confirmed behaviourally as well: the 76-folder sweep and the
six-branch negative observation above both run through this rule, and the
negative observation produces both an ERROR and a WARN from it.

### 3. `close-n` / `check_feature_oracle_verdict_recorded` (T02) — wired into the closing lint

```
$ grep -n "close-n\|check_feature_oracle_verdict_recorded" specfuse/loop/closing_requirements.py
353:            id="close-n", wu_type="close", phase="pre-squash",
363:            enforced_by="check_feature_oracle_verdict_recorded",

$ grep -n "check_feature_oracle_verdict_recorded" specfuse/loop/lint_closing.py
297:def check_feature_oracle_verdict_recorded(req: creq.Requirement, ctx: ClosingContext):
410:    "check_feature_oracle_verdict_recorded": check_feature_oracle_verdict_recorded,
```

REGISTRY ENTRY at `closing_requirements.py:353`, naming
`enforced_by="check_feature_oracle_verdict_recorded"`. DEFINITION at
`lint_closing.py:297`. CALL SITE: the guard is bound into the `_CHECKS` dispatch
table at `lint_closing.py:410` and invoked at `lint_closing.py:512`
(`checker = _CHECKS.get(req.enforced_by)`, then `result = checker(req, ctx)` at
`523`), inside `lint_closing()`, which `main_closing()` calls at
`lint_closing.py:537`, which `lint_plan.main()` calls under `--closing` at
`lint_plan.py:2232`.

A registry entry naming a guard the dispatch table has no entry for is not a
silent pass either — `lint_closing.py:513-521` emits an explicit
"registry/lint drift, escalate" finding.

**Verdict: wired.** Confirmed behaviourally by the live negative observation:
`close-n` fired on this very close when the verdict line was removed and cleared
when it was restored.

### 4. The exit-127 attribution branch (T05) — wired into the same `verify()` oracle path

T05 is the unit added after the judge's `not_met`, so its wiring is the one this
attempt most owes evidence for. It introduces **no new named helper** — the
"definition" is an optional out-parameter on the existing runner plus an inline
branch in `verify()`, which is precisely the narrow change the WU asked for. The
audit question is therefore whether both halves are on the executed path, not
whether a symbol has a caller.

```
$ grep -n "_capture_returncodes" specfuse/loop/loop.py
4069:    _capture_returncodes: "dict | None" = None,
4087:    `_capture_returncodes` (FEAT-2026-0101/T05) is an optional out-parameter:
4166:            if _capture_returncodes is not None:
4167:                _capture_returncodes[gate["name"]] = proc.returncode
4280:    gate_results = _run_gate_set(gate_set, feature_dir, _capture_returncodes=returncodes)

$ grep -n "127" specfuse/loop/loop.py
4092:    oracle command could not even be found" (exit 127) from "the oracle ran
4282:        # An oracle the shell could not even run (exit 127 — "command not
4290:            and returncodes.get("feature_oracle") == 127):
4297:        f"could not be run (exit 127 — command not found). This "
```

PRODUCER at `loop.py:4166-4167`, inside `_run_gate_set`'s subprocess branch — the
raw `returncode` is recorded under the gate's name. CONSUMER at `loop.py:4289-4290`,
inside `verify()`, guarded on `g["name"] == "feature_oracle" and not g["ok"]`.
The two are connected at `loop.py:4280`, where `verify()` passes the dict it
allocated at `4279` (`returncodes = {} if oracle_declared else None`). All three
line numbers fall inside `verify()`/`_run_gate_set`, both of which item 1 above
already established are reached from `run()`.

Two properties this audit checked specifically, because both are ways this
branch could have landed inert:

- **The out-parameter is actually populated on the oracle gate.** It is written
  in the same loop iteration that spawns the subprocess, so any gate that runs
  records a status. A `SKIP`ped gate (failed `needs:` dependency) never spawns
  and records nothing — `returncodes.get("feature_oracle")` then returns `None`,
  which is not `127`, so the branch correctly declines rather than misreporting.
- **The branch is reachable only when an oracle was declared.** `oracle_declared`
  is `gate_file is not None and oracle_command`; when it is falsy, `returncodes`
  stays `None` and `_run_gate_set` sees its default — so behaviour for every
  gate that declares no oracle is byte-identical to pre-T05, which is what the
  contract promised.

**Verdict: wired, and confirmed behaviourally rather than only structurally.**
The live probe under bullets 4–5 of the measurements drives the real
`loop.verify()` four times: the nonexistent-binary case reports the
configuration problem naming the gate file, and two boundary cases — including
an oracle printing the literal words `command not found` — stay ordinary
`FAIL`s. A branch that never fired, or that fired on everything, would show up
in that transcript. Neither did.

### 5. T04's four authoring surfaces — content, not symbols

T04 introduced no callable symbol, so "definition without a caller" does not
apply. The equivalent question is whether each surface's text sits on the path a
drafting session actually reads. All four greps are reproduced under bullet 7 of
the measurements and all four returned hits: the key with its comment in
`GATE.template.md` (mirrored byte-identically into `specfuse/loop/data/templates/`),
the refusal in `/draft-feature`'s SKILL.md at line 53 with the tracer-bullet
framing at line 276, §14 in `/authoring-work-units` at line 179, and
`docs/methodology.md` carrying the key's one definition (line 89) plus §7's
`plan-next` oracle-progression obligation (line 570) that points at it. Both
skill copies are `diff -r`-identical to their `plugins/` originals.

### Audit result

**Four of four wired; no definition found without a caller in the path it
names.** The escalation trigger — "a definition with no call site in the named
path" — did not fire, and neither did the sweep-disagreement trigger.

**What this audit does not claim.** It establishes that each guard is reachable
and that each fires on a purpose-built bad input. It does not establish that the
oracle ran during T02's, T03's, T04's and T05's own attempts — the artifacts
cannot answer that after the fact — nor that a future gate's oracle will be
stronger than this one's. Both are carried in "What the loop did NOT verify"
rather than absorbed into this verdict.

Two guards belonging to **other** features were again found inert during this
audit — `close-f` (via `summarize_attempt_failure_classes` scoped by `gate_n`)
and `close-l` (via `extract_wu_criteria`'s numbered-item regex). Neither is a
symbol T01–T05 introduced, both sit outside this WU's editable scope, and both
are recorded in the lessons and in "What the loop did NOT verify" rather than
folded into this verdict.

## Cost analysis

**Which planned number.** This close's work unit names `planned_cost_usd`
**$19.00**; `PLAN.md` frontmatter now reads **$21.50**. The WU body is stale by
exactly T05's $2.50 — T05 was added to `PLAN.md` after this close WU was
written, and nobody re-wrote the close body's parenthetical. $21.50 is the
number to reconcile against, and it is the per-WU sum: T01 $3.00, T02 $2.50,
T03 $2.50, T04 $3.00, T05 $2.50, close $8.00. Both figures are reported here so
the discrepancy is on the record rather than silently resolved.

All actuals below are summed from `events.jsonl` `attempt_outcome` payloads —
every attempt, including failed ones — not from the WUs' frontmatter, which
carries only the last attempt's cost.

| WU | Planned | Actual | Delta | Attempts |
|---|---|---|---|---|
| T01 tracer bullet | $3.00 | $3.6376 | +$0.6376 (+21.3%) | 1, passed |
| T02 close requirement | $2.50 | $5.0005 | +$2.5005 (+100.0%) | 3 failed + re-arm, then 1 passed |
| T03 lint rule | $2.50 | $1.9601 | −$0.5399 (−21.6%) | 1, passed |
| T04 authoring surfaces | $3.00 | $1.8249 | −$1.1751 (−39.2%) | 1, passed |
| T05 oracle attribution | $2.50 | $0.5631 | −$1.9369 (−77.5%) | 1, passed |
| **substantive subtotal** | **$13.50** | **$12.9862** | **−$0.5138 (−3.8%)** | 8 attempts, 1 re-arm |
| G1-CLOSE attempt 1 | $8.00 | $9.4483 | +$1.4483 (+18.1%) | 1, passed then judged `not_met` |
| **total so far** | **$21.50** | **$22.4345** | **+$0.9345 (+4.3%)** | this attempt not yet recorded |

Wall clock across the five substantive units: 8932.6s (2h29m), from
`events.jsonl` `attempt_outcome` durations. The close's attempt 1 added 942.3s.

**The delta, named.** Against the current $21.50 plan the feature is **+$0.93
(+4.3%) over**, and that is before this second close session is priced — which
will push it decisively over, because the close was budgeted once and is being
run twice. Against the stale $19.00 in the WU body it is +$3.43 (+18.1%). The
substantive units alone came in **under** plan by $0.51 (−3.8%).

**Restart count: 4 `driver_staleness_detected` events, 3 of them halting.**
Three carry `reason: driver_restart_required` and `halted: true` — after T01
(22:47:59Z, `driver_paths: [loop.py]`), after T02's passing re-armed attempt
(00:36:09Z, `[closing_requirements.py, lint_closing.py]`), and after T05
(02:14:09Z, `[loop.py]`). The fourth (01:14:34Z) is a gate-boundary summary
carrying `edits` and `dispatched_after: []`, with no `reason` and no halt.
`PLAN.md` predicted three restarts, one per unit editing `specfuse/loop/*.py`
(T01, T02, T03); the units that actually forced one were T01, T02 and T05. T03
completed at 00:10:36Z between T02's escalation and its re-arm and produced no
staleness event; T04 edits no driver module and correctly produced none. So the
prediction was right about the *count* for the wrong reason, and T05 — a unit
that did not exist when the prediction was made — supplied the third.

**Re-arm count: 2, and only one of them is in `events.jsonl`.** T02's re-arm is
recorded as a `re_arm_dispatched` event (00:21:48Z, `re_arm_count: 1`). This
close's own re-arm after the judge's `not_met` is recorded **only** in
`WU-90-gate-1-close.md`'s frontmatter (`re_arm_count: 1`, `re_arm_history` with
`prior_status: done`, `prior_cost_usd: 9.448288`, and the reason naming issue
#3260). A reader reconstructing this feature's history from `events.jsonl`
alone would count one re-arm and miss the one that caused an entire second
close. That is an observability gap in the event log, not a bookkeeping error
in the frontmatter, and it is carried into "What the loop did NOT verify".

### Did this feature's recalibration hold?

`PLAN.md` set these estimates from FEAT-2026-0102's actuals (~$1.10 per
substantive unit plus headroom) rather than from the earlier guesses that made
0102's estimates run 2.6× high. On the substantive work the recalibration held,
and on the second axis — how many times a unit or a close runs — it did not.

- **On first-pass work, it held with room to spare.** Excluding T02's three
  spinning attempts, substantive spend was $9.0288 against $13.50 planned —
  **0.67× of plan**, against 2.6× *over* before. Four of five units landed
  under estimate; only T01 came in over, at +21.3%.
- **On the feature as delivered, the substantive half still held**: $12.9862
  against $13.50, −3.8%, *with* the spinning absorbed. This is the number that
  moved most since attempt 1, which reported +12.9% over — T05's $0.5631 against
  a $2.50 budget is what pulled the subtotal back under.
- **The close is where the estimate broke, and not by being too small.** $8.00
  bought one close attempt. The gate needed two, because the first was judged
  `not_met`. Attempt 1 alone was +18.1% over its own budget; the re-run is
  unbudgeted entirely.

The honest summary is that the *per-attempt* estimate recalibrated well and the
*per-unit* estimate still cannot see attempt count — the same finding attempt 1
recorded about T02's spinning, now confirmed a second time in a different shape.
T02 showed a unit can need three attempts; this close shows a **terminal close
can need two**, and a judge that may lower `met` to `not_met` makes that a
structural possibility for every judged gate, not an accident. Neither is
predictable from unit size. This matters beyond bookkeeping: `planned_cost_usd`
feeds `evaluate_auto_close`'s per-WU ratio checks, so an estimate padded for
possible re-runs would make gates auto-close that should not. Estimate the
one-attempt cost and let the overrun be visible — which is what happened here,
and it is why the overrun is legible at all.

## What the loop did NOT verify

Seven criteria this feature's own machinery could not settle, each with the
criterion, the reason it is unsettled, and the surface where it actually gets
checked.

1. **Whether a future `plan-next`'s gate-2 oracle is stronger than gate 1's.**
   Reason: unenforceable by construction — deciding it means comparing two
   shell commands for strength, which is not decidable. `PLAN.md` states this
   as a known limit rather than faking a lint rule for it. Where it is checked:
   `plan-next`'s review summary, per `docs/methodology.md:565-575`, read by the
   human at `/arm-gate`. This feature is single-gate and terminal, so it never
   armed a gate 2 and the obligation has not yet had a first real firing —
   which is exactly the marker-gated-guard weakness `[FEAT-2026-0070/G2-CLOSE]`
   names, accepted here because the alternative is a rule that cannot be
   written.
2. **That the oracle actually ran during T02's, T03's, T04's and T05's own
   attempts.** Reason: `attempt_outcome` events record `outcome`,
   `failure_class` and `failure_signature`, not which gates composed the set,
   so the artifacts cannot answer it after the fact. Where it is checked: this
   close's own driver-run verification traverses the identical code path
   (`run()` → `execute_unit_attempt(gate_file=gate.file)` → `verify()`), and
   the call-chain audit above establishes the path is unconditional for every
   unit type. A per-attempt record of the executed gate list would settle it
   directly and does not exist.
3. **The runner behaviours the oracle inherits on platforms other than this
   one.** Reason: `oracle_env: macos_local`; the timeout, process-group kill
   and Windows bash routing come from `_run_gate_set` and were not exercised
   here for the oracle specifically. Where it is checked: `_run_gate_set`'s own
   pre-existing tests and CI. The reuse argument is what makes this acceptable
   — the oracle adds no new execution path to test.
4. **Whether the four WARN-ing gates get real oracles.** Reason: writing one
   for each means designing three unrelated features inside this one; `PLAN.md`
   puts it explicitly out of scope. Where it is checked: the lint rule itself,
   which escalates each WARN to ERROR the moment its feature flips to `active`
   — the moment its author is thinking about it.
5. **Whether `close-f` and `close-l` can fire at all on this repo's own work
   units.** Reason: no oracle in this feature asks that question, and the
   answer turned out to be no for both (see the first lesson). Where it is
   checked: nowhere today. Both are guards from earlier features, outside this
   WU's editable scope, and are reported here rather than fixed.
6. **Whether a pre-flight check could catch an unrunnable oracle before any
   unit dispatches — the bar as originally written.** Reason: deciding whether
   an arbitrary shell string will resolve requires evaluating pipes, `&&`,
   shell functions, aliases and `PATH` as they will exist at run time; it is
   not reliably decidable, which is why `GATE-01.md` moved it out of scope
   rather than shipping a check that would be wrong in both directions — a
   false CONFIGURATION ERROR on a valid compound command is worse than the
   misattribution it replaces. Where it is checked: nowhere, by design, and
   this is a **deliberate reduction in scope, not an oversight**. What ships
   instead is run-time attribution (bullet 5), which catches the same operator
   mistake one dispatch later. A gate whose oracle is a typo now costs one
   attempt to discover instead of zero — that residual cost is the price of the
   narrowing and is recorded here so it is not rediscovered as a surprise.
7. **That this feature's own re-arm history is reconstructible from
   `events.jsonl`.** Reason: it is not. T02's re-arm emitted a
   `re_arm_dispatched` event; this close's re-arm after the judge's `not_met`
   emitted none, and survives only in `WU-90-gate-1-close.md`'s frontmatter
   (`re_arm_count`, `re_arm_history`). Any tooling that counts re-arms from the
   event log undercounts, and the undercount hides the most expensive kind —
   the one that re-runs a whole terminal close. Where it is checked: nowhere
   today. The event log's own emission points are outside this WU's editable
   scope; this is reported, not fixed.

## Consumer-visible contract changes

Three additions and two behaviour changes. All are additive and absent-key
behaviour is unchanged, so no existing project file needs an edit — but a
project whose **active** feature has a gate with no `feature_oracle` will see
its plan lint go red on the next run, and that is deliberate.

1. **A new `GATE-NN.md` frontmatter key: `feature_oracle`.** One command per
   gate, the executable proof of that gate's definition of done. The driver
   reads it in `verify()` and appends it to every unit's gate set in that gate;
   the close re-runs it and records the verdict. Absent means inert — a gate
   without the key verifies byte-identically to before. Declared-but-empty, or
   a non-string value, is a CONFIGURATION ERROR naming the gate file, refused
   before the unit's gates run. A declared oracle whose command **exits 127**
   is likewise re-reported as a configuration problem naming the gate file
   rather than as an ordinary gate `FAIL` — see item 5.
2. **A new plan-lint rule, ERROR on active features:
   `lint_feature_oracle_declared`.** A gate declaring no `feature_oracle` is
   ERROR when its feature is `active`, WARN when `planned`/`blocked`/`deferred`,
   and skipped when the gate is `passed` or the feature is `done`/`abandoned`.
   This is the one item here that can turn a previously-green `specfuse lint`
   red without any local edit.
3. **A new closing-lint requirement: `close-n`.** When a gate declares a
   `feature_oracle`, the close's `RETROSPECTIVE.md` must carry a
   `### feature_oracle: PASS` or `### feature_oracle: FAIL` line inside its
   `## Measurements` section, or `specfuse lint --closing` fails pre-squash.
   Conditional on the declaration: a gate that declares no oracle imposes no
   requirement.
4. **`/draft-feature` now refuses to draft a gate without a `feature_oracle`,
   and `GATE.template.md` ships the key.** Drafting behaviour changes for every
   new gate; `/authoring-work-units` §14 states the matching tracer-bullet rule
   (stubs permitted only in the unit that turns the oracle green), and
   `docs/methodology.md` documents the key in one place and adds §7's
   `plan-next` oracle-progression obligation.

5. **An oracle the shell cannot run is now attributed to the gate file, not to
   the work unit (behaviour change).** When a declared `feature_oracle` exits
   **127** — the shell's stable, locale-independent "command not found" status
   — `verify()` re-reports the failure as `CONFIGURATION ERROR: <gate file>
   declares feature_oracle: '<command>' but that command could not be run`,
   instead of the bare `### feature_oracle: FAIL` an ordinary red gate
   produces. The attempt still fails and nothing passes silently; what changes
   is **who the report blames**. A typo'd declaration previously told the next
   agent its code was broken, so it burned attempts fixing code that was never
   at fault. Two boundaries are deliberate and were measured: an oracle that
   executes and exits non-zero for a real reason stays an ordinary failure, and
   so does one that *prints* the words "command not found" while failing —
   classification keys on exit status, never on message text. Scope is the
   oracle gate only; a non-oracle gate exiting 127 is unchanged. A consumer
   parsing gate reports for the literal string `### feature_oracle: FAIL` will
   no longer match this one case.

Not consumer-visible and listed here only so the enumeration is honest:
`verify()` gained an optional keyword-only `gate_file` parameter, and
`read_gate_feature_oracle` is a new module-level function in
`specfuse/loop/loop.py`. Neither is a surface a scaffolded project calls;
`_accepts_gate_file` keeps pre-existing test doubles working unchanged.
`_run_gate_set` gained an optional `_capture_returncodes` out-parameter (T05);
its documented `{"name", "ok", "report"}` return contract is unchanged, and
callers that omit the parameter see byte-identical behaviour.

`CHANGELOG.md`'s `Unreleased` section carries items 1–5, classified and traced
to `FEAT-2026-0101`. Item 5 is folded into item 1's entry rather than filed
separately: it is the same frontmatter key's behaviour, and two entries
describing one key's failure modes would read as two features.

## Lessons

### 1. A guard keyed on a WU-ID gate number never sees a substantive unit's failures

`_gate_number_from_wu_id` parses `G(\d+)-` — it resolves
`FEAT-2026-0101/G1-CLOSE` to `1` and `FEAT-2026-0101/T02` to `None`. Every
substantive WU in this methodology is named `T01`, `T02`, …, so a caller that
passes `gate_n` filters out every implementation unit's `attempt_outcome` and
keeps only closing WUs — which the same call then excludes by
`exclude_correlation_id`. Measured on this feature:

```
summarize_attempt_failure_classes(fd, 1,    exclude=G1-CLOSE) -> "(no non-passing attempts in scope)"
summarize_attempt_failure_classes(fd, None, exclude=G1-CLOSE) -> tests | 3 | test_package_data_matches_canonical
```

Three real failed attempts, and the gate-scoped call — the one
`ClosingContext.failures_present()` and `_precreate_retrospective_stub` both
make — reports none. So `close-f` did not apply to this close and no
`### Failure-class breakdown` was pre-created. The section above exists because
this close wrote it deliberately, not because the guard asked for it.

The same audit found a second instance of the class:
`_DEBT_AC_ITEM_RE = r"(?m)^\s*\d+\.\s+(.*)$"` matches only **numbered**
acceptance-criterion items, while this repo's work units — and its own
templates and `/authoring-work-units` house style — use `-` bullets.
`extract_wu_criteria` therefore returned `status: ok` with **zero criteria**
for all four substantive WUs, `GATE-01-CRITERIA.md` was never seeded, and
`close-l` never applied.

The generalizable rule: **a guard that derives its scope by parsing an
identifier or matching a list marker must be tested against a real artifact
from the repository it guards, not only against a fixture written to match the
parser.** Both guards pass their own unit tests. Both are silent on every
artifact this repository actually produces, and both fail *open* — they report
"nothing to check" rather than "cannot check", which is indistinguishable from
success in a close's transcript. A guard's own tests cannot detect this; only
running it against real on-disk work units can. Neither function is a symbol
this feature introduced (`_gate_number_from_wu_id` cites FEAT-2026-0015,
`summarize_attempt_failure_classes` cites issue #145, `_DEBT_AC_ITEM_RE` belongs
to the auto-close debt summary), and both sit outside this WU's editable scope.

### 2. An acceptance criterion that demands an undecidable property is a drafting defect, and narrowing it is the honest fix — but the narrowing must be declared

This gate's definition of done originally required a declared-but-unrunnable
`feature_oracle` to be a CONFIGURATION ERROR **"before any unit dispatches"**,
for any command that "cannot be resolved". Attempt 1 recorded `met`. The judge
lowered it to `not_met` and was right to: a `feature_oracle` is an arbitrary
shell string, and deciding in advance whether one will resolve means evaluating
pipes, `&&`, shell functions, aliases and `PATH` as they will exist at run time.
There is no correct implementation of that criterion, so the close could not
have honestly claimed it — and the criterion could not have been satisfied by
any amount of further work.

The failure is not in the close and not in the code. It is in the **drafting**:
the criterion described a desirable property ("a typo'd oracle should not read
as the unit's defect") in terms of an undecidable implementation ("detect it
before dispatch"), and nothing between drafting and the judge tested whether the
property as worded was reachable at all. `planning-discipline.md` §2 already
demands that escalation *predicates* be satisfiable and this gate's own arming
discipline re-ran that sweep; nobody asked the same question of the definition
of done, which is the document the judge grades against.

Two responses, and only one of them is honest. Weakening the wording to whatever
the code already did would be the `never-touch.md` failure — silencing a gate to
make a unit pass. What happened instead is that the *property* was kept and the
*mechanism* was narrowed: pre-flight resolution is now explicitly out of scope,
run-time attribution by exit status 127 is what T05 delivers, and the residual
cost — a typo'd oracle now costs one dispatch to discover instead of zero — is
written down as a known limit rather than buried. **The narrowing itself is the
thing that has to be visible.** A close that re-measures against a quietly
edited bar and reports green has laundered a `not_met` into a `met`, and the
judge is deliberately not shown the close's own prose, so a narrowing announced
only in the retrospective's argument section would never reach it. It belongs in
the measurements, next to the number it makes green.

Drafting-time check, mechanical enough to apply: for each bullet of a definition
of done, name the command that would prove it. A bullet for which no command can
be written — because the property is undecidable, or observable only in
production, or requires a human — is not an acceptance criterion. It is a
`## Post-merge checklist` line, a `type: human` work unit, or a `PLAN.md` known
limit, and `close-discipline.md` §2 already provides all three channels.

**The cost corollary, measured twice on this feature.** A `planned_cost_usd` is
a per-unit number and cannot see run count. T02 showed a unit can need three
attempts, for $3.9574 against a $2.50 budget. This gate showed a **terminal
close can need two**, because a judge may lower `met` to `not_met` — which makes
a second close a structural possibility for every judged gate, not an accident.
The substantive units came in 3.8% *under* plan; the feature is over anyway,
entirely on close re-runs. Do not pad the estimate for this: `planned_cost_usd`
feeds `evaluate_auto_close`'s per-WU ratio checks, so padding makes gates
auto-close that should not. Estimate the one-attempt cost and let the overrun
stay visible — it is legible here precisely because nobody padded it.
