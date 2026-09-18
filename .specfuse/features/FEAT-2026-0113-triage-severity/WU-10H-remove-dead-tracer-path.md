---
id: FEAT-2026-0113/T10H
type: implementation
status: pending
attempts: 0
planned_cost_usd: 1.50
produces:
  - specfuse/agent/severity_backfill.py
  - tests/test_severity_backfill_end_to_end.py
---

# T10H — remove `backfill_severity`, the superseded tracer-bullet path

**Objective.** Delete the single-issue path T07 built as gate 3's walking
skeleton, now that T10's `run_backfill` is the real run shape, and move its one
behavioural assertion onto code that ships.

**Context.** Hygiene unit. Gate 3's broad run failed at close entry:

```
these public symbols have no caller outside tests/ and are not in BASELINE:
  backfill_severity (specfuse/agent/severity_backfill.py)
```

`backfill_severity` (`:244`) was T07's tracer bullet: a single-issue path that
made the gate's `feature_oracle` runnable before any layer existed. T10 built
`run_backfill` (`:130`) as the real shape and `main()` (`:334`) calls that one.
The module's own docstring already records the split — *"`run_backfill` does not
call it and does not share its…"* — so the skeleton has been dead since T10
landed and nothing noticed until the ratchet ran.

**This is a genuinely dead symbol, not a BASELINE candidate.** `BASELINE` is for
a symbol that lands ahead of its callers by design, which is what `T03`'s
`read_severity_rubric` was earlier in this gate. This one's caller was
deliberately replaced. Waiving it would record a reason for code that should not
exist, and the next reader would inherit that as fact.

**The coverage question is already answered, and answering it is what makes the
deletion safe** (`#3328`'s ruling: never delete a test to delete its subject
without checking where the behaviour is covered). `backfill_severity` has two
test references in `tests/test_severity_backfill_end_to_end.py`:

- `test_marked_issue_without_severity_is_amended_then_labelled` (`:60`) — the
  marker-before-label claim. **Already covered against shipping code** by
  `tests/test_severity_backfill_apply.py:32`
  (`test_marker_is_amended_before_the_label_is_added`), which asserts the same
  ordering with an index comparison through `run_backfill`'s write path.
- `test_import_exposes_backfill_severity_and_the_named_stub` (`:135`) — an
  import check on a symbol this unit removes.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_caller_check_ratchet` fails on HEAD before
   this unit runs, naming `backfill_severity`, and passes after — with **no new
   `BASELINE` entry**, asserted by the tuple's length being unchanged.
2. `backfill_severity` is removed from `specfuse/agent/severity_backfill.py`,
   and `grep -c "def backfill_severity" specfuse/agent/severity_backfill.py`
   reports `0`.
3. The module docstring's paragraph describing `backfill_severity` as the
   tracer-bullet path is removed with it — a docstring naming a function that no
   longer exists is the same defect one level up.
4. `tests/test_severity_backfill_end_to_end.py`'s two references are resolved:
   the import check is deleted, and the behavioural test is **deleted rather
   than repointed**, because `tests/test_severity_backfill_apply.py:32` already
   asserts the same ordering against `run_backfill`. Criterion 5 is what proves
   that claim rather than trusting it.
5. `python3 -m unittest tests.test_severity_backfill_apply -v` passes and its
   output names `test_marker_is_amended_before_the_label_is_added` — the
   ordering coverage this unit relies on is shown to exist and to run, not
   assumed from a file read.
6. The full `tests` gate passes and the `coverage` gate emits its marker again,
   confirming the second failing check was downstream of the first.

**Do not touch.** Named surfaces rather than whole files, since this unit
legitimately edits a file it must also protect most of. In the backfill module,
the protected surfaces are the **`run_backfill` and `main` function bodies and
every other definition in it except `backfill_severity`**: this unit deletes
exactly that one function plus the docstring paragraph describing it, and
changes no behaviour of the path that ships. `tests/test_severity_backfill_apply.py` and
`tests/test_severity_backfill_run.py`, which cover the live path and must pass
**unedited** — a test edited to accommodate this deletion is evidence the
deletion is wrong. `tests/test_caller_check_ratchet.py`'s `BASELINE` tuple.
`specfuse/loop/triage.py`. `pyproject.toml`'s console-script entry, which points
at `main` and is unaffected.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_caller_check_ratchet tests.test_severity_backfill_apply tests.test_severity_backfill_run tests.test_severity_backfill_limit -b`.

**Escalation triggers.** If removing `backfill_severity` breaks any test in
`tests/test_severity_backfill_apply.py` or `tests/test_severity_backfill_run.py`,
stop — that means the live path depends on it and the diagnosis that it is dead
is wrong. If the ordering assertion named in criterion 5 does not exist or does
not run, stop and report that instead of deleting the test that would then be
the only coverage of it.
