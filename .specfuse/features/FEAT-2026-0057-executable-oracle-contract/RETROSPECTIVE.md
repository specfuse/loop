<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0057: the pre-dispatch half, built, then wired

Single terminal gate, four implementation work units, one close run twice. The
feature's headline claim is that a work unit can declare `prep:` and `oracles:` in
its frontmatter, that the driver runs them **before** dispatch — prep fail-fast,
oracles capture-all — and that the captured output reaches the session as input
under a byte budget that preserves verdicts.

This is the second close. The first returned `partially_met` on a measured
finding: T01–T03 built three correct, tested modules and **nothing called them**.
T04 was armed against that finding and has landed. This document is a rewrite for
the feature as a whole, not an append; the first pass's findings appear here as
history that has been re-measured, and three of its four follow-ups are discharged
by evidence produced in this session.

**The mechanism now works, and this close still could not observe it working in
the one place it was supposed to.** The dispatch path calls the runner, the
capture reaches `wu.body` before `dispatch()` reads it, and an end-to-end probe
through the real `execute_unit_attempt` produces the `## Captured oracle output
(pre-dispatch)` header. But this session — a real dispatched close declaring
`oracles: [oracles]`, chosen deliberately as the adoption proof — received **no
such section in its prompt**. The cause is measured below and it is not a code
defect. It is why the verdict is `met_locally` rather than `met`.

## Gate 1 — a work unit can declare prep steps and oracles that run before its session

### What was built

**T01 — the pre-dispatch runner (`done`, 1 attempt, $0.98 against $4.00).**
`specfuse/loop/prerun.py` ships `run_pre_dispatch(wu, feature_dir, cfg)`,
`resolve_prerun_sets(wu, cfg)`, and `PREP_HALT_CLASS = "prep_halt"`. Prep entries
run in declared order and stop at the first non-zero exit; oracles run capture-all
on prep success; an unresolvable set name returns a named CONFIGURATION ERROR
mirroring `verify()`'s `extra_gates` phrasing; a unit declaring neither key returns
the empty outcome without invoking `_run_gate_set`. It calls `_run_gate_set`
rather than reimplementing gate execution, exactly as the scope boundary required.

**T02 — the capture budget (`done`, 2 attempts, $1.67 against $3.50).**
`specfuse/loop/prerun_capture.py` ships `format_oracle_capture(results)` and
`ORACLE_CAPTURE_BUDGET_BYTES = 8000`. The budget is split evenly across oracles;
each oracle's report is fitted through `select_gate_report_lines` (FEAT-2026-0068)
rather than a positional tail, and any truncation carries an explicit
`... [N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES] ...` marker. The 8000
figure was not guessed — it is the `max_chars` `truncate_failure_note`
(`loop.py:2169`) already uses for the same class of injected content, reused and
cited in a comment at the constant.

**T03 — the declaration and the written contract (`done`, 1 attempt, $1.40 against
$2.50).** `.specfuse/verification.yml` gained a top-level `oracles:` key with two
self-contained entries (`recent-commits`, `diff-stat`), appended without touching
the `code` / `doc` / `plannext` bodies — the additivity the gate's sequencing
rested on. `tests/test_oracle_set_declared.py` guards it structurally in both
directions. `.specfuse/skills/verification/SKILL.md` gained a "Pre-dispatch:
`prep` and `oracles`" section with a `prep`-vs-`oracles`-vs-`extra_gates` table and
an explicit choosing rule.

**T04 — the wiring (`done`, 1 attempt, $5.14 against $3.50).** The unit the first
close's FU-1 and FU-2 asked for, and the only unit in this gate for which
`specfuse/loop/loop.py` was in scope. It added `prep: list[str]` and
`oracles: list[str]` to the `WorkUnit` dataclass, gave `load_wu` a parse branch for
each with the same string-or-list-or-raise handling `extra_gates` gets, and put the
call site inside `execute_unit_attempt` (`loop.py:3246-3255`) — deferred imports,
because `specfuse.loop.prerun` imports `_run_gate_set` from `loop` and a
module-level import would be circular. A halt returns the new `"prep_halted"`
outcome *before* `dispatch()` is reached; `run()`'s branch at `loop.py:5794`
resets the tree, flips the WU to `blocked_human`, emits an `attempt_outcome`
carrying `halt_class` and a `human_escalation` event with `reason: "prep_halted"`,
and commits bookkeeping — a halt shape distinct from an agent-reported block and
from an exit-time verification failure. `tests/test_prerun_wiring.py` guards all
of it in eight tests.

### The first close's three negative probes, re-run

Acceptance criterion 1b. All three were re-run in this session against live code.
Actual output, not a summary.

**Probe 1 — the `WorkUnit` dataclass field list.** First pass (quoted from the
prior retrospective) ended at `extra_gates`. This session:

```
$ python3 -c "import dataclasses, specfuse.loop.loop as L; print([f.name for f in dataclasses.fields(L.WorkUnit)])"
['wu_id', 'file', 'depends_on', 'type', 'model', 'status', 'attempts', 'title',
 'body', 'effort', 'unsandboxed', 'unsandboxed_rationale', 'verdict',
 'produces_driver_helper', 'produces', 'extra_gates', 'prep', 'oracles']
```

`prep` and `oracles` are present. **The field-list half of FU-1 is discharged.**

