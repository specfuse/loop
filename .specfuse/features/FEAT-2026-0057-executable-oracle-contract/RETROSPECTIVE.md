<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0057: the pre-dispatch half, built but not wired

Single terminal gate, three implementation work units, one close. The feature's
headline claim is that a work unit can declare `prep:` and `oracles:` in its
frontmatter, that the driver runs them **before** dispatch — prep fail-fast,
oracles capture-all — and that the captured output reaches the session as input
under a byte budget that preserves verdicts.

**Two of the three modules exist, are correct, and are tested. Nothing calls
them.** `specfuse/loop/prerun.py` and `specfuse/loop/prerun_capture.py` are
importable, documented, and covered — and the only references to their symbols
anywhere in this repository are their own test files. `WorkUnit` has no `prep`
or `oracles` field, `load_wu` never parses those keys, and no dispatch path
imports either module. A work unit declaring both keys today produces exactly
the same pre-dispatch outcome as one declaring neither: the empty one.

That was measured in this session, not inferred, and it is why the verdict is
`partially_met` rather than `met`. Every oracle the three producing units named
re-ran green. The gap is not that an oracle disagrees with a self-report — it is
that no producing unit's criteria ever named an oracle for the wiring, so all
three passed honestly while the feature-level definition of done went unmet.
That composite is the exact failure `close-discipline.md` §1 exists to catch.

## Gate 1 — a work unit can declare prep steps and oracles that run before its session

### What was built

**T01 — the pre-dispatch runner (`done`, 1 attempt, $0.98 against $4.00).**
`specfuse/loop/prerun.py` ships `run_pre_dispatch(wu, feature_dir, cfg)`,
`resolve_prerun_sets(wu, cfg)`, and `PREP_HALT_CLASS = "prep_halt"`. Prep entries
run in declared order and stop at the first non-zero exit; oracles run capture-all
on prep success; an unresolvable set name returns a named CONFIGURATION ERROR
mirroring `verify()`'s `extra_gates` phrasing; a unit declaring neither key
returns the empty outcome without invoking `_run_gate_set`. It calls
`_run_gate_set` rather than reimplementing gate execution, exactly as the scope
boundary required. Oracle: `tests/test_prerun_oracles.py`, red on HEAD (the file
did not exist).

**T02 — the capture budget (`done`, 2 attempts, $1.67 against $3.50).**
`specfuse/loop/prerun_capture.py` ships `format_oracle_capture(results)` and
`ORACLE_CAPTURE_BUDGET_BYTES = 8000`. The budget is split evenly across oracles;
each oracle's report is fitted through `select_gate_report_lines` (FEAT-2026-0068)
rather than a positional tail, and any truncation carries an explicit
`... [N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES] ...` marker. The 8000
figure was **not guessed** — the WU's escalation trigger forbade that — it is the
`max_chars` `truncate_failure_note` (`loop.py:2169`) already uses for the same
class of injected content in this repo, reused and cited in a comment at the
constant. Oracle: `tests/test_prerun_capture.py`, red on HEAD.

**T03 — the declaration and the written contract (`done`, 1 attempt, $1.40
against $2.50).** `.specfuse/verification.yml` gained a top-level `oracles:` key
with two self-contained entries (`recent-commits`, `diff-stat`), appended without
touching the `code` / `doc` / `plannext` bodies or the header comments — the
additivity the gate's sequencing rested on. `tests/test_oracle_set_declared.py`
guards it structurally in both directions. `.specfuse/skills/verification/SKILL.md`
gained a "Pre-dispatch: `prep` and `oracles`" section with a
`prep`-vs-`oracles`-vs-`extra_gates` table and an explicit choosing rule, which
is the part that matters most: this feature exists because `extra_gates` shipped,
did most of the job, and was never found.

### What was not built, measured rather than assumed

This is the finding. It was produced by grepping for callers of every symbol the
three units declared in `produces_driver_helper`, then by loading a real work unit
through the driver's own parser.

**1. `WorkUnit` carries no `prep` or `oracles` field.** The dataclass fields, read
from the live class in this session:

```
['wu_id', 'file', 'depends_on', 'type', 'model', 'status', 'attempts', 'title',
 'body', 'effort', 'unsandboxed', 'unsandboxed_rationale', 'verdict',
 'produces_driver_helper', 'produces', 'extra_gates']
```

