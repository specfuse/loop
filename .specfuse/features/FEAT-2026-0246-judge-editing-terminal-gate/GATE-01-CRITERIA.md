### T01#1

- **criterion:** `tests/test_terminal_judge_editing_end_to_end.py::FiresOnSingleGateJudgeEdit` fails
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end.FiresOnSingleGateJudgeEdit tests.test_terminal_judge_editing_end_to_end.CleanFeatureClosesUnchanged -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T01#2

- **criterion:** `tests/test_arm_eval_terminal.py` covers: a judge-module path fires; a universal
- **oracle:** python3 -m unittest tests.test_arm_eval_terminal -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T01#3

- **criterion:** `python3 -m unittest tests.test_arm_eval tests.test_arm_eval_wiring
- **oracle:** python3 -m unittest tests.test_arm_eval tests.test_arm_eval_wiring tests.test_lifecycle_integration -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T01#4

- **criterion:** A schema check accepts the new `terminal_judge_editing_evaluated` event (the
- **oracle:** python3 .specfuse/scripts/event_type_gate.py && python3 -m unittest tests.test_driver_event_registry_covers_emitters -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T02#1

- **criterion:** `tests/test_terminal_judge_editing_end_to_end.py::AcknowledgedStopProceeds` and
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end.AcknowledgedStopProceeds tests.test_terminal_judge_editing_end_to_end.NewPathRefires -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T02#2

- **criterion:** `tests/test_arm_eval_terminal.py` adds: full coverage → clean; partial coverage →
- **oracle:** python3 -m unittest tests.test_arm_eval_terminal -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T02#3

- **criterion:** `tests/test_lint_judge_edit_acknowledged.py` covers: valid field passes; missing
- **oracle:** python3 -m unittest tests.test_lint_judge_edit_acknowledged -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T02#4

- **criterion:** `specfuse lint .specfuse/features/FEAT-2026-0246-judge-editing-terminal-gate`
- **oracle:** python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0246-judge-editing-terminal-gate
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T03#1

- **criterion:** The three oracle classes fail once un-skipped on the T01/T02 tree (no brief text;
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end.EveryAutonomyLevelStops tests.test_terminal_judge_editing_end_to_end.AutoClosePathStops tests.test_terminal_judge_editing_end_to_end.BriefHasSixParts -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_terminal_judge_editing_end_to_end.py

### T03#2

- **criterion:** `grep -rn "judge_editing_terminal" specfuse/loop/loop.py` shows the reason used at
- **oracle:** grep -rln judge_editing_terminal specfuse --include=*.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_terminal_judge_editing_end_to_end.py

### T03#3

- **criterion:** `python3 -m unittest tests.test_lifecycle_integration -b` passes.
- **oracle:** python3 -m unittest tests.test_lifecycle_integration -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/loop.py, tests/test_terminal_judge_editing_end_to_end.py

### T04#1

- **criterion:** `tests/test_judge_editing_terminal_docs.py` with the new assertions fails on HEAD's
- **oracle:** python3 -m unittest tests.test_judge_editing_terminal_docs tests.test_terminal_judge_editing_end_to_end.DocsNoLongerRecommendReview -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/concepts/autonomy-stop-classes.md, specfuse/loop/data/docs/concepts/autonomy-stop-classes.md, tests/test_judge_editing_terminal_docs.py, tests/test_terminal_judge_editing_end_to_end.py

### T04#2

- **criterion:** Each pair of copies is byte-identical:
- **oracle:** cmp plugins/specfuse/skills/draft-feature/SKILL.md .specfuse/skills/draft-feature/SKILL.md && cmp docs/methodology.md specfuse/loop/data/docs/methodology.md && cmp docs/concepts/autonomy-stop-classes.md specfuse/loop/data/docs/concepts/autonomy-stop-classes.md
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/concepts/autonomy-stop-classes.md, specfuse/loop/data/docs/concepts/autonomy-stop-classes.md, tests/test_judge_editing_terminal_docs.py, tests/test_terminal_judge_editing_end_to_end.py

### T04#3

- **criterion:** `grep -rn "the only checkpoint the change gets" docs plugins .specfuse/skills specfuse/loop/data`
- **oracle:** ! grep -rn "the only checkpoint the change gets" docs plugins .specfuse/skills specfuse/loop/data
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/concepts/autonomy-stop-classes.md, specfuse/loop/data/docs/concepts/autonomy-stop-classes.md, tests/test_judge_editing_terminal_docs.py, tests/test_terminal_judge_editing_end_to_end.py

### T05#1

- **criterion:** The new regression test fails on the current tree and passes after the fix.
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end.PatchRestoresOriginals -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py

### T05#2

- **criterion:** `python3 -m unittest tests.test_terminal_judge_editing_end_to_end.EveryAutonomyLevelStops tests.test_verify_empty_gate_set tests.test_timeout_kill_portable tests.test_tiered_verification_e2e -b`
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end.EveryAutonomyLevelStops tests.test_verify_empty_gate_set tests.test_timeout_kill_portable tests.test_tiered_verification_e2e -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py

### T05#3

- **criterion:** `python3 -m unittest tests.test_terminal_judge_editing_end_to_end -v -b` (the
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end -v -b && ! grep -nE 'unittest\.skip|@skip|skipTest' tests/test_terminal_judge_editing_end_to_end.py
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py

### T06#1

- **criterion:** `tests/test_arm_eval_terminal.py`: the keys for a fixture with a judge-path
- **oracle:** python3 -m unittest tests.test_arm_eval_terminal -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py

### T06#2

- **criterion:** `tests/test_terminal_judge_editing_end_to_end.py`: the halt message for a
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end.BriefShowsThePasteReadyAcknowledgement -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py

### T06#3

- **criterion:** The `feature_oracle` and `tests.test_lifecycle_integration` still pass.
- **oracle:** python3 -m unittest tests.test_terminal_judge_editing_end_to_end tests.test_lifecycle_integration -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `4d501615eb0e284b3a953ee90cbf90a4b7541767`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py