**Probe 2 — a real WU file through `load_wu`, passed to `run_pre_dispatch`.** Run
twice: once against **this work unit's own live file**, and once against a
temporary unit declaring both keys (the first pass's exact shape).

Against the live `WU-90-gate-1-close.md`, with the repository's real
`verification.yml`:

```
wu.prep    = []
wu.oracles = ['oracles']
verification.yml top-level keys: ['code', 'doc', 'oracles', 'plannext']
resolve_prerun_sets ->
   prep entries  : []
   oracle entries: [{'name': 'recent-commits', 'command': 'git log --oneline -20'},
                    {'name': 'diff-stat', 'command': 'git --no-pager diff --stat main'}]
   error         : None
```

Against a temporary unit declaring `prep: [probe-prep]` and
`oracles: [probe-oracles]`, with a synthetic `verification.yml`-shaped cfg whose
entries are `echo` commands — synthetic deliberately, because the repository's own
`oracles` set is two `git` commands and this unit's **Do not touch** section
forbids running `git`:

```
WorkUnit has attr prep?    True -> ['probe-prep']
WorkUnit has attr oracles? True -> ['probe-oracles']
extra_gates parsed as:     []
run_pre_dispatch ->
   halted        : False
   halt_class    : None
   message       : None
   prep_results  : [{'name': 'prep-ok', 'ok': True, 'report': '### prep-ok: PASS\n```\n$ echo PREP-RAN\nPREP-RAN\n...'}]
   oracle_results: [{'name': 'orc-a', 'ok': True, 'report': '### orc-a: PASS\n```\n$ echo ORACLE-A-OUTPUT\n...'},
                    {'name': 'orc-b', 'ok': True, 'report': '### orc-b: PASS\n```\n$ echo ORACLE-B-OUTPUT\n...'}]
```

The first pass got `([], [], None)` and
`{'halted': False, 'halt_class': None, 'message': None, 'prep_results': [], 'oracle_results': []}`
for the identical input. **Non-empty `prep_results` and `oracle_results`: the probe
half of FU-1 is discharged.**

**Probe 3 — the repo-wide caller grep.** Same seven symbols, same exclusions
(`.venv/`, `build/`, `.git/`), hit counts by file:

```
$ grep -rn 'run_pre_dispatch\|resolve_prerun_sets\|PREP_HALT_CLASS\|format_oracle_capture\|ORACLE_CAPTURE_BUDGET_BYTES\|prerun_capture\|loop\.prerun' . --exclude-dir=.venv --exclude-dir=build --exclude-dir=.git | awk -F: '{print $1}' | sort | uniq -c | sort -rn
  42 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/RETROSPECTIVE.md
  15 tests/test_prerun_oracles.py
  15 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-04-wire-dispatch-path.md
  14 tests/test_prerun_capture.py
  12 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-02-capture-budget-injection.md
  10 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-01-pre-dispatch-runner.md
   9 tests/test_prerun_wiring.py
   8 specfuse/loop/prerun_capture.py
   8 specfuse/loop/prerun.py
   7 specfuse/loop/loop.py
   2 CHANGELOG.md
   ...
```

The first pass found **zero** in `specfuse/loop/loop.py`. This one finds **seven**.
**The caller-grep half of FU-1 and FU-2 is discharged.**

**Probe 4 — end-to-end, added by this close because probes 1–3 prove wiring but not
delivery.** `execute_unit_attempt` called with the real code path and a stub
`dispatch_fn` that captures the body the session would have received:

````
outcome: passed
--- body the stub session received (tail) ---
## Captured oracle output (pre-dispatch)

### oracle: orc-a (OK)
### orc-a: PASS
```
$ echo ORACLE-A-OUTPUT
ORACLE-A-OUTPUT
...
```

### oracle: orc-b (OK)
...
ORACLE_CAPTURE_BUDGET_BYTES = 8000 | PREP_HALT_CLASS = prep_halt
````

The header FU-2's re-run condition named, in the body a real dispatch would carry.
**FU-2's mechanism is discharged in code.**

### The finding: this session got no injected section, and why

This work unit's body says plainly that if T04 landed correctly the prompt would
carry a `## Captured oracle output (pre-dispatch)` section, and that its absence
should be reported as a finding. **It is absent.** The prompt this session
received is byte-for-byte the body of `WU-90-gate-1-close.md` as it sits on disk,
ending at the *Escalation triggers* list, with nothing appended.

Probes 1–4 rule out every code-level explanation: the keys parse, the set
resolves to the two real `git` entries, the runner is called at
`loop.py:3250` unguarded by any `try`, the mutation at `loop.py:3255` writes
`wu.body`, and `dispatch()` at `loop.py:2381` builds the prompt as
`preamble + "\n\n" + wu.body`. Called in a fresh interpreter, that exact path
produces the header.

The cause is **process staleness in the running driver**, and the timestamps are
decisive:

| Fact | Value | Source |
|---|---|---|
| Driver process start | `Wed Aug  5 09:30:46 2026` local = **13:30:46 UTC** | `ps -eo pid,lstart,command`, PID 12759, `python3 -u .specfuse/scripts/loop.py --feature FEAT-2026-0057` |
| Gate 1 baseline probe | `2026-08-05T13:30:46.953628+00:00` | `GATE-01.md` frontmatter — same second, confirming PID 12759 is this run |
| T04 session start | `2026-08-05T13:35:25.427248+00:00` | `WU-04` frontmatter `started_at` |
| T04 duration | `1413.382s` → landed ≈ **13:58:58 UTC** | `WU-04` frontmatter |
| This close's session start | `2026-08-05T13:58:59.057829+00:00` | `WU-90` frontmatter `started_at` |

The driver imported `specfuse/loop/loop.py` at 13:30:46 UTC — **four minutes
before T04's session began and roughly twenty-eight minutes before T04's edit to
that file existed on disk.** Python caches modules in `sys.modules` at first
import; the `execute_unit_attempt` executing in PID 12759 is the pre-T04
function object, which has no pre-dispatch call at all. T04's *deferred* import of
`specfuse.loop.prerun` does not help: the deferral moves the callee's import to
call time, but the call site itself lives in the stale `execute_unit_attempt`, so
it is never reached.

This is a real, generalizable hazard rather than an inconvenience: **a work unit
that modifies the driver cannot take effect for any work unit dispatched by the
same driver process, including the close that judges it.** It is the
self-hosting form of the harness-migration hazard `.specfuse/LEARNINGS.md`
already warns about, and it is promoted below. It is also why the verdict is
`met_locally`: every claim is verified by in-process evidence, and the one
observation that would make it `met` — a real dispatched session finding the
section in its prompt — requires a driver restart this session cannot perform.

### A new finding: an informational oracle has no verdict, so every capture block claims it is missing one

Produced by probe 4, and visible in its output above. `format_oracle_capture`
fits each oracle's report through `select_gate_report_lines`, which is a
**pass/fail verdict selector**. An `oracles` entry is by definition informational —
`git log --oneline -20` has no verdict to find — so the selector appends its
`NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary
anywhere in its output — the lines above are the tail only, and may be unrelated
to the failure. Run the command directly.` banner to **every** oracle block,
including short, complete, untruncated ones.

Two costs. The banner is false on its face for a complete capture — nothing was
truncated and there is no failure to be unrelated to. And its final sentence tells
the reading agent to *run the command directly*, which is the exact behaviour this
feature exists to eliminate and which, for this repository's own `oracles` set, a
close work unit is forbidden to do. Routed as FU-5; `select_gate_report_lines` and
`prerun_capture.py` are both on this unit's **Do not touch** list.

### The pre-existing selector defect (first pass's FU-4), re-run and unchanged

`select_gate_report_lines` still does not recognise ruff's summary as a verdict.
Re-run in this session against the exact string from T02's attempt-1
`failure_excerpt`:

```
>>> select_gate_report_lines("specfuse/loop/prerun_capture.py:58:9: B905 `zip()` without an explicit `strict=` parameter\nFound 1 error.\n", 15)
['specfuse/loop/prerun_capture.py:58:9: B905 `zip()` without an explicit `strict=` parameter',
 'Found 1 error.',
 'NO VERDICT FOUND: ...']
>>> select_gate_report_lines("All checks passed!\n", 15)
['All checks passed!', 'NO VERDICT FOUND: ...']
```

Both ruff verdicts — failing and passing — are unrecognised, so for this
repository's `lint` gate `_fit_to_budget` pins nothing and degrades to a
positional tail. Unchanged from the first pass; carried forward as FU-4.

### Oracles re-run fresh

Acceptance criterion 1. Every command below was executed in this session and its
exit code read directly. Nothing is inherited from a producing unit's `RESULT`
block.

Scoped red→green tests named in T01, T02, and T04, plus T03's structural guard:

```
$ python3 -m unittest tests.test_prerun_oracles.TestPreDispatch.test_prep_failure_halts_before_dispatch
Ran 1 test in 0.013s / OK                                              EXIT=0
$ python3 -m unittest tests.test_prerun_capture.TestCapture.test_verdict_survives_truncation
Ran 1 test in 0.000s / OK                                              EXIT=0
$ python3 -m unittest tests.test_prerun_wiring -v
  test_failing_prep_halts_before_dispatch ................ ok
  test_no_prep_no_oracles_is_a_no_op ..................... ok
  test_oracle_capture_appended_to_body_before_dispatch ... ok
  test_absent_defaults_empty ............................. ok
  test_list_preserved .................................... ok
  test_string_coerced_to_list ............................ ok
  test_wrong_type_raises ................................. ok
  test_declared_prep_and_oracles_reach_the_runner ........ ok
Ran 8 tests in 0.032s / OK                                             EXIT=0
$ python3 -m unittest tests.test_oracle_set_declared
Ran 2 tests in 0.001s / OK                                             EXIT=0
$ python3 -m unittest tests.test_prerun_oracles tests.test_prerun_capture
Ran 11 tests in 0.034s / OK                                            EXIT=0
```

Symbol-existence checks for all four units — the check that exists because a green
`code` gate cannot detect a symbol that is absent:

```
$ python3 -c "from specfuse.loop.prerun import run_pre_dispatch, resolve_prerun_sets, PREP_HALT_CLASS"
prerun OK prep_halt                                                    EXIT=0
$ python3 -c "from specfuse.loop.prerun_capture import format_oracle_capture, ORACLE_CAPTURE_BUDGET_BYTES"
prerun_capture OK 8000                                                 EXIT=0
$ python3 -c "assert 'prep' in fields and 'oracles' in fields"          # T04's produces_driver_helper
WorkUnit.prep / WorkUnit.oracles OK                                    EXIT=0
```

The full `code` gate set, all sixteen entries as `.specfuse/verification.yml`
declares them:

```
tests                        Ran 2333 tests in 100.853s / OK (skipped=3)  EXIT=0
lint                         All checks passed!                           EXIT=0
security                     Medium: 0  High: 0  (Low: 92, below -ll)      EXIT=0
coverage                     TOTAL 7530 stmts, 517 miss, 93%              EXIT=0
leak-scan                    gitleaks 8.30.1 / clean                      EXIT=0
event-type-gate              0 errors, 52 files, 1211 events              EXIT=0
roadmap-link-gate            0 error(s), 8 warning(s)                     EXIT=0
arm-sweep-gate               13 evaluable swept clean                     EXIT=0
monitoring-example-lint      structurally valid                           EXIT=0
leak-scan-hook (bats)        3 tests ok                                   EXIT=0
sync-scaffold-bats           9 tests ok                                   EXIT=0
sync-scaffold-symlinks-bats  4 tests ok                                   EXIT=0
init-sh-shim-bats            5 tests ok                                   EXIT=0
init-skills-bats             1 test ok                                    EXIT=0
hookspath-conflict-bats      4 tests ok                                   EXIT=0
```

The test count moved 2325 → 2333 (+8), exactly `tests/test_prerun_wiring.py`.
Coverage held at 93% across 7530 statements (up from 7492).

And this WU's own declared gate:

```
$ python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0057-executable-oracle-contract
OK — .specfuse/features/FEAT-2026-0057-executable-oracle-contract is structurally valid.   EXIT=0
```

**The `oracles` set T03 declared was still not executed here.** Both entries are
`git` commands and this work unit's **Do not touch** section forbids running `git`
at all — the same constraint as the first pass, and the reason the injected
capture was supposed to be the answer. Its structural guard ran instead. Recorded
under *What the loop did NOT verify*.

**No re-run oracle disagreed with any producing unit's self-report.** All four
units' oracles are green, all four `done` claims are honest, and the escalation
trigger for oracle-vs-self-report disagreement did not fire.

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3, by grepping the packaging manifests and
every shipped copy of each changed path — not from the plan's prediction. The
same items are reflected in `CHANGELOG.md`'s `Unreleased`, whose three
FEAT-2026-0057 entries were written by the **first** close and each carried a
"the driver does not yet call it" caveat that T04 has made false; they are
corrected in the same edit, and a fourth entry is added for T04's behavioural
change.

**1. The driver now honours `prep:` and `oracles:` in work-unit frontmatter.**
*(changed — the one item with real blast radius)* This is a behaviour change for
every downstream project on upgrade, not an additive import path. Three
sub-surfaces, all measured:

- `load_wu` gained parse branches for both keys with the same contract
  `extra_gates` has: a string is coerced to a one-element list, a list is
  preserved, and any other type raises
  ``ValueError: `prep` must be a string or list of strings``. A project whose
  work units carry a `prep:` or `oracles:` key of the wrong shape now **fails to
  load** where it previously ignored the key. Guarded by
  `tests/test_prerun_wiring.py::TestPrepOraclesParsing::test_wrong_type_raises`.
- Every dispatched attempt now calls `run_pre_dispatch` and `load_verification()`
  before spawning the session, for **every** work unit, not only ones declaring the
  keys. A unit declaring neither returns the empty outcome without invoking
  `_run_gate_set` (`test_no_prep_no_oracles_is_a_no_op`), so the cost is one dict
  construction — but the call is unconditional, and a project with an unparseable
  `verification.yml` now fails earlier than before.
- A new terminal outcome, `prep_halted`, flips the WU to `blocked_human` and emits
  two events: an `attempt_outcome` with `outcome: "prep_halted"` plus `halt_class`
  and `summary` extras, and a `human_escalation` with `reason: "prep_halted"`.
  Anything parsing `events.jsonl` outcome or escalation-reason values sees a value
  it has never seen. The `event-type-gate` passes on the current corpus (0 errors
  over 1211 events), which tells us the envelope is valid, not that a downstream
  consumer's own parser enumerates the value.

**2. `specfuse/loop/prerun.py` — a new importable module in the shipped wheel.**
*(added)* `pyproject.toml`'s `[tool.setuptools.packages.find] include = ["specfuse*"]`
puts every module under `specfuse/` in the wheel, so `run_pre_dispatch`,
`resolve_prerun_sets`, and `PREP_HALT_CLASS` are importable by any consumer that
installs the package. Additive as an import path — nothing previously occupied it.
**The first close's caveat that "the driver does not call it, so installing this
version changes no observable driver behaviour" is now false**, superseded by
item 1.

**3. `specfuse/loop/prerun_capture.py` — a new importable module in the shipped
wheel.** *(added)* Same packaging path; `format_oracle_capture` and
`ORACLE_CAPTURE_BUDGET_BYTES` are importable. Same superseded caveat.

**4. The `verification` skill's `prep` / `oracles` contract, which the driver now
honours.** *(changed)* `plugins/specfuse/skills/verification/SKILL.md` and the
vendored `.specfuse/skills/verification/SKILL.md` carry the "Pre-dispatch: `prep`
and `oracles`" section T03 wrote. The first close's headline consumer risk was
that this documentation ran **ahead** of behaviour — a consumer adopting
`oracles: [my-set]` got silence. That risk is now closed: the documented contract
is the implemented contract. The change of record here is the removal of a
documentation-vs-behaviour gap, which is why it is classified `changed` rather than
left standing as the `added` the first close logged.

**Two gaps the plan predicted, re-grepped, and still absent.** Both were findings
in the first pass and neither producing unit was scoped to close them, so both
persist — and item 1 makes the second one materially worse than it was:

- **`prep` / `oracles` are absent from `WU.template.md`.**
  `grep -n "prep\|oracles\|extra_gates"` returns **no match** in either the
  canonical `specfuse/loop/data/templates/WU.template.md` or the vendored
  `.specfuse/templates/WU.template.md`. This close work unit's own body asserts
  that the feature "adds two frontmatter keys to the scaffold's work-unit
  template". Measured: **it does not.** The template blast radius is zero, and the
  two keys are undocumented in the one file a work-unit author reads while
  authoring.
- **The `oracles` set is absent from the shipped `verification.yml.example`.**
  `grep -n "^oracles:"` returns nothing in either
  `specfuse/loop/data/verification.yml.example` or the vendored
  `.specfuse/verification.yml.example`; both still declare `code`, `doc`, and
  `plannext` only. That file is in `scaffold.py`'s `_VERSIONED_OVERLAY_EXACT`, so
  `specfuse upgrade` overwrites it — meaning the omission is not a
  local-drift artifact but the shipped seed. The net downstream state after this
  feature: the driver reads `oracles:`, and a project has neither a template
  documenting the key nor a seeded set to point it at. Live and undiscoverable.

**No undeclared consumer-visible change was found**, so the escalation trigger for
that case did not fire. Item 1 traces to T04's `produces: [specfuse/loop/loop.py,
tests/test_prerun_wiring.py]`; items 2–4 trace to T01/T02/T03's `produces:` lists,
with the one benign provenance note carried from the first pass — T03 declared
`.specfuse/skills/verification/SKILL.md` while the canonical copy is
`plugins/specfuse/skills/verification/SKILL.md`; both changed identically and the
mirror is `scripts/sync-scaffold.sh`'s job. Human acknowledgment of this list is
the gate review's business (`autonomy_default: review`; the gate lands at
`awaiting_review` on a hedged verdict).

## Cost analysis

Every figure below was read from `events.jsonl` first. `events.jsonl` is now
complete for this feature — it holds 19 events including **both** G1-CLOSE
`attempt_outcome` records the first retrospective reported as missing. Where a
figure came from frontmatter instead, the line says so.

| Work unit | Planned | Attempts | Actual | Variance | Source |
|---|---|---|---|---|---|
| T01 — pre-dispatch runner | $4.00 | 1 | **$0.9773100** | −$3.02 (−76%) | `events.jsonl` |
| T02 — capture budget | $3.50 | 2 | **$1.6730475** | −$1.83 (−52%) | `events.jsonl` |
| T03 — declaration and docs | $2.50 | 1 | **$1.3987404** | −$1.10 (−44%) | `events.jsonl` |
| T04 — the wiring | $3.50 | 1 | **$5.1367995** | **+$1.64 (+47%)** | `events.jsonl` |
| **Implementation subtotal** | **$13.50** | **5** | **$9.1858974** | −$4.31 (−32%) | — |
| G1-CLOSE (pass 1, both attempts) | $5.00 | 2 | **$10.6878210** | **+$5.69 (+114%)** | `events.jsonl` |
| **Feature lifetime, recorded** | **$18.50** (`PLAN.md`) | **7** | **$19.8737184** | **+$1.37 (+7%)** | — |
| Gate budget | $30.00 | — | headroom **$10.13** before this pass | — | `GATE-01.md` |

Per-attempt ledger, in emission order:

```
T01       attempt 1  passed                        $0.9773100    383.207s
T02       attempt 1  FAILED  lint / B905           $0.9017985    431.404s
T02       attempt 2  passed                        $0.7712490    745.600s
T03       attempt 1  passed                        $1.3987404    754.855s
G1-CLOSE  attempt 1  closing_deliverable_missing   $5.7257470    991.292s
G1-CLOSE  attempt 2  passed                        $4.9620740   1014.603s
T04       attempt 1  passed                        $5.1367995   1413.382s
                                                  -----------  ----------