`extra_gates` is there — it is the mechanism the existing-mechanism search found.
`prep` and `oracles` are not, and `load_wu` has no parse branch for them
(`loop.py:612-622` handles `extra_gates` only).

**2. The negative observation.** A temporary work-unit file declaring
`prep: [code]` and `oracles: [oracles]`, loaded through `load_wu` and passed to
`run_pre_dispatch` with a `verification.yml`-shaped cfg containing both sets:

```
WorkUnit has attr prep?    False
WorkUnit has attr oracles? False
extra_gates parsed as:     []
resolve_prerun_sets ->     ([], [], None)
run_pre_dispatch ->        {'halted': False, 'halt_class': None, 'message': None,
                            'prep_results': [], 'oracle_results': []}
```

`resolve_prerun_sets` reads both fields through `getattr(wu, "prep", None)`, which
on a real `WorkUnit` is unconditionally `None`. So the runner resolves to two
empty lists and returns the "no pre-dispatch work" outcome — the same value it
returns for a unit that declared nothing. The declaration is inert, and nothing
anywhere reports that it was ignored.

**3. Nothing imports either module outside its own tests.** Repo-wide grep for
`run_pre_dispatch`, `resolve_prerun_sets`, `PREP_HALT_CLASS`,
`format_oracle_capture`, `ORACLE_CAPTURE_BUDGET_BYTES`, `prerun_capture`, and
`loop.prerun`, excluding `.venv/`, `build/`, and `.git/`: **28 hits, all of them
in `tests/test_prerun_oracles.py`, `tests/test_prerun_capture.py`, or the modules'
own docstrings and internals.** Zero in `specfuse/loop/loop.py`. The dispatch path
is byte-for-byte what it was before the feature started.

**4. This close was itself the obvious first consumer, and it was not one.**
`WU-90`'s frontmatter declares `oracle_env: macos_local` and no `oracles:` key.
The `oracles` set T03 declared — `recent-commits` and `diff-stat`, whose stated
purpose in `verification.yml`'s own comment is "for a close session to read
instead of re-running `git log` itself and burning a turn on it" — was not
injected into this session, and this session's WU body forbids running `git` at
all. The one adoption the feature was built for did not happen on the feature's
own close.

### Oracles re-run fresh

Acceptance criterion 1. Every command below was executed in this session and its
exit code read directly. Nothing here is inherited from a producing unit's
`RESULT` block.

Scoped red→green tests named in T01 and T02, and T03's structural guard:

```
$ python3 -m unittest tests.test_prerun_oracles.TestPreDispatch.test_prep_failure_halts_before_dispatch
Ran 1 test in 0.020s / OK                                              EXIT=0
$ python3 -m unittest tests.test_prerun_capture.TestCapture.test_verdict_survives_truncation
Ran 1 test in 0.000s / OK                                              EXIT=0
$ python3 -m unittest tests.test_oracle_set_declared
Ran 2 tests in 0.001s / OK                                             EXIT=0
```

Symbol-existence checks (T01 criterion 7, T02 criterion 7) — the check that exists
because a green `code` gate cannot detect a symbol that is absent:

```
$ python3 -c "from specfuse.loop.prerun import run_pre_dispatch, resolve_prerun_sets, PREP_HALT_CLASS"
                                                                       EXIT=0
$ python3 -c "from specfuse.loop.prerun_capture import format_oracle_capture, ORACLE_CAPTURE_BUDGET_BYTES"
                                                                       EXIT=0   (budget = 8000)
```

The full `code` gate set, all sixteen entries as `.specfuse/verification.yml`
declares them:

```
tests                        Ran 2325 tests in 129.906s / OK (skipped=3)   EXIT=0
lint                         All checks passed!                            EXIT=0
security                     Medium: 0                                     EXIT=0
coverage                     TOTAL 7492 stmts, 506 miss, 93%               EXIT=0
leak-scan                    gitleaks 8.30.1 / clean                       EXIT=0
event-type-gate              0 errors, 52 files, 1202 events               EXIT=0
roadmap-link-gate            0 error(s), 8 warning(s)                      EXIT=0
arm-sweep-gate               13 evaluable swept clean                      EXIT=0
monitoring-example-lint      structurally valid                            EXIT=0
leak-scan-hook (bats)        3 tests ok                                    EXIT=0
sync-scaffold-bats           9 tests ok                                    EXIT=0
sync-scaffold-symlinks-bats  4 tests ok                                    EXIT=0
init-sh-shim-bats            5 tests ok                                    EXIT=0
init-skills-bats             1 test ok                                     EXIT=0
hookspath-conflict-bats      4 tests ok                                    EXIT=0
```

