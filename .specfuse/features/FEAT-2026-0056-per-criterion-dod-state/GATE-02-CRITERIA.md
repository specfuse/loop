### T05#1

- **criterion:** `tests/test_loop_criteria_survival.py::test_criteria_artifact_survives_attempt_reset`
- **state:** `unverified`

### T05#2

- **criterion:** `specfuse/loop/criteria_state.py` exports `criteria_filename(gate_n: int) -> str`
- **oracle:** python3 -c "from specfuse.loop.criteria_state import criteria_filename as f, CRITERIA_FILENAME_RE as R; assert f(1)=='GATE-01-CRITERIA.md' and f(12)=='GATE-12-CRITERIA.md'; assert R.match('GATE-01-CRITERIA.md') and not R.match('GATE-01.md') and not R.match('GATE-01-REVIEW.md') and not R.match('RETROSPECTIVE.md')"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#3

- **criterion:** `grep -nE 'GATE-\{[a-z_]+[^}]*\}-CRITERIA\.md' specfuse/` returns matches only
- **oracle:** grep -rnE 'GATE-\{[a-z_]+[^}]*\}-CRITERIA\.md' specfuse/
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#4

- **criterion:** `_clean_attempt_untracked` does not unlink a file whose basename matches
- **oracle:** python3 -m unittest tests.test_loop_criteria_survival
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#5

- **criterion:** In that same tree and the same call, an unrelated untracked file created after
- **oracle:** python3 -m unittest tests.test_loop_criteria_survival
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#6

- **criterion:** `_clean_attempt_untracked` still never unlinks `events_path` — the existing
- **oracle:** python3 -m unittest tests.test_loop_criteria_survival  (2 tests, OK — `test_events_jsonl_carve_out_is_intact` creates events.jsonl after the untracked snapshot and asserts it survives with contents intact)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `04fbc80`
- **attempt:** `1`
- **provenance:** Flipped `fail` → `pass` post-close by an operator-directed session on 2026-08-06, not by the close WU. `G2-CLOSE` recorded `fail` correctly: at sha `f25e790` the behaviour held but no assertion existed, and repairing it was outside that unit's boundary. The hedged-verdict follow-up record in `RETROSPECTIVE.md` names the exact re-run condition — *"a work unit adds an assertion … and `python3 -m unittest tests.test_loop_criteria_survival` then reports at least 2 tests, OK. At that point `T05#6` flips to `state: pass` and this entry is discharged."* That condition was met at `04fbc80`, and the flip follows the record's own stated rule rather than a reader's inference. The assertion was mutation-verified: replacing `keep = events_path.resolve()` with `keep = None` in `_clean_attempt_untracked` fails this test and only this test.

### T05#7

- **criterion:** The `untracked_before = untracked_paths()` assignment in `run()` remains **outside**
- **oracle:** grep -n 'untracked_before = untracked_paths()' specfuse/loop/loop.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#8

- **criterion:** `python3 -c "from specfuse.loop.criteria_state import criteria_filename, CRITERIA_FILENAME_RE"`
- **oracle:** python3 -c "from specfuse.loop.criteria_state import criteria_filename, CRITERIA_FILENAME_RE"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#9

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest tests.test_loop_criteria_survival
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T05#10

- **criterion:** The full `code` gate set passes, including `coverage report --fail-under=90`.
- **oracle:** `.specfuse/verification.yml` `code` gate set, all 14 gates, re-run in full this session
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#1

- **criterion:** `tests/test_lint_closing_criteria_pristine.py::test_pristine_seeded_entry_is_not_a_finding`
- **state:** `unverified`

### T06#2

- **criterion:** `check_criteria_state_well_formed` returns **zero** findings for an artifact whose
- **oracle:** python3 -m unittest tests.test_lint_closing_criteria_pristine
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#3

- **criterion:** It returns **exactly one** finding for an entry with `state: pass` and no `kind:`
- **oracle:** in-session probe: check_criteria_state_well_formed over five synthetic artifacts (pass+no-kind, unverified+oracle+no-kind, broad-pass-stale-attempt, two-pristine, broad-pass-current-attempt)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#4

- **criterion:** It returns **exactly one** finding for an entry with `state: unverified`, no
- **oracle:** in-session probe: check_criteria_state_well_formed over five synthetic artifacts (pass+no-kind, unverified+oracle+no-kind, broad-pass-stale-attempt, two-pristine, broad-pass-current-attempt)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#5

- **criterion:** It returns **exactly one** finding for a `broad` entry with `state: pass` whose
- **oracle:** in-session probe: check_criteria_state_well_formed over five synthetic artifacts (pass+no-kind, unverified+oracle+no-kind, broad-pass-stale-attempt, two-pristine, broad-pass-current-attempt)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#6

- **criterion:** T03's `tests/test_lint_closing_criteria.py` is **unedited** and still passes
- **oracle:** python3 -m unittest tests.test_lint_closing_criteria
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#7

- **criterion:** **Initial-state probe.** Seed a scratch copy of a real feature folder through the
- **oracle:** python3 .specfuse/scripts/lint_plan.py <scratch copy of this feature folder seeded through the real loop._precreate_criteria_state_stub> --closing
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#8