attempt_outcome sum                                $19.8737184  5734.343s (95m 34.3s)
```

Frontmatter reconciliation, each line checked independently against the events
above:

- T01 `cost_usd: 0.97731` ✔
- T02 `cost_usd: 1.673048` = $0.9017985 + $0.7712490 ✔; `duration_seconds: 1177.004` = 431.404 + 745.600 ✔
- T03 `cost_usd: 1.39874` ✔
- T04 `cost_usd: 5.136799` ✔ (frontmatter and event agree)
- `WU-90` `cumulative_cost_usd: 10.687821` = $5.7257470 + $4.9620740 ✔;
  `cumulative_duration_seconds: 2005.895` = 991.292 + 1014.603 ✔. This is the
  lifetime figure `re_arm_count: 1` and `folded_through_re_arm: 1` say the driver
  folded; `cost_usd: 0.0` on the same file is this pass's not-yet-written value,
  not a contradiction.
- Lifetime sum $19.8737184 = the `attempt_outcome` total ✔

**This pass's own spend is not in the table.** It is written at `task_completed`,
after this session ends, and adding an estimate of it here is the recall-instead-of-read
the criterion forbids. The $19.87 is the feature's lifetime **through the end of
T04**; the true lifetime total is that plus this session.

**Units diverging from plan by more than a third — all five of them.**

- **T01 (−76%), T02 (−52%), T03 (−44%).** One cause, common to all three: each
  shipped one focused module plus one test file, with its oracle named, its
  red-on-HEAD condition spelled out verbatim, and a **Do not touch** list drawing
  the boundary at the exact seam. Estimates were priced for work of that size done
  from ambiguity; the specs removed the ambiguity. The first close named this and
  it survives re-measurement.
- **T04 (+47%, $5.14 against $3.50).** The only unit to overrun, and the reason is
  the mirror image of the three underruns: it was the one unit whose scope was a
  *seam* rather than a module. It touched the repository's largest file, had to
  discover that a module-level import would be circular and reshape the call to a
  deferred one, had to mirror the `blocked` branch's full bookkeeping shape (tree
  reset, status flip, two event emissions, a bookkeeping commit) without being
  handed it, and had to add eight tests spanning three test classes. It landed in
  one attempt, which is the right thing to notice: the overrun bought a correct
  first-pass seam crossing, and $1.64 is a good price for the wiring whose absence
  cost the first close $10.69.
- **G1-CLOSE pass 1 (+114%, $10.69 against $5.00).** Two attempts, the first of
  which cost $5.73 and produced **zero** committed files — refused post-session by
  `assert_changelog_entry_for_contract_changes` with the summary
  ``'Consumer-visible contract changes' names a real change but CHANGELOG.md's
  Unreleased section has no entry tracing to FEAT-2026-0057``. That single guard
  refusal is 29% of the feature's entire recorded lifetime spend. The second
  attempt, at $4.96, came in *under* the $5.00 estimate — the estimate was right;
  the guard round-trip was the cost.

**The close remains the most expensive thing in a feature whose purpose is
reducing close cost.** Pass 1 alone was 54% of recorded lifetime spend. Whether
this feature repays that is not yet answerable, because the mechanism has still
never delivered captured output to a real session.

### Failure-class breakdown

Two non-passing attempts among the seven recorded — 28.6% of attempts,
$6.6275455 of $19.8737184 (**33.4%**) of recorded spend.

| `failure_class` | `failure_signature` | Attempts | Spend | Duration | Unit |
|---|---|---|---|---|---|
| `lint` | `B905` | 1 | $0.9017985 | 431.404s | T02 attempt 1 |
| *(null — driver refusal)* | `closing_deliverable_missing` | 1 | $5.7257470 | 991.292s | G1-CLOSE attempt 1 |

`B905` is flake8-bugbear's `zip-without-explicit-strict`, raised by `ruff` against
`specfuse/loop/prerun_capture.py:58` — a one-line mechanical defect with an
available autofix, costing a full fresh attempt. The `ruff` invocation is the
second entry in the `code` gate set and runs after `tests`, so the attempt paid for
the full suite before the linter rejected it.

The second row is the expensive one and it is a different shape entirely. Its
`outcome` is `closing_deliverable_missing` but its `failure_class` and
`failure_signature` are both **null**, because it is a driver-side
`closing_requirements` refusal rather than a gate failure — `files_touched: []`,
no artifact survived. A close that writes a correct contract-changes enumeration
and forgets the paired `CHANGELOG.md` append pays a full re-attempt. This close
avoided it by treating the enumeration and the changelog append as one write from
one understanding, which is exactly what `close-discipline.md` §3 instructs.

## What the loop did NOT verify

**1. The declared `oracles` set was never executed, in either pass.**
- *Criterion:* T03's criterion 1 — `.specfuse/verification.yml` declares an
  `oracles` set with self-contained commands; and this close's criterion 1, which
  names the `oracles` set among the oracles to re-run.
- *Why not verified here:* both entries (`recent-commits`, `diff-stat`) are `git`
  commands, and this work unit's **Do not touch** section states that the driver
  owns all git and that this session must never run it. The injected capture was
  designed to be the answer to exactly this, and it did not arrive.
- *Where it actually gets checked:* structurally by
  `tests/test_oracle_set_declared.py`, green here. Behaviourally, the first time a
  driver process started *after* T04's commit dispatches a WU declaring
  `oracles: [oracles]`.

**2. That the injected section reaches a real dispatched session.**
- *Criterion:* `GATE-01.md`'s definition of done — "The captured oracle output
  reaches the session as input."
- *Why not verified here:* proven in-process by probe 4 through the real
  `execute_unit_attempt`, and by
  `test_oracle_capture_appended_to_body_before_dispatch`. Not observed in a real
  dispatch, because the driver process running this feature predates T04's edit —
  measured above with timestamps.
- *Where it actually gets checked:* the next dispatch by a driver process started
  after commit `a5e5bba`. FU-2R below.

**3. That `run_pre_dispatch`'s prep-halt reaches an operator as a distinct halt.**
- *Criterion:* `GATE-01.md`'s definition of done — "halts distinctly when prep
  fails."
- *Why not verified here:* the branch now exists (`loop.py:5794`) and is unit-tested
  end-to-end at the `execute_unit_attempt` boundary
  (`test_failing_prep_halts_before_dispatch` asserts `dispatch_fn` was never
  called). The `run()`-level bookkeeping — `blocked_human` flip, the two events,
  the `PREP HALT` operator line, the bookkeeping commit — has never fired on real
  input, because no work unit in this repository declares `prep:`.
- *Where it actually gets checked:* the first real prep failure. Until then the
  operator-facing half is code and not observation. FU-3R below.

**4. Behaviour of the two new modules for a downstream consumer.**
- *Criterion:* the consumer-visible enumeration, items 2 and 3.
- *Why not verified here:* this repository is the only corpus this session has, and
  no external consumer imports either module. Their exercised surface is this
  repo's driver plus three test files.
- *Where it actually gets checked:* nowhere automatically. Note the change from the
  first pass: the reassuring half of this entry ("a downstream project that
  upgrades sees no behaviour change") **no longer holds** — item 1 of the
  enumeration is a real behaviour change on upgrade.

**No auto-close debt was inherited.** One gate, one close, no predecessor gate
auto-closed; `grep -rn "specfuse:autoclose-debt"` over the feature folder returns
no matches. `auto_close_disabled: true` on `WU-90` held — this body ran, three
times across two passes.

**A first-pass finding is retracted.** The first retrospective recorded, and
promoted to `.specfuse/LEARNINGS.md`, that "a close work unit's attempts leave no
record in `events.jsonl`" (its FU-3), on the observation that the file held ten
events and zero for `G1-CLOSE`. That observation was accurate *at the moment it was
made* and the conclusion drawn from it was wrong. The file now holds both
`attempt_outcome` records and the `task_completed`. The real mechanism is
narrower and more useful: **a close's own attempt events are buffered in
`wu_events` and flushed only at the WU's terminal outcome**, so a close session
reading `events.jsonl` mid-flight sees everything about every prior unit and
nothing about itself — including nothing about its own earlier attempts, whose
events are in a buffer that a refused attempt's tree reset discards and a later
attempt rebuilds. The LEARNINGS entry is corrected accordingly rather than left
standing.

## Hedged-verdict follow-up record

Five entries, per `close-discipline.md` §2. FU-1 and FU-2 from the first pass are
**discharged** and are not repeated here; FU-3 is **retracted** as described above.
The entries below are the residue: two re-run conditions that need a restarted
driver, one that needs a real prep failure, the first pass's FU-4 unchanged, and
one new finding this close produced.

### FU-1R — the mechanism has never delivered captured output to a real dispatched session

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The captured
  oracle output reaches the session as input, under a byte budget that preserves
  verdicts rather than tails."*
- **Why it is unmet here:** the code path is complete and verified in-process
  (probe 4, plus `test_oracle_capture_appended_to_body_before_dispatch`), but this
  session — a real dispatched close declaring `oracles: [oracles]`, chosen as the
  adoption proof — received no `## Captured oracle output (pre-dispatch)` section.
  Root cause measured, not inferred: the driver process (PID 12759) imported
  `specfuse/loop/loop.py` at 13:30:46 UTC, roughly 28 minutes before T04's edit to
  that file existed on disk, and Python caches modules at first import, so the
  `execute_unit_attempt` in memory is the pre-T04 function with no pre-dispatch
  call. Not a code defect and not the FU-2 defect surviving.