And this WU's own declared gate:

```
$ python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0057-executable-oracle-contract
OK — structurally valid                                                EXIT=0
```

**The `oracles` set T03 declared was not re-run here.** Both its entries are `git`
commands and this work unit's **Do not touch** section forbids running `git` at
all. Its structural guard (`tests/test_oracle_set_declared.py`) ran instead, and
the omission is recorded under *Deferred verification*.

**Every oracle passes and the definition of done is still unmet.** That sentence
is the whole point of §1. The `code` gate was green throughout; it was green
before the feature started too, and it would stay green if both new modules were
deleted, because nothing depends on them.

### A second, smaller finding: `select_gate_report_lines` does not recognise ruff's verdict

Found while reading T02's attempt-1 `failure_excerpt`, and directly load-bearing
for T02's own mechanism. The captured `lint` report ended:

```
specfuse/loop/prerun_capture.py:58:9: B905 `zip()` without an explicit `strict=` parameter
Found 1 error.
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary
anywhere in its output — the lines above are the tail only, and may be unrelated
to the failure. Run the command directly.
```

Re-run in this session against the selector directly: `select_gate_report_lines`
returns the two real lines plus the `NO VERDICT FOUND` banner — it does **not**
treat `Found 1 error.` as a verdict line. So for this repository's `lint` gate,
`_fit_to_budget` pins nothing and degrades to a positional tail, which is the
precise defect FEAT-2026-0068 fixed for `tests` and `coverage` and which T02's
criterion 3 was written against. It happens not to bite yet — ruff's output is
short and the whole thing fits inside an 8000-byte share — but the guarantee T02
claims does not hold for every gate in this repo's own set. Routed below rather
than fixed: `select_gate_report_lines` is on this unit's **Do not touch** list and
was on T02's.

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3, by grepping the packaging manifests and
every shipped copy of each changed path — **not** from the plan's prediction. The
same three items are appended to `CHANGELOG.md`'s `Unreleased`.

The measurement contradicts this work unit's own framing in two directions, which
is exactly what FEAT-2026-0060's lesson warns about.

**1. `specfuse/loop/prerun.py` — a new importable module in the shipped wheel.**
*(added)* `pyproject.toml`'s `[tool.setuptools.packages.find] include = ["specfuse*"]`
puts every module under `specfuse/` in the wheel, so `run_pre_dispatch`,
`resolve_prerun_sets`, and `PREP_HALT_CLASS` are importable by any consumer that
installs the package. Blast radius: additive — nothing previously occupied that
import path, and no existing symbol changed. **Caveat that belongs in the same
breath:** the driver does not call it, so installing this version changes no
observable driver behaviour.

**2. `specfuse/loop/prerun_capture.py` — a new importable module in the shipped
wheel.** *(added)* Same packaging path; `format_oracle_capture` and
`ORACLE_CAPTURE_BUDGET_BYTES` are importable. Same caveat: no caller.

**3. The `verification` skill documents a `prep` / `oracles` frontmatter contract
the driver does not yet honour.** *(added, and the one item with real consumer
risk)* `plugins/specfuse/skills/verification/SKILL.md` — the plugin-shipped copy,
byte-identical to the vendored `.specfuse/skills/verification/SKILL.md`, both
verified identical by `cmp` in this session — now carries a "Pre-dispatch: `prep`
and `oracles`" section stating that both keys resolve against `verification.yml`
set names and both run before dispatch. A consumer who reads that section and adds
`oracles: [my-set]` to a work unit gets **silence**: no pre-dispatch run, no
captured output, and no warning that the key was ignored, because `load_wu` never
looks at it. This is the blast radius actually measured, and it is documentation
running ahead of behaviour rather than a code contract.

**Two changes the plan predicted and the grep did not find.** Recorded because the
close WU's own body asserts the first of them:

