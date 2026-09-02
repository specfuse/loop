---
id: FEAT-2026-0085/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
model: sonnet
effort: medium
oracle_env: macos_local
produces_driver_helper: write_stub_retrospective_terminal
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/closing_requirements.py
  - tests/test_autoclose_stub_states_what_passed.py
---

# An auto-closed gate states what the driver proved instead of deferring every criterion

**Objective.** Stop the auto-close stubs from listing every acceptance
criterion as `deferred:` under "What the loop did NOT verify", and retire the
debt marker and the terminal close's obligation to reconcile it.

**Context.** FEAT-2026-0085/T02; read `PLAN.md`. Today
`write_stub_retrospective_terminal` (`loop.py:5026`) and the intermediate
sibling append `build_autoclose_debt_enumeration` (`:4899`): a marker plus up
to 40 `deferred:` lines, one per criterion. `precreate_dispatch_skeleton`
(`:3061`) then seeds a deferral heading into the terminal close, and
`assert_autoclose_debt_reconciled` (`:6308`, requirement `close-g`) refuses a
close that does not name each gate. FEAT-2026-0050 shows the effect: 19
criteria deferred by a gate whose units all passed their gate set, reconciled
by a close that could only restate them. An auto-close fires only when every
substantive unit's final attempt passed the driver's gates; that is what was
verified, and the stub should say so. Replace the enumeration with three
lines: which units passed, which gate set each ran, and the cost line the
predicate already computes. Delete the marker regex, `close-g`, the assertion,
the precreate branch, `DEFERRAL_HEADING_TEXT`, and `_DEBT_CRITERIA_CAP`.
`stamp_gate_auto_close_note` keeps its cost and predicate lines and drops the
pointer to the deferred list. Red test first.

**Acceptance criteria.**

- `tests/test_autoclose_stub_states_what_passed.py::test_terminal_stub_has_no_deferred_lines` fails on HEAD and passes after: an auto-closed fixture's `RETROSPECTIVE.md` contains no `deferred:` line, no `specfuse:autoclose-debt` marker, and one line per substantive unit naming its gate set.
- `grep -rn "autoclose-debt\|DEFERRAL_HEADING\|build_autoclose_debt_enumeration\|assert_autoclose_debt_reconciled\|close-g\b" specfuse/ | wc -l` reports 0.
- `tests/test_autoclose_stub_states_what_passed.py::test_terminal_close_after_autoclosed_gate_needs_no_deferral_section`: a terminal close on a fixture with an auto-closed gate 1 passes `assert_closing_deliverables` and `verify_post_pass_invariants` with a retrospective carrying no "What the loop did NOT verify" heading.
- `tests/test_autoclose_deferral_visibility.py` and `tests/test_autoclose_gate_note.py` are rewritten to the new stub, not deleted.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `VERDICT_VALUES` and the verdict guards (T01); `evaluate_auto_close`
in `gate_eval.py` (the predicate is unchanged); `escalation.py` (T03); `.specfuse/rules/`,
`docs/`, `plugins/` (T05); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above.

**Escalation triggers.** Emit `status: blocked` if any consumer other than the
four functions named above reads the debt marker; name it rather than leaving
a dangling reader.
