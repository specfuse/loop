---
id: FEAT-2026-0057/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
oracle_env: macos_local
generated_surfaces: []
provenance: "FEAT-2026-0057/G1-CLOSE second-pass RETROSPECTIVE.md follow-up FU-5 — every captured oracle block carries a false NO VERDICT FOUND banner whose closing sentence instructs the reading agent to run the command itself, which is the behaviour this feature exists to eliminate."
produces:
  - specfuse/loop/prerun_capture.py
  - tests/test_prerun_capture.py
produces_driver_helper:
  - format_oracle_capture
---

# Stop informational oracle captures carrying a false "NO VERDICT FOUND" banner

**Objective.** An oracle capture that is complete and within budget reads as what
it is — a captured result — with no verdict banner and no instruction to re-run
the command.

**Context.** Correlation ID `FEAT-2026-0057/T06`. Read `RETROSPECTIVE.md` in this
folder, follow-up **FU-5**, before starting. It carries the observed output.

`format_oracle_capture` fits every oracle's report through
`select_gate_report_lines`, which is a **pass/fail verdict selector** built for
gate reports (FEAT-2026-0068). An `oracles` entry is informational by design —
`git log --oneline -20` has no verdict and never will — so the selector appends
its banner to **every** oracle block, including short, complete, untruncated ones:

```
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary
anywhere in its output — the lines above are the tail only, and may be unrelated
to the failure. Run the command directly.
```

Two defects in one string. The claim is **false** for a complete capture: nothing
was truncated, and there is no failure for the lines to be unrelated to. And the
final sentence instructs the reading agent to run the command itself — the exact
behaviour this feature exists to eliminate, and something a close work unit in this
repository is explicitly forbidden to do, since `git` is on its **Do not touch**
list. A close following that instruction would be told to break its own contract.

This is a distinct seam from FU-4 / issue #723. FU-4 is *"the selector does not
recognise ruff's verdict."* This is *"an informational oracle has no verdict and
should not be run through a verdict selector at all."* Fixing one does not fix the
other.

**Incremental edit to two files T02 already delivered.** Both paths in `produces:`
exist and are `done`; this unit does not create them and must not rewrite them.
The edit is narrow and bounded:

- `specfuse/loop/prerun_capture.py` — change **only** how a report within its
  budget share is rendered (suppress the verdict banner) and ensure the
  `Run the command directly.` sentence cannot reach the output. The budget bound,
  the per-oracle block structure, the `### oracle: <name> (OK|FAIL)` headers, and
  the dropped-bytes marker all stay exactly as T02 built them.
- `tests/test_prerun_capture.py` — **append** the new test named in criterion 1.
  Do not modify or delete any existing test; criterion 5 asserts they all still
  pass unchanged.

Grounding files:

- `specfuse/loop/prerun_capture.py` — `format_oracle_capture` and its
  `_fit_to_budget` helper. This is the file you change.
- `specfuse/loop/loop.py` — `select_gate_report_lines`, which emits the banner.
  You **call** it or stop calling it; you do not modify it.
- `tests/test_prerun_capture.py` — T02's tests, which you extend. The existing
  truncation and budget assertions must keep passing unchanged.

Binding rules apply by reference: `.specfuse/rules/result-contract.md`,
`.specfuse/rules/never-touch.md`, `.specfuse/rules/security-boundaries.md`,
`.specfuse/rules/correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_prerun_capture.py::TestCapture::test_complete_capture_carries_no_verdict_banner`
   exists and **fails on HEAD before this work unit runs** (the test is new; the
   current behaviour emits the banner). Scoped run:
   `python3 -m unittest tests.test_prerun_capture.TestCapture.test_complete_capture_carries_no_verdict_banner`.
2. `format_oracle_capture([{'name': 'x', 'ok': True, 'report': '<short informational capture>'}])`
   returns a section containing the capture text and **no** `NO VERDICT FOUND`
   substring.
3. The string `Run the command directly.` never appears in a section returned by
   `format_oracle_capture`, for any input — truncated or not. An `oracles` capture
   must never instruct its reader to re-run the command.
4. A report exceeding its share of the budget **still** carries the explicit
   `[N byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES]` marker. Silent truncation
   remains a failure; this unit removes a false banner, not the honest one.
5. Every existing test in `tests/test_prerun_capture.py` still passes unchanged —
   the budget bound, the verdict-aware line selection for reports that *do* carry a
   verdict, and the no-oracles-no-section case.
6. The test in criterion 1 passes after the edits.

**Do not touch.**

- `select_gate_report_lines` in `specfuse/loop/loop.py`. Its gate-report behaviour
  is correct for gate reports and is relied on by `_run_gate_set`. If the fix
  seems to require changing it, that is an escalation — see below. Issue #723
  covers its separate ruff defect and is not this unit's work.
- `specfuse/loop/prerun.py` — T01's runner. This unit changes formatting only.
- `specfuse/loop/loop.py` generally, including T04's call site. The section this
  unit returns is appended by existing code that needs no change.
- `.specfuse/verification.yml`, the scaffold seeds (T05's), other features'
  folders, generated directories, secrets, `.git/`. See
  `.specfuse/rules/never-touch.md`.
- **The driver owns all git.** You edit files only — never run `git`.

**Verification.**

- The `code` gate set in `.specfuse/verification.yml`.
- The scoped red→green run named in criteria 1 and 6.
- `python3 -m unittest tests.test_prerun_capture` — the whole class, to prove
  criterion 5.

**Escalation triggers.**

- If suppressing the banner for informational captures cannot be done inside
  `prerun_capture.py` without modifying `select_gate_report_lines`, emit
  `status: blocked` with the coupling. Changing the shared selector would alter
  gate FAIL reports, which is a different blast radius and a different decision.
- If an existing `tests/test_prerun_capture.py` test asserts the banner's presence,
  block rather than deleting the assertion — that would mean T02 specified the
  behaviour deliberately and the conflict needs a human.
- Blocked is a respectable outcome (`.specfuse/rules/result-contract.md` rule 4).