- **`prep` / `oracles` are absent from `WU.template.md`.** `grep -n "prep\|oracles\|extra_gates"`
  returns no match in either the canonical `specfuse/loop/data/templates/WU.template.md`
  or the vendored `.specfuse/templates/WU.template.md`. No producing unit listed
  either copy in `produces:`. This close's dispatch note claims the feature "adds
  two frontmatter keys to the scaffold's work-unit template"; it does not. The
  downstream template blast radius today is **zero**.
- **The `oracles` set is absent from the shipped `verification.yml.example`.**
  `grep -n "^oracles:"` returns nothing in either
  `specfuse/loop/data/verification.yml.example` or the vendored
  `.specfuse/verification.yml.example`; both still declare `code`, `doc`, and
  `plannext` only. T03's `produces:` named `.specfuse/verification.yml` — this
  repository's own config — and that is what changed. A project running
  `specfuse init` or `specfuse upgrade` receives no `oracles` set.

**No undeclared consumer-visible change was found**, so the escalation trigger for
that case did not fire. Every changed shipped path traces to a producing unit's
`produces:` list, with one benign provenance note: T03 declared
`.specfuse/skills/verification/SKILL.md` while the canonical copy is
`plugins/specfuse/skills/verification/SKILL.md`. Both changed, identically; the
mirror is `scripts/sync-scaffold.sh`'s job and the content is the declared content.
Human acknowledgment of this list is the gate review's business
(`autonomy_default: review`; the gate lands at `awaiting_review`).

## Cost analysis

Read from `events.jsonl`'s `attempt_outcome` payloads, not recalled. Every figure
below reconciles against the producing unit's own frontmatter.

| Work unit | Planned | Attempts | Actual | Variance |
|---|---|---|---|---|
| T01 — pre-dispatch runner | $4.00 | 1 | **$0.9773100** | −$3.02 (−76%) |
| T02 — capture budget | $3.50 | 2 | **$1.6730475** | −$1.83 (−52%) |
| T03 — declaration and docs | $2.50 | 1 | **$1.3987404** | −$1.10 (−44%) |
| **Implementation subtotal** | **$10.00** | **4** | **$4.0490979** | **−$5.95 (−60%)** |
| G1-CLOSE | $5.00 | 2 recorded in frontmatter | **not in `events.jsonl` — see below** | unmeasurable |
| **Feature total** | **$15.00** (`PLAN.md`) | — | **≥ $4.05, upper bound unknown** | — |
| Gate budget | $19.00 | — | recorded headroom **$14.95** | — |

Per-attempt ledger, in emission order:

```
T01  attempt 1  passed  $0.9773100   383.207s
T02  attempt 1  FAILED  $0.9017985   431.404s   failure_class=lint  signature=B905
T02  attempt 2  passed  $0.7712490   745.600s
T03  attempt 1  passed  $1.3987404   754.855s
                        -----------  ---------
attempt_outcome sum     $4.0490979   2315.066s (38m 35.1s)
```

Frontmatter reconciliation, each line checked independently:

- T01 `cost_usd: 0.97731` = $0.9773100 rounded ✔
- T02 `cost_usd: 1.673048` = $0.9017985 + $0.7712490 = $1.6730475 rounded ✔
- T03 `cost_usd: 1.39874` = $1.3987404 rounded ✔
- Sum of the three = $4.0490979 = the `attempt_outcome` total ✔

**All three implementation units diverged from plan by more than a third, all in
the same direction — under, by 44% to 76%.** The cause is common to all three and
worth naming rather than celebrating: each unit shipped one focused module plus
one test file, with its oracle named, its red-on-HEAD condition spelled out
verbatim, and its **Do not touch** list drawing the boundary at the exact seam
(`_run_gate_set`, `select_gate_report_lines`, the three existing gate-set bodies).
Estimates were set for work of that size done from ambiguity; the specs removed
the ambiguity. The same discipline is *why* the wiring is missing — no unit's
scope included the dispatch call site, and no unit's estimate covered it. The
underspend and the unmet definition of done are the same fact seen twice.

