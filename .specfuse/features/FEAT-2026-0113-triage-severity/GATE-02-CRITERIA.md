### T02H#1

- **criterion:** `python3 -m unittest tests.test_triage_severity_end_to_end -v -b` — gate 2's
- **oracle:** `git cat-file -e 8169640:tests/test_triage_severity_end_to_end.py` -> ABSENT (exit 1) at the pre-unit tree; `python3 -m unittest tests.test_triage_severity_end_to_end -v -b` -> `Ran 5 tests`, `OK` (exit 0) at HEAD
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T02H#2

- **criterion:** The module drives `TriageProvider.execute` end to end with an injected runner,
- **oracle:** `git show 3f1c2f7:tests/test_triage_severity_end_to_end.py` -- the unit as shipped drives `TriageProvider.execute` through an injected `runner(argv, check=False)` double, no live `gh` and no network; the HEAD module keeps that shape (`_make_runner`) and runs green (exit 0) with no network reachable
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T02H#3

- **criterion:** It asserts the `gh` argv sequence a run issues **today** for one untriaged
- **oracle:** `git show 3f1c2f7:...` shows the order asserted structurally (`marker_call, label_call = edit_calls`, then per-call `--body`/`--add-label` exclusivity); re-measured at HEAD by the in-session argv probe, case D -- `gh issue edit --body` at position 3 precedes `gh issue edit --add-label` at position 4. CAVEAT recorded in RETROSPECTIVE.md: T06's rewrite dropped the test-level ordering assertion for the severity-free path; the behaviour is measured, the assertion is not present at HEAD
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T02H#4

- **criterion:** No severity assertion appears in this unit. Severity is not on the path yet,
- **oracle:** `git show 3f1c2f7:... | grep -n severity` -> exactly 1 hit, line 9, inside the module docstring (prose naming T06); zero severity assertions in the unit as shipped
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T02H#5

