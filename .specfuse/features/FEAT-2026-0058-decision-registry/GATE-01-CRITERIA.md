### T01#1

- **criterion:** `tests/test_decisions_format.py::TestDecisionsFormat::test_status_is_a_closed_set`
- **oracle:** python3 -m unittest tests.test_decisions_format.TestDecisionsFormat.test_status_is_a_closed_set
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T01#2

- **criterion:** A parser reads a `DECISIONS.md` into entries carrying id, statement, owner,
- **oracle:** python3 -m unittest tests.test_decisions_format.TestDecisionsFormat.test_parses_well_formed_entry tests.test_decisions_format.TestDecisionsFormat.test_malformed_entry_is_reported_not_dropped
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T01#3

- **criterion:** A decision whose status is `overridden-pending-signoff` **or** which was ever
- **oracle:** python3 -m unittest tests.test_decisions_format.TestDecisionsFormat.test_overridden_pending_signoff_requires_provenance_fields tests.test_decisions_format.TestDecisionsFormat.test_ratified_after_override_is_distinguishable_from_ratified_from_start
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T01#4

- **criterion:** `.specfuse/templates/DECISIONS.template.md` exists and is byte-identical to
- **oracle:** cmp .specfuse/templates/DECISIONS.template.md specfuse/loop/data/templates/DECISIONS.template.md && python3 -m unittest tests.test_scaffold_data_in_sync
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T01#5

- **criterion:** This feature's `DECISIONS.md` contains D1–D4 from `PLAN.md`, each with an
- **oracle:** python3 -c "from specfuse.loop.decisions_format import parse_decisions; from pathlib import Path; r=parse_decisions(Path('.specfuse/features/FEAT-2026-0058-decision-registry/DECISIONS.md').read_text()); assert [e.decision_id for e in r.entries]==['D1','D2','D3','D4'] and not r.errors and all(e.owner and e.provenance for e in r.entries)"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T01#6

- **criterion:** 6. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
- **oracle:** python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#1

- **criterion:** `tests/test_decision_citation_lint.py::TestCitationIntegrity::test_dangling_decision_id_is_an_error`
- **oracle:** python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_dangling_decision_id_is_an_error tests.test_decision_citation_lint.TestCitationIntegrity.test_dangling_decision_id_exits_nonzero
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#2

- **criterion:** An artifact reproducing a decision's **statement text** instead of citing its
- **oracle:** python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_restatement_with_one_clause_altered_is_caught
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#3

- **criterion:** **A legitimate quotation is not a false positive.** The exemption is
- **oracle:** python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_legitimate_quotation_with_citation_is_not_a_false_positive
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#4

- **criterion:** `done` and `abandoned` features are exempt as sealed history, the same
- **oracle:** python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_done_feature_is_exempt tests.test_decision_citation_lint.TestCitationIntegrity.test_abandoned_feature_is_exempt
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#5

- **criterion:** A feature with **no** `DECISIONS.md` is not an error: the registry is opt-in
- **oracle:** python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_feature_with_no_decisions_md_is_not_an_error
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#6

- **criterion:** **The check runs clean over this repository's real tree**, with the
- **oracle:** python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_check_runs_clean_over_this_repository
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T02#7

- **criterion:** `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
- **oracle:** python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T03#1

- **criterion:** `tests/test_decision_override_lint.py::TestOverrideSignoff::test_unsigned_override_is_an_error`
- **oracle:** python3 -m unittest tests.test_decision_override_lint.TestOverrideSignoff.test_unsigned_override_is_an_error tests.test_decision_override_lint.TestOverrideSignoff.test_unsigned_override_exits_nonzero
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T03#2

- **criterion:** A decision at `ratified` that carries `overridden_from` **must** also carry
- **oracle:** python3 -m unittest tests.test_decision_override_lint.TestOverrideSignoff.test_ratified_from_override_without_signoff_is_an_error
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T03#3

- **criterion:** `signed_off_by` is required to be non-empty and not a placeholder. The
- **oracle:** python3 -m unittest tests.test_decision_override_lint.TestOverrideSignoff.test_placeholder_signed_off_by_is_an_error
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T03#4

- **criterion:** A decision that was never overridden needs no provenance fields, and their
- **oracle:** python3 -m unittest tests.test_decision_override_lint.TestOverrideSignoff.test_never_overridden_decision_needs_no_provenance
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T03#5

- **criterion:** The error message names the decision ID and the missing field, so an operator
- **oracle:** python3 -m unittest tests.test_decision_override_lint.TestOverrideSignoff.test_error_names_decision_id_and_missing_field
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`

### T03#6

- **criterion:** `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
- **oracle:** python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `565ecfb2b5a39bc079b350a000041635f294f523`
- **attempt:** `2`