**The close's spend is not recorded anywhere, and that is itself a finding.**
`WU-90`'s frontmatter reads `attempts: 2` and carries no `cost_usd`,
`duration_seconds`, or token fields; `events.jsonl` contains **zero** events with
correlation ID `FEAT-2026-0057/G1-CLOSE` — not a `task_started`, not an
`attempt_outcome`. The file holds 10 events, all for T01/T02/T03. So two close
cycles ran (the first of them refused post-session by
`assert_changelog_entry_for_contract_changes`, per this session's dispatch note)
and left no cost trail at all. The `$4.05` total above is therefore a **lower
bound on the feature**, and no upper bound can be stated from the repository's own
records. Named rather than estimated: inventing a plausible close figure is
exactly the recall-instead-of-read this criterion forbids. Routed below.

### Failure-class breakdown

One non-passing attempt among the four recorded — 25% of recorded attempts,
$0.9017985 of $4.0490979 (22.3%) of recorded spend.

| `failure_class` | `failure_signature` | Attempts | Spend | Unit |
|---|---|---|---|---|
| `lint` | `B905` | 1 | $0.9017985 | T02 attempt 1 |

`B905` is flake8-bugbear's `zip-without-explicit-strict`, raised by `ruff` against
`specfuse/loop/prerun_capture.py:58` — a one-line mechanical defect with an
available autofix, costing a full fresh attempt at $0.90 and 431 seconds. T02's
attempt 2 passed. The `ruff` invocation is the second entry in this repo's `code`
gate set and runs after `tests`, so the attempt paid for the full 2300-test suite
before the linter rejected it.

**Two non-passing close attempts are missing from this table**, and they are the
larger number. `WU-90` carries `attempts: 2` with no matching events, so neither
their spend nor their failure class can be tabulated. The one thing known about
them is the dispatch note's statement that a prior attempt failed
`assert_changelog_entry_for_contract_changes` — a driver refusal, not a gate
failure, which is consistent with it never reaching the `attempt_outcome` emitter.

## Deferred verification

Per acceptance criterion 3, one entry per acceptance criterion not verified
in-loop.

**1. The declared `oracles` set was never executed.**
- *Criterion:* T03's criterion 1 — `.specfuse/verification.yml` declares an
  `oracles` set "with at least one entry, each carrying both `name` and
  `command`, and each command self-contained."
- *Why not verified here:* both entries (`recent-commits`, `diff-stat`) are `git`
  commands, and this work unit's **Do not touch** section states plainly that the
  driver owns all git and that this session must never run it. Running them to
  verify them would have violated the unit's own boundary.
- *Where it actually gets checked:* structurally, by
  `tests/test_oracle_set_declared.py`, which ran green here and asserts the set is
  non-empty and every entry carries both keys. Behaviourally, nowhere — the first
  time a session is dispatched with `oracles: [oracles]` and the driver actually
  reads it, which cannot happen until FU-1 lands.

**2. That `run_pre_dispatch`'s prep-halt reaches an operator as a distinct halt.**
- *Criterion:* `GATE-01.md`'s definition of done — "the driver … halts distinctly
  when prep fails."
- *Why not verified here:* `PREP_HALT_CLASS` exists and `run_pre_dispatch` returns
  it, verified by T01's tests. But no caller consumes the outcome, so there is no
  halt path to observe — the driver has no branch that reads `halted` or
  `halt_class`. Verifying it would require the wiring that FU-1 describes.
- *Where it actually gets checked:* the first real prep failure after FU-1 lands.
  Until then the halt class is a constant in an unread return value.

**3. Behaviour of either new module for a downstream consumer.**
- *Criterion:* the consumer-visible enumeration above, items 1 and 2 — both
  modules ship in the wheel.
- *Why not verified here:* this repository is the only corpus the session has, and
  no consumer imports either module. Their entire exercised surface is the two
  test files.
- *Where it actually gets checked:* nowhere automatically. Since the driver does
  not call them, a downstream project that upgrades sees no behaviour change at
  all — which is the honest and reassuring half of the same fact.

## What the loop did NOT verify

**The feature's central claim is unverified because it is unbuilt.** Stated
plainly and first, because it is the largest thing this document has to say and no
amount of green gate output changes it: the driver does not run `prep`, does not
run `oracles`, does not inject captured output into any session prompt, and does
not know those two frontmatter keys exist. The evidence is under *What was not
built* — the dataclass field list, the negative probe through `load_wu`, and the
caller grep — and it was produced by measurement, not by reading a `RESULT` block.

**No oracle disagreed with any producing unit's self-report, and none could
have.** T01, T02, and T03 each named oracles scoped to their own module: a red→green
test, a symbol import, a structural guard, plus the shared `code` gate. All fifteen
re-ran green here. None of them could observe a missing caller, because none of
them asserts on the dispatch path. The escalation trigger for oracle-vs-self-report
disagreement therefore did not fire — and the definition of done is still unmet.
That is not a contradiction; it is the reason `close-discipline.md` §1 asks for a
**feature-level** re-run rather than a re-check of each unit's own oracle.

**The close's own cost is unrecorded and unverifiable.** Two close cycles produced
zero `events.jsonl` entries. Every cost figure in this document is a lower bound on
the feature, and the `$14.95` gate headroom above is the headroom against
*recorded* spend, not against actual spend. Routed as FU-3.

**No auto-close debt was inherited.** This feature has one gate and one close, no
predecessor gate auto-closed, and `grep -rn "specfuse:autoclose-debt"` over the
feature folder returns no matches. `auto_close_disabled: true` on `WU-90` held —
this body ran, twice.

**`select_gate_report_lines` does not recognise ruff's `Found N error(s).` as a
verdict**, re-run and confirmed in this session against the exact string from
T02's own failure excerpt. T02's verdict-preservation guarantee therefore does not
hold for this repository's `lint` gate. Routed as FU-4; not fixed, because the
selector is on this unit's **Do not touch** list.

## Hedged-verdict follow-up record

Four entries, per `close-discipline.md` §2. The first two are the unmet halves of
the definition of done; the second two are findings this close produced that no
criterion asked for.

### FU-1 — the driver does not read `prep:` or `oracles:` from work-unit frontmatter

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"A work unit
  can declare `prep:` and `oracles:` in its frontmatter, both resolving against
  `.specfuse/verification.yml` set names."* And *"The driver runs prep fail-fast
  and oracles capture-all **before** dispatching the session, and halts distinctly
  when prep fails."*
- **Why it is unmet here:** `WorkUnit` has no `prep` or `oracles` field and
  `load_wu` has no parse branch for either key — only `extra_gates`
  (`loop.py:612-622`). `resolve_prerun_sets` reads both through
  `getattr(wu, "prep", None)`, which on a real `WorkUnit` is unconditionally
  `None`, so `run_pre_dispatch` returns the empty outcome for a unit that declared
  both keys. No dispatch path imports `specfuse.loop.prerun`. Verified in this
  session by the probe quoted under *What was not built*.
- **Why it was not fixed in this session:** `specfuse/loop/loop.py` and `tests/`
  are on this work unit's **Do not touch** list, which states that a defect found
  here is a finding to route, not a fix to make. Wiring the dispatch path is a
  substantive implementation unit, not a close's edit.
- **The exact re-run condition that would upgrade the verdict to `met`:** add
  `prep: list[str]` and `oracles: list[str]` to `WorkUnit` and parse both in
  `load_wu` with the same string-or-list handling `extra_gates` gets at
  `loop.py:612-622`; call `run_pre_dispatch(wu, feature_dir, cfg)` from the
  dispatch path *before* the session is started; and branch on the returned
  `halted` / `halt_class`, surfacing `PREP_HALT_CLASS` as a halt distinct from any
  exit-time verification failure. It upgrades to `met` when the probe under *What
  was not built* — a real WU file declaring `prep: [<set>]` and `oracles: [<set>]`
  loaded through `load_wu` — returns non-empty `prep_results` and
  `oracle_results`, and when a WU whose prep entry exits non-zero halts before
  dispatch with `halt_class == "prep_halt"` and no later prep entry executed.
- **kind:** `externally-verifiable-later`

### FU-2 — captured oracle output never reaches a session prompt

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The captured
  oracle output reaches the session as input, under a byte budget that preserves
  verdicts rather than tails."* And T02's own criterion 5 — *"The formatted section
  is appended to the work-unit body handed to the session, and a work unit with no
  `oracles` receives no section and no marker."*
- **Why it is unmet here:** `format_oracle_capture` is called from exactly one
  place in the repository — `tests/test_prerun_capture.py`. Nothing in
  `specfuse/loop/loop.py` imports `specfuse.loop.prerun_capture`, and the
  work-unit body handed to a session is assembled without it. The *budget* half of
  the criterion is met and tested (≤ 8000 bytes for any input, verdict-aware line
  selection, explicit dropped-bytes marker); the *reaches the session* half is not.
  This is the half of T02's criterion 5 that its named oracles do not assert:
  `tests/test_prerun_capture.py` tests the formatter's return value, never its
  delivery.
- **Why it was not fixed in this session:** same boundary as FU-1 —
  `specfuse/loop/loop.py` and `tests/` are **Do not touch**.
- **The exact re-run condition that would upgrade the verdict to `met`:** after
  FU-1's wiring, pass `run_pre_dispatch`'s `oracle_results` through
  `format_oracle_capture` and append the returned section to the work-unit body
  the session receives. It upgrades to `met` when a dispatched session's prompt
  contains the `## Captured oracle output (pre-dispatch)` header with one
  `### oracle: <name> (OK|FAIL)` block per declared entry, when a WU declaring no
  `oracles` receives neither header nor marker, and when the appended section's
  byte length is ≤ `ORACLE_CAPTURE_BUDGET_BYTES`. The natural first proof is a
  close work unit declaring `oracles: [oracles]` and reading the injected output
  instead of re-deriving it — the adoption this feature was built for, and the one
  this close could not perform.
- **kind:** `externally-verifiable-later`

### FU-3 — a close work unit's attempts leave no record in `events.jsonl`

- **The criterion, verbatim:** this work unit's acceptance criterion 2 — *"actual
  spend is reconciled against `planned_cost_usd: 15.00` and against each unit's own
  estimate (T01 $4.00, T02 $3.50, T03 $2.50, **this close $5.00**), read from
  `events.jsonl` rather than recalled."*
- **Why it is unmet here:** the close's own estimate cannot be reconciled against
  anything. `WU-90` reads `attempts: 2` and carries no cost or duration fields;
  `events.jsonl` holds 10 events, all for T01/T02/T03, and **zero** carrying
  correlation ID `FEAT-2026-0057/G1-CLOSE`. Three of the four figures the criterion
  names were read and reconciled to the cent; the fourth has no source. Reconciling
  it from memory is precisely what the criterion forbids, so it is left unreconciled
  and named.
- **Why it was not fixed in this session:** the emitter is in
  `specfuse/loop/loop.py`, **Do not touch**, and the missing events are historical
  — a later write cannot recover spend that was never recorded.
- **The exact re-run condition that would upgrade the verdict to `met`:** determine
  whether a close attempt refused post-session by a `closing_requirements` guard
  (here `assert_changelog_entry_for_contract_changes`) reaches the `attempt_outcome`
  emitter at all; if it does not, emit one carrying the guard ID as
  `failure_class` / `failure_signature` before the refusal returns. It upgrades to
  `met` for a *future* feature when a guard-refused close attempt produces an
  `attempt_outcome` event whose cost matches the attempt, so a terminal close can
  reconcile its own estimate the way it reconciles every other unit's. This
  feature's two lost cycles are not recoverable.
- **kind:** `externally-verifiable-later`

### FU-4 — `select_gate_report_lines` does not treat ruff's summary as a verdict

- **The criterion, verbatim:** T02's criterion 3 — *"When an oracle's output
  exceeds its share of the budget, the retained lines are selected via
  `select_gate_report_lines`, so a verdict line near the top of the output
  survives while the middle is dropped."*
- **Why it is unmet here:** met for the gates FEAT-2026-0068 tuned it against, not
  universally. Re-run in this session on the exact captured `lint` output from
  T02's own attempt-1 `failure_excerpt`, the selector returns the file line, the
  `Found 1 error.` line, and a `NO VERDICT FOUND` banner — it does not classify
  ruff's summary as a verdict, so nothing is pinned and `_fit_to_budget` degrades
  to a positional tail for this repository's `lint` gate. Not yet harmful (ruff's
  output fits well inside an 8000-byte share) but the stated guarantee does not
  hold across this repo's own gate set.
