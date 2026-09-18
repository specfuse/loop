### T07#1

- **criterion:** `tests/test_severity_backfill_end_to_end.py::SeverityBackfill::test_marked_issue_without_severity_is_amended_then_labelled`
- **oracle:** Red-before: `git cat-file -e be190bc:tests/test_severity_backfill_end_to_end.py` -> ABSENT (exit 1). Green at T07's own tree: `git archive deec4ce | tar -x` into a scratch dir, then `python3 -m unittest ...SeverityBackfill.test_marked_issue_without_severity_is_amended_then_labelled -v -b` -> `Ran 1 test`, `OK` (exit 0). The named test does NOT exist at HEAD: T10H deleted it with `backfill_severity` (authorised by T10H#4). Ordering coverage at HEAD is `tests/test_severity_backfill_apply.py::BackfillApply::test_marker_is_amended_before_the_label_is_added` -> `Ran 4 tests`, `OK` (exit 0), plus this close's argv probe (cases A/B/D: marker index < label index on every writing case)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07#2

- **criterion:** `test_the_conductor_cannot_reach_the_backfill`: `grep -c severity_backfill
- **oracle:** `grep -c severity_backfill specfuse/agent/run.py` -> `0` (exit 1, negative observation); `git diff main deec4ce -- specfuse/agent/run.py` -> 0 lines at T07's tree; `git diff main -- specfuse/agent/run.py` -> 0 lines at HEAD. `tests.test_severity_backfill_end_to_end` -> `Ran 2 tests`, `OK` (exit 0) at HEAD, which is where `test_the_conductor_cannot_reach_the_backfill` lives
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07#3

- **criterion:** `GATE-03.md`'s `feature_oracle` command exits 0 at this unit's tree — the
- **oracle:** `GATE-03.md`'s `feature_oracle` (`python3 -m unittest tests.test_severity_backfill_end_to_end -v -b`) at T07's extracted tree -> 3 of its 4 tests `OK` (exit 0); the 4th, `test_pyproject_registers...`, shells out to `git show` and returns 128 in a `.git`-less archive, an extraction artefact, and it is green at HEAD. Oracle at HEAD -> `Ran 2 tests`, `OK` (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07#4

- **criterion:** `python3 -c "from specfuse.agent.severity_backfill import backfill_severity"`
- **oracle:** At T07's tree `git show deec4ce:specfuse/agent/severity_backfill.py | grep -c 'def _amend_marker'` -> `1`, and the extracted-tree run of `test_import_exposes_backfill_severity_and_the_named_stub` -> `OK` (exit 0). CAVEAT recorded in RETROSPECTIVE.md: T07 left a SECOND stub, `_STUB_SEVERITY`, which its own docstring names as stubbed; only `_amend_marker` was covered by a deletion criterion, and `_STUB_SEVERITY` survives at HEAD with no reader (`grep -rn _STUB_SEVERITY specfuse/ tests/` -> 1 hit, its own definition)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08#1

- **criterion:** `tests/test_severity_backfill_marker.py::BackfillSelection::test_marked_issue_without_severity_is_a_candidate`
- **oracle:** Red-before: `git cat-file -e deec4ce:tests/test_severity_backfill_marker.py` -> ABSENT (exit 1). `python3 -m unittest tests.test_severity_backfill_marker -b` -> `Ran 11 tests`, `OK` (exit 0), including `BackfillSelection.test_marked_issue_without_severity_is_a_candidate`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08#2

- **criterion:** Each exclusion is asserted on its own row, not as a bundle: an issue carrying
- **oracle:** Four separately-named exclusion tests exist and run: `test_excludes_harvester_finding_issue`, `test_excludes_agent_escalation_issue`, `test_excludes_marker_naming_unknown_category`, `test_excludes_issue_with_no_marker` (tests/test_severity_backfill_marker.py:54,64,82,92) -> all `ok` in the `Ran 11 tests`, `OK` (exit 0) run above. One row per exclusion, not a bundle
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08#3

- **criterion:** `limit` bounds both the fetch and the result: the listing argv carries
- **oracle:** `grep -c '"issue", "list"' specfuse/loop/triage.py` -> `1` (exit 0) at HEAD: the listing is still issued through the module's single `_list_open_issues`. `test_limit_bounds_the_result_not_the_listing` and `test_issues_a_single_listing_call` both `ok` in the run above. NOTE: T08's `--limit` semantics were WRONG against real data and T08H replaced them; see T08H#1-#5 and RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08#4

- **criterion:** `amend_marker_severity(body, severity)` replaces the body's existing marker in
- **oracle:** `grep -c 'specfuse:triage' specfuse/loop/triage.py` -> `3` (exit 0) at HEAD; `grep -rn 'def amend_marker_severity' specfuse/` -> exactly one hit, `specfuse/loop/triage.py:418`; the function body renders through `render_marker` (read at :432). `test_replaces_marker_in_place_keeping_category_and_confidence` and `test_renders_through_render_marker` both `ok` in the run above
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08#5

- **criterion:** `amend_marker_severity` returns its input unchanged, by string equality, for a
- **oracle:** `test_returns_body_unchanged_when_no_marker` and `test_returns_body_unchanged_when_severity_already_present` (tests/test_severity_backfill_marker.py:152,157) both `ok` in the `Ran 11 tests`, `OK` (exit 0) run above
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07H#1

- **criterion:** `python3 -m unittest tests.test_build_provenance -v` fails on HEAD before
- **oracle:** Red-before is recorded by the driver's own `baseline_attribution` event at 2026-09-18T11:18:17Z: `{gate: tests, failure_signature: test_the_declared_console_scripts_match_the_wired_set}`, attributed to FEAT-2026-0113/T09, i.e. the tree before T07H. Re-derived here structurally: `git show 36f41e4:pyproject.toml` declares 7 console scripts while `git show 36f41e4:tests/test_build_provenance.py` lists 6 `ENTRY_MODULES`. Green at HEAD: `python3 -m unittest tests.test_build_provenance -b` -> `Ran 13 tests`, `OK` (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07H#2

- **criterion:** `specfuse/agent/severity_backfill.py` imports `warn_if_out_of_tree` from
- **oracle:** Call site read directly: `specfuse/agent/severity_backfill.py:41` imports `warn_if_out_of_tree` from `specfuse.loop.build_provenance`, and `:270-271` shows `def main(...)` followed immediately by `warn_if_out_of_tree()` as the first statement, before `build_parser().parse_args()`. Same position as the other six entry points
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07H#3

- **criterion:** `specfuse/agent/severity_backfill.py` is added to
- **oracle:** `ENTRY_MODULES` at HEAD carries `specfuse/agent/severity_backfill.py` as its 7th entry (tests/test_build_provenance.py, read directly); `test_each_entry_point_calls_the_check` covers it and is `ok` in the `Ran 13 tests`, `OK` (exit 0) run
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07H#4

- **criterion:** The `ENTRY_MODULES` tuple gains exactly one entry and loses none — asserted
- **oracle:** `git show 36f41e4:tests/test_build_provenance.py` -> 6-entry tuple; HEAD -> 7-entry tuple; the six original entries are byte-identical and in the same order, the new one appended. Exactly one gained, none lost
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T07H#5

- **criterion:** The full `tests` gate passes, and the `coverage` gate produces its marker
- **oracle:** The driver's once-per-gate broad run, CITED NOT RE-RUN: `broad_run_result` at 2026-09-18T12:00:11.966737+00:00, gate 3, `ok: true`, `failing: []`, over the 18-tree digest pinned in `GATE-03.md`'s `broad_run:` block -- which is the tree this close runs against (working-tree source == HEAD 0b40830, `git diff HEAD -- specfuse/ tests/ pyproject.toml` is empty). Per the dispatch contract this session ran no full suite and no coverage
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08H#1

- **criterion:** `tests/test_severity_backfill_limit.py::LimitBoundsCandidates::
- **oracle:** Red-before: `git cat-file -e 79b9b95:tests/test_severity_backfill_limit.py` -> ABSENT (exit 1). `python3 -m unittest tests.test_severity_backfill_limit -b` -> `Ran 4 tests`, `OK` (exit 0), including `LimitBoundsCandidates.test_limit_counts_candidates_not_listed_issues`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08H#2

