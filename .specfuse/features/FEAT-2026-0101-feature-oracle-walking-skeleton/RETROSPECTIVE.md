# Retrospective — FEAT-2026-0101, the feature oracle and the walking skeleton

## Gate 1

A gate's definition of done is now an executable command. `GATE-NN.md`
frontmatter carries one `feature_oracle`; `verify()` reads it, appends it to
the gate list the unit was already going to run, and hands the whole list to
the existing `_run_gate_set`. The close re-runs it and records the verdict
where the judge reads. A lint rule refuses a gate that declares none once its
feature goes `active`.

Four substantive units (T01 tracer bullet, T02 close requirement, T03 lint
rule, T04 authoring surfaces), one terminal close. One unit spun three
attempts and was re-armed.

## Measurements

Every command below was run in this close session, in this working tree, on
branch `feat/FEAT-2026-0101-feature-oracle-walking-skeleton`. Exit statuses
are the shell's, read directly.

### feature_oracle: PASS

```
$ python3 -m unittest tests.test_feature_oracle_e2e -q
Ran 4 tests in 0.060s
OK
exit 0
```

This is the gate's declared `feature_oracle`, re-run fresh. It is the
feature-level question the four units were each too small to ask: it builds a
temp feature folder whose `GATE-01.md` declares an oracle, drives a real
`WorkUnit` through `verify()`, and asserts the oracle command **executed** —
proven by a marker file the command itself writes — not that a helper returned
the right value.

**This verdict is not the guard-wiring audit.** It proves the mechanism runs
in this session against a synthetic feature folder. It says nothing about
whether the lint rule, the closing requirement, or the authoring surfaces are
reachable from the paths they were meant to intercept. Those are audited
separately, below, and the two must not be read as one result.

### Definition of done, bullet by bullet

| # | `GATE-01.md` definition-of-done bullet | Command run in this session | Exit |
|---|---|---|---|
| 1 | Gate declares `feature_oracle`; driver reads it, synthesizes a one-element gate list, runs it through the existing `_run_gate_set`; no second execution path | `python3 -m unittest tests.test_feature_oracle_e2e -q` (all 4) plus `grep -n "_run_gate_set(" specfuse/loop/*.py` | 0 / 0 |
| 2 | The oracle runs as part of **every unit's verification** in that gate | `python3 -m unittest tests.test_feature_oracle_e2e -q` (`test_declared_oracle_runs_during_unit_verification`, `test_failing_oracle_fails_the_unit`) + call-chain audit below | 0 |
| 3 | The close re-runs it and records the verdict in `## Measurements`; `specfuse lint --closing` fails a close that omits it | `python3 -m unittest tests.test_close_records_feature_oracle -q`; negative observation below | 0 |
| 4 | A declared-but-unrunnable oracle is a CONFIGURATION ERROR, never a silent skip or pass | `python3 -m unittest tests.test_feature_oracle_e2e -q` (`test_empty_oracle_is_configuration_error`) | 0 |
| 5 | No-oracle gate: ERROR when `active`, WARN when `planned`/`blocked`/`deferred`, skipped when gate `passed` or feature `done`/`abandoned`; corpus sweep zero ERRORs and exactly four WARNs | `python3 -m unittest tests.test_lint_feature_oracle_declared -q`; the sweep and the negative observation below | 0 |
| 6 | `GATE.template.md` carries the key; `/draft-feature` refuses a gate without one; `plan-next` drafts the next oracle and states in its review summary how it advances the prior gate's; `methodology.md` documents it in one home | five greps below + `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_scaffold_resources -q` | 0 |
| 7 | Per-criterion state and the narrow/broad oracle contract (`close-discipline.md` §5) | `specfuse lint --closing` from the checkout — `close-l` reported not-applicable | see §7 note |

Bullet 1's second command, verbatim:

```
$ grep -n "_run_gate_set(" specfuse/loop/*.py
specfuse/loop/prerun.py:120:        result = _run_gate_set([gate], feature_dir)[0]
specfuse/loop/prerun.py:132:    oracle_results = _run_gate_set(oracle_gates, feature_dir) if oracle_gates else []
specfuse/loop/loop.py:4067:def _run_gate_set(gate_set: list, feature_dir: Path) -> list[dict]:
specfuse/loop/loop.py:4265:    gate_results = _run_gate_set(gate_set, feature_dir)
specfuse/loop/loop.py:4294:    gate_results = _run_gate_set(gate_set, feature_dir)
exit 0
```