- **Why it was not fixed in this session:** `select_gate_report_lines` lives in
  `specfuse/loop/loop.py`, on this unit's **Do not touch** list and on T02's.
- **The exact re-run condition that would upgrade the verdict to `met`:** teach
  `select_gate_report_lines` to recognise ruff's `Found N error(s).` and
  `All checks passed!` as verdict lines. It upgrades to `met` when
  `select_gate_report_lines(<ruff failing output>, window=15)` returns the
  `Found N error` line without the `NO VERDICT FOUND` banner, and when a synthetic
  ruff report of 500+ lines still shows that summary after `format_oracle_capture`
  bounds it.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** All four entries are `externally-verifiable-later`, so
in-repo rework exists for every one of them and the operator has a real choice
between accepting this hedge and arming work units against FU-1 and FU-2. FU-1 and
FU-2 are the definition of done; FU-3 and FU-4 are independent findings that would
not block a `met` on their own. The precedent for this shape is FEAT-2026-0067,
whose first close returned `partially_met` with one named re-run condition, whose
operator chose fix-and-re-close, and whose re-armed close cleared the hedge.

## Lessons promoted

Three entries in `.specfuse/LEARNINGS.md`, all tagged `FEAT-2026-0057/G1-CLOSE`.

**1. Per-unit oracles cannot see a missing caller — the feature-level oracle is a
different question, and it needs its own criterion.** This is the run's central
lesson and it is not the one the WU body predicted. Every acceptance criterion in
all three producing units was satisfiable by a module in isolation: a red→green
test on the module, an import of its symbols, a structural guard on a config key.
All three passed honestly. The feature-level claim — the driver runs this before
dispatch — was asserted by no criterion in any unit, so the composite went unbuilt
while every part was green.