- **criterion:** The listing is paged until `limit` candidates are found or open issues are
- **oracle:** `test_pages_until_limit_found_without_shrinking_the_window` (tests/test_severity_backfill_limit.py:65) `ok` in the run above. Re-measured independently in this close: an injected runner over 84 issues whose only candidates are the 80th-84th, `list_severity_backfill_candidates(..., limit=3)` -> 3 candidates `[800, 801, 802]`, `gh issue list` window requested = `100`. The window is `_BACKFILL_PAGE_SIZE` (= `DEFAULT_LIST_LIMIT`, triage.py:359) and grows by that step (`window += _BACKFILL_PAGE_SIZE`, :415); it is never the candidate limit
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08H#3

- **criterion:** Exhaustion terminates: a repository with fewer candidates than `limit`
- **oracle:** `test_exhaustion_terminates_with_fewer_candidates_than_limit` (:80) `ok` in the run above. Independently re-measured: 13 open issues of which 2 are candidates, `limit=50` -> 2 returned after exactly 1 `gh issue list` call (finite), loop exits on `len(issues) < window`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08H#4

- **criterion:** `test_a_zero_candidate_run_reports_why`: a run selecting no candidates prints
- **oracle:** `test_a_zero_candidate_run_reports_why` (:92) `ok` in the run above. Independently re-measured by capturing stdout of `run_backfill` + `_print_run_report` over 5 unmarked issues: `'no severity-backfill candidates found in acme-widget/example under limit=5\n'` -- names the repository and the limit, exit 0, not silence
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T08H#5

