### T01#1

- **criterion:** `tests/test_ids.py` and the oracle's clause-1/2/8 classes fail on HEAD (the module
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#2

- **criterion:** `tests/test_ids.py` parses every directory name under `.specfuse/features/` and every
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#3

- **criterion:** A malformed `ids.key` (`acme`, `A`, `TOOLONG1`, `1ABC`) is an ERROR from
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#4

- **criterion:** `python3 -m unittest tests.test_lint_plan_errors tests.test_lint_roadmap tests.test_layout tests.test_layout_validation tests.test_layout_no_layout_goldens -b`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T01#5

- **criterion:** `grep -nF 'FEAT-\d{4}-\d{4}' specfuse/loop/lint_plan.py specfuse/loop/lint_roadmap.py`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/layout.py, specfuse/loop/lint_plan.py, specfuse/loop/lint_roadmap.py, tests/test_ids.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#1

- **criterion:** `tests/test_ids_call_sites.py` drives each site with a keyed ID and fails on the T01
- **state:** `unverified`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#2

- **criterion:** The partial-lookup test resolves `0008` to `FEAT-ACME-2026-0008-x` and to
- **state:** `unverified`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#3

- **criterion:** `grep -rnF 'FEAT-\d{4}-\d{4}' specfuse/` returns only `specfuse/loop/ids.py`.
- **state:** `unverified`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T02#4

- **criterion:** `python3 -m unittest tests.test_lifecycle_integration tests.test_agent_policy_schema -b`
- **state:** `unverified`
- **covers:** specfuse/loop/agent_policy.py, specfuse/loop/changelog.py, specfuse/loop/gh_features.py, specfuse/loop/promotion.py, specfuse/loop/upgrade_merge_gate.py, specfuse/loop/gate_eval.py, specfuse/loop/loop.py, tests/test_ids_call_sites.py, tests/test_keyed_feature_ids_end_to_end.py

### T03#1

- **criterion:** `tests/test_roadmap_add_skill.py`: its `FEAT_RE`, `FEAT_ROW_RE` and `PLAN_FEAT_RE`
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/roadmap-add/SKILL.md, plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, tests/test_roadmap_add_skill.py, tests/test_keyed_feature_ids_end_to_end.py

### T03#2

- **criterion:** `python3 -m unittest tests.test_skills_vendored_in_sync -b` passes after the sync.
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/roadmap-add/SKILL.md, plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, tests/test_roadmap_add_skill.py, tests/test_keyed_feature_ids_end_to_end.py

### T03#3

- **criterion:** The skill still states the #771/#1872 rules (source (c) advisory, implausible source
- **state:** `unverified`
- **covers:** plugins/specfuse/skills/roadmap-add/SKILL.md, plugins/specfuse/skills/draft-feature/SKILL.md, .specfuse/skills/roadmap-add/SKILL.md, .specfuse/skills/draft-feature/SKILL.md, tests/test_roadmap_add_skill.py, tests/test_keyed_feature_ids_end_to_end.py

### T04#1

- **criterion:** `tests/test_lint_roadmap_unkeyed_rows.py`: fires on an unkeyed `planned` row with a
- **state:** `unverified`
- **covers:** specfuse/loop/lint_roadmap.py, tests/test_lint_roadmap_unkeyed_rows.py, tests/test_keyed_feature_ids_end_to_end.py

### T04#2

- **criterion:** `lint_roadmap` over this repository (no key) reports no new finding.
- **state:** `unverified`
- **covers:** specfuse/loop/lint_roadmap.py, tests/test_lint_roadmap_unkeyed_rows.py, tests/test_keyed_feature_ids_end_to_end.py

### T05#1

- **criterion:** `tests/test_ids_migrate.py`: dry run writes nothing and lists candidates and skips;
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate.py, tests/test_keyed_feature_ids_end_to_end.py

### T05#2

- **criterion:** Running `--apply` twice is idempotent (second run finds no candidates).
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate.py, tests/test_keyed_feature_ids_end_to_end.py