- **criterion:** The full `tests` gate passes: this module is additive and edits no existing
- **oracle:** `git show 3f1c2f7 --stat` -> the only test file touched is `tests/test_triage_severity_end_to_end.py`, +106 and no deletions; `git cat-file -e 8169640:` confirms it did not previously exist, so the addition is additive by construction. Full-suite claim is the driver's broad run, cited not re-run
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_severity_rubric.py::SeverityRubric::test_rubric_reads_label_descriptions`
- **oracle:** module absent at the pre-unit tree; `python3 -m unittest tests.test_severity_rubric -v -b` -> `Ran 10 tests`, `OK` (exit 0), including `SeverityRubric.test_rubric_reads_label_descriptions`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#2

- **criterion:** `grep -c '"label", "list"' specfuse/loop/labels.py` returns `1`: the extracted
- **oracle:** `grep -c '"label", "list"' specfuse/loop/labels.py` -> `1` (exit 0); `python3 -m unittest tests.test_provision_labels tests.test_label_provisioning_runner_contract tests.test_caller_check_ratchet -b` -> `Ran 28 tests`, `OK` (exit 0), all three modules unedited by this gate
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#3

- **criterion:** The rubric reader returns `{severity_value: description}`. When the repository
- **oracle:** in-session probe of `read_severity_rubric` over five label-set shapes: declares-own returns its own descriptions only; declares-none returns the full four-entry `DEFAULT_SEVERITY_RUBRIC`. Corroborated by `test_rubric_reads_label_descriptions`, `test_no_severity_labels_defined_returns_the_shipped_default`, `test_repository_scheme_never_gets_specfuse_authored_values`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#4

- **criterion:** A repository defining a `severity:*` label whose value is in `SEVERITY_VALUES`
- **oracle:** in-session probe, row `severity:high` described empty + `severity:low` described -> `{'high': <shipped text>, 'low': 'Their own low.'}`: the shipped definition for that value only, the repository's own description kept. Test: `test_empty_description_gets_shipped_definition_for_that_value_only`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#5

- **criterion:** Provisioning is conditional and narrow: the four labels are created — through
- **oracle:** in-session argv probe: every declares-own shape (four described, critical/major/minor, empty-description, out-of-vocabulary-only) issues **0** `gh label create`; declares-none issues exactly 4, each carrying `--force`. Tests: `test_repository_defining_its_own_scheme_gets_zero_create_calls`, `test_no_severity_labels_defined_provisions_the_four_defaults`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#6

- **criterion:** A failed label creation is reported and never raised, and leaves the rubric
- **oracle:** `test_failed_label_creation_is_not_raised_and_rubric_stays_usable` green inside the 10-case module run (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T03#7

- **criterion:** An absent `gh` binary, a non-zero `gh label list` exit, and unparseable output
- **oracle:** `test_missing_gh_binary_returns_empty_dict`, `test_nonzero_list_exit_returns_empty_dict`, `test_unparseable_list_output_returns_empty_dict` -- three separate cases, all green in the module run (exit 0), each with an injected runner and no live `gh`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T04#1

- **criterion:** `tests/test_triage_severity_write.py::SeverityWrite::test_marker_is_written_before_label`
- **oracle:** `python3 -m unittest tests.test_triage_severity_write -v -b` -> `Ran 7 tests`, `OK` (exit 0), including `SeverityWrite.test_marker_is_written_before_label`, which asserts on the recorded call order; module absent at the pre-unit tree
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T04#2

- **criterion:** `render_marker` emits today's two-field string byte-identically when no severity
- **oracle:** in-session byte-equality probe: `render_marker` over the full `CATEGORIES` x `CONFIDENCES` cross-product (10 shapes) against the literal `<!-- specfuse:triage category={c} confidence={f} -->` -> **0** mismatches; three-field form renders `... confidence=high severity=critical -->`. Tests: `RenderMarkerShape.test_two_field_form_is_byte_identical`, `test_severity_appended_as_third_field`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T04#3

- **criterion:** A decision carrying no `severity` key produces the identical `gh` argv sequence
- **oracle:** in-session argv probe case D (no severity on the decision) -> `gh issue edit <n> --repo o/r --body <two-field marker>` then `gh issue edit <n> --repo o/r --add-label triage:bug`, identical to today's sequence; `python3 -m unittest tests.test_triage_apply -b` green unedited inside the 40-test run (exit 0). Test: `NoSeverityKeyIsUnaffected.test_argv_sequence_matches_pre_existing_expectation`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T04#4

- **criterion:** A failed `severity:<value>` label write is recorded on the returned row and
- **oracle:** `SeverityLabelFailureTolerated.test_failed_severity_label_write_recorded_not_raised` green in the module run (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T04#5

- **criterion:** The repair branch is idempotent for severity: an issue whose marker carries
- **oracle:** `SeverityRepairIsIdempotent.test_marked_issue_missing_severity_label_gets_it_added` and `test_marked_issue_with_severity_label_already_present_does_nothing` -- both green in the module run (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T05#1

- **criterion:** `tests/test_triage_severity_classify.py::SeverityPrompt::test_prompt_unchanged_when_rubric_is_empty`
- **oracle:** `python3 -m unittest tests.test_triage_severity_classify -v -b` -> `Ran 12 tests`, `OK` (exit 0), including `SeverityPrompt.test_prompt_unchanged_when_rubric_is_empty`; module absent at the pre-unit tree
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T05#2

- **criterion:** Given a non-empty rubric, the prompt names each severity value beside the
- **oracle:** `test_prompt_names_each_severity_value_beside_its_definition` and `test_module_holds_no_copy_of_the_shipped_default_rubric` green; corroborated by a negative observation -- `grep -c 'Minor impact\|Moderate impact\|Major impact\|Severe impact\|DEFAULT_SEVERITY_RUBRIC' specfuse/agent/triage_invoke.py` -> `0` (exit 1), and `grep -rn DEFAULT_SEVERITY_RUBRIC --include='*.py' specfuse/` shows the single definition at `specfuse/loop/labels.py:347`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T05#3

- **criterion:** `classify_result` returns `(category, confidence)` unchanged for every input it
- **oracle:** `ClassifyResultUnchanged` -- `test_two_field_marker_still_returns_category_and_confidence`, `test_three_field_marker_still_returns_only_category_and_confidence`, `test_empty_output_returns_none` -- plus `ClassifySeverityFailsClosed.test_returns_rubric_matched_severity_at_high_confidence`, all green in the module run (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T05#4

- **criterion:** An absent `severity=` field, an empty value, a value outside the given rubric,
- **oracle:** `ClassifySeverityFailsClosed` -- `test_absent_severity_field_yields_none`, `test_empty_severity_value_yields_none`, `test_severity_outside_rubric_yields_none`, `test_non_high_confidence_yields_none_even_with_matching_severity`, `test_empty_output_yields_none` -- five negative observations, case by case, all green (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T06#1

- **criterion:** `tests/test_triage_severity_end_to_end.py::SeverityEndToEnd::test_severity_recorded_when_labels_are_defined`
- **oracle:** gate `feature_oracle` `python3 -m unittest tests.test_triage_severity_end_to_end -v -b` -> `Ran 5 tests`, `OK` (exit 0), including `SeverityEndToEnd.test_severity_recorded_when_labels_are_defined`; independently re-measured by the in-session argv probe, case A: `--body` carrying `severity=high` at position 3, `--add-label triage:bug,severity:high` at position 4
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T06#2

- **criterion:** `test_repository_with_its_own_labels_is_not_interfered_with`: with an injected
- **oracle:** in-session argv probe over the WHOLE call sequence, cases A and B (B = the measured real-world scheme `severity:critical|major|minor`, all described): `gh label create` calls **0**, argv containing `--description` **0**, in both. Test: `test_repository_with_its_own_labels_is_not_interfered_with`. Rubric-level probe adds three more declares-own shapes, all **0** creates
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T06#3

- **criterion:** Both the listing and any provisioning are once per `execute` run, not once per
- **oracle:** in-session argv probe case E -- three untriaged issues through `execute`: exactly **1** `gh label list`, exactly **4** `gh label create` (one per label, no repeat), 14 calls total. Test: `test_listing_and_provisioning_happen_once_per_run`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`

### T06#4

- **criterion:** A failing label listing, or an absent `gh` binary, leaves the run classifying
- **oracle:** in-session argv probe case D (listing returns exit 1) -> `gh label list` (fails), `claude`, `gh issue edit --body <two-field marker, no severity=>`, `gh issue edit --add-label triage:bug`; **0** creates, no raise, run completes. Test: `test_failing_label_listing_degrades_to_todays_write_sequence`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4ad0253647b8f5c461a1b56723549a802138c1c0`
- **attempt:** `1`