- **criterion:** `list_untriaged`'s own `limit` semantics are **unchanged** — it is a
- **oracle:** `list_untriaged` is untouched by T08H: `git diff 79b9b95 0d9a400 -- specfuse/loop/triage.py` adds `_BACKFILL_PAGE_SIZE` and rewrites `list_severity_backfill_candidates` only. Its existing tests run unedited: `python3 -m unittest tests.test_triage tests.test_triage_apply -b` is inside the gates-1-and-2 regression run -> `Ran 45 tests`, `OK` (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T09#1

- **criterion:** `tests/test_severity_backfill_apply.py::BackfillApply::test_marker_is_amended_before_the_label_is_added`
- **oracle:** Red-before: `git cat-file -e f0833ab:tests/test_severity_backfill_apply.py` -> ABSENT (exit 1). `python3 -m unittest tests.test_severity_backfill_apply -b` -> `Ran 4 tests`, `OK` (exit 0), including `BackfillApply.test_marker_is_amended_before_the_label_is_added`. Re-measured by argv in this close's independent probe: cases A/B/D each show `gh issue edit <n> --repo <r> --body <marker carrying severity=>` at a lower call index than `gh issue edit <n> --repo <r> --add-label severity:<v>`, and the amended marker's `category=bug confidence=high` are byte-identical to the input
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T09#2

- **criterion:** `test_an_issue_already_carrying_a_severity_is_never_written`: a decision whose
- **oracle:** `test_an_issue_already_carrying_a_severity_is_never_written` (tests/test_severity_backfill_apply.py:66) `ok` in the run above. Re-measured by argv: a run over `[#801 marker carries severity=high, #802 marker carries none]` selects only `[802]` and issues `gh issue edit` for `802` twice and for `801` zero times
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T09#3

- **criterion:** A failed label write is recorded on the returned row and never raised, with
- **oracle:** `test_a_failed_label_write_is_recorded_and_never_raised_marker_stays` (:79) and `test_a_failed_marker_write_leaves_the_label_unwritten` (:95) both `ok` in the `Ran 4 tests`, `OK` (exit 0) run above; `apply_severity_backfill` records `marker_error`/`label_error` on the row and re-raises neither (read at specfuse/agent/severity_backfill.py:100-125)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T09#4

- **criterion:** The write path neither lists nor classifies: `grep -c '"issue", "list"'` and
- **oracle:** MEASURED, NOT MET. `git show d859fc6:specfuse/agent/severity_backfill.py | grep -c '"issue", "list"'` -> **1**, not `0`, at T09's own tree; at HEAD `grep -c '"issue", "list"' specfuse/agent/severity_backfill.py` -> **1** (specfuse/agent/severity_backfill.py:218, inside `_find_issue`). The criterion requires BOTH greps to report `0`. The other three clauses DO hold: `grep -c run_claude` at d859fc6 -> `0`; `grep -c 'def _amend_marker'` at HEAD -> `0` (exit 1); `grep -rn 'def amend_marker_severity' specfuse/` -> exactly one hit. `_find_issue` was T07's tracer-bullet helper and T09 was never scoped to delete it; T10H removed its only caller (`backfill_severity`) and left it, so at HEAD it is dead code with no caller repo-wide (`grep -rn _find_issue --include=*.py .` -> 1 hit, its own definition). The caller ratchet is public-symbol-only and cannot see it. Follow-up recorded in FOLLOW-UPS.md
- **kind:** `narrow`
- **state:** `fail`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10#1

- **criterion:** `tests/test_severity_backfill_run.py::BackfillRun::test_rubric_is_read_once_and_each_candidate_is_classified`
- **oracle:** Red-before: `git cat-file -e d859fc6:tests/test_severity_backfill_run.py` -> ABSENT (exit 1). `python3 -m unittest tests.test_severity_backfill_run -b` -> `Ran 7 tests`, `OK` (exit 0), including `BackfillRun.test_rubric_is_read_once_and_each_candidate_is_classified` and `test_listing_and_provisioning_happen_once_per_run`. Re-measured by argv: over 2 candidates the sequence is exactly one `gh label list`, one `gh issue list`, two `claude`, then two marker/label pairs -- the listing is once per run
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10#2

- **criterion:** `test_a_low_confidence_or_out_of_rubric_answer_writes_nothing`: for a
- **oracle:** `test_a_low_confidence_or_out_of_rubric_answer_writes_nothing` (tests/test_severity_backfill_run.py:130) `ok` in the run above; `grep -c 'def classify_severity' specfuse/agent/severity_backfill.py` -> `0` (exit 1, negative observation) -- it imports `triage_invoke.classify_severity` rather than re-deriving it. Independently observed: this close's first probe pass handed the classifier a JSON answer instead of a marker, `classify_severity` returned `None` for every candidate, and the run issued ZERO `gh issue edit` calls under `apply=True` -- fail-closed, seen rejecting a purpose-built bad input
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10#3

- **criterion:** `test_an_empty_rubric_makes_the_run_a_no_op`: when `read_severity_rubric`
- **oracle:** `test_an_empty_rubric_makes_the_run_a_no_op_on_failed_listing` (:150) and `test_an_empty_rubric_makes_the_run_a_no_op_on_out_of_vocabulary_scheme` (:170) both `ok` in the run above. Re-measured by argv, probe case C (repository declaring `severity:p0`/`severity:p1` only): rubric `{}`, the WHOLE call sequence is 1 call (`gh label list`), zero `claude`, zero `gh issue edit`, and `reason` is set to "the repository's severity rubric is empty -- nothing for a classification to be checked against"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10#4

- **criterion:** `test_without_apply_nothing_is_written`: over the same three candidates, a run
- **oracle:** `test_without_apply_nothing_is_written` (:186) `ok` in the run above. Independently re-measured over 3 candidates with `apply=False`: `gh issue edit` calls = **0**, stdout = `'#701: severity=high\n#702: severity=high\n#703: severity=high\n'` (one line per selected issue), exit 0
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10#5

- **criterion:** `test_backfill_creates_no_labels`: across every case above,
- **oracle:** `grep -c '"label", "create"' specfuse/agent/severity_backfill.py` -> `0` (exit 1, negative observation). `test_backfill_creates_no_labels_against_a_repository_with_its_own_scheme` (:205) `ok`. Re-measured by argv over the WHOLE call sequence in four declares-own shapes (probe cases A/B/C/E): `gh label create` = **0** and argv carrying `--description` = **0** in every one; the declares-none control (case D) shows 4 creates, all before the first `--add-label`, proving the probe can see a create when one occurs
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10H#1

- **criterion:** `python3 -m unittest tests.test_caller_check_ratchet` fails on HEAD before
- **oracle:** Red-before is recorded by the driver's own `broad_run_result` + `human_escalation` at 2026-09-18T11:50:55Z: gate 3, `broad_run_gate_failure`, `{gate: tests, failure_signature: test_no_symbol_outside_the_baseline_is_called_only_by_tests}`. Green at HEAD: `python3 -m unittest tests.test_caller_check_ratchet -b` -> `Ran 5 tests`, `OK` (exit 0). No new BASELINE entry: `git diff 29f4ef2 96c0f04 -- tests/test_caller_check_ratchet.py` is EMPTY, so the tuple is byte-unchanged across T10H
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10H#2

- **criterion:** `backfill_severity` is removed from `specfuse/agent/severity_backfill.py`,
- **oracle:** `grep -c 'def backfill_severity' specfuse/agent/severity_backfill.py` -> `0` (exit 1, negative observation); `git show --stat 96c0f04` -> `specfuse/agent/severity_backfill.py | 61 -----`, deletions only
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10H#3

- **criterion:** The module docstring's paragraph describing `backfill_severity` as the
- **oracle:** Module docstring read directly at HEAD (specfuse/agent/severity_backfill.py:3-30): no paragraph naming `backfill_severity` remains. CAVEAT recorded in RETROSPECTIVE.md: the `#:` comment on `_STUB_SEVERITY` (:46) still reads "Stands in for T10's classification session (gate 3, walking skeleton)" -- a comment describing a stub for a path that has shipped, on a constant with no reader
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10H#4

- **criterion:** `tests/test_severity_backfill_end_to_end.py`'s two references are resolved:
- **oracle:** `git diff 0d9a400 96c0f04 -- tests/test_severity_backfill_end_to_end.py` -> both references removed, `78 ----` deletions and zero insertions: `test_marked_issue_without_severity_is_amended_then_labelled` deleted (not repointed) and `test_import_exposes_backfill_severity_and_the_named_stub` deleted. The replacement coverage claim is proved by T10H#5, not trusted
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10H#5

- **criterion:** `python3 -m unittest tests.test_severity_backfill_apply -v` passes and its
- **oracle:** `python3 -m unittest tests.test_severity_backfill_apply -v -b` -> `Ran 4 tests`, `OK` (exit 0) and its verbose output names `test_marker_is_amended_before_the_label_is_added`; `grep -n` locates it at tests/test_severity_backfill_apply.py:32. The module is unedited by T10H (`git show --stat 96c0f04` does not list it), so the deletion did not accommodate itself by editing its own replacement
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T10H#6

- **criterion:** The full `tests` gate passes and the `coverage` gate emits its marker again,
- **oracle:** The driver's once-per-gate broad run, CITED NOT RE-RUN: `broad_run_result` at 2026-09-18T12:00:11.966737+00:00, gate 3, `ok: true`, `failing: []` -- both `tests` and `coverage` green, confirming the `no_gate_marker` coverage failure at 11:50 was downstream of the ratchet failure. This session ran no full suite and no coverage gate
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T11#1

- **criterion:** `specfuse-backfill-severity --repo <OWNER/NAME> --limit 5` is run
- **oracle:** `WU-11-live-corpus-dry-run.md`'s `evidence:` field records the command, the repository and 5 selected issues (#1902 #1895 #1893 #1883 #1876); `GATE-03-REVIEW.md` carries the `## Live-corpus dry run (T11, 2026-09-18)` heading with the verbatim stdout, `EXIT=0`, and a per-row table giving each issue's marker line. Run as the module (`python3 -m specfuse.agent.severity_backfill`) rather than the console script, which is not on PATH until a reinstall -- same `main()`, recorded in the paste. `--apply` not passed
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T11#2

- **criterion:** You confirm on that paste that every selected issue carries a triage marker
- **oracle:** The paste states "Every selected issue carries a triage marker with **no `severity=` field** ... Confirmed", with the marker shown per row. The operator DID name issues that should not be touched: `### Finding carried to the close: three selected issues already carry a human-assigned severity` -- #1902/#1895/#1893 carry `severity:minor`/`severity:major`/`severity:major` applied by a person while their markers carry no `severity=`. Masked today by the single-entry rubric; carried to this close and re-carried as a prerequisite on issue 3355
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`

### T11#3

- **criterion:** The unit is closed with
- **oracle:** `WU-11-live-corpus-dry-run.md` frontmatter at HEAD: `type: human`, `status: done`, `attempts: 0`, with a non-empty `evidence:` string naming the command, the repository and the selection count. Committed as `f34f373 chore(loop): FEAT-2026-0113/T11 done -- live dry run recorded`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `0b408300ea99c136945d1f44e210d3620f7edd6a`
- **attempt:** `1`
