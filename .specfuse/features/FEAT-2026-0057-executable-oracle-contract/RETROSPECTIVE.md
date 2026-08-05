<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0057: the pre-dispatch half, built, wired, seeded, and finally observed

Single terminal gate, six implementation work units, one close run three times.
The feature's headline claim is that a work unit can declare `prep:` and
`oracles:` in its frontmatter, that the driver runs them **before** dispatch —
prep fail-fast, oracles capture-all — and that the captured output reaches the
session as input under a byte budget.

This is the third close, and it is the first one that could see the thing the
feature exists to do. Pass 1 returned `partially_met`: T01–T03 built three
correct, tested modules and nothing called them. Pass 2 returned `met_locally`
after T04 wired the call site, because the driver process running that pass had
imported `loop.py` before T04 edited it and therefore dispatched the close with
the pre-T04 code. This pass runs on a freshly started driver process, and:

**The captured oracle output arrived. It is quoted verbatim below, from this
session's own prompt.** That single observation discharges FU-1R, the follow-up
that has capped this feature's verdict for two passes.

This document is a rewrite for the feature as a whole, not an append. The prior
passes' findings appear as history that has been re-measured.

Two things are worse than pass 2 recorded, and both are stated plainly here
rather than reconciled away. **T06 did not discharge FU-5.** Its fix landed in a
branch that the production path never reaches, its own test was written to an
input shape that avoids the defect, and the proof is in this session's injected
capture: it carries the false `NO VERDICT FOUND` banner and the instruction to
`Run the command directly.` — for two `git` commands this work unit is forbidden
to run. And **FU-4 is unchanged**.

## Gate 1 — a work unit can declare prep steps and oracles that run before its session

### The FU-1R proof — the injected capture, quoted

**The `## Captured oracle output (pre-dispatch)` section is PRESENT in this
session's prompt.** Not inferred from the code being correct; pass 2 proved the
code correct and received nothing. Quoted verbatim, in full:

````
## Captured oracle output (pre-dispatch)

### oracle: recent-commits (OK)
### recent-commits: PASS
```
$ git log --oneline -20
a146c77 chore(loop): gate 1 baseline probed clean
7427a21 chore(loop): hold G1-CLOSE at blocked_human for the T05/T06 run
4a7ff35 chore(loop): FEAT-2026-0057 round 3 — T05 seeds, T06 banner fix
2163d8b chore(loop): gate 1 awaiting_review
83cfad3 feat: Close gate 1 — retrospective, lessons, docs, and terminal verdict
a5e5bba feat: Wire the pre-dispatch runner into the driver's dispatch path
53c9932 chore(loop): gate 1 baseline probed clean
a685c75 chore(loop): re-arm FEAT-2026-0057 gate 1 with T04 wiring unit
ed731f4 chore(loop): gate 1 awaiting_review
8902d0a feat: Close gate 1 — retrospective, lessons, docs, and terminal verdict
96bd242 feat: Declare this repo's oracle set and document the pre-dispatch contract
4242a35 feat: Bound the captured oracle output and inject it into the session prompt
5da9db7 feat: Add the pre-dispatch runner for `prep` and `oracles` work-unit frontmatter
f6bc1a1 chore(loop): gate 1 baseline probed clean
a2af1d0 chore(loop): FEAT-2026-0057 plan baseline snapshot
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### oracle: diff-stat (OK)
### diff-stat: PASS
```
$ git --no-pager diff --stat main
 CHANGELOG.md                                       |  11 +
 docs/methodology.md                                |   4 +-
 plugins/specfuse/skills/verification/SKILL.md      |  44 ++
 specfuse/loop/data/docs/methodology.md             |   4 +-
 specfuse/loop/data/templates/WU.template.md        |  12 +
 specfuse/loop/data/verification.yml.example        |   8 +
 specfuse/loop/loop.py                              |  98 ++-
 specfuse/loop/prerun.py                            | 136 ++++
 specfuse/loop/prerun_capture.py                    | 109 +++
 tests/test_oracle_set_declared.py                  |  66 ++
 tests/test_prerun_capture.py                       |  90 +++
 tests/test_prerun_oracles.py                       | 152 ++++
 tests/test_prerun_wiring.py                        | 198 +++++
 tests/test_seed_documents_prerun_keys.py           |  30 +
 32 files changed, 3375 insertions(+), 8 deletions(-)
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```
````

Everything FU-1R's re-run condition named is satisfied:

- the `## Captured oracle output (pre-dispatch)` header is present;
- one `### oracle: <name> (OK|FAIL)` block per declared entry — `recent-commits`
  and `diff-stat`, the exact two entries T03 declared;
- `recent-commits` carries real `git log --oneline -20` output and `diff-stat`
  carries real `git --no-pager diff --stat main` output, both reflecting the
  live branch;
- neither block carries a `[N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES]`
  marker, so neither was truncated and the section is trivially within the
  8000-byte budget.

The capture also did the job it was built for. This work unit's **Do not touch**
list forbids running `git`, and both prior passes recorded the declared `oracles`
set as *never executed* for exactly that reason. This pass read the commit log
and the changeset shape out of its own prompt instead. That is the feature
working.

**And the same quoted block is the evidence that T06's fix does not work in
production.** Both captures end in the banner T06 was armed to remove.

### What was built

**T01 — the pre-dispatch runner (`done`, 1 attempt, $0.98 against $4.00).**
`specfuse/loop/prerun.py` ships `run_pre_dispatch(wu, feature_dir, cfg)`,
`resolve_prerun_sets(wu, cfg)`, and `PREP_HALT_CLASS = "prep_halt"`. Prep entries
run in declared order and stop at the first non-zero exit; oracles run capture-all
on prep success; an unresolvable set name returns a named CONFIGURATION ERROR
mirroring `verify()`'s `extra_gates` phrasing; a unit declaring neither key
returns the empty outcome without invoking `_run_gate_set`. It calls
`_run_gate_set` rather than reimplementing gate execution, as the scope boundary
required.

**T02 — the capture budget (`done`, 2 attempts, $1.67 against $3.50).**
`specfuse/loop/prerun_capture.py` ships `format_oracle_capture(results)` and
`ORACLE_CAPTURE_BUDGET_BYTES = 8000`. The budget is split evenly across oracles;
each oracle's report is fitted through `select_gate_report_lines` rather than a
positional tail, and truncation carries an explicit
`... [N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES] ...` marker. The 8000
figure is `truncate_failure_note`'s existing `max_chars` for the same class of
injected content, reused and cited at the constant.

**T03 — the declaration and the written contract (`done`, 1 attempt, $1.40
against $2.50).** `.specfuse/verification.yml` gained a top-level `oracles:` key
with two self-contained entries (`recent-commits`, `diff-stat`), appended without
touching the `code` / `doc` / `plannext` bodies. `tests/test_oracle_set_declared.py`
guards it structurally in both directions.
`plugins/specfuse/skills/verification/SKILL.md` and its vendored mirror gained a
"Pre-dispatch: `prep` and `oracles`" section with a
`prep`-vs-`oracles`-vs-`extra_gates` table and an explicit choosing rule.

**T04 — the wiring (`done`, 1 attempt, $5.14 against $3.50).** The unit pass 1
asked for, and the only unit in this gate for which `specfuse/loop/loop.py` was
in scope. It added `prep: list[str]` and `oracles: list[str]` to `WorkUnit`, gave
`load_wu` a parse branch for each with the same string-or-list-or-raise handling
`extra_gates` gets, and put the call site inside `execute_unit_attempt` with
deferred imports (a module-level import would be circular). A halt returns the
new `"prep_halted"` outcome *before* `dispatch()` is reached; `run()`'s branch
resets the tree, flips the WU to `blocked_human`, emits an `attempt_outcome`
carrying `halt_class` and a `human_escalation` with `reason: "prep_halted"`, and
commits bookkeeping. `tests/test_prerun_wiring.py` guards it in eight tests.