- **Why it was not fixed in this session:** there is nothing to fix in code, and
  restarting the driver is the operator's action, not this session's — this unit
  edits files only.
- **The exact re-run condition that would upgrade the verdict to `met`:** stop the
  driver process and start a fresh one on a tree containing commit `a5e5bba`, then
  dispatch any work unit declaring `oracles: [oracles]`. It upgrades to `met` when
  that session's prompt contains the `## Captured oracle output (pre-dispatch)`
  header with one `### oracle: <name> (OK|FAIL)` block per declared entry — for
  this repo's set, `recent-commits` carrying `git log --oneline -20` output and
  `diff-stat` carrying `git --no-pager diff --stat main` output — and when the
  appended section's byte length is ≤ `ORACLE_CAPTURE_BUDGET_BYTES`. Re-arming this
  same close unit against a restarted driver is the cheapest form of that proof.
- **kind:** `externally-verifiable-later`

### FU-2R — `prep`'s operator-facing halt path has never fired on real input

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The driver
  runs prep fail-fast and oracles capture-all **before** dispatching the session,
  and halts distinctly when prep fails."*
- **Why it is unmet here:** the fail-fast half is verified —
  `test_failing_prep_halts_before_dispatch` asserts `execute_unit_attempt` returns
  `"prep_halted"` and `dispatch_fn` is never called. The *distinct halt* half is
  the `run()` branch at `loop.py:5794`: tree reset, `blocked_human` flip,
  `attempt_outcome` with `halt_class`, `human_escalation` with
  `reason: "prep_halted"`, a bookkeeping commit, and a `PREP HALT` operator line.
  No work unit in this repository declares `prep:`, so none of that has ever
  executed against a real failing prep entry, and the same stale-process condition
  as FU-1R would have prevented it here in any case.
