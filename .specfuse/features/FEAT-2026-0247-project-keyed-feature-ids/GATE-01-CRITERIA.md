### T01#1

- **criterion:** `tests/test_ids.py` and the oracle's clause-1/2/8 classes fail on HEAD (the module
- **oracle:** python3 -m unittest tests.test_ids tests.test_keyed_feature_ids_end_to_end.Clause1AllocationContinuesLegacyNumbering tests.test_keyed_feature_ids_end_to_end.Clause2KeyedFeatureLints tests.test_keyed_feature_ids_end_to_end.Clause8UnkeyedRepoIsUnchanged -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#2

- **criterion:** `tests/test_ids.py` parses every directory name under `.specfuse/features/` and every
- **oracle:** python3 -m unittest tests.test_ids.RealCorpus -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#3

- **criterion:** A malformed `ids.key` (`acme`, `A`, `TOOLONG1`, `1ABC`) is an ERROR from
- **oracle:** python3 -m unittest tests.test_ids tests.test_layout_validation -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#4

- **criterion:** `python3 -m unittest tests.test_lint_plan_errors tests.test_lint_roadmap tests.test_layout tests.test_layout_validation tests.test_layout_no_layout_goldens -b`
- **oracle:** python3 -m unittest tests.test_lint_plan_errors tests.test_lint_roadmap tests.test_layout tests.test_layout_validation tests.test_layout_no_layout_goldens -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#5

- **criterion:** `grep -nF 'FEAT-\d{4}-\d{4}' specfuse/loop/lint_plan.py specfuse/loop/lint_roadmap.py`
- **oracle:** sh -c '! grep -nF 'FEAT-\d{4}-\d{4}' specfuse/loop/lint_plan.py specfuse/loop/lint_roadmap.py'
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#1

- **criterion:** `tests/test_ids_call_sites.py` drives each site with a keyed ID and fails on the T01
- **oracle:** python3 -m unittest tests.test_ids_call_sites -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#2

- **criterion:** The partial-lookup test resolves `0008` to `FEAT-ACME-2026-0008-x` and to
- **oracle:** python3 -m unittest tests.test_ids_call_sites.PartialLookup -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#3

- **criterion:** `grep -rnF 'FEAT-\d{4}-\d{4}' specfuse/` returns only `specfuse/loop/ids.py`.
- **oracle:** sh -c '! grep -rnF 'FEAT-\d{4}-\d{4}' specfuse/ | grep -v "^specfuse/loop/ids.py:"'
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#4

- **criterion:** `python3 -m unittest tests.test_lifecycle_integration tests.test_agent_policy_schema -b`
- **oracle:** python3 -m unittest tests.test_lifecycle_integration tests.test_agent_policy_schema -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T03#1

- **criterion:** `tests/test_roadmap_add_skill.py`: its `FEAT_RE`, `FEAT_ROW_RE` and `PLAN_FEAT_RE`
- **oracle:** python3 -m unittest tests.test_roadmap_add_skill tests.test_keyed_feature_ids_end_to_end.Clause4SkillsAllocateThroughIdsNext -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/roadmap-add/SKILL.md, plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, tests/test_roadmap_add_skill.py, tests/test_keyed_feature_ids_end_to_end.py

### T03#2

- **criterion:** `python3 -m unittest tests.test_skills_vendored_in_sync -b` passes after the sync.
- **oracle:** python3 -m unittest tests.test_skills_vendored_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/roadmap-add/SKILL.md, plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, tests/test_roadmap_add_skill.py, tests/test_keyed_feature_ids_end_to_end.py

### T03#3

- **criterion:** The skill still states the #771/#1872 rules (source (c) advisory, implausible source
- **oracle:** sh -c 'grep -c -E "#771|#1872" .specfuse/skills/roadmap-add/SKILL.md | grep -qv "^0$" && grep -q "source (d)" .specfuse/skills/roadmap-add/SKILL.md'
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** plugins/specfuse/skills/roadmap-add/SKILL.md, plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, tests/test_roadmap_add_skill.py, tests/test_keyed_feature_ids_end_to_end.py

### T04#1

- **criterion:** `tests/test_lint_roadmap_unkeyed_rows.py`: fires on an unkeyed `planned` row with a
- **oracle:** python3 -m unittest tests.test_lint_roadmap_unkeyed_rows -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/lint_roadmap.py, tests/test_lint_roadmap_unkeyed_rows.py, tests/test_keyed_feature_ids_end_to_end.py

### T04#2

- **criterion:** `lint_roadmap` over this repository (no key) reports no new finding.
- **oracle:** python3 -c "from pathlib import Path; from specfuse.loop import lint_roadmap as l; f=l.lint_roadmap(Path('.')); [print(x) for x in f]; import sys; sys.exit(1 if any(getattr(x,'severity','')=='error' for x in f) else 0)"
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/lint_roadmap.py, tests/test_lint_roadmap_unkeyed_rows.py, tests/test_keyed_feature_ids_end_to_end.py

### T05#1

- **criterion:** `tests/test_ids_migrate.py`: dry run writes nothing and lists candidates and skips;
- **oracle:** python3 -m unittest tests.test_ids_migrate -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate.py, tests/test_keyed_feature_ids_end_to_end.py

### T05#2

