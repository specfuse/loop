### T01#1

- **criterion:** `tests/test_terminal_judge_editing_end_to_end.py::FiresOnSingleGateJudgeEdit` fails
- **state:** `unverified`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T01#2

- **criterion:** `tests/test_arm_eval_terminal.py` covers: a judge-module path fires; a universal
- **state:** `unverified`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T01#3

- **criterion:** `python3 -m unittest tests.test_arm_eval tests.test_arm_eval_wiring
- **state:** `unverified`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T01#4

- **criterion:** A schema check accepts the new `terminal_judge_editing_evaluated` event (the
- **state:** `unverified`
- **covers:** tests/test_terminal_judge_editing_end_to_end.py, tests/test_arm_eval_terminal.py, specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/data/schemas/driver-event.schema.json

### T02#1

- **criterion:** `tests/test_terminal_judge_editing_end_to_end.py::AcknowledgedStopProceeds` and
- **state:** `unverified`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T02#2

- **criterion:** `tests/test_arm_eval_terminal.py` adds: full coverage → clean; partial coverage →
- **state:** `unverified`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T02#3

- **criterion:** `tests/test_lint_judge_edit_acknowledged.py` covers: valid field passes; missing
- **state:** `unverified`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T02#4

- **criterion:** `specfuse lint .specfuse/features/FEAT-2026-0246-judge-editing-terminal-gate`
- **state:** `unverified`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/loop.py, specfuse/loop/lint_plan.py, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_arm_eval_terminal.py, tests/test_terminal_judge_editing_end_to_end.py, tests/test_lint_judge_edit_acknowledged.py

### T03#1

- **criterion:** The three oracle classes fail once un-skipped on the T01/T02 tree (no brief text;
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_terminal_judge_editing_end_to_end.py

### T03#2

- **criterion:** `grep -rn "judge_editing_terminal" specfuse/loop/loop.py` shows the reason used at
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_terminal_judge_editing_end_to_end.py

### T03#3

- **criterion:** `python3 -m unittest tests.test_lifecycle_integration -b` passes.
- **state:** `unverified`
- **covers:** specfuse/loop/loop.py, tests/test_terminal_judge_editing_end_to_end.py

### T04#1

- **criterion:** `tests/test_judge_editing_terminal_docs.py` with the new assertions fails on HEAD's
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/concepts/autonomy-stop-classes.md, specfuse/loop/data/docs/concepts/autonomy-stop-classes.md, tests/test_judge_editing_terminal_docs.py, tests/test_terminal_judge_editing_end_to_end.py

### T04#2

- **criterion:** Each pair of copies is byte-identical:
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/concepts/autonomy-stop-classes.md, specfuse/loop/data/docs/concepts/autonomy-stop-classes.md, tests/test_judge_editing_terminal_docs.py, tests/test_terminal_judge_editing_end_to_end.py

### T04#3

- **criterion:** `grep -rn "the only checkpoint the change gets" docs plugins .specfuse/skills specfuse/loop/data`
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/concepts/autonomy-stop-classes.md, specfuse/loop/data/docs/concepts/autonomy-stop-classes.md, tests/test_judge_editing_terminal_docs.py, tests/test_terminal_judge_editing_end_to_end.py
