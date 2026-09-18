<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# FEAT-2026-0113 — follow-ups

Written by `FEAT-2026-0113/G3-CLOSE` under `close-discipline.md` §2: the terminal
verdict is `not_met`, and each entry below is one tracked follow-up the driver files
as a `specfuse:follow-up` issue. Entry 1 is the failed acceptance criterion; entries
2 and 3 are findings this close measured that no criterion owned and that would
otherwise survive only as retrospective prose.

### T09 criterion 4 is not met: the backfill module still contains a `gh issue list` call site, now dead

**Tracked as #3358.**

**Criterion, verbatim (FEAT-2026-0113/T09, acceptance criterion 4):**

> The write path neither lists nor classifies: `grep -c '"issue", "list"'` and
> `grep -c "run_claude"` over `specfuse/agent/severity_backfill.py` both report `0`
> at this unit's tree, and `grep -c "def _amend_marker"` over the same file reports
> `0` — T07's stub is gone and `amend_marker_severity` has one definition repo-wide
> (`grep -rn "def amend_marker_severity" specfuse/` reports exactly one hit).

**Evidence.**

```
$ git show d859fc6:specfuse/agent/severity_backfill.py | grep -c '"issue", "list"'
1                                   # criterion requires 0, at T09's own tree
$ grep -c '"issue", "list"' specfuse/agent/severity_backfill.py
1                                   # still 1 at HEAD (0b40830), line 218
$ git show d859fc6:specfuse/agent/severity_backfill.py | grep -c run_claude
0                                   # this half holds
$ grep -c "def _amend_marker" specfuse/agent/severity_backfill.py
0                                   # exit 1 — this half holds
$ grep -rn "def amend_marker_severity" specfuse/
specfuse/loop/triage.py:418:def amend_marker_severity(...)   # one hit — holds
```

The `"issue", "list"` hit is `_find_issue` (`specfuse/agent/severity_backfill.py:215`),
T07's tracer-bullet helper. T09 was never scoped to delete it, and the criterion's
grep is module-scoped while its claim ("the write path") is function-scoped.

**It is now worse than a wrong grep: the helper is dead.** `T10H` removed
`backfill_severity`, `_find_issue`'s only caller, and left the helper behind. The same
is true of `_STUB_SEVERITY`, whose `#:` comment still reads "Stands in for T10's
classification session (gate 3, walking skeleton)".

```
$ grep -rn "_find_issue" --include="*.py" . | grep -v .venv | grep -v /build/
specfuse/agent/severity_backfill.py:215:def _find_issue(...)     # its own definition, no caller
$ grep -rn "_STUB_SEVERITY" --include="*.py" specfuse/ tests/
specfuse/agent/severity_backfill.py:47:_STUB_SEVERITY = "medium"  # its own definition, no reader
```

`tests/test_caller_check_ratchet.py` cannot see either: the ratchet reports **public**
symbols whose only callers are tests, so a private helper orphaned by a deletion is
invisible to it. `backfill_severity` was caught; `_find_issue` and `_STUB_SEVERITY`
were not, in the same deletion.

**Re-run condition.** `_find_issue` and `_STUB_SEVERITY` are removed from
`specfuse/agent/severity_backfill.py` (with `json` and any other import left
unreferenced by the removal), and **both** of the following hold at that tree:

```
grep -c '"issue", "list"' specfuse/agent/severity_backfill.py   -> 0
grep -c run_claude specfuse/agent/severity_backfill.py          -> 2   (the live classifier path)
```

plus `python3 -m unittest tests.test_severity_backfill_run tests.test_severity_backfill_apply
tests.test_severity_backfill_limit tests.test_caller_check_ratchet -b` green and the full
`tests` and `coverage` gates green. Note the second grep deliberately expects `2`, not
`0`: T09's criterion asked for `0` at a tree where the classifier had not yet landed,
and `run_backfill` legitimately calls `run_claude` at HEAD. Re-asserting `0` there
would be re-running a criterion against a module that has since changed shape.

**Worth considering with it (not required by the re-run condition):** the ratchet's
blind spot is the general case, not this instance. A private symbol left with no
reader after a deletion is exactly the class `caller_check` exists for, and it
declines to look at underscore-prefixed names.

### The gate 3 `feature_oracle` passes while asserting only half the milestone it declares

**Tracked as #3359.**

**Not an acceptance criterion — a finding this close measured.** `GATE-03.md` declares:

```yaml
feature_oracle: "python3 -m unittest tests.test_severity_backfill_end_to_end -v -b"
```

and its Definition of done describes what that oracle drives:

> … is re-read under `specfuse-backfill-severity --apply`, its marker amended with
> `severity=` and the `severity:<value>` label projected after it; **and** the same
> repository under a conductor run with no flag is left untouched, asserted by argv.
> **Both halves are in one module because the milestone is the pair.**