**2. `produces_driver_helper` names symbols; it does not name callers.** T01 and
T02 both declared their new symbols there, and both declarations are accurate. A
symbol-existence check is precisely the gap the WU bodies said it filled — "the
`code` gate passes when no test asserts a symbol exists and cannot detect its
absence" — and it filled exactly that gap and no more. Existence and integration
are two claims; the frontmatter surface only carries the first.

**3. The existing-mechanism search worked, and the roadmap entry it corrected is
the reason the scope was right.** The predicted lesson did land: three greps found
that `verification.yml` named sets, `extra_gates` per-WU selection, `_run_gate_set`
execution and capture, and FEAT-2026-0068's verdict-aware selection all already
shipped, so the roadmap's originally-framed goal was ~70% built. `PLAN.md` recorded
the verdict, dropped the duplicate GATE-frontmatter declaration surface, and scoped
the feature to the one missing thing — timing. The three units came in 60% under
estimate because of it. The search is not what failed here; the search's own output
named the seam correctly and no unit was given the seam to cross.

## Verdict

**`partially_met`.**

Verified fresh in this session, none of it inherited from a producing unit's
`RESULT` block:

- `specfuse/loop/prerun.py` and `specfuse/loop/prerun_capture.py` exist, import
  cleanly, and behave as their units specified — prep fail-fast with a distinct
  halt class, oracles capture-all, a named CONFIGURATION ERROR for an unknown set,
  an empty outcome for a unit declaring neither key, and a budget-bounded section
  with verdict-aware line selection and an explicit dropped-bytes marker.