**T05 — the shipped seeds (`done`, 1 attempt, $0.89 against $2.50).** Armed
against FU-3R. `specfuse/loop/data/templates/WU.template.md` now documents
`prep`, `oracles`, **and** `extra_gates` in its `AUTHOR-SET FIELDS` block, each
naming that it resolves against a `verification.yml` set name and each saying
*when* it runs. `specfuse/loop/data/verification.yml.example` gained a commented
`oracles:` set with a worked example and a note that entries are informational
captures rather than pass/fail gates. `tests/test_seed_documents_prerun_keys.py`
guards both. `scripts/sync-scaffold.sh` propagated both to the vendored copies.

Bringing `extra_gates` along was the right call and is worth recording: it has
shipped since issue #62 and was undocumented in the template an author fills in,
which is the mechanical explanation for this feature's founding observation —
the mechanism existed, did most of what was wanted, and nobody used it.

**T06 — the banner fix (`done`, 1 attempt, $0.68 against $2.50). This unit did
not achieve what it was armed to achieve.** Measured below.

### The first close's three negative probes, re-run

Acceptance criterion 1b. All three re-run in this session against live code.
Actual output, not a summary.

**Probe 1 — the `WorkUnit` dataclass field list.**

```
$ .venv/bin/python3 -c "import dataclasses, specfuse.loop.loop as L; print([f.name for f in dataclasses.fields(L.WorkUnit)])"
['wu_id', 'file', 'depends_on', 'type', 'model', 'status', 'attempts', 'title',
 'body', 'effort', 'unsandboxed', 'unsandboxed_rationale', 'verdict',
 'produces_driver_helper', 'produces', 'extra_gates', 'prep', 'oracles']
EXIT=0
```

Pass 1's list ended at `extra_gates`. `prep` and `oracles` are present.
**The field-list half of FU-1 is discharged.**

**Probe 2 — a real WU file through `load_wu`, passed to `run_pre_dispatch`.**
Run twice: once against this work unit's own live file, once against a temporary
unit declaring both keys.

Against the live `WU-90-gate-1-close.md`, with the repository's real
`verification.yml`:

```
wu.prep        = []
wu.oracles     = ['oracles']
wu.extra_gates = []
verification.yml top-level keys: ['code', 'doc', 'oracles', 'plannext']
resolve_prerun_sets ->
   prep entries  : []
   oracle entries: [{'name': 'recent-commits', 'command': 'git log --oneline -20'},
                    {'name': 'diff-stat', 'command': 'git --no-pager diff --stat main'}]
   error         : None
EXIT=0
```

Against a temporary unit declaring `prep: [probe-prep]` and
`oracles: [probe-oracles]`, with a synthetic cfg whose entries are `echo`
commands — synthetic deliberately, because the repository's own `oracles` set is
two `git` commands this unit may not run:

```
WorkUnit has attr prep?    True -> ['probe-prep']
WorkUnit has attr oracles? True -> ['probe-oracles']
extra_gates parsed as:     []
run_pre_dispatch ->
   halted        : False
   halt_class    : None
   message       : None
   prep_results  : [{'name': 'prep-ok', 'ok': True, 'report': '### prep-ok: PASS\n```\n$ echo PREP-RAN\nPREP-RAN\nNO VERDICT FOUND: ... Run the command directly.\n```'}]
   oracle_results: [{'name': 'orc-a', 'ok': True, 'report': '### orc-a: PASS\n```\n$ echo ORACLE-A-OUTPUT\nORACLE-A-OUTPUT\nNO VERDICT FOUND: ... Run the command directly.\n```'},
                    {'name': 'orc-b', 'ok': True, 'report': '### orc-b: PASS\n```\n$ echo ORACLE-B-OUTPUT\nORACLE-B-OUTPUT\nNO VERDICT FOUND: ... Run the command directly.\n```'}]
EXIT=0
```

Pass 1 got `([], [], None)` and
`{'halted': False, 'halt_class': None, 'message': None, 'prep_results': [], 'oracle_results': []}`
for the identical input. **Non-empty `prep_results` and `oracle_results`: the
probe half of FU-1 is discharged.**

This probe also carries the T06 finding in plain sight, and it is the measurement
that explains it: the `NO VERDICT FOUND ... Run the command directly.` string is
**already inside `result["report"]`** when `run_pre_dispatch` returns. It is put
there by `_run_gate_set`, which builds each report as
`f"### {name}: PASS\n\`\`\`\n$ {command}\n" + "\n".join(select_gate_report_lines(out, window=15)) + "\n\`\`\`"`.
`format_oracle_capture` receives it pre-baked.

**Probe 3 — the repo-wide caller grep.** Same symbols, same exclusions, hit
counts by file:

```
$ grep -rn 'run_pre_dispatch\|resolve_prerun_sets\|PREP_HALT_CLASS\|format_oracle_capture\|ORACLE_CAPTURE_BUDGET_BYTES\|prerun_capture\|loop\.prerun' . --exclude-dir=.venv --exclude-dir=build --exclude-dir=.git | awk -F: '{print $1}' | sort | uniq -c | sort -rn
  38 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/RETROSPECTIVE.md
  17 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-06-oracle-capture-banner.md
  16 tests/test_prerun_capture.py
  15 tests/test_prerun_oracles.py
  15 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-04-wire-dispatch-path.md
  12 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-02-capture-budget-injection.md
  10 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-01-pre-dispatch-runner.md
   9 tests/test_prerun_wiring.py
   8 specfuse/loop/prerun_capture.py
   8 specfuse/loop/prerun.py
   7 specfuse/loop/loop.py
   3 CHANGELOG.md
   3 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/events.jsonl
   3 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-90-gate-1-close.md
   2 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/PLAN.md
   2 .specfuse/LEARNINGS.md
   1 plugins/specfuse/skills/verification/SKILL.md
   1 .specfuse/skills/verification/SKILL.md
   1 .specfuse/features/FEAT-2026-0057-executable-oracle-contract/WU-03-adoption-proof-docs.md
```

Pass 1 found **zero** in `specfuse/loop/loop.py`. This one finds **seven**.
**The caller-grep half of FU-1 and FU-2 is discharged.**

### FU-3R re-verified — discharged, with one literal caveat

The close's discharge condition: *"both key names appear in both shipped template
copies and `^oracles:` matches in both example copies."*

```
$ grep -n "prep\|oracles\|extra_gates" specfuse/loop/data/templates/WU.template.md
44:- `prep` — OPTIONAL. Name of a `verification.yml` set to run **before dispatch**,
48:- `oracles` — OPTIONAL. Name of a `verification.yml` set to run **before dispatch**,
52:- `extra_gates` — OPTIONAL. Name of a `verification.yml` set unioned onto the
55:  `.specfuse/skills/verification/SKILL.md` § `oracles` vs `extra_gates`.
EXIT=0

$ grep -n "prep\|oracles\|extra_gates" .specfuse/templates/WU.template.md
44:- `prep` — OPTIONAL. Name of a `verification.yml` set to run **before dispatch**,
48:- `oracles` — OPTIONAL. Name of a `verification.yml` set to run **before dispatch**,
52:- `extra_gates` — OPTIONAL. Name of a `verification.yml` set unioned onto the
55:  `.specfuse/skills/verification/SKILL.md` § `oracles` vs `extra_gates`.
EXIT=0

$ diff specfuse/loop/data/templates/WU.template.md .specfuse/templates/WU.template.md
IDENTICAL
```

Both key names in both copies, byte-identical. **First half discharged.**

The second half needs an honest caveat rather than a pass:

```
$ grep -n "^oracles:" specfuse/loop/data/verification.yml.example
EXIT=1                       # no match

$ grep -n "^oracles:" .specfuse/verification.yml.example
EXIT=1                       # no match

$ grep -n "oracles" specfuse/loop/data/verification.yml.example
70:# Pre-dispatch sets, referenced by a WU's `prep`/`oracles` frontmatter keys —
73:# .specfuse/skills/verification/SKILL.md § Pre-dispatch for prep vs oracles.
74:# oracles:
EXIT=0

$ diff specfuse/loop/data/verification.yml.example .specfuse/verification.yml.example
IDENTICAL
```

The literal `^oracles:` does **not** match, because the seeded set is commented:

```yaml
# Pre-dispatch sets, referenced by a WU's `prep`/`oracles` frontmatter keys —
# they run BEFORE the session is dispatched, not at exit. Entries here are
# informational captures, not pass/fail gates; see
# .specfuse/skills/verification/SKILL.md § Pre-dispatch for prep vs oracles.
# oracles:
#   - name: recent-history
#     command: "git log --oneline -10 && git diff --stat main"
```

This is a phrasing mismatch between two documents, not a defect. T05's own
criterion 3 asked for a **commented** `oracles:` set, and its criterion 4 asked
the guard to accept `^oracles:` *"(commented or live)"* — which
`tests/test_seed_documents_prerun_keys.py` implements as
`re.search(r"^\s*#?\s*oracles:", ..., re.MULTILINE)` and which passes. This
close's discharge line dropped the "(commented or live)" qualifier. Commented is
also the right shape: a live `oracles:` set in the seed would run two `git`
commands for every work unit in every downstream project that never asked for
them.

**FU-3R is discharged on substance**, with the literal-regex divergence recorded
here so a later reader does not re-derive it as a finding.

### FU-5 re-verified — NOT discharged. T06's fix does not reach the production path

The close's discharge condition: *"`format_oracle_capture` returns no
`NO VERDICT FOUND` substring for a short complete capture and never emits
`Run the command directly.` for any input."* The second half is false. Both
halves of the measurement, run this session:

**Test A — a synthetic short capture (the shape T06's criteria describe). Passes.**

````
$ .venv/bin/python3 -c "format_oracle_capture([{'name':'x','ok':True,'report':'### x: PASS\n```\n$ echo hi\nhi\n```'}])"
## Captured oracle output (pre-dispatch)

### oracle: x (OK)
### x: PASS
```
$ echo hi
hi
```
NO VERDICT FOUND present? False
Run the command directly present? False
EXIT=0
````

**Test B — a report shaped as `_run_gate_set` actually builds it, which is the
only shape the production path ever produces. Fails.**

````
$ .venv/bin/python3 -c "<20-line git-log-shaped output -> select_gate_report_lines -> report -> format_oracle_capture>"
banner in report? True
--- format_oracle_capture output ---
## Captured oracle output (pre-dispatch)

### oracle: recent-commits (OK)
### recent-commits: PASS
```
$ git log --oneline -20
005e30a3 commit subject line 5
...
0165ec05 commit subject line 19
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

NO VERDICT FOUND in section? True
Run the command directly. in section? True
section bytes: 808
EXIT=0
````

**And Test C — this session's own injected prompt, quoted at the top of this
document, carries both strings. That is the defect observed in production, not
in a probe.**

**Root cause, measured.** T06 added the filter inside `_fit_to_budget`
(`specfuse/loop/prerun_capture.py:59`):

```python
lines = [ln for ln in select_gate_report_lines(report, window=15) if ln != _NO_VERDICT_NOTE]
```

That line sits **after** the early return four lines above it:

```python
raw_bytes = report.encode("utf-8")
if len(raw_bytes) <= budget:
    return report, 0          # <-- raw report, unfiltered
```

So the filter runs only when a report **exceeds** its budget share. For a report
within its share — the common case, and the case for both of this repo's
oracles — `format_oracle_capture` returns the report untouched. And the report it
was handed already contains the banner, because `_run_gate_set` composed it from
`select_gate_report_lines` output before `prerun.py` ever returned. T06 filtered
the wrong copy, on the wrong branch.

**Why T06's own oracle did not catch it.**
`tests/test_prerun_capture.py::TestCapture::test_complete_capture_carries_no_verdict_banner`
builds its input as:

```python
log_lines = "\n".join(f"abc{i:04d} commit message {i} " + "x" * 40 for i in range(300))
results = [{"name": "git_log", "ok": True, "report": log_lines}]
```

300 lines × ~60 bytes ≈ 18 KB — deliberately over budget, so it exercises the
truncation branch where the filter lives, and it asserts the dropped-bytes marker
is present. Its input is also a **raw** log with no banner in it. So the test
covers neither of the two conditions under which the defect appears: a report
already carrying the banner, and a report small enough to skip truncation
entirely. It passes honestly and proves less than its name says.

The test name promises "complete capture"; the fixture is a truncated one.

**This is not an oracle disagreeing with a self-report, and the escalation
trigger for that correctly did not fire.** Re-run this session:
`python3 -m unittest tests.test_prerun_capture` → `Ran 6 tests / OK`, and the
full `code` gate set is green. Every oracle T06 declared agrees with T06's
`done`. What is false is T06's **criterion 3** — *"The string `Run the command
directly.` never appears in a section returned by `format_oracle_capture`, for
any input — truncated or not"* — measured against an input its test never used.
This is the same shape this feature's own
[`feature-oracle-is-a-different-question`] lesson describes and pass 1 hit: every
unit green, the feature-level question unasked. Routed as **FU-5R** below, not
fixed here — `specfuse/loop/prerun_capture.py` and `tests/` are on this unit's
**Do not touch** list.

### The pre-existing selector defect (FU-4), re-run and unchanged

```
$ select_gate_report_lines("specfuse/loop/prerun_capture.py:58:9: B905 `zip()` without an explicit `strict=` parameter\nFound 1 error.\n", 15)
'specfuse/loop/prerun_capture.py:58:9: B905 `zip()` without an explicit `strict=` parameter'
'Found 1 error.'
'NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in '

$ select_gate_report_lines("All checks passed!\n", 15)
'All checks passed!'
'NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in '
```

Both ruff verdicts — failing and passing — still unrecognised. Unchanged from
both prior passes; carried forward as FU-4.

### Oracles re-run fresh

Acceptance criterion 1. Every command below executed in this session, exit code
read directly. Nothing inherited from a producing unit's `RESULT` block. Run
unsandboxed: this repo's integration tests falsely red under the sandbox.

Scoped red→green tests named in T01, T02, T04, T05, and T06, plus T03's
structural guard:

```
$ .venv/bin/python3 -m unittest tests.test_prerun_oracles.TestPreDispatch.test_prep_failure_halts_before_dispatch
Ran 1 test in 0.011s / OK                                              EXIT=0
$ .venv/bin/python3 -m unittest tests.test_prerun_capture.TestCapture.test_verdict_survives_truncation
Ran 1 test in 0.000s / OK                                              EXIT=0
$ .venv/bin/python3 -m unittest tests.test_prerun_capture.TestCapture.test_complete_capture_carries_no_verdict_banner
Ran 1 test in 0.000s / OK                                              EXIT=0
$ .venv/bin/python3 -m unittest tests.test_prerun_wiring
Ran 8 tests in 0.024s / OK                                             EXIT=0
$ .venv/bin/python3 -m unittest tests.test_oracle_set_declared
Ran 2 tests in 0.001s / OK                                             EXIT=0
$ .venv/bin/python3 -m unittest tests.test_seed_documents_prerun_keys
Ran 1 test in 0.001s / OK                                              EXIT=0
$ .venv/bin/python3 -m unittest tests.test_prerun_capture
Ran 6 tests in 0.017s / OK                                             EXIT=0
```

Symbol-existence checks for all six units:

```
$ .venv/bin/python3 -c "from specfuse.loop.prerun import run_pre_dispatch, resolve_prerun_sets, PREP_HALT_CLASS"
prerun OK prep_halt                                                    EXIT=0
$ .venv/bin/python3 -c "from specfuse.loop.prerun_capture import format_oracle_capture, ORACLE_CAPTURE_BUDGET_BYTES"
prerun_capture OK 8000                                                 EXIT=0
$ .venv/bin/python3 -c "assert 'prep' in fields and 'oracles' in fields"
WorkUnit.prep / WorkUnit.oracles OK                                    EXIT=0
```

The full `code` gate set, all sixteen entries as `.specfuse/verification.yml`
declares them:

```
tests                        Ran 2335 tests in 96.807s / OK (skipped=3)  EXIT=0
lint                         All checks passed!                          EXIT=0
security                     Medium: 0  High: 0                          EXIT=0
coverage                     TOTAL 7530 stmts, 517 miss, 93%             EXIT=0
leak-scan                    gitleaks 8.30.1 / clean                     EXIT=0
event-type-gate              0 errors, 52 files, 1225 events             EXIT=0
roadmap-link-gate            0 error(s), 8 warning(s)                    EXIT=0
arm-sweep-gate               13 evaluable swept clean                    EXIT=0
monitoring-example-lint      structurally valid                          EXIT=0
leak-scan-hook (bats)        3 tests ok                                  EXIT=0
sync-scaffold-bats           9 tests ok                                  EXIT=0
sync-scaffold-symlinks-bats  4 tests ok                                  EXIT=0
init-sh-shim-bats            5 tests ok                                  EXIT=0
init-skills-bats             1 test ok                                   EXIT=0
hookspath-conflict-bats      4 tests ok                                  EXIT=0
```

The test count moved 2333 → 2335 (+2): T05's seed guard and T06's banner test.
Across the feature, 2325 → 2335 (+10). Coverage held at 93% across 7530
statements — unchanged from pass 2, as expected: T05 added seed data and a test
but no production statements, and T06's edit was one line plus a docstring.

And this WU's own declared gate (`plannext`):

```
$ .venv/bin/python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0057-executable-oracle-contract
OK — .specfuse/features/FEAT-2026-0057-executable-oracle-contract is structurally valid.   EXIT=0
```

**The declared `oracles` set WAS executed this pass** — by the driver, before
dispatch, and its output is quoted at the top of this document. That is the first
time in three passes, and it closes the gap both prior retrospectives recorded
under *What the loop did NOT verify*.

**No re-run oracle disagreed with any producing unit's self-report.** All six
units' oracles are green and all six `done` claims are honest against the oracles
those units declared. The disagreement recorded above is between T06's prose
criterion 3 and a probe its own test never ran — a feature-level finding, routed
as FU-5R, not an oracle contradiction.

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3, by grepping the packaging manifests and
every shipped copy of each changed path. The same items are reflected in
`CHANGELOG.md`'s `Unreleased`; two entries written by earlier passes had become
factually false and are corrected in the same edit rather than left standing.

**1. The driver now honours `prep:` and `oracles:` in work-unit frontmatter.**
*(changed — the item with real blast radius)* A behaviour change for every
downstream project on upgrade. Three sub-surfaces, all measured:

- `load_wu` gained parse branches for both keys with the same contract
  `extra_gates` has: a string is coerced to a one-element list, a list is
  preserved, any other type raises
  ``ValueError: `prep` must be a string or list of strings``. A project whose
  work units carry a `prep:` or `oracles:` key of the wrong shape now **fails to
  load** where it previously ignored the key. Guarded by
  `tests/test_prerun_wiring.py::TestPrepOraclesParsing::test_wrong_type_raises`.
- Every dispatched attempt now calls `run_pre_dispatch` and `load_verification()`
  before spawning the session, for **every** work unit, not only ones declaring
  the keys. A unit declaring neither returns the empty outcome without invoking
  `_run_gate_set` (`test_no_prep_no_oracles_is_a_no_op`), so the cost is one dict
  construction — but the call is unconditional, and a project with an unparseable
  `verification.yml` now fails earlier than before.
- A new terminal outcome, `prep_halted`, flips the WU to `blocked_human` and
  emits two events: an `attempt_outcome` with `outcome: "prep_halted"` plus
  `halt_class` and `summary` extras, and a `human_escalation` with
  `reason: "prep_halted"`. Anything parsing `events.jsonl` outcome or
  escalation-reason values sees a value it has never seen. `event-type-gate`
  passes on the current corpus (0 errors over 1225 events), which says the
  envelope is valid, not that a downstream parser enumerates the value.

**2. `specfuse/loop/prerun.py` — a new importable module in the shipped wheel.**
*(added)* `pyproject.toml`'s `[tool.setuptools.packages.find] include = ["specfuse*"]`
puts every module under `specfuse/` in the wheel, so `run_pre_dispatch`,
`resolve_prerun_sets`, and `PREP_HALT_CLASS` are importable by any consumer.
Additive as an import path.

**3. `specfuse/loop/prerun_capture.py` — a new importable module in the shipped
wheel.** *(added)* Same packaging path; `format_oracle_capture` and
`ORACLE_CAPTURE_BUDGET_BYTES` are importable.

**4. The `verification` skill's `prep` / `oracles` contract.** *(changed)*
`plugins/specfuse/skills/verification/SKILL.md` and the vendored
`.specfuse/skills/verification/SKILL.md` carry T03's "Pre-dispatch: `prep` and
`oracles`" section; `diff` reports the two copies identical. Pass 1's headline
consumer risk was that this documentation ran **ahead** of behaviour; T04 closed
that gap, so the change of record is the removal of a documentation-vs-behaviour
mismatch.

**5. `WU.template.md` now documents `prep`, `oracles`, and `extra_gates` — in a
file `specfuse upgrade` overwrites.** *(changed — new this pass, T05)* Measured
blast radius, not predicted: `templates/` is in `scaffold.py`'s
`_VERSIONED_OVERLAY_PREFIXES` (`specfuse/loop/scaffold.py:398`), so
`specfuse upgrade` overwrites `.specfuse/templates/WU.template.md` in every
downstream project. `[tool.setuptools.package-data]` ships
`"specfuse.loop" = ["data/**/*", "data/*"]`, so the canonical seed travels in the
wheel. Every project that upgrades gets a template documenting three frontmatter
keys, one of which (`extra_gates`) has shipped undocumented since issue #62. The
content is documentation only — no behaviour rides on it — but the file is
genuinely shipped and genuinely overwritten, which is the FEAT-2026-0060 lesson's
other direction: this is the case where the file really is shipped.

**6. `verification.yml.example` now seeds a commented `oracles:` set.**
*(changed — new this pass, T05)* `verification.yml.example` is in
`_VERSIONED_OVERLAY_EXACT` (`scaffold.py:399`), so `specfuse upgrade` overwrites
it outright, and `scaffold.py:164` maps it to `verification.yml` on `init`. The
set is **commented**, so a fresh `specfuse init` produces a `verification.yml`
with no live `oracles` set and therefore no behaviour change — the seed is
discoverable documentation, not an activated gate. That is the correct blast
radius for a set whose worked example runs two `git` commands.

**7. Captured oracle sections still carry a `NO VERDICT FOUND` banner and a
`Run the command directly.` instruction.** *(fixed — partially, T06)* T06
suppressed the banner on the truncation path, so an over-budget capture is now
clean; captures within budget are not, because the banner arrives pre-baked from
`_run_gate_set`. Any downstream project adopting `oracles:` gets prompt text
telling its agent to re-run the captured command. Enumerated here because it is
consumer-facing prompt content, and corrected in `CHANGELOG.md` rather than left
described as fully fixed. FU-5R.

**No undeclared consumer-visible change was found**, so that escalation trigger
did not fire. Item 1 traces to T04's `produces:`; items 2–4 to T01/T02/T03's;
items 5–6 to T05's `produces: [specfuse/loop/data/templates/WU.template.md,
specfuse/loop/data/verification.yml.example, tests/test_seed_documents_prerun_keys.py]`;
item 7 to T06's. One benign provenance note carried from pass 1: T03 declared
`.specfuse/skills/verification/SKILL.md` while the canonical copy is
`plugins/specfuse/skills/verification/SKILL.md`; both changed identically and the
mirror is `scripts/sync-scaffold.sh`'s job. Human acknowledgment of this list is
the gate review's business (`autonomy_default: review`; the gate lands at
`awaiting_review` on a hedged verdict).

## Cost analysis

Sources are named per line, per acceptance criterion 2. Every figure for a unit
other than this close came from `events.jsonl` (33 events, 10 `attempt_outcome`
records). This close's own figure came from **frontmatter** — `re_arm_count: 2`
and `folded_through_re_arm: 2` mean the driver folded both prior cycles into
`cumulative_cost_usd`. This pass's own attempt is in neither source: a close's
attempt events are buffered in `wu_events` and flushed only at terminal outcome.

| Work unit | Planned | Attempts | Actual | Variance | Source |
|---|---|---|---|---|---|
| T01 — pre-dispatch runner | $4.00 | 1 | **$0.9773100** | −$3.02 (−76%) | `events.jsonl` |
| T02 — capture budget | $3.50 | 2 | **$1.6730475** | −$1.83 (−52%) | `events.jsonl` |
| T03 — declaration and docs | $2.50 | 1 | **$1.3987404** | −$1.10 (−44%) | `events.jsonl` |
| T04 — the wiring | $3.50 | 1 | **$5.1367995** | **+$1.64 (+47%)** | `events.jsonl` |
| T05 — shipped seeds | $2.50 | 1 | **$0.8878656** | −$1.61 (−64%) | `events.jsonl` |
| T06 — banner fix | $2.50 | 1 | **$0.6805809** | −$1.82 (−73%) | `events.jsonl` |
| **Implementation subtotal** | **$18.50** | **7** | **$10.7543439** | −$7.75 (−42%) | — |
| G1-CLOSE (passes 1–2, three attempts) | $5.00 | 3 | **$16.0195120** | **+$11.02 (+220%)** | `events.jsonl`, cross-checked against frontmatter |
| **Feature lifetime through T06** | **$23.50** (`PLAN.md`) | **10** | **$26.7738559** | **+$3.27 (+14%)** | — |
| Gate budget | $40.00 | — | headroom **$13.23** before this pass | — | `GATE-01.md` frontmatter |

Per-attempt ledger from `events.jsonl`, in emission order:

```
T01       attempt 1  passed                        $0.9773100    383.207s
T02       attempt 1  FAILED  lint / B905           $0.9017985    431.404s
T02       attempt 2  passed                        $0.7712490    745.600s
T03       attempt 1  passed                        $1.3987404    754.855s
G1-CLOSE  attempt 1  closing_deliverable_missing   $5.7257470    991.292s   (pass 1)
G1-CLOSE  attempt 2  passed                        $4.9620740   1014.603s   (pass 1)
T04       attempt 1  passed                        $5.1367995   1413.382s
G1-CLOSE  attempt 1  passed                        $5.3316910   1026.518s   (pass 2)
T05       attempt 1  passed                        $0.8878656    519.344s
T06       attempt 1  passed                        $0.6805809    565.945s
                                                  -----------  ----------
attempt_outcome sum                               $26.7738559   7846.150s (130m 46.2s)
```

Frontmatter reconciliation, each line checked independently against the events:

- T01 `cost_usd: 0.97731` ✔
- T02 `cost_usd: 1.673048` = $0.9017985 + $0.7712490 ✔; `duration_seconds: 1177.004` = 431.404 + 745.600 ✔
- T03 `cost_usd: 1.39874` ✔
- T04 `cost_usd: 5.136799` ✔
- T05 `cost_usd: 0.887866` ✔
- T06 `cost_usd: 0.680581` ✔
- `WU-90` `cumulative_cost_usd: 16.019512` = $5.7257470 + $4.9620740 + $5.3316910 ✔ **exactly**;
  `cumulative_duration_seconds: 3032.413` = 991.292 + 1014.603 + 1026.518 ✔. `cost_usd: 0.0`
  on the same file is this pass's not-yet-written value, not a contradiction.
- Lifetime sum $26.7738559 = the `attempt_outcome` total ✔

**This pass's own spend is not in the table.** It is written at `task_completed`
after this session ends. The feature's **lifetime** total across all three passes
is $26.7738559 **plus this session** — the $26.77 is complete through T06.

**Units diverging from plan by more than a third — all seven of them.**

- **T01 (−76%), T02 (−52%), T03 (−44%), T05 (−64%), T06 (−73%).** One cause,
  common to all five: each shipped one focused module or seed edit plus one test
  file, with its oracle named, its red-on-HEAD condition spelled out verbatim,
  and a **Do not touch** list drawing the boundary at the exact seam. Estimates
  were priced for work of that size done from ambiguity; the specs removed the
  ambiguity. Two prior passes named this and it survives a third measurement.
  **T06's underspend now reads differently, though**: at $0.68 against $2.50 it
  is the cheapest unit in the feature, and it did not do its job. A spec precise
  enough to make the work cheap also made it possible to satisfy the letter of
  the criteria without meeting them — see the lessons.
- **T04 (+47%, $5.14 against $3.50).** The only unit to overrun, for the mirror
  reason: its scope was a *seam* rather than a module. It touched the largest
  file in the repo, discovered that a module-level import would be circular and
  reshaped the call to a deferred one, mirrored the `blocked` branch's full
  bookkeeping shape without being handed it, and added eight tests across three
  classes. It landed in one attempt. The overrun bought a correct first-pass seam
  crossing, and $1.64 is a good price for the wiring whose absence cost pass 1
  $10.69.
- **G1-CLOSE (+220%, $16.02 against $5.00 across three recorded attempts).** The
  dominant cost in the feature and the thing most worth reading. Three attempts
  before this one, each of which was individually reasonable: attempt 1 of pass 1
  cost $5.73 and produced **zero committed files**, refused post-session by
  `assert_changelog_entry_for_contract_changes`; attempt 2 of pass 1 cost $4.96,
  *under* the $5.00 estimate; pass 2's single attempt cost $5.33 and produced a
  correct, thorough retrospective that could not observe the mechanism because
  the driver process was stale. Only one of the three was avoidable by better
  work inside the session. The other two were paid for **sequencing** — a guard
  round-trip and a process restart — and no amount of care inside a close session
  recovers either.

**The close is 60% of this feature's recorded lifetime spend**, on a feature
whose purpose is reducing close cost. That is the number to carry forward, and
the honest reading is that the two structural costs (guard round-trip, driver
restart) are now both understood and both have durable rules attached, while the
mechanism itself has finally been observed to work. Whether the feature repays
$26.77 depends on adoption, which is now possible for the first time: as of T05,
a downstream author has a template that names the keys and a seed that shows the
shape.

### Failure-class breakdown

Two non-passing attempts among the ten recorded — 20.0% of attempts,
$6.6275455 of $26.7738559 (**24.8%**) of recorded spend.

| `failure_class` | `failure_signature` | Attempts | Spend | Duration | Unit |
|---|---|---|---|---|---|
| `lint` | `B905` | 1 | $0.9017985 | 431.404s | T02 attempt 1 |
| *(null — driver refusal)* | `closing_deliverable_missing` | 1 | $5.7257470 | 991.292s | G1-CLOSE pass 1 attempt 1 |

`B905` is flake8-bugbear's `zip-without-explicit-strict`, raised by `ruff`
against `specfuse/loop/prerun_capture.py:58` — a one-line mechanical defect with
an available autofix, costing a full fresh attempt. The `ruff` invocation is the
second entry in the `code` gate set and runs after `tests`, so the attempt paid
for the full 2300-test suite before the linter rejected it.

The second row is the expensive one and a different shape entirely. Its
`outcome` is `closing_deliverable_missing` but `failure_class` and
`failure_signature` are both **null**, because it is a driver-side
`closing_requirements` refusal rather than a gate failure — `files_touched: []`,
no artifact survived. A breakdown grouping only on `failure_class` drops the
single most expensive attempt in the feature; group on `outcome` too.

Both subsequent close passes avoided that refusal by treating the §3 enumeration
and the `CHANGELOG.md` append as one write from one understanding, which is what
`close-discipline.md` §3 instructs, and by running `specfuse-lint --closing`
before reporting.

## What the loop did NOT verify

**1. That `run_pre_dispatch`'s prep-halt reaches an operator as a distinct halt.**
- *Criterion:* `GATE-01.md`'s definition of done — "halts distinctly when prep
  fails."
- *Why not verified here:* the branch exists and is unit-tested end-to-end at the
  `execute_unit_attempt` boundary (`test_failing_prep_halts_before_dispatch`
  asserts `dispatch_fn` was never called, re-run green this session). The
  `run()`-level bookkeeping — `blocked_human` flip, the two events, the
  `PREP HALT` operator line, the bookkeeping commit — has never fired on real
  input, because no work unit in this repository declares `prep:`. This pass
  could have observed it only by adding one, which is an implementation edit this
  reflective unit may not make.
- *Where it actually gets checked:* the first real prep failure. FU-2R below.

**2. That the fix for the capture banner works for a downstream consumer.**
- *Criterion:* T06's criterion 3, and this close's FU-5 discharge condition.
- *Why not verified here:* it was verified, and it **failed** — see the FU-5
  section. What is not verified is any claim that it works; the enumeration item
  7 and FU-5R record the measured state instead.
- *Where it actually gets checked:* `format_oracle_capture` called on a report
  produced by `_run_gate_set`, or any real dispatched session declaring
  `oracles:`. This session is such a check and it reports the defect present.

**3. Behaviour of the two new modules for a downstream consumer.**
- *Criterion:* the consumer-visible enumeration, items 2 and 3.
- *Why not verified here:* this repository is the only corpus this session has,
  and no external consumer imports either module. Their exercised surface is this
  repo's driver plus four test files.
- *Where it actually gets checked:* nowhere automatically. Item 1 of the
  enumeration is a real behaviour change on upgrade, so "a downstream project
  that upgrades sees no behaviour change" does **not** hold.

**4. That `specfuse init` into an empty directory produces the seeded `oracles`
example.**
- *Criterion:* FU-3R's re-run condition named this as its third clause.
- *Why not verified here:* the two clauses that matter were verified directly
  (both keys in both template copies; the commented set in both example copies,
  byte-identical). Running `specfuse init` into a scratch directory would have
  been a fourth measurement of the same seed files, and `scaffold.py:164`'s
  `"verification.yml.example": "verification.yml"` mapping plus the green
  `sync-scaffold-bats` and `init-sh-shim-bats` suites already cover the copy
  path. Recorded rather than claimed.
- *Where it actually gets checked:* `tests/sync_scaffold.bats` and
  `tests/init_sh_shim.bats`, both green here; end-to-end, the next real
  `specfuse init`.

**No auto-close debt was inherited.** One gate, one close, no predecessor gate
auto-closed; `grep -rn "specfuse:autoclose-debt"` over the feature folder returns
only this document's own mention of the marker string.
`auto_close_disabled: true` on `WU-90` held — this body ran, four times across
three passes.

**Pass 1's retracted finding stays retracted.** Its
`close-attempts-leave-no-ledger` entry generalised a true observation into a
false rule. `events.jsonl` now holds all three prior `G1-CLOSE` attempt records
and their sum matches `cumulative_cost_usd` to the cent. The real mechanism is
narrower: a close's attempt events are buffered in `wu_events` and flushed at
terminal outcome, so a close reading the file mid-flight is blind to itself.

## Hedged-verdict follow-up record

Four entries, per `close-discipline.md` §2. **FU-1R is discharged** by the
injected capture quoted at the top of this document and is not repeated here.
**FU-3R is discharged** on substance. The entries below are the residue: one
condition that needs a real prep failure, the pre-existing selector defect, the
FU-5 defect T06 did not close, and the sequencing rule that governs the fix.

### FU-2R — `prep`'s operator-facing halt path has never fired on real input

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The driver
  runs prep fail-fast and oracles capture-all **before** dispatching the session,
  and halts distinctly when prep fails."*
- **Why it is unmet here:** the oracles-capture-all half is now **met by direct
  observation** — this session's prompt carries both declared oracles' output,
  run before dispatch. The fail-fast half is verified in code:
  `test_failing_prep_halts_before_dispatch` asserts `execute_unit_attempt`
  returns `"prep_halted"` and `dispatch_fn` is never called, re-run green this
  session. The *distinct halt* half is the `run()` branch: tree reset,
  `blocked_human` flip, `attempt_outcome` with `halt_class`, `human_escalation`
  with `reason: "prep_halted"`, a bookkeeping commit, and a `PREP HALT` operator
  line. No work unit in this repository declares `prep:`, so none of that has
  executed against a real failing prep entry.
- **Why it was not fixed in this session:** `specfuse/loop/loop.py` and `tests/`
  are on this unit's **Do not touch** list, and declaring a `prep:` set on a live
  work unit is an implementation edit, not a close's.
- **The exact re-run condition that would upgrade the verdict to `met`:** dispatch
  a work unit declaring a `prep:` set whose first entry exits non-zero. It
  upgrades to `met` when the WU's status is `blocked_human`, `events.jsonl`
  carries an `attempt_outcome` with `outcome: "prep_halted"` and
  `halt_class: "prep_halt"` plus a `human_escalation` with
  `reason: "prep_halted"`, no session was spawned (the attempt's cost is $0.00),
  and no later `prep` entry in the set executed.
- **kind:** `externally-verifiable-later`

### FU-5R — the captured-oracle banner survives T06; the fix sits on an unreachable branch

- **The criterion, verbatim:** T06's criterion 3 — *"The string `Run the command
  directly.` never appears in a section returned by `format_oracle_capture`, for
  any input — truncated or not. An `oracles` capture must never instruct its
  reader to re-run the command."* And `GATE-01.md`'s definition of done — *"under
  a byte budget that preserves verdicts rather than tails."*
- **Why it is unmet here:** measured three ways this session, all recorded in
  full above. (a) `format_oracle_capture` on a report shaped as `_run_gate_set`
  actually builds one returns a section containing both `NO VERDICT FOUND` and
  `Run the command directly.`. (b) `run_pre_dispatch` returns `oracle_results`
  whose `report` values **already contain** the banner, because `_run_gate_set`
  composes each report from `select_gate_report_lines` output before
  `format_oracle_capture` is reached. (c) This session's own injected prompt
  carries the banner on both oracle blocks — the defect in production, telling a
  work unit forbidden to run `git` to go run `git`. Root cause:
  `prerun_capture.py`'s filter at line 59 sits after the
  `if len(raw_bytes) <= budget: return report, 0` early return at lines 56–57, so
  it runs only on the truncation path. T06's test
  (`test_complete_capture_carries_no_verdict_banner`) builds an ~18 KB raw log
  with no banner in it, exercising the one branch where the filter lives and
  neither condition under which the defect appears.
- **Why it was not fixed in this session:** `specfuse/loop/prerun_capture.py`,
  `select_gate_report_lines`, and `tests/` are all on this unit's **Do not
  touch** list. This is a reflective unit; a defect found here is routed.
- **The exact re-run condition that would upgrade the verdict to `met`:** strip
  `_NO_VERDICT_NOTE` from the report on **both** branches of `_fit_to_budget` —
  including the within-budget early return — or, better, stop composing the
  banner into `oracles` reports at their source in `prerun.py`. It upgrades to
  `met` when, for a report built the way `_run_gate_set` builds one (fenced
  block, `select_gate_report_lines` output, no pass/fail verdict in the command's
  output), `format_oracle_capture` returns a section containing **neither**
  `NO VERDICT FOUND` nor `Run the command directly.` at any size — under budget
  and over it — while an over-budget report still carries the explicit
  `[N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES]` marker; and when a real
  dispatched session's injected capture is clean.
- **kind:** `externally-verifiable-later`

### FU-4 — `select_gate_report_lines` does not treat ruff's summary as a verdict

Carried forward from both prior passes unchanged; re-run this session and
confirmed still open.

- **The criterion, verbatim:** T02's criterion 3 — *"When an oracle's output
  exceeds its share of the budget, the retained lines are selected via
  `select_gate_report_lines`, so a verdict line near the top of the output
  survives while the middle is dropped."*
- **Why it is unmet here:** met for the gates FEAT-2026-0068 tuned it against,
  not universally. Re-run on the exact captured `lint` output from T02's own
  attempt-1 `failure_excerpt`, the selector returns the file line, the
  `Found 1 error.` line, and a `NO VERDICT FOUND` banner; on ruff's passing
  output it returns `All checks passed!` and the same banner. Neither ruff
  verdict is recognised, so nothing is pinned and `_fit_to_budget` degrades to a
  positional tail for this repository's `lint` gate. Not yet harmful — ruff's
  output fits inside an 8000-byte share — but the stated guarantee does not hold
  across this repo's own gate set.
- **Why it was not fixed in this session:** `select_gate_report_lines` lives in
  `specfuse/loop/loop.py`, on this unit's **Do not touch** list and on T02's.
- **The exact re-run condition that would upgrade the verdict to `met`:** teach
  `select_gate_report_lines` to recognise ruff's `Found N error(s).` and
  `All checks passed!` as verdict lines. It upgrades to `met` when
  `select_gate_report_lines(<ruff failing output>, 15)` returns the
  `Found 1 error.` line without the `NO VERDICT FOUND` banner, and when a
  synthetic ruff report of 500+ lines still shows that summary after
  `format_oracle_capture` bounds it.
- **kind:** `externally-verifiable-later`

### FU-6R — a fix to the capture path cannot be proved by the same driver process that dispatched its prover

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The captured
  oracle output reaches the session as input, under a byte budget that preserves
  verdicts rather than tails."* Specifically the standing constraint on how any
  future fix to it gets proved.
- **Why it is unmet here:** recorded as a follow-up rather than a lesson-only
  note because it binds the FU-5R re-run condition above.
  `execute_unit_attempt` imports `specfuse.loop.prerun_capture` at call time but
  calls it unconditionally for **every** work unit, so the first dispatch of any
  driver process caches the module. A unit that fixes `prerun_capture.py` and a
  close that reads its own injected prompt to verify the fix therefore cannot
  share a driver process — the close would read the pre-fix formatter. This gate
  already paid for the one-layer-up version of this (T04, pass 2, $5.33) and
  spent a whole planned invocation avoiding it for T06 — and T06's fix still did
  not land, for an unrelated reason, which means the sequencing cost was paid for
  nothing this round.
- **Why it was not fixed in this session:** it is not a code defect. It is a
  property of Python module caching plus the driver's own dispatch shape, and the
  mitigation is operational.
- **The exact re-run condition that would upgrade the verdict to `met`:** land the
  FU-5R fix in one driver invocation, stop the driver, and re-arm this close in a
  **freshly started** process. It upgrades to `met` when that session's injected
  `## Captured oracle output (pre-dispatch)` section contains neither
  `NO VERDICT FOUND` nor `Run the command directly.` — the same observation this
  pass just made in the negative.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** All four entries are `externally-verifiable-later`
(`verdict_ceiling_for_kinds` → `rework exists`), so in-repo rework or an operator
action exists for every one and the operator has a real choice between accepting
this hedge and clearing it. FU-5R is the cheapest and the most consequential: a
two-line change to `_fit_to_budget`, plus a test built on a `_run_gate_set`-shaped
input, plus the driver restart FU-6R describes. FU-2R needs one work unit
declaring a failing `prep:` set. FU-4 is independent and would not block a `met`
on its own.

## Lessons promoted

Three new entries in `.specfuse/LEARNINGS.md`, all tagged
`FEAT-2026-0057/G1-CLOSE`, plus one existing entry corrected.

**1. A red→green test written against a synthetic input can green a fix that
never runs in production.** T06 is the cleanest instance this repo has produced.
Its criterion said "for any input"; its test built one input, chose it large
enough to force truncation, and built it from raw text with no banner — so the
test exercised the exact branch the fix was placed on and skipped both conditions
under which the bug appears. Cheapest unit in the feature, $0.68, one attempt,
every oracle green, defect intact and now visible in this close's own prompt. The
rule is about *where the fixture comes from*: when a unit fixes a formatter, a
parser, or any function whose input is produced by other code in the same repo,
its test must construct that input **through the real producer**, not by hand.

**2. When a fix targets a function with an early return, the criteria must name
which branch.** `_fit_to_budget` has two paths and the common one is the early
return. T06's edit landed on the other. Nothing in its acceptance criteria, its
grounding-file list, or its escalation triggers distinguished them, and nothing
in the `code` gate could.

**3. The sequencing tax is real, is now understood, and was paid for nothing this
round.** This gate spent a full extra driver invocation and a `blocked_human`
hold specifically so T06's fix would be visible to this close — correct
reasoning, correctly executed, and the close still reports the banner, because
the fix itself was ineffective. Restarting the driver buys you an *honest*
observation; it does not buy you a *good* one.

**4. A correction, not a new lesson.** The existing
[`informational-output-has-no-verdict`] entry is extended with the mechanism this
pass measured: the banner is composed into the report by `_run_gate_set`, before
any oracle-specific formatter sees it, so filtering it downstream in
`format_oracle_capture` addresses a copy rather than the source.

The prior passes' entries — `no-unit-owns-the-seam`,
`feature-oracle-is-a-different-question`, `close-is-blind-to-its-own-ledger`, and
`driver-edits-need-a-restart` — are left standing unchanged. Two are now
independently validated a second time: `feature-oracle-is-a-different-question`
predicted exactly the shape of the T06 finding (every unit oracle green, the
feature-level question unasked), and `driver-edits-need-a-restart` is what made
this pass's FU-1R proof possible at all.

## Verdict

**`met_locally`.**

Verified fresh in this session, none of it inherited from a producing unit's
`RESULT` block. Against `GATE-01.md`'s definition of done, criterion by
criterion:

1. *"A work unit can declare `prep:` and `oracles:` in its frontmatter, both
   resolving against `.specfuse/verification.yml` set names."* — **met.**
   `WorkUnit` carries both fields, `load_wu` parses both, and this work unit's own
   live file resolves `oracles: [oracles]` to the two real entries.
2. *"The driver runs prep fail-fast and oracles capture-all before dispatching the
   session, and halts distinctly when prep fails."* — **met locally.** The
   oracles half is now **observed**: this session's prompt carries both declared
   oracles, run before dispatch. The prep half is verified in code and has never
   fired on real input (FU-2R).
3. *"The captured oracle output reaches the session as input, under a byte budget
   that preserves verdicts rather than tails."* — **met on reaching, qualified on
   content.** The section arrived, in a real dispatched session, with both blocks
   complete and untruncated — the observation two passes could not make. The
   truncation policy itself is verdict-aware and tested. But the delivered content
   carries a false `NO VERDICT FOUND` banner and an instruction to run the
   captured command directly (FU-5R), and the selector does not recognise ruff's
   verdicts (FU-4).
4. *"This repo declares and uses one real oracle set, guarded structurally, with
   the contract documented alongside `extra_gates` so the difference between
   pre-dispatch and exit is written down."* — **met.** Declared in
   `.specfuse/verification.yml`; guarded by `tests/test_oracle_set_declared.py`
   and `tests/test_seed_documents_prerun_keys.py`; documented alongside
   `extra_gates` in both skill copies and now in both `WU.template.md` copies;
   and **used** — this session is the use, and its output is quoted above. This
   is the criterion that moved furthest this pass.
5. *"Every implementation work unit in this gate is `done`."* — **met.** T01,
   T02, T03, T04, T05, T06, all `done`, verified by reading the six frontmatter
   blocks.
6. *"The terminal close has run: retrospective, lessons, docs, and verdict."* —
   **met.** This document, three LEARNINGS additions and one correction,
   `CHANGELOG.md` corrections and two new entries, and this verdict.

The feature's central claim is now demonstrated rather than argued: a work unit
declared `oracles:`, the driver ran them before the session started, and the
session read the result instead of re-deriving it. FU-1R — the follow-up that
capped two passes — is discharged by observation.

`met` is still not right, for two reasons that are smaller than FU-1R was and are
not the same reason. The prep-halt path has never run against a real failure
(FU-2R), and the output the mechanism delivers carries a banner that is false and
actively counter-productive (FU-5R) — measured in this session's own prompt,
after a work unit was armed to remove it and reported `done`. Claiming `met` on
a capture that instructs its reader to go run the command directly would be
claiming the opposite of what this feature exists to do.

The gate lands at `awaiting_review` and `PLAN.md` stays `active`
(`verdict_permits_terminal_flips` returns True only for `met`). The operator's
choice is between accepting the hedge and arming one small unit for FU-5R —
a two-line branch fix plus a test built from a `_run_gate_set`-shaped input —
followed by a driver restart, per FU-6R.


## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Recorded:** 2026-08-05T16:11:28Z

**Verdict ceiling at acceptance:** `rework exists` — computed by
`closing_requirements.verdict_ceiling_for_kinds` over the kinds present. All four
standing entries are `externally-verifiable-later`, so in-repo rework or an
operator action could raise this verdict. The operator accepted now instead of
waiting for those conditions.

**Operator's reason, verbatim:**

> Mechanism is working and gaps found will be covered later

**Tracking surfaces.** None of the four entries is `routed-finding`, so this
skill's per-entry tracking prompt did not apply. The operator nonetheless filed
each as a GitHub issue before accepting:

| Entry | Issue |
|---|---|
| FU-2R | specfuse/loop#758 |
| FU-5R | specfuse/loop#756 |
| FU-4  | specfuse/loop#723 |
| FU-6R | specfuse/loop#757 |

**These follow-ups are NOT discharged.** They are carried forward exactly as open
as they were when the close wrote them. Accepting a hedge means shipping with
known-open items, not resolving them. The four entries below are reproduced
verbatim from the *Hedged-verdict follow-up record* above; none is paraphrased,
dropped, or marked complete.

---

### FU-2R — `prep`'s operator-facing halt path has never fired on real input

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The driver
  runs prep fail-fast and oracles capture-all **before** dispatching the session,
  and halts distinctly when prep fails."*
- **Why it is unmet here:** the oracles-capture-all half is now **met by direct
  observation** — this session's prompt carries both declared oracles' output,
  run before dispatch. The fail-fast half is verified in code:
  `test_failing_prep_halts_before_dispatch` asserts `execute_unit_attempt`
  returns `"prep_halted"` and `dispatch_fn` is never called, re-run green this
  session. The *distinct halt* half is the `run()` branch: tree reset,
  `blocked_human` flip, `attempt_outcome` with `halt_class`, `human_escalation`
  with `reason: "prep_halted"`, a bookkeeping commit, and a `PREP HALT` operator
  line. No work unit in this repository declares `prep:`, so none of that has
  executed against a real failing prep entry.
- **Why it was not fixed in this session:** `specfuse/loop/loop.py` and `tests/`
  are on this unit's **Do not touch** list, and declaring a `prep:` set on a live
  work unit is an implementation edit, not a close's.
- **The exact re-run condition that would upgrade the verdict to `met`:** dispatch
  a work unit declaring a `prep:` set whose first entry exits non-zero. It
  upgrades to `met` when the WU's status is `blocked_human`, `events.jsonl`
  carries an `attempt_outcome` with `outcome: "prep_halted"` and
  `halt_class: "prep_halt"` plus a `human_escalation` with
  `reason: "prep_halted"`, no session was spawned (the attempt's cost is $0.00),
  and no later `prep` entry in the set executed.
- **kind:** `externally-verifiable-later`

### FU-5R — the captured-oracle banner survives T06; the fix sits on an unreachable branch

- **The criterion, verbatim:** T06's criterion 3 — *"The string `Run the command
  directly.` never appears in a section returned by `format_oracle_capture`, for
  any input — truncated or not. An `oracles` capture must never instruct its
  reader to re-run the command."* And `GATE-01.md`'s definition of done — *"under
  a byte budget that preserves verdicts rather than tails."*
- **Why it is unmet here:** measured three ways this session, all recorded in
  full above. (a) `format_oracle_capture` on a report shaped as `_run_gate_set`
  actually builds one returns a section containing both `NO VERDICT FOUND` and
  `Run the command directly.`. (b) `run_pre_dispatch` returns `oracle_results`
  whose `report` values **already contain** the banner, because `_run_gate_set`
  composes each report from `select_gate_report_lines` output before
  `format_oracle_capture` is reached. (c) This session's own injected prompt
  carries the banner on both oracle blocks — the defect in production, telling a
  work unit forbidden to run `git` to go run `git`. Root cause:
  `prerun_capture.py`'s filter at line 59 sits after the
  `if len(raw_bytes) <= budget: return report, 0` early return at lines 56–57, so
  it runs only on the truncation path. T06's test
  (`test_complete_capture_carries_no_verdict_banner`) builds an ~18 KB raw log
  with no banner in it, exercising the one branch where the filter lives and
  neither condition under which the defect appears.
- **Why it was not fixed in this session:** `specfuse/loop/prerun_capture.py`,
  `select_gate_report_lines`, and `tests/` are all on this unit's **Do not
  touch** list. This is a reflective unit; a defect found here is routed.
- **The exact re-run condition that would upgrade the verdict to `met`:** strip
  `_NO_VERDICT_NOTE` from the report on **both** branches of `_fit_to_budget` —
  including the within-budget early return — or, better, stop composing the
  banner into `oracles` reports at their source in `prerun.py`. It upgrades to
  `met` when, for a report built the way `_run_gate_set` builds one (fenced
  block, `select_gate_report_lines` output, no pass/fail verdict in the command's
  output), `format_oracle_capture` returns a section containing **neither**
  `NO VERDICT FOUND` nor `Run the command directly.` at any size — under budget
  and over it — while an over-budget report still carries the explicit
  `[N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES]` marker; and when a real
  dispatched session's injected capture is clean.
- **kind:** `externally-verifiable-later`

### FU-4 — `select_gate_report_lines` does not treat ruff's summary as a verdict

Carried forward from both prior passes unchanged; re-run this session and
confirmed still open.

- **The criterion, verbatim:** T02's criterion 3 — *"When an oracle's output
  exceeds its share of the budget, the retained lines are selected via
  `select_gate_report_lines`, so a verdict line near the top of the output
  survives while the middle is dropped."*
- **Why it is unmet here:** met for the gates FEAT-2026-0068 tuned it against,
  not universally. Re-run on the exact captured `lint` output from T02's own
  attempt-1 `failure_excerpt`, the selector returns the file line, the
  `Found 1 error.` line, and a `NO VERDICT FOUND` banner; on ruff's passing
  output it returns `All checks passed!` and the same banner. Neither ruff
  verdict is recognised, so nothing is pinned and `_fit_to_budget` degrades to a
  positional tail for this repository's `lint` gate. Not yet harmful — ruff's
  output fits inside an 8000-byte share — but the stated guarantee does not hold
  across this repo's own gate set.
- **Why it was not fixed in this session:** `select_gate_report_lines` lives in
  `specfuse/loop/loop.py`, on this unit's **Do not touch** list and on T02's.
- **The exact re-run condition that would upgrade the verdict to `met`:** teach
  `select_gate_report_lines` to recognise ruff's `Found N error(s).` and
  `All checks passed!` as verdict lines. It upgrades to `met` when
  `select_gate_report_lines(<ruff failing output>, 15)` returns the
  `Found 1 error.` line without the `NO VERDICT FOUND` banner, and when a
  synthetic ruff report of 500+ lines still shows that summary after
  `format_oracle_capture` bounds it.
- **kind:** `externally-verifiable-later`

### FU-6R — a fix to the capture path cannot be proved by the same driver process that dispatched its prover

- **The criterion, verbatim:** `GATE-01.md`'s definition of done — *"The captured
  oracle output reaches the session as input, under a byte budget that preserves
  verdicts rather than tails."* Specifically the standing constraint on how any
  future fix to it gets proved.
- **Why it is unmet here:** recorded as a follow-up rather than a lesson-only
  note because it binds the FU-5R re-run condition above.
  `execute_unit_attempt` imports `specfuse.loop.prerun_capture` at call time but
  calls it unconditionally for **every** work unit, so the first dispatch of any
  driver process caches the module. A unit that fixes `prerun_capture.py` and a
  close that reads its own injected prompt to verify the fix therefore cannot
  share a driver process — the close would read the pre-fix formatter. This gate
  already paid for the one-layer-up version of this (T04, pass 2, $5.33) and
  spent a whole planned invocation avoiding it for T06 — and T06's fix still did
  not land, for an unrelated reason, which means the sequencing cost was paid for
  nothing this round.
- **Why it was not fixed in this session:** it is not a code defect. It is a
  property of Python module caching plus the driver's own dispatch shape, and the
  mitigation is operational.
- **The exact re-run condition that would upgrade the verdict to `met`:** land the
  FU-5R fix in one driver invocation, stop the driver, and re-arm this close in a
  **freshly started** process. It upgrades to `met` when that session's injected
  `## Captured oracle output (pre-dispatch)` section contains neither
  `NO VERDICT FOUND` nor `Run the command directly.` — the same observation this
  pass just made in the negative.
- **kind:** `externally-verifiable-later`