One definition and four call sites, all pre-existing: `4265` is `verify()`,
`4294` is `probe_baseline()`, and `prerun.py`'s two are the pre-dispatch input
oracles. The feature oracle is appended to the list `verify()` was already
building and goes through `4265` with everything else — no fifth call site,
no `subprocess` of its own, no second execution path.

Bullet 6's five greps, verbatim results:

```
$ grep -n "feature_oracle" .specfuse/templates/GATE.template.md
4:# feature_oracle: "<command>"   # REQUIRED for a drafted gate. The executable proof of
exit 0

$ grep -c "feature_oracle" plugins/specfuse/skills/draft-feature/SKILL.md
4                                          (criterion asked for >= 2)
exit 0

$ grep -n "tracer bullet" plugins/specfuse/skills/authoring-work-units/SKILL.md
(hit; §14 "Tracer bullet — stubs permitted only in the unit that turns the oracle green")
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
$ diff -r plugins/specfuse/skills/draft-feature .specfuse/skills/draft-feature            -> exit 0
$ diff -r plugins/specfuse/skills/authoring-work-units .specfuse/skills/authoring-work-units -> exit 0
$ diff .specfuse/rules/close-discipline.md specfuse/loop/data/rules/close-discipline.md  -> exit 0
$ diff .specfuse/templates/GATE.template.md specfuse/loop/data/templates/GATE.template.md -> exit 0
```

**§7 note.** `GATE-01-CRITERIA.md` does not exist for this gate, so `close-l`
(`check_criteria_state_well_formed`, `applies_when=criteria_artifact_present`)
never applied and no `kind`/`state` entries were written. The artifact was not
skipped by choice — the driver's own seeder produced nothing. See the first
lesson: this is one of two guards found inert on this repo's artifacts, and
neither is a symbol this feature introduced.

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
No fifth WARN, no ERROR, no missing entry. FEAT-2026-0011 has no gate files
and therefore produces no finding of either severity, which is what `PLAN.md`
predicted.

**Negative observation — the rule seen rejecting a purpose-built bad input.**
A green sweep proves the rule is quiet; it does not prove the rule fires. Four
synthetic one-gate feature folders, built in a temp directory, one per branch
of the graduation:

```
[ERROR expected (active, no oracle)]   ERRORs=1 WARNs=0
   ERROR: FEAT-9999-9999/GATE-01: gate declares no `feature_oracle` in an active feature — see .specfuse/roadmap.md's oracle contract and declare one before the next dispatch.
[WARN expected (planned, no oracle)]   ERRORs=0 WARNs=1
   WARN: FEAT-9999-9999/GATE-01: gate declares no `feature_oracle` — required before this feature goes active. See .specfuse/roadmap.md's oracle contract.
[clean expected (active, oracle declared)]  ERRORs=0 WARNs=0
[skip expected (done feature)]              ERRORs=0 WARNs=0
exit 0
```

All four branches behave as specified. The rule is not a rule that fires on
nothing.

**Negative observation — `close-n` seen rejecting a close that omits the
verdict.** Run live against this feature folder, from the checkout, with the
`### feature_oracle: PASS` line temporarily removed from this document and
then restored:

```
$ python3 -m specfuse.loop.lint_plan <this feature dir> --closing      # line removed
FAIL — 1 unmet closing requirement(s):
  - close-n: gate 1 declares feature_oracle but RETROSPECTIVE.md's 'Measurements' section records no 'feature_oracle' PASS/FAIL verdict — would fail check_feature_oracle_verdict_recorded after squash
exit 1

$ python3 -m specfuse.loop.lint_plan <this feature dir> --closing      # line restored
CLOSING-READY
exit 0
```

The exact transcript is reproduced under "Oracles re-run fresh" below.

