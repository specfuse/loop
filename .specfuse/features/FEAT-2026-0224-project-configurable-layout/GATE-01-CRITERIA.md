### T01#1

- **criterion:** `tests/test_layout_end_to_end.py::NoLayoutGetIsToday` and `::EntriesLayoutGet`
- **oracle:** python3 -m unittest tests.test_layout_end_to_end.NoLayoutGetIsToday tests.test_layout_end_to_end.EntriesLayoutGet -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_end_to_end.py, tests/test_layout.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py

### T01#2

- **criterion:** `tests/test_layout.py` covers: file absent; file present with no `decisions:`
- **oracle:** python3 -m unittest tests.test_layout -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_end_to_end.py, tests/test_layout.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py

### T01#3

- **criterion:** `python3 -m unittest tests.test_judge_path_registry -b` passes with `layout.py`
- **oracle:** python3 -m unittest tests.test_judge_path_registry -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_end_to_end.py, tests/test_layout.py, specfuse/loop/layout.py, specfuse/loop/arm_eval.py

### T02#1

- **criterion:** `tests/test_layout_validation.py` (every case above) and
- **oracle:** python3 -m unittest tests.test_layout_validation tests.test_layout_end_to_end -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_validation.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T02#2

- **criterion:** Each rejected form has exactly one test whose name states it (e.g.
- **oracle:** python3 -m unittest tests.test_layout_validation -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_validation.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T02#3

- **criterion:** `tests.test_layout` still passes, and `load()` on every invalid fixture returns a
- **oracle:** python3 -m unittest tests.test_layout tests.test_layout_validation -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_validation.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T03#1

- **criterion:** `tests/test_layout_link.py` and
- **oracle:** python3 -m unittest tests.test_layout_link tests.test_layout_end_to_end -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_link.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T03#2

- **criterion:** The no-layout ADR case is asserted against the literal string from
- **oracle:** python3 -m unittest tests.test_layout_link.RenderLink.test_no_layout_adr_matches_skill_example -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_link.py, tests/test_layout_end_to_end.py, specfuse/loop/layout.py

### T04#1

- **criterion:** `tests/test_layout_no_layout_goldens.py` passes on this unit's tree, and
- **oracle:** python3 -m unittest tests.test_layout_no_layout_goldens -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T04#2

- **criterion:** Positive control: `GOLDEN_LINT["blocked_dangling"]` contains at least one ERROR
- **oracle:** python3 -m unittest tests.test_layout_no_layout_goldens -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T05#1

- **criterion:** Each case above is a named test in `tests/test_lint_roadmap.py`; the missing-anchor,
- **oracle:** python3 -m unittest tests.test_lint_roadmap -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_lint_roadmap.py, tests/test_layout_end_to_end.py, specfuse/loop/lint_roadmap.py

### T05#2

- **criterion:** `tests/test_layout_no_layout_goldens.py` passes **unchanged**: this unit does not
- **oracle:** python3 -m unittest tests.test_layout_no_layout_goldens -b; git diff b784c60 HEAD -- tests/test_layout_no_layout_goldens.py | grep -c '^-[^-]'
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_lint_roadmap.py, tests/test_layout_end_to_end.py, specfuse/loop/lint_roadmap.py

### T05#3

- **criterion:** `tests/test_layout_end_to_end.py::LintChecksDecisionLinks` passes.
- **oracle:** python3 -m unittest tests.test_layout_end_to_end.LintChecksDecisionLinks -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** tests/test_lint_roadmap.py, tests/test_layout_end_to_end.py, specfuse/loop/lint_roadmap.py

### T06#1

- **criterion:** `tests/test_block_feature_layout.py` fails on HEAD (no such command in the skill)
- **oracle:** python3 -m unittest tests.test_block_feature_layout -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/block-feature/SKILL.md, .specfuse/skills/block-feature/SKILL.md, tests/test_block_feature_layout.py

### T06#2

- **criterion:** `python3 -m unittest tests.test_skills_vendored_in_sync -b` passes.
- **oracle:** python3 -m unittest tests.test_skills_vendored_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/block-feature/SKILL.md, .specfuse/skills/block-feature/SKILL.md, tests/test_block_feature_layout.py

### T07#1

- **criterion:** `tests/test_layout_end_to_end.py::TemplateFollowsStyle` fails on HEAD and passes
- **oracle:** python3 -m unittest tests.test_layout_end_to_end.TemplateFollowsStyle -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** specfuse/loop/data/roadmap.template.md, .specfuse/roadmap.template.md, specfuse/loop/scaffold.py, specfuse/loop/layout.py, plugins/specfuse/skills/attention/SKILL.md, .specfuse/skills/attention/SKILL.md, plugins/specfuse/skills/gate-status/SKILL.md, .specfuse/skills/gate-status/SKILL.md, plugins/specfuse/skills/groom-backlog/SKILL.md, .specfuse/skills/groom-backlog/SKILL.md, plugins/specfuse/skills/pick-feature/SKILL.md, .specfuse/skills/pick-feature/SKILL.md, plugins/specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, docs/methodology.md, docs/skills.md, tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T07#2

- **criterion:** `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b`
- **oracle:** python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** specfuse/loop/data/roadmap.template.md, .specfuse/roadmap.template.md, specfuse/loop/scaffold.py, specfuse/loop/layout.py, plugins/specfuse/skills/attention/SKILL.md, .specfuse/skills/attention/SKILL.md, plugins/specfuse/skills/gate-status/SKILL.md, .specfuse/skills/gate-status/SKILL.md, plugins/specfuse/skills/groom-backlog/SKILL.md, .specfuse/skills/groom-backlog/SKILL.md, plugins/specfuse/skills/pick-feature/SKILL.md, .specfuse/skills/pick-feature/SKILL.md, plugins/specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, docs/methodology.md, docs/skills.md, tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py

### T07#3

- **criterion:** `grep -rn "an ADR" plugins/specfuse/skills/{attention,gate-status,groom-backlog,pick-feature,roadmap-add}/SKILL.md docs/methodology.md docs/skills.md`
- **oracle:** grep -rn "an ADR" plugins/specfuse/skills/{attention,gate-status,groom-backlog,pick-feature,roadmap-add}/SKILL.md docs/methodology.md docs/skills.md (no output)
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `03c0f2a0f6a7123868da25e1ba22ccbfbd5cd2e1`
- **attempt:** `1`
- **covers:** specfuse/loop/data/roadmap.template.md, .specfuse/roadmap.template.md, specfuse/loop/scaffold.py, specfuse/loop/layout.py, plugins/specfuse/skills/attention/SKILL.md, .specfuse/skills/attention/SKILL.md, plugins/specfuse/skills/gate-status/SKILL.md, .specfuse/skills/gate-status/SKILL.md, plugins/specfuse/skills/groom-backlog/SKILL.md, .specfuse/skills/groom-backlog/SKILL.md, plugins/specfuse/skills/pick-feature/SKILL.md, .specfuse/skills/pick-feature/SKILL.md, plugins/specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, docs/methodology.md, docs/skills.md, tests/test_layout_no_layout_goldens.py, tests/test_layout_end_to_end.py
