### tests: FAIL
```
$ python3 -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_specfuse_tree_complete (test_init_integration.TestInitFullLayout.test_specfuse_tree_complete)
Traceback (most recent call last):
AssertionError: Items in the first set but not the second:
FAIL: test_no_module_is_unclassified (test_judge_path_registry.TestEveryModuleIsClassified.test_no_module_is_unclassified)
Traceback (most recent call last):
AssertionError: Items in the first set but not the second:
FAIL: test_init_writes_full_tree (test_scaffold_init.TestScaffoldInitWritesTree.test_init_writes_full_tree)
Traceback (most recent call last):
AssertionError: Items in the first set but not the second:
... (4163 line(s) elided) ...

======================================================================
FAIL: test_iter_scaffold_files_lists_all_seed (test_scaffold_resources.TestScaffoldResources.test_iter_scaffold_files_lists_all_seed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christian/Specfuse/loop/tests/test_scaffold_resources.py", line 60, in test_iter_scaffold_files_lists_all_seed
    self.assertEqual(relpaths, _EXPECTED_RELPATHS)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Items in the first set but not the second:
'templates/DECISIONS.template.md'

----------------------------------------------------------------------
Ran 3447 tests in 129.800s

FAILED (failures=4, skipped=1)
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
```

### security: PASS
```
$ bandit -r specfuse .specfuse/scripts -ll
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 7

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 113
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 113
Files skipped (0):
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### coverage: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
AssertionError: Items in the first set but not the second:
FAIL: test_no_module_is_unclassified (test_judge_path_registry.TestEveryModuleIsClassified.test_no_module_is_unclassified)
Traceback (most recent call last):
AssertionError: Items in the first set but not the second:
FAIL: test_init_writes_full_tree (test_scaffold_init.TestScaffoldInitWritesTree.test_init_writes_full_tree)
Traceback (most recent call last):
AssertionError: Items in the first set but not the second:
FAIL: test_iter_scaffold_files_lists_all_seed (test_scaffold_resources.TestScaffoldResources.test_iter_scaffold_files_lists_all_seed)
Traceback (most recent call last):
AssertionError: Items in the first set but not the second:
Ran 3447 tests in 132.611s
FAILED (failures=4, skipped=1)
   POST-PASS INVARIANT FAILED — archive_anchor_missing: feat-2026-9500
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
... (2382 line(s) elided) ...
   [13:07:22] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed e17cfb959e826c9085345323f87cbc489d2f12d4

[13:07:23] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [13:07:23] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed d2bbe366b864d1381b5f2221a1562388bc6f5bb7

[13:07:23] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [13:07:23] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed adf5f110725545d59f86b7d31d092f6dcd1dcba3

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: the close recorded verdict `none recorded`, which is neither a pass nor a recognised hedge, so the terminal flips were withheld and there is no follow-up record to accept. A close that records no usable verdict has not finished its job. Inspect RETROSPECTIVE.md / events.jsonl before flipping anything by hand.
```

### leak-scan: PASS
```
$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
WARN: queue: 'FEAT-2026-0050' is roadmap status 'done'
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 63 events.jsonl file(s), 1575 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
WARN: roadmap.md:70: FEAT-2026-0052's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0052)' or '[→ archive](roadmap-archive.md#feat-2026-0052)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 2 warning(s)
```

### arm-sweep-gate: PASS
```
$ python3 .specfuse/scripts/arm_sweep_gate.py
branch-observation table:
  budget_projection          observed=[clean, fired]; NEVER not_evaluable
  judge_editing              observed=[clean, fired]; NEVER not_evaluable
  decision_class_paths       observed=[clean]; NEVER fired, NEVER not_evaluable
  retroactive_edits          observed=[clean, fired]; NEVER not_evaluable
  drift_caps                 observed=[clean, fired]; NEVER not_evaluable
  missing_provenance         observed=[clean, fired]; NEVER not_evaluable
  open_questions_human_only  observed=[clean, fired]; NEVER not_evaluable
  plan_next_lint             observed=[clean]; NEVER fired, NEVER not_evaluable
evaluable=25 evaluated=25 could_not_evaluate=0 excluded_no_baseline=42
ok: 25 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
```

### leak-scan-hook: PASS
```
$ bats tests/leak_scan_hook.bats
1..3
ok 1 hook exits 0 when the scanner is clean
ok 2 hook exits 1 when the scanner reports a leak
ok 3 hook exits 1 when the scanner is missing
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### sync-scaffold-bats: PASS
```
$ bats tests/sync_scaffold.bats
1..9
ok 1 sync copies all canonical files to specfuse/loop/data/
ok 2 sync copies file contents correctly
ok 3 sync is idempotent (second run exits 0 and reports unchanged)
ok 4 sync updates a stale file and reports it
ok 5 sync exits non-zero if canonical source dir is missing
ok 6 vendor records a baseline so a later local edit is detectable
ok 7 core moving forward is a clean fast-forward, not a conflict
ok 8 a local edit to a vendored file halts the sync and names the file
ok 9 the halt does not clobber the local edit
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### sync-scaffold-symlinks-bats: PASS
```
$ bats tests/sync_scaffold_symlinks.bats
1..4
ok 1 sync creates a missing discovery link for a skill with no .claude/skills entry
ok 2 sync leaves an existing discovery link byte-identical
ok 3 sync does not modify or remove an entry resolving outside .specfuse/skills/
ok 4 sync is idempotent for discovery links (second run creates nothing)
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### init-sh-shim-bats: PASS
```
$ bats tests/init_sh_shim.bats
1..5
ok 1 init mode: delegates to 'specfuse init <target>'
ok 2 upgrade mode: delegates to 'specfuse upgrade <target>'
ok 3 upgrade --dry-run: forwards --dry-run flag to specfuse upgrade
ok 4 specfuse absent: exits non-zero with pip install hint
ok 5 no target: exits non-zero with usage
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### init-skills-bats: PASS
```
$ bats tests/init_skills_idempotent.bats
1..1
ok 1 source repo holds skill content in .specfuse (real), not .claude
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### hookspath-conflict-bats: PASS
```
$ bats tests/hookspath_conflict.bats
1..4
ok 1 install-hooks.sh then setup.sh: both hooks active under hooksPath
ok 2 setup.sh then install-hooks.sh: both hooks active under hooksPath
ok 3 install-hooks.sh alone: both hooks active under hooksPath
ok 4 setup.sh alone: both hooks active under hooksPath
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md b/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
index 38c9f06..a6c4a91 100644
--- a/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
+++ b/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0058/T01
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 4.00
 oracle_env: macos_local
 produces:
@@ -10,6 +10,11 @@ produces:
   - specfuse/loop/data/templates/DECISIONS.template.md
   - .specfuse/features/FEAT-2026-0058-decision-registry/DECISIONS.md
   - tests/test_decisions_format.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.13.0
+started_at: 2026-08-20T16:58:47.403592+00:00
 ---
 
 # Define the DECISIONS.md format and fill it for this feature
diff --git a/tests/test_scaffold_data_in_sync.py b/tests/test_scaffold_data_in_sync.py
index 6ebba24..f0ce679 100644
--- a/tests/test_scaffold_data_in_sync.py
+++ b/tests/test_scaffold_data_in_sync.py
@@ -28,6 +28,7 @@ TRACKED = {
     "templates/PLAN.template.md",
     "templates/WU.template.md",
     "templates/LEARNINGS-pending.template.md",
+    "templates/DECISIONS.template.md",
     "rules/close-discipline.md",
     "rules/correlation-ids.md",
     "rules/design-for-diagnosis.md",

```