- **Why it was not fixed in this session:** `specfuse/loop/loop.py` and `tests/`
  are on this unit's **Do not touch** list; a finding here is routed, not fixed.
- **The exact re-run condition that would upgrade the verdict to `met`:** on a
  restarted driver, dispatch a work unit declaring a `prep:` set whose first entry
  exits non-zero. It upgrades to `met` when the WU's status is `blocked_human`,
  `events.jsonl` carries an `attempt_outcome` with `outcome: "prep_halted"` and
  `halt_class: "prep_halt"` plus a `human_escalation` with
  `reason: "prep_halted"`, no session was spawned (the attempt's cost is $0.00),
  and no later `prep` entry in the set executed.
- **kind:** `externally-verifiable-later`

### FU-3R — the two new frontmatter keys are live in the driver and absent from every shipped seed

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"This repo
  declares and uses one real oracle set, guarded structurally, with the contract
  documented alongside `extra_gates` so the difference between pre-dispatch and
  exit is written down."* And this close's criterion 4, which names
  `.specfuse/templates/WU.template.md` and the shipped `verification.yml.example`
  as the paths to check.
- **Why it is unmet here:** re-grepped this session. `prep` / `oracles` appear in
  **neither** `specfuse/loop/data/templates/WU.template.md` nor
  `.specfuse/templates/WU.template.md`; `^oracles:` appears in **neither**
  `specfuse/loop/data/verification.yml.example` nor
  `.specfuse/verification.yml.example`. Both were findings in the first pass, and
  T04 changed the stakes rather than the facts: before T04 the gap was harmless
  (nothing read the keys), and now the driver reads them while a downstream project
  gets no template documenting them and no seeded set to point them at. The
  `verification` skill documents the contract — that half is met — but the skill is
  not what an author reads while filling in frontmatter.
- **Why it was not fixed in this session:** no producing unit listed either
  template or either example in `produces:`, and adding shipped scaffold content is
  an implementation unit's work, not a close's edit.
- **The exact re-run condition that would upgrade the verdict to `met`:** add
  `prep:` and `oracles:` to the canonical `specfuse/loop/data/templates/WU.template.md`
  frontmatter notes alongside `extra_gates`, add a commented `oracles:` set to
  `specfuse/loop/data/verification.yml.example`, and run `scripts/sync-scaffold.sh`
  so the vendored copies match. It upgrades to `met` when
  `grep -n "prep\|oracles" ` finds both keys in both template copies, `^oracles:`
  matches in both example copies, and `specfuse init` into an empty directory
  produces a `verification.yml` carrying the set.
- **kind:** `externally-verifiable-later`

### FU-4 — `select_gate_report_lines` does not treat ruff's summary as a verdict

Carried forward from the first pass unchanged; re-run in this session and
confirmed still open.

- **The criterion, verbatim:** T02's criterion 3 — *"When an oracle's output
  exceeds its share of the budget, the retained lines are selected via
  `select_gate_report_lines`, so a verdict line near the top of the output
  survives while the middle is dropped."*
- **Why it is unmet here:** met for the gates FEAT-2026-0068 tuned it against, not
  universally. Re-run on the exact captured `lint` output from T02's own attempt-1
  `failure_excerpt`, the selector returns the file line, the `Found 1 error.` line,
  and a `NO VERDICT FOUND` banner; on ruff's passing output it returns
  `All checks passed!` and the same banner. Neither ruff verdict is recognised, so
  nothing is pinned and `_fit_to_budget` degrades to a positional tail for this
  repository's `lint` gate. Not yet harmful — ruff's output fits inside an
  8000-byte share — but the stated guarantee does not hold across this repo's own
  gate set.
- **Why it was not fixed in this session:** `select_gate_report_lines` lives in
  `specfuse/loop/loop.py`, on this unit's **Do not touch** list and on T02's.
- **The exact re-run condition that would upgrade the verdict to `met`:** teach
  `select_gate_report_lines` to recognise ruff's `Found N error(s).` and
  `All checks passed!` as verdict lines. It upgrades to `met` when
  `select_gate_report_lines(<ruff failing output>, 15)` returns the
  `Found 1 error.` line without the `NO VERDICT FOUND` banner, and when a synthetic
  ruff report of 500+ lines still shows that summary after `format_oracle_capture`
  bounds it.
- **kind:** `externally-verifiable-later`

### FU-5 — every captured oracle block carries a false "NO VERDICT FOUND" banner telling the agent to run the command itself

New in this pass; produced by probe 4.

- **The criterion, verbatim:** T02's criterion 3, same as FU-4 — the retained lines
  are selected via `select_gate_report_lines`. And `GATE-01.md`'s definition of
  done — *"under a byte budget that preserves verdicts rather than tails."*
- **Why it is unmet here:** `format_oracle_capture` fits every oracle's report
  through `select_gate_report_lines`, which is a **pass/fail verdict selector**.
  An `oracles` entry is informational by design and has no verdict — `git log
  --oneline -20` never will — so the selector appends its banner to every oracle
  block, including short complete untruncated ones. Observed directly in probe 4:
  a two-line `echo ORACLE-A-OUTPUT` capture came back carrying
  ``NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary
  anywhere in its output — the lines above are the tail only, and may be unrelated
  to the failure. Run the command directly.`` Two problems: the claim is false for
  a complete capture (nothing was truncated, there is no failure), and the final
  instruction is the exact behaviour this feature exists to eliminate — worse, for
  this repository's own `oracles` set a close work unit is *forbidden* to follow
  it. This is a design seam FU-4 does not cover: FU-4 is "the selector does not
  know ruff's verdict", this is "an informational oracle has no verdict and should
  not be run through a verdict selector at all".
- **Why it was not fixed in this session:** `specfuse/loop/prerun_capture.py` and
  `select_gate_report_lines` are both on this unit's **Do not touch** list.
- **The exact re-run condition that would upgrade the verdict to `met`:** have
  `format_oracle_capture` fit a report to budget without a verdict banner when the
  report is already within its share, and suppress the `Run the command directly.`
  sentence for `oracles` captures in every case. It upgrades to `met` when
  `format_oracle_capture([{'name':'x','ok':True,'report':'<a short informational capture>'}])`
  returns a section containing the capture and **no** `NO VERDICT FOUND` substring,
  while a report exceeding its share still carries the explicit
  `[N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES]` marker.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** All five entries are `externally-verifiable-later`
(`verdict_ceiling_for_kinds` → `rework exists`), so in-repo rework or an operator
action exists for every one of them and the operator has a real choice between
accepting this hedge and clearing it. FU-1R is the cheapest by a wide margin: it
needs a driver restart and a re-arm of this same close unit, no code change at all.
FU-2R and FU-3R are the remaining halves of the definition of done; FU-4 and FU-5
are independent findings that would not block a `met` on their own.

## Lessons promoted

Two new entries in `.specfuse/LEARNINGS.md` and one correction, all tagged
`FEAT-2026-0057/G1-CLOSE`.

**1. A work unit that edits the driver cannot take effect for anything the same
driver process dispatches — including the close that judges it.** This is the run's
central lesson and the one that cost it a clean verdict. T04 wired the dispatch
path correctly, in one attempt, with eight tests; the very next unit dispatched was
the close designed to observe that wiring, and it observed nothing, because the
driver had imported `loop.py` 28 minutes before the wiring existed. Nothing in the
gate could have caught it: T04's oracles all run in fresh interpreters, and the
close's oracles do too. The self-hosting form of the harness-migration hazard, and
a restart is the whole fix.

**2. An informational oracle has no verdict, so running its output through a
pass/fail verdict selector produces a confident lie.** Every captured block in this
feature's own mechanism carries a `NO VERDICT FOUND ... Run the command directly.`
banner. The reuse of `select_gate_report_lines` was a good instinct — it is the
right budgeting primitive and the alternative was a positional tail — but a
primitive built to answer "did this gate pass?" mis-serves a capture whose purpose
is that there is no question to answer.

**3. A correction, not a new lesson.** The first pass's
`close-attempts-leave-no-ledger` entry generalised from a true observation to a
false rule. Rewritten to the mechanism that is actually true: a close's own attempt
events are buffered and flushed at terminal outcome, so a close reading
`events.jsonl` mid-flight is blind to itself and to its own prior attempts — which
is a real constraint on writing a cost analysis, and is not "the ledger is never
written".

The first pass's other two lessons — `no-unit-owns-the-seam` and
`feature-oracle-is-a-different-question` — are left standing unchanged and are now
independently validated: T04 was armed directly from them, named the call site in
its `produces:`, wrote criteria whose oracles fail if the call is deleted, and
landed in one attempt.

## Verdict

**`met_locally`.**

Verified fresh in this session, none of it inherited from a producing unit's
`RESULT` block. Against `GATE-01.md`'s definition of done, criterion by criterion:

1. *"A work unit can declare `prep:` and `oracles:` in its frontmatter, both
   resolving against `.specfuse/verification.yml` set names."* — **met.**
   `WorkUnit` carries both fields, `load_wu` parses both, and this work unit's own
   live file resolves `oracles: [oracles]` to the two real entries.
2. *"The driver runs prep fail-fast and oracles capture-all before dispatching the
   session, and halts distinctly when prep fails."* — **met locally.** The call
   site exists at `loop.py:3250` and returns `"prep_halted"` before `dispatch()`;
   the distinct-halt bookkeeping exists at `loop.py:5794`. Neither has fired on
   real input (FU-2R).
3. *"The captured oracle output reaches the session as input, under a byte budget
   that preserves verdicts rather than tails."* — **met locally, and the byte-budget
   half is qualified.** Probe 4 through the real `execute_unit_attempt` produces the
   header; this real dispatched session did not receive it (FU-1R), and "preserves
   verdicts" does not hold for ruff (FU-4) or for informational captures at all
   (FU-5).
4. *"This repo declares and uses one real oracle set, guarded structurally, with
   the contract documented alongside `extra_gates`."* — **partially met.** Declared
   and guarded: yes. Documented alongside `extra_gates`: yes, in both shipped skill
   copies. *Used:* `WU-90` declares it and got nothing back, and neither shipped
   seed carries the keys or the set (FU-3R).
5. *"Every implementation work unit in this gate is `done`."* — **met.** T01, T02,
   T03, T04.
6. *"The terminal close has run: retrospective, lessons, docs, and verdict."* —
   **met.** This document, three LEARNINGS writes, four `CHANGELOG.md` entries, and
   this verdict.

Everything the feature claims is true in code and verified by executed commands in
this session. The single thing standing between `met_locally` and `met` is an
observation, not a fix: a driver process started after commit `a5e5bba` dispatching
a work unit that declares `oracles:`. `met` on the evidence available here would be
a claim from the wrong environment, which this unit's escalation triggers name
explicitly.

The gate lands at `awaiting_review` and `PLAN.md` stays `active`
(`verdict_permits_terminal_flips` returns True only for `met`). On this evidence
that is the correct terminal state, and the operator has an unusually cheap path
out of it: restart the driver and re-arm this close.
