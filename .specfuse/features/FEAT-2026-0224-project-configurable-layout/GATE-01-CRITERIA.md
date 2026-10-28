### T01#1

- **criterion:** `tests/test_layout_end_to_end.py::NoLayoutGetIsToday` and `::EntriesLayoutGet`
- **state:** `unverified`
- **covers:** tests/test_layout_end_to_end.py, tests/test_layout.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py

### T01#2

- **criterion:** `tests/test_layout.py` covers: file absent; file present with no `decisions:`
- **state:** `unverified`
- **covers:** tests/test_layout_end_to_end.py, tests/test_layout.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py

### T01#3

- **criterion:** `python3 -m unittest tests.test_judge_path_registry -b` passes with `layout.py`
- **state:** `unverified`
- **covers:** tests/test_layout_end_to_end.py, tests/test_layout.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py

### T02#1

- **criterion:** `tests/test_layout_validation.py` (every case above) and
- **state:** `unverified`
- **covers:** tests/test_layout_validation.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T02#2

- **criterion:** Each rejected form has exactly one test whose name states it (e.g.
- **state:** `unverified`
- **covers:** tests/test_layout_validation.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T02#3

- **criterion:** `tests.test_layout` still passes, and `load()` on every invalid fixture returns a
- **state:** `unverified`
- **covers:** tests/test_layout_validation.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T03#1

- **criterion:** `tests/test_layout_link.py` and
- **state:** `unverified`
- **covers:** tests/test_layout_link.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T03#2

- **criterion:** The no-layout ADR case is asserted against the literal string from
- **state:** `unverified`
- **covers:** tests/test_layout_link.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T04#1

- **criterion:** `tests/test_layout_no_layout_goldens.py` passes on this unit's tree, and
- **state:** `unverified`
- **covers:** tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T04#2

- **criterion:** Positive control: `GOLDEN_LINT["blocked_dangling"]` contains at least one ERROR
- **state:** `unverified`
- **covers:** tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T05#1

- **criterion:** Each case above is a named test in `tests/test_lint_roadmap.py`; the missing-anchor,
- **state:** `unverified`
- **covers:** tests/test_lint_roadmap.py, tests/test_layout_end_to_end.py, specfuse/loop/lint_roadmap.py

### T05#2

- **criterion:** `tests/test_layout_no_layout_goldens.py` passes **unchanged**: this unit does not
- **state:** `unverified`
- **covers:** tests/test_lint_roadmap.py, tests/test_layout_end_to_end.py, specfuse/loop/lint_roadmap.py

### T05#3

- **criterion:** `tests/test_layout_end_to_end.py::LintChecksDecisionLinks` passes.
- **state:** `unverified`
- **covers:** tests/test_lint_roadmap.py, tests/test_layout_end_to_end.py, specfuse/loop/lint_roadmap.py

### T06#1

- **criterion:** `tests/test_block_feature_layout.py` fails on HEAD (no such command in the skill)
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/block-feature/SKILL.md, .specfuse/skills/block-feature/SKILL.md, tests/test_block_feature_layout.py

### T06#2

- **criterion:** `python3 -m unittest tests.test_skills_vendored_in_sync -b` passes.
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/block-feature/SKILL.md, .specfuse/skills/block-feature/SKILL.md, tests/test_block_feature_layout.py

### T07#1

- **criterion:** `tests/test_layout_end_to_end.py::TemplateFollowsStyle` fails on HEAD and passes
- **state:** `unverified`
- **covers:** specfuse/loop/data/roadmap.template.md, .specfuse/roadmap.template.md, specfuse/loop/scaffold.py, specfuse/loop/layout.py, plugins/specfuse/skills/attention/SKILL.md, .specfuse/skills/attention/SKILL.md, plugins/specfuse/skills/gate-status/SKILL.md, .specfuse/skills/gate-status/SKILL.md, plugins/specfuse/skills/groom-backlog/SKILL.md, .specfuse/skills/groom-backlog/SKILL.md, plugins/specfuse/skills/pick-feature/SKILL.md, .specfuse/skills/pick-feature/SKILL.md, plugins/specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, docs/methodology.md, docs/skills.md, tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T07#2

- **criterion:** `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b`
- **state:** `unverified`
- **covers:** specfuse/loop/data/roadmap.template.md, .specfuse/roadmap.template.md, specfuse/loop/scaffold.py, specfuse/loop/layout.py, plugins/specfuse/skills/attention/SKILL.md, .specfuse/skills/attention/SKILL.md, plugins/specfuse/skills/gate-status/SKILL.md, .specfuse/skills/gate-status/SKILL.md, plugins/specfuse/skills/groom-backlog/SKILL.md, .specfuse/skills/groom-backlog/SKILL.md, plugins/specfuse/skills/pick-feature/SKILL.md, .specfuse/skills/pick-feature/SKILL.md, plugins/specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, docs/methodology.md, docs/skills.md, tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T07#3

- **criterion:** `grep -rn "an ADR" plugins/specfuse/skills/{attention,gate-status,groom-backlog,pick-feature,roadmap-add}/SKILL.md docs/methodology.md docs/skills.md`
- **state:** `unverified`
- **covers:** specfuse/loop/data/roadmap.template.md, .specfuse/roadmap.template.md, specfuse/loop/scaffold.py, specfuse/loop/layout.py, plugins/specfuse/skills/attention/SKILL.md, .specfuse/skills/attention/SKILL.md, plugins/specfuse/skills/gate-status/SKILL.md, .specfuse/skills/gate-status/SKILL.md, plugins/specfuse/skills/groom-backlog/SKILL.md, .specfuse/skills/groom-backlog/SKILL.md, plugins/specfuse/skills/pick-feature/SKILL.md, .specfuse/skills/pick-feature/SKILL.md, plugins/specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, docs/methodology.md, docs/skills.md, tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py