- **criterion:** **Positive control.** In that same scratch copy, annotate one entry with
- **oracle:** python3 .specfuse/scripts/lint_plan.py <scratch copy of this feature folder seeded through the real loop._precreate_criteria_state_stub> --closing
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#9

- **criterion:** **Corpus sweep, from source.** `for d in .specfuse/features/*/; do python3 .specfuse/scripts/lint_plan.py "$d" --closing; done`
- **oracle:** for d in .specfuse/features/*/; do python3 .specfuse/scripts/lint_plan.py "$d" --closing; done  (from the .specfuse/scripts/ shim, not the installed console script)
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#10

- **criterion:** The `close-l` and `close-intermediate-f` records in
- **oracle:** python3 -c "from specfuse.loop import closing_requirements as c; print([(r.id, r.applies_when, r.enforced_by) for v in c.CLOSING_REQUIREMENTS.values() for r in v if r.id in ('close-l','close-intermediate-f')])"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#11

- **criterion:** `python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"`
- **oracle:** python3 -c "from specfuse.loop.lint_closing import check_criteria_state_well_formed"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T06#12

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest tests.test_lint_closing_criteria_pristine
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#1

- **criterion:** `tests/test_criteria_worklist.py::test_broad_pass_never_carries_forward` exists
- **state:** `unverified`

### T07#2

- **criterion:** `specfuse/loop/criteria_state.py` exports `build_reverification_worklist(entries,
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#3

- **criterion:** The function is pure: `grep -n 'open(\|Path(\|subprocess\|os\.' ` over the
- **oracle:** python3 -c "import inspect, re; from specfuse.loop import criteria_state as cs; print([l for l in inspect.getsource(cs.build_reverification_worklist).splitlines() if re.search(r'open\(|Path\(|subprocess|os\.', l)])"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#4

- **criterion:** An entry with `kind: narrow`, `state: pass`, a non-empty `oracle:`, and a
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#5

- **criterion:** An entry with `kind: broad` and `state: pass` lands in `reverify` — asserted for
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#6

- **criterion:** An entry with `kind: narrow` and `state: fail` lands in `reverify`.
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#7

- **criterion:** An entry with `state: unverified` lands in `reverify`, whatever its `kind`.
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#8

- **criterion:** An entry whose `kind` is absent, and one whose `kind` is not in `ORACLE_KINDS`,
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#9

- **criterion:** `carry_forward` and `reverify` partition the input exactly:
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#10

- **criterion:** Two `reverify` entries whose `oracle:` strings are byte-identical produce **one**
- **oracle:** in-session probe: build_reverification_worklist over 9 synthetic entries covering every kind/state combination
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#11

- **criterion:** `python3 -c "from specfuse.loop.criteria_state import build_reverification_worklist"`
- **oracle:** python3 -c "from specfuse.loop.criteria_state import build_reverification_worklist"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T07#12

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest tests.test_criteria_worklist
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#1

- **criterion:** `tests/test_loop_worklist_injection.py::test_close_dispatch_prompt_carries_worklist`
- **state:** `unverified`

### T08#2

- **criterion:** `specfuse/loop/loop.py` exports `format_reverification_worklist(wu, feature_dir)
- **oracle:** in-session probe: format_reverification_worklist over the three empty-string cases and a 3-entry artifact (1 narrow-pass, 1 broad-pass, 1 narrow-fail sharing an oracle)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#3

- **criterion:** For an artifact holding at least one carry-forward entry and at least one
- **oracle:** in-session probe: format_reverification_worklist over the three empty-string cases and a 3-entry artifact (1 narrow-pass, 1 broad-pass, 1 narrow-fail sharing an oracle)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#4

- **criterion:** The returned section lists each `oracle_groups` pair from T07 once, naming the
- **oracle:** in-session probe: format_reverification_worklist over the three empty-string cases and a 3-entry artifact (1 narrow-pass, 1 broad-pass, 1 narrow-fail sharing an oracle)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#5

- **criterion:** The section contains a literal, unconditional statement that the close's own
- **oracle:** observed directly in this session's own dispatched work-unit body — the '## Re-verification worklist (gate 2)' section the driver appended at dispatch
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#6

- **criterion:** No entry with `kind: broad` appears in the section's carried-forward list —
- **oracle:** in-session probe: format_reverification_worklist over the three empty-string cases and a 3-entry artifact (1 narrow-pass, 1 broad-pass, 1 narrow-fail sharing an oracle)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#7

- **criterion:** `execute_unit_attempt` appends the section to `wu.body` after the `oracle_section`
- **oracle:** observed directly in this session's own dispatched work-unit body — the '## Re-verification worklist (gate 2)' section the driver appended at dispatch
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#8

- **criterion:** A `plan-next` work unit's body is unchanged by the same call path — asserted with
- **oracle:** in-session probe: format_reverification_worklist over the three empty-string cases and a 3-entry artifact (1 narrow-pass, 1 broad-pass, 1 narrow-fail sharing an oracle)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#9

- **criterion:** `python3 -c "from specfuse.loop.loop import format_reverification_worklist"`
- **oracle:** python3 -c "from specfuse.loop.loop import format_reverification_worklist"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`

### T08#10

- **criterion:** The test named in criterion 1 **passes** after this WU's edits.
- **oracle:** python3 -m unittest tests.test_loop_worklist_injection
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `f25e790`
- **attempt:** `1`