- `.specfuse/verification.yml` declares a two-entry `oracles` set, guarded
  structurally in both directions, added without touching the three existing set
  bodies — the additivity the gate's sequencing depended on.
- The `verification` skill documents `prep` / `oracles` against `extra_gates` with
  a choosing rule, in both shipped copies, verified byte-identical.
- All three implementation work units are `done`, the terminal close has run, and
  the full `code` gate set plus `plannext` are green at 2325 tests and 93% coverage.

Not met, measured rather than assumed:

- **The driver does not read `prep:` or `oracles:`.** `WorkUnit` carries neither
  field, `load_wu` parses neither key, and a real work unit declaring both yields
  the empty pre-dispatch outcome (FU-1).
- **Captured output never reaches a session.** `format_oracle_capture` has no
  caller outside its own test file (FU-2).
- **No work unit uses the declared `oracles` set** — including this close, whose
  own body forbids the `git` commands that set exists to run on its behalf.

The two new modules ship in the wheel and are therefore consumer-visible, but they
change no observable driver behaviour, so a downstream project that upgrades sees
nothing new. The one real consumer risk is documentation ahead of behaviour: the
shipped `verification` skill describes a frontmatter contract that a consumer can
adopt and be met with silence. That item, and the two the plan predicted but the
grep did not find, are enumerated above and in `CHANGELOG.md`'s `Unreleased`.

Both unmet criteria are `externally-verifiable-later` with re-run conditions
written to be authorable-from. The gate lands at `awaiting_review` and `PLAN.md`
stays `active`, which on this evidence is the correct terminal state.
