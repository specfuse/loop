### T04#1

- **criterion:** `tests/test_drafting_reply_shape.py` names
- **oracle:** `python3 -m unittest tests.test_drafting_reply_shape.ReplyTemplateRoundTripTests.test_template_block_parses_back_to_every_question -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T04#2

- **criterion:** `render_question_issue` writes a copyable answer-template block naming every
- **oracle:** `python3 -m unittest tests.test_drafting_reply_shape.ReplyTemplateRoundTripTests.test_template_block_parses_back_to_every_question -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T04#3

- **criterion:** `escalation.validate_escalation_body` still returns `[]` on the rendered
- **oracle:** `python3 -m unittest tests.test_drafting_reply_shape.ReplyTemplateRoundTripTests.test_body_still_conforms_to_escalation_shape -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T04#4

- **criterion:** A bare-number reply still yields no bindings and `evaluate_answer_gate`
- **oracle:** `python3 -m unittest tests.test_drafting_reply_shape.ReplyTemplateRoundTripTests.test_bare_number_reply_still_binds_nothing_and_falls_back -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T04#5

- **criterion:** Every question in a set carries a line in the template block, elicitation and
- **oracle:** `python3 -m unittest tests.test_drafting_reply_shape.ReplyTemplateRoundTripTests.test_template_names_every_question_including_elicitation -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T05#1

- **criterion:** `tests/test_draft_feature_answers_mode.py` names
- **oracle:** `python3 -m unittest tests.test_draft_feature_answers_mode.AnswersSuppliedModeTests.test_mode_section_states_the_answers_rule -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T05#2

- **criterion:** `SKILL.md` carries a new `## Answers-supplied mode` section stating: the
- **oracle:** `python3 -m unittest tests.test_draft_feature_answers_mode.AnswersSuppliedModeTests.test_mode_section_states_the_answers_rule -v  # Ran 1 test / OK, exit 0; section read directly at plugins/specfuse/skills/draft-feature/SKILL.md:357-392`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T05#3

- **criterion:** The drafted folder lands `status: planned` and unarmed in this mode, stated
- **oracle:** `python3 -m unittest tests.test_draft_feature_answers_mode.AnswersSuppliedModeTests.test_mode_section_states_the_answers_rule -v  # asserts the literal "`status: planned` and unarmed" in the section; Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T05#4

- **criterion:** The change is **additive**: every heading and hard rule present in HEAD's
- **oracle:** `python3 -m unittest tests.test_draft_feature_answers_mode.AnswersSuppliedModeTests.test_answers_mode_is_additive_and_does_not_interleave -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T05#5

- **criterion:** Both surfaces — `plugins/specfuse/skills/draft-feature/SKILL.md` and
- **oracle:** `python3 -m unittest tests.test_draft_feature_answers_mode.AnswersSuppliedModeTests.test_canonical_and_vendored_skill_are_byte_identical -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T06#1

- **criterion:** `tests/test_drafting_invoke.py` names
- **oracle:** `python3 -m unittest tests.test_drafting_invoke.RefusesFallbackTests.test_build_invocation_refuses_a_fallback_result -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T06#2

- **criterion:** `build_invocation` raises on an `AnswerGateResult` whose `outcome` is
- **oracle:** `python3 -m unittest tests.test_drafting_invoke.RefusesFallbackTests.test_build_invocation_refuses_a_fallback_result -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T06#3

- **criterion:** `build_invocation` returns a `(argv, prompt)` tuple and runs no subprocess —
- **oracle:** `python3 -m unittest tests.test_drafting_invoke.BuildInvocationTests.test_returns_argv_and_prompt_tuple tests.test_drafting_invoke.BuildInvocationTests.test_module_runs_no_subprocess -v  # Ran 2 tests / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T06#4

- **criterion:** The prompt names every question id and its effective answer, and names every
- **oracle:** `python3 -m unittest tests.test_drafting_invoke.BuildInvocationTests.test_prompt_names_every_question_id_and_effective_answer tests.test_drafting_invoke.BuildInvocationTests.test_prompt_names_every_assumption_verbatim -v  # Ran 2 tests / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T06#5

- **criterion:** `read_result` parses the session's RESULT block and raises on any status
- **oracle:** `python3 -m unittest tests.test_drafting_invoke.ReadResultTests -v  # Ran 4 tests / OK (complete parses; blocked, missing block and empty all raise), exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T07#1

- **criterion:** `tests/test_feature_provider_drafting_dispatch.py` names
- **oracle:** `python3 -m unittest tests.test_feature_provider_drafting_dispatch.DraftReadyDispatchesTests.test_draft_ready_invokes_drafting_not_escalation -v  # Ran 1 test / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T07#2

- **criterion:** On `DISPOSITION_NEEDS_DRAFTING` with a `draft_ready` answer-gate result,
- **oracle:** `python3 -m unittest tests.test_feature_provider_drafting_dispatch.DraftReadyDispatchesTests.test_draft_ready_invokes_drafting_not_escalation -v  # Ran 1 test / OK, exit 0. Scope limit: proved only with an injected answer_gate — see RETROSPECTIVE.md § Hedged-verdict follow-up record, entry 1.`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T07#3

- **criterion:** On `DISPOSITION_NEEDS_DRAFTING` with a `fallback` result, the returned
- **oracle:** `python3 -m unittest tests.test_feature_provider_drafting_dispatch.FallbackDispatchesTests -v  # Ran 2 tests / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T07#4

- **criterion:** The module docstring no longer claims `needs_drafting` always escalates, and
- **oracle:** `python3 -c "import specfuse.agent.providers.feature as m; d=m.__doc__; assert 'always escalates' not in d; assert 'two branches' in d and 'draft_ready' in d and 'fallback' in d"  # exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`

### T07#5

- **criterion:** `python3 -m unittest tests.test_drafting_answer_gate -v` still passes — the
- **oracle:** `python3 -m unittest tests.test_drafting_answer_gate -v  # Ran 11 tests / OK, exit 0`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `ac80f64`
- **attempt:** `1`