- **criterion:** Running `--apply` twice is idempotent (second run finds no candidates).
- **oracle:** python3 -m unittest tests.test_ids_migrate.Migrate.test_apply_is_idempotent -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate.py, tests/test_keyed_feature_ids_end_to_end.py

### T05#3

- **criterion:** The command never touches `.specfuse/features/`, `events.jsonl`, `CHANGELOG.md` or
- **oracle:** python3 -m unittest tests.test_ids_migrate.Migrate.test_archive_rewritten_and_features_untouched -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate.py, tests/test_keyed_feature_ids_end_to_end.py

### T06#1

- **criterion:** `tests/test_keyed_feature_ids_docs.py` asserts each surface above names `ids.key`,
- **oracle:** python3 -m unittest tests.test_keyed_feature_ids_docs -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/glossary.md, specfuse/loop/data/docs/glossary.md, docs/getting-started.md, .specfuse/roadmap.template.md, specfuse/loop/data/roadmap.template.md, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_keyed_feature_ids_docs.py

### T06#2

- **criterion:** `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b`
- **oracle:** python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/glossary.md, specfuse/loop/data/docs/glossary.md, docs/getting-started.md, .specfuse/roadmap.template.md, specfuse/loop/data/roadmap.template.md, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_keyed_feature_ids_docs.py

### T06#3

- **criterion:** No doc claims a prompt asks for the key (none does).
- **oracle:** sh -c '! grep -rniE "(prompt|asks?)[^.]*(for|you for) the (project )?key" docs/methodology.md docs/getting-started.md docs/glossary.md .specfuse/skills/roadmap-add/SKILL.md .specfuse/skills/draft-feature/SKILL.md | grep -vi "no prompt"'
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/glossary.md, specfuse/loop/data/docs/glossary.md, docs/getting-started.md, .specfuse/roadmap.template.md, specfuse/loop/data/roadmap.template.md, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_keyed_feature_ids_docs.py

### T07#1

- **criterion:** A methodology-core PR with the changes above is merged (record its URL in
- **oracle:** sh -c 'grep -q "specfuse/specfuse/pull/232" .specfuse/features/FEAT-2026-0247-project-keyed-feature-ids/WU-07-core-grammar-and-schemas.md'
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`

### T07#2

- **criterion:** `bash scripts/sync-scaffold.sh` vendors them into `.specfuse/` and
- **oracle:** python3 -m unittest tests.test_scaffold_data_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`

### T07#3

- **criterion:** The oracle's clause-7 class is un-skipped and passes: a keyed correlation ID
- **oracle:** python3 -m unittest tests.test_keyed_feature_ids_end_to_end.Clause7KeyedCorrelationIdValidatesAgainstEnvelope -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`

### T07#4

- **criterion:** `python3 -m unittest tests.test_validate_event tests.test_scaffold_data_in_sync -b`
- **oracle:** python3 -m unittest tests.test_validate_event tests.test_scaffold_data_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`

### T08#1

- **criterion:** `tests/test_ids_migrate_all.py`, in a temporary git repository with two features,
- **oracle:** python3 -m unittest tests.test_ids_migrate_all -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_keyed_feature_ids_end_to_end.py

### T08#2

- **criterion:** `--planned-only` behaves exactly as after T05 (`tests.test_ids_migrate` unchanged
- **oracle:** python3 -m unittest tests.test_ids_migrate -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_keyed_feature_ids_end_to_end.py

### T09#1

- **criterion:** `tests/test_ids_aliases.py`: with an alias map, each of the three sites resolves the
- **oracle:** python3 -m unittest tests.test_ids_aliases -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/loop.py, specfuse/loop/gate_eval.py, specfuse/loop/gh_features.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_ids_aliases.py, tests/test_keyed_feature_ids_end_to_end.py

### T09#2

- **criterion:** `python3 -m unittest tests.test_lifecycle_integration tests.test_keyed_feature_ids_docs tests.test_scaffold_data_in_sync -b`
- **oracle:** python3 -m unittest tests.test_lifecycle_integration tests.test_keyed_feature_ids_docs tests.test_scaffold_data_in_sync -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/ids.py, specfuse/loop/loop.py, specfuse/loop/gate_eval.py, specfuse/loop/gh_features.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_ids_aliases.py, tests/test_keyed_feature_ids_end_to_end.py

### T10#1

- **criterion:** `python3 -m unittest tests.test_judge_path_registry tests.test_caller_check_ratchet tests.test_layout_no_layout_goldens -b`
- **oracle:** python3 -m unittest tests.test_judge_path_registry tests.test_caller_check_ratchet tests.test_layout_no_layout_goldens -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/ids.py, tests/test_layout_no_layout_goldens.py, tests/test_ids.py

### T10#2

- **criterion:** `python3 -m unittest tests.test_ids tests.test_ids_migrate tests.test_ids_migrate_all tests.test_keyed_feature_ids_end_to_end -b`
- **oracle:** python3 -m unittest tests.test_ids tests.test_ids_migrate tests.test_ids_migrate_all tests.test_keyed_feature_ids_end_to_end -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `d3ff271dff0c08260df61cf09fb43f7997b44d2e`
- **attempt:** `1`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/ids.py, tests/test_layout_no_layout_goldens.py, tests/test_ids.py