**Evidence.** At HEAD the module holds two tests and neither is the first half:

```
$ python3 -m unittest tests.test_severity_backfill_end_to_end -v -b
test_pyproject_registers_exactly_one_new_console_script_no_dependency_change ... ok
test_the_conductor_cannot_reach_the_backfill ... ok
Ran 2 tests ... OK                                                        # exit 0
```

`test_marked_issue_without_severity_is_amended_then_labelled` was deleted by `T10H`
(`git diff 0d9a400 96c0f04 -- tests/test_severity_backfill_end_to_end.py` → 78
deletions, 0 insertions). That deletion was **authorised and coverage-checked** —
T10H's body named `tests/test_severity_backfill_apply.py:32` as the surviving ordering
assertion and its criterion 5 required it to be shown running, which this close
re-verified (`Ran 4 tests`, `OK`). The behaviour is covered. What is not covered is
the gate's own declared feature-level question: the command declared to ask it no
longer asks it, and it passes.

**Re-run condition.** Either (a) `tests/test_severity_backfill_end_to_end.py` regains
an end-to-end assertion that drives `main()`/`run_backfill` with `--apply` over an
injected runner whose listing returns one marked, severity-less issue, and asserts
`gh issue edit … --body <marker with severity=>` precedes `gh issue edit …
--add-label severity:<v>` on call order — **and** `GATE-03.md`'s
`feature_oracle` still names that module; or (b) `GATE-03.md`'s `feature_oracle` is
re-pointed at a command that does assert the pair, with the change recorded in
`GATE-03-REVIEW.md`. Silently leaving a passing two-test structural module as the
gate's feature-level oracle is the outcome this entry exists to prevent.

### The measured 31 are selectable but not classifiable, and backfill can contradict a human-applied severity once the rubric widens

**Tracked as #3360.**

**Not an acceptance criterion — the feature's motivating question, answered `not yet`.**
`PLAN.md` opened on 31 bug-marked issues carrying a marker and no severity label,
permanently stranded under a `medium` floor.

**Evidence (`FEAT-2026-0113/T11`, read-only live run, `--apply` not passed; full paste
in `GATE-03-REVIEW.md` under `## Live-corpus dry run (T11, 2026-09-18)`).**

```
$ python3 -m specfuse.agent.severity_backfill --repo <the measured repository> --limit 5
#1902: no usable classification, skipped
#1895: no usable classification, skipped
#1893: no usable classification, skipped
#1883: severity=critical
#1876: no usable classification, skipped
EXIT=0
```

- **Selectable:** `--limit 100` → 74 candidates, `--limit 200` → 84, against 191 open
  issues — a superset of the 31.
- **Classifiable:** 1 of 5 sampled. That repository declares
  `severity:critical`/`major`/`minor`; only `critical` is in
  `agent_policy.SEVERITY_VALUES`, so `read_severity_rubric` returns a single-entry
  rubric and `classify_severity` fails closed on everything else. Re-measured in this
  close against an injected runner: that scheme → `rubric == ['critical']`; a fully
  disjoint scheme (`p0`/`p1`) → `{}` and a one-call no-op run.
- **The collision that is latent today:** `#1902`, `#1895` and `#1893` already carry
  `severity:minor` / `severity:major` / `severity:major` — applied by a person — while
  their markers carry no `severity=`. The predicate selects on the marker, so they are
  candidates. Masked only because the one-word rubric skips them.

**Re-run condition.** This entry is discharged when, against the repository where the
31 were measured, a `--limit 200` dry run reports a **classified** severity for a
majority of its candidates *and* reports zero rows whose issue already carries a
`severity:*` label the run would contradict. Concretely that needs, in order:

1. **`#3355`** — a shipped default alias table, so `severity:major` reads without every
   operator writing the same map; **or** `#3356` — an opt-in mode harmonising a
   repository's own labels onto the standard vocabulary, which dissolves the mismatch
   rather than translating around it. `#3356` reuses this gate's selection and write
   machinery.
2. **A reconciliation path, which is a prerequisite for `#3355` and does not exist.**
   An issue whose label already states a severity must have its marker written **from
   that label**, not from a fresh classification. Without it, widening the rubric makes
   the classifier answer `high` for an issue a person labelled `minor`, the write path
   adds `severity:high` beside the human's `severity:minor`, and `read_severity_label`
   returns whichever it recognises first — the agent silently overriding a person at
   the floor. This is already recorded as a prerequisite on `#3355`; it is restated
   here because it is the one outcome this feature must not ship into.
3. **A first `--apply` run against a real repository**, which has never happened: every
   write in this feature has only ever been observed against an injected runner. That
   is by design (`T11`'s Do-not-touch forbade `--apply`), and it means the write half
   of gate 1's carried residual is re-carried rather than discharged.