### T05#3

- **criterion:** The command never touches `.specfuse/features/`, `events.jsonl`, `CHANGELOG.md` or
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate.py, tests/test_keyed_feature_ids_end_to_end.py

### T06#1

- **criterion:** `tests/test_keyed_feature_ids_docs.py` asserts each surface above names `ids.key`,
- **state:** `unverified`
- **covers:** docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/glossary.md, specfuse/loop/data/docs/glossary.md, docs/getting-started.md, .specfuse/roadmap.template.md, specfuse/loop/data/roadmap.template.md, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_keyed_feature_ids_docs.py

### T06#2

- **criterion:** `python3 -m unittest tests.test_scaffold_data_in_sync tests.test_skills_vendored_in_sync -b`
- **state:** `unverified`
- **covers:** docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/glossary.md, specfuse/loop/data/docs/glossary.md, docs/getting-started.md, .specfuse/roadmap.template.md, specfuse/loop/data/roadmap.template.md, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_keyed_feature_ids_docs.py

### T06#3

- **criterion:** No doc claims a prompt asks for the key (none does).
- **state:** `unverified`
- **covers:** docs/methodology.md, specfuse/loop/data/docs/methodology.md, docs/glossary.md, specfuse/loop/data/docs/glossary.md, docs/getting-started.md, .specfuse/roadmap.template.md, specfuse/loop/data/roadmap.template.md, specfuse/loop/data/schemas/driver-event.schema.json, tests/test_keyed_feature_ids_docs.py

### T07#1

- **criterion:** A methodology-core PR with the changes above is merged (record its URL in
- **state:** `unverified`

### T07#2

- **criterion:** `bash scripts/sync-scaffold.sh` vendors them into `.specfuse/` and
- **state:** `unverified`

### T07#3

- **criterion:** The oracle's clause-7 class is un-skipped and passes: a keyed correlation ID
- **state:** `unverified`

### T07#4

- **criterion:** `python3 -m unittest tests.test_validate_event tests.test_scaffold_data_in_sync -b`
- **state:** `unverified`

### T08#1

- **criterion:** `tests/test_ids_migrate_all.py`, in a temporary git repository with two features,
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_keyed_feature_ids_end_to_end.py

### T08#2

- **criterion:** `--planned-only` behaves exactly as after T05 (`tests.test_ids_migrate` unchanged
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, tests/test_ids_migrate_all.py, tests/test_keyed_feature_ids_end_to_end.py

### T09#1

- **criterion:** `tests/test_ids_aliases.py`: with an alias map, each of the three sites resolves the
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/loop.py, specfuse/loop/gate_eval.py, specfuse/loop/gh_features.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_ids_aliases.py, tests/test_keyed_feature_ids_end_to_end.py

### T09#2

- **criterion:** `python3 -m unittest tests.test_lifecycle_integration tests.test_keyed_feature_ids_docs tests.test_scaffold_data_in_sync -b`
- **state:** `unverified`
- **covers:** specfuse/loop/ids.py, specfuse/loop/loop.py, specfuse/loop/gate_eval.py, specfuse/loop/gh_features.py, docs/methodology.md, specfuse/loop/data/docs/methodology.md, tests/test_ids_aliases.py, tests/test_keyed_feature_ids_end_to_end.py

### T10#1

- **criterion:** `python3 -m unittest tests.test_judge_path_registry tests.test_caller_check_ratchet tests.test_layout_no_layout_goldens -b`
- **state:** `unverified`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/ids.py, tests/test_layout_no_layout_goldens.py, tests/test_ids.py

### T10#2

- **criterion:** `python3 -m unittest tests.test_ids tests.test_ids_migrate tests.test_ids_migrate_all tests.test_keyed_feature_ids_end_to_end -b`
- **state:** `unverified`
- **covers:** specfuse/loop/arm_eval.py, specfuse/loop/ids.py, tests/test_layout_no_layout_goldens.py, tests/test_ids.py