**A trap worth recording.** The first `specfuse lint --closing` of this
session ran the pipx-installed build, which predates `close-n` and reported
four findings without it. The command printed its own warning
("measuring the INSTALLED build, not your checkout — results can be
confidently wrong rather than failing") and every closing-lint result above
is from `python3 -m specfuse.loop.lint_plan ... --closing` in the checkout.

### Failure-class breakdown

| failure_class | non-passed attempts | dominant signature |
|---------------|---------------------|--------------------|
| tests | 3 | test_package_data_matches_canonical |
| **total** | **3** | — |

All three belong to T02, before its re-arm. Two were
`test_package_data_matches_canonical` (the `.specfuse/rules/` →
`specfuse/loop/data/rules/` mirror left stale) and one was
`test_every_requirement_names_a_real_guard_function` (a registry entry naming
a guard function that did not exist). The two constraints are independent and
neither is discoverable from the code being edited; each attempt satisfied one
and broke the other. The re-arm wrote both constraints into the WU body
verbatim and the retry passed at one attempt.

This table was produced by `summarize_attempt_failure_classes(feature_dir,
None, exclude_correlation_id="FEAT-2026-0101/G1-CLOSE")`. Called the way the
driver calls it — with `gate_n=1` — the same function returns
`(no non-passing attempts in scope)`. See the first lesson.

### Oracles re-run fresh for this close

```
$ python3 -m unittest discover -s tests -q
Ran 3768 tests in 154.745s
OK (skipped=3)
exit 0

$ bash scripts/smoke-test.sh
26 TAP assertions, 0 failures across 6 suites
exit 0

$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
exit 0

$ python3 .specfuse/scripts/lint_plan.py <this feature dir>      # the `plannext` gate set
WARN: WU-04-authoring-surfaces.md: implementation WU mentions driver wiring (['loop.py']) but `produces_driver_helper` frontmatter is empty.
OK — <this feature dir> is structurally valid.
exit 0

$ python3 -m unittest tests.test_feature_oracle_e2e -q          # the gate's feature_oracle
Ran 4 tests in 0.060s / OK / exit 0

$ python3 -m unittest tests.test_close_records_feature_oracle -q
Ran 3 tests in 0.285s / OK / exit 0

$ python3 -m unittest tests.test_lint_feature_oracle_declared -q
Ran 6 tests in 0.010s / OK / exit 0

$ python3 -m unittest tests.test_scaffold_data_in_sync tests.test_scaffold_resources -q
Ran 9 tests in 0.015s / OK / exit 0

$ for d in .specfuse/features/*/; do python3 -m specfuse.loop.lint_plan "$d"; done
feature folders linted: 76
folders with ERROR: 0
```

`specfuse lint` over every feature folder: **76 linted, 0 with any ERROR.**

Both the full suite and the smoke script were run twice: once before this
document, `CHANGELOG.md` and `.specfuse/LEARNINGS.md` were written (3768 tests,
160.396s, `OK`; 26 TAP assertions, exit 0) and once after (the transcript
above). The satisfiability sweep, the gate's `feature_oracle` and the 76-folder
`specfuse lint` were likewise re-run after the edits with identical results.
The one WARN from the `plannext` gate is on T04 and is pre-existing — that unit
edits no driver module and declares no `produces_driver_helper`; it does not
affect the gate's exit status.

The `close-n` negative observation, in full:

```
$ python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton --closing
FAIL — 1 unmet closing requirement(s) in .specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton:
  - close-n: gate 1 declares feature_oracle but RETROSPECTIVE.md's 'Measurements' section records no 'feature_oracle' PASS/FAIL verdict — would fail check_feature_oracle_verdict_recorded after squash
exit 1
```

with `### feature_oracle: PASS` deleted from this document, and:

```
$ python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton --closing
CLOSING-READY — .specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton
exit 0
```

with it restored.

## Guard-wiring audit

`[FEAT-2026-0008/G1-CLOSE]`: a feature that fixes a methodology failure mode
must verify at close that its guards **landed and are wired into the path they
were meant to intercept**. A definition is not evidence; a call site is. Three
symbols, each audited twice.

### 1. `read_gate_feature_oracle` (T01) — wired into `verify()`

```
$ grep -n "def read_gate_feature_oracle" specfuse/loop/loop.py
4484:def read_gate_feature_oracle(gate_file: Path) -> "str | None":

$ grep -n "read_gate_feature_oracle(" specfuse/loop/loop.py
4254:        oracle_command = read_gate_feature_oracle(Path(gate_file))
4484:def read_gate_feature_oracle(gate_file: Path) -> "str | None":
```

DEFINITION at `loop.py:4484`. CALL SITE at `loop.py:4254`. `verify()` spans
`loop.py:4193` to `loop.py:4269` (the next top-level `def` is `probe_baseline`
at `4270`), so `4254` is inside `verify()`. The call is followed at `4262` by
`gate_set = gate_set + [{"name": "feature_oracle", "command": oracle_command}]`
and at `4265` by the single pre-existing `_run_gate_set(gate_set, feature_dir)`.

The chain from the driver's real dispatch path, so the wiring is not merely
test-visible:

```
run()                       loop.py:7940  execute_unit_attempt(..., gate_file=gate.file)
execute_unit_attempt()      loop.py:4732  verify_fn(wu, feature_dir, gate_file=gate_file)
verify()                    loop.py:4254  read_gate_feature_oracle(Path(gate_file))
verify()                    loop.py:4265  _run_gate_set(gate_set, feature_dir)
```

`gate.file` is `feature_dir / g["file"]` (`loop.py:867,872`) — a real path to
the WU's own `GATE-NN.md`, passed unconditionally for every unit in the gate,
not only closing ones. `_accepts_gate_file(verify_fn)` at `4731` is a
compatibility branch for test doubles whose signature predates the parameter;
the production `verify` accepts it and takes the `4732` branch.

**Verdict: wired.** Definition and call site both present, call site inside
`verify()`, and `verify()` reached from `run()` with a non-`None` `gate_file`.

### 2. `lint_feature_oracle_declared` (T03) — wired into the plan-lint entry point

```
$ grep -n "lint_feature_oracle_declared" specfuse/loop/lint_plan.py
971:def lint_feature_oracle_declared(feature_dir: Path, plan_fm: dict) -> list[str]:
2055:    errs.extend(lint_feature_oracle_declared(feature_dir, fm))
```

DEFINITION at `lint_plan.py:971`. CALL SITE at `lint_plan.py:2055`, inside
`_lint_impl()` (`1675` to `2093`), immediately after its sibling rules
`lint_ac_observable` and `lint_close_verdict_not_predecided`. `lint()`
(`lint_plan.py:1660`) delegates to `_lint_impl`, and `main()` calls `lint()` at
`lint_plan.py:2235` — the path `specfuse lint <feature-dir>` actually takes.

**Verdict: wired.** Confirmed behaviourally as well: the 76-folder sweep and
the four-branch negative observation above both run through this rule and both
produce findings.

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
`lint_closing.py:297`. CALL SITE: the guard is bound into the `_CHECKS`
dispatch table at `lint_closing.py:410` and invoked at `lint_closing.py:512`
(`checker = _CHECKS.get(req.enforced_by)`, then `result = checker(req, ctx)` at
`522`), inside `lint_closing()`, which `main_closing()` calls at
`lint_closing.py:538`, which `lint_plan.main()` calls under `--closing` at
`lint_plan.py:2233`.

A registry entry naming a guard the dispatch table has no entry for is not a
silent pass either — `lint_closing.py:513-521` emits an explicit
"registry/lint drift, escalate" finding.

**Verdict: wired.** Confirmed behaviourally by the live negative observation:
`close-n` fired on this very close when the verdict line was removed and
cleared when it was restored.

### 4. T04's four authoring surfaces — content, not symbols

T04 introduced no callable symbol, so "definition without a caller" does not
apply. The equivalent question is whether each surface's text is on the path a
drafting session actually reads. All four greps are reproduced under bullet 6
of the measurements table and all four returned hits: the key with its comment
in `GATE.template.md` (mirrored byte-identically into
`specfuse/loop/data/templates/`), the refusal in `/draft-feature`'s SKILL.md at
line 53 with the tracer-bullet framing at line 276, §14 in
`/authoring-work-units`, and `docs/methodology.md` carrying the key's one
definition (line 89) plus §7's `plan-next` oracle-progression obligation
(line 570) that points at it. Both skill copies are `diff`-identical.

### Audit result

**Three of three symbols wired; no definition found without a caller in the
path it names.** No escalation trigger fired.

Two guards belonging to *other* features were found inert during this audit —
neither is a symbol T01–T04 introduced, and both are recorded in the first
lesson and in "What the loop did NOT verify" rather than being folded into
this verdict.

## Cost analysis

`planned_cost_usd: 19.00` in `PLAN.md` frontmatter is the sum of the five
per-WU estimates: T01 $3.00, T02 $2.50, T03 $2.50, T04 $3.00, close $8.00.

| WU | Planned | Actual | Delta | Attempts |
|---|---|---|---|---|
| T01 tracer bullet | $3.00 | $3.6376 | +$0.6376 (+21.3%) | 1, passed |
| T02 close requirement | $2.50 | $5.0005 | +$2.5005 (+100.0%) | 3 failed + re-arm, then 1 passed |
| T03 lint rule | $2.50 | $1.9601 | −$0.5399 (−21.6%) | 1, passed |
| T04 authoring surfaces | $3.00 | $1.8249 | −$1.1751 (−39.2%) | 1, passed |
| **substantive subtotal** | **$11.00** | **$12.4231** | **+$1.4231 (+12.9%)** | 7 attempts, 1 re-arm |
| G1-CLOSE | $8.00 | recorded by the driver at outcome | — | this session |

Wall clock across the four substantive units: 8045.4s (2h14m), from
`events.jsonl` `attempt_outcome` durations.

**Restart count: 2.** `events.jsonl` carries two `driver_staleness_detected`
events with `reason: driver_restart_required`, after T01 (22:47:59Z) and after
T02's passing re-armed attempt (00:36:09Z). `PLAN.md` predicted three, one per
unit editing `specfuse/loop/*.py` (T01, T02, T03). T03 completed at 00:10:36Z
between T02's escalation and its re-arm and produced no staleness event; T04
edits no driver module and correctly produced none. So the plan over-predicted
restarts by one.

**Re-arm count: 1** (T02, `re_arm_count: 1`, reason recorded as "both hidden
constraints now written into the WU, retry from clean slate").

### Did this feature's recalibration hold?

`PLAN.md` set these estimates from FEAT-2026-0102's actuals (~$1.10 per
substantive unit plus headroom) rather than from the earlier guesses that made
0102's estimates run 2.6× high. Two readings, and they disagree:

- **On first-pass work, yes, and by a wide margin.** Excluding the three
  spinning attempts, substantive spend was $8.4657 against $11.00 planned —
  **1.30× high**, down from 2.6×. Three of four units landed within ±40% of
  estimate; T03 and T04 came in under.
- **On the feature as delivered, no — it went 12.9% over.** The entire
  overrun is one WU: T02's three failed attempts cost $3.9574, which is 31.9%
  of all substantive spend and more than the whole $2.50 the unit was
  budgeted. Absorb that and the headroom is gone.

The honest summary is that the *per-attempt* estimate recalibrated well and
the *per-unit* estimate did not, because a per-unit estimate silently assumes
one attempt. A unit carrying two independent, non-discoverable constraints
costs three attempts, and no amount of tightening the per-attempt number
predicts that. This matters beyond bookkeeping: `planned_cost_usd` feeds
`evaluate_auto_close`'s per-WU ratio checks, so an estimate padded for
possible spinning would make gates auto-close that should not.

## What the loop did NOT verify

Five criteria this feature's own machinery could not settle, each with the
reason and the surface that actually checks it.

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
2. **That the oracle actually ran during T02's, T03's and T04's own
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

## Consumer-visible contract changes

Three additions and one behaviour change. All are additive and absent-key
behaviour is unchanged, so no existing project file needs an edit — but a
project whose **active** feature has a gate with no `feature_oracle` will see
its plan lint go red on the next run, and that is deliberate.

1. **A new `GATE-NN.md` frontmatter key: `feature_oracle`.** One command per
   gate, the executable proof of that gate's definition of done. The driver
   reads it in `verify()` and appends it to every unit's gate set in that gate;
   the close re-runs it and records the verdict. Absent means inert — a gate
   without the key verifies byte-identically to before. Declared-but-empty, or
   a non-string value, is a CONFIGURATION ERROR naming the gate file, refused
   before the unit's gates run.
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

Not consumer-visible and listed here only so the enumeration is honest:
`verify()` gained an optional keyword-only `gate_file` parameter, and
`read_gate_feature_oracle` is a new module-level function in
`specfuse/loop/loop.py`. Neither is a surface a scaffolded project calls;
`_accepts_gate_file` keeps pre-existing test doubles working unchanged.

`CHANGELOG.md`'s `Unreleased` section carries items 1–4, classified and traced
to `FEAT-2026-0101`.

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

### 2. A per-unit cost estimate silently assumes one attempt

This feature's estimates were recalibrated from FEAT-2026-0102's actuals and
the recalibration worked on the thing it was aimed at: excluding spinning,
substantive spend ran 1.30× high against 2.6× before. The feature still came
in 12.9% over, because one unit spun three attempts for $3.9574 — more than
the whole $2.50 that unit was budgeted, and 31.9% of all substantive spend.

Sharpening the per-attempt number does not help: the variance is in the
attempt *count*, and it was predictable from the unit's shape rather than its
size. T02 carried two independent constraints — the
`.specfuse/rules/` → `specfuse/loop/data/rules/` mirror and "a registry entry
needs a real guard function" — neither discoverable from the code being edited,
and each of the three attempts satisfied one and broke the other. The re-arm
that wrote both constraints into the WU body verbatim passed at one attempt for
$1.04.

Two consequences. When AUTHORING: a unit that must satisfy two constraints
invisible from its own diff should name both in its body up front — that is
what turned three failures into one pass here, and it cost less than one
attempt to write. When ESTIMATING: do not pad `planned_cost_usd` for possible
spinning. It feeds `evaluate_auto_close`'s per-WU ratio checks, so padded
estimates make gates auto-close that should not — the exact failure
`PLAN.md`'s cost-calibration note was written to avoid. Estimate the
one-attempt cost and let the overrun be visible.
