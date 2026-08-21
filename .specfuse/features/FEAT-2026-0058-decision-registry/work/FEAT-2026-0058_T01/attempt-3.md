### tests: PASS
```
$ python3 -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
... (4123 line(s) elided) ...
"Restored" alone hides that anything happened. ... ok
test_a_detached_head_start_restores_nothing (test_worktree_restore.TestRestoreRefusesRatherThanRisksWork.test_a_detached_head_start_restores_nothing) ... ok
test_a_dirty_tree_is_not_forced (test_worktree_restore.TestRestoreRefusesRatherThanRisksWork.test_a_dirty_tree_is_not_forced)
A checkout here could discard a dispatched session's work. ... ok
test_a_failed_checkout_is_reported (test_worktree_restore.TestRestoreRefusesRatherThanRisksWork.test_a_failed_checkout_is_reported) ... ok
test_a_raising_git_never_propagates (test_worktree_restore.TestRestoreRefusesRatherThanRisksWork.test_a_raising_git_never_propagates) ... ok
test_an_unreadable_status_is_not_forced_either (test_worktree_restore.TestRestoreRefusesRatherThanRisksWork.test_an_unreadable_status_is_not_forced_either) ... ok
test_author_model_effort_override_is_preserved (test_wu_execution_metadata.TestWUExecutionMetadata.test_author_model_effort_override_is_preserved)
An explicit model/effort override survives the stamp (same value). ... ok
test_dispatch_stamps_model_effort_gateset_driver_started (test_wu_execution_metadata.TestWUExecutionMetadata.test_dispatch_stamps_model_effort_gateset_driver_started) ... ok

----------------------------------------------------------------------
Ran 3449 tests in 137.462s

OK (skipped=1)
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

### coverage: PASS
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
[13:24:56] bug-1 failed after 0s — RuntimeError: boom on bug-1
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
Ran 3449 tests in 138.783s
OK (skipped=1)
   POST-PASS INVARIANT FAILED — archive_anchor_missing: feat-2026-9500
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
... (2434 line(s) elided) ...
specfuse/monitor/autofix_run.py                       78     17    78%
specfuse/monitor/autofix_state.py                     70      0   100%
specfuse/monitor/cli.py                              248      5    98%
specfuse/monitor/diagnose_cli.py                      48      6    88%
specfuse/monitor/diagnosis.py                         80      6    92%
specfuse/monitor/fingerprint.py                       10      0   100%
specfuse/monitor/issues.py                           107      7    93%
specfuse/monitor/providers/__init__.py                 0      0   100%
specfuse/monitor/providers/_azure_auth.py              9      1    89%
specfuse/monitor/providers/azure_app_insights.py     125     13    90%
specfuse/monitor/providers/azure_service_bus.py      117     24    79%
specfuse/monitor/redaction.py                         20      0   100%
specfuse/monitor/schedule.py                         110      5    95%
----------------------------------------------------------------------
TOTAL                                              11191    712    94%
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
ok: no validation errors across 64 events.jsonl file(s), 1578 event(s) checked
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

### sync-scaffold-bats: FAIL
```
$ bats tests/sync_scaffold.bats
# (in test file tests/sync_scaffold.bats, line 92)
#   `[ "$status" -eq 0 ]' failed
ok 5 sync exits non-zero if canonical source dir is missing
not ok 6 vendor records a baseline so a later local edit is detectable
# (in test file tests/sync_scaffold.bats, line 125)
#   `[ "$status" -eq 0 ]' failed
not ok 7 core moving forward is a clean fast-forward, not a conflict
# (in test file tests/sync_scaffold.bats, line 132)
#   `[ "$status" -eq 0 ]' failed
not ok 8 a local edit to a vendored file halts the sync and names the file
# (in test file tests/sync_scaffold.bats, line 143)
#   `[ "$status" -eq 0 ]' failed
not ok 9 the halt does not clobber the local edit
# (in test file tests/sync_scaffold.bats, line 154)
#   `[ "$status" -eq 0 ]' failed
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### sync-scaffold-symlinks-bats: FAIL
```
$ bats tests/sync_scaffold_symlinks.bats
1..4
not ok 1 sync creates a missing discovery link for a skill with no .claude/skills entry
# (in test file tests/sync_scaffold_symlinks.bats, line 72)
#   `[ "$status" -eq 0 ]' failed
not ok 2 sync leaves an existing discovery link byte-identical
# (in test file tests/sync_scaffold_symlinks.bats, line 82)
#   `[ "$status" -eq 0 ]' failed
not ok 3 sync does not modify or remove an entry resolving outside .specfuse/skills/
# (in test file tests/sync_scaffold_symlinks.bats, line 90)
#   `[ "$status" -eq 0 ]' failed
not ok 4 sync is idempotent for discovery links (second run creates nothing)
# (in test file tests/sync_scaffold_symlinks.bats, line 98)
#   `[ "$status" -eq 0 ]' failed
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
index 38c9f06..6c46378 100644
--- a/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
+++ b/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0058/T01
 type: implementation
 status: pending
-attempts: 0
+attempts: 3
 planned_cost_usd: 4.00
 oracle_env: macos_local
 produces:
diff --git a/scripts/sync-scaffold.sh b/scripts/sync-scaffold.sh
index 588a108..0db803b 100755
--- a/scripts/sync-scaffold.sh
+++ b/scripts/sync-scaffold.sh
@@ -241,6 +241,7 @@ FILES=(
   templates/GATE.template.md
   templates/PLAN.template.md
   templates/WU.template.md
+  templates/DECISIONS.template.md
   rules/close-discipline.md
   rules/correlation-ids.md
   rules/design-for-diagnosis.md
diff --git a/specfuse/loop/arm_eval.py b/specfuse/loop/arm_eval.py
index 10d645e..cfc69b5 100644
--- a/specfuse/loop/arm_eval.py
+++ b/specfuse/loop/arm_eval.py
@@ -137,6 +137,8 @@ NON_JUDGE_MODULES = {
     "build_provenance.py": "warns when the running build is not the working "
         "tree's; prints a diagnostic and changes no verdict",
     "changelog.py": "parses and stamps CHANGELOG.md; no gate reads it",
+    "decisions_format.py": "DECISIONS.md schema and parser; data and parsing "
+        "only, no lint wiring and no verdict read",
     "driver_edit.py": "applies operator edits to a feature folder",
     "escalation.py": "renders and files needs-human records after a halt",
     "events_stats.py": "aggregates the event trail for reporting",
diff --git a/tests/test_init_integration.py b/tests/test_init_integration.py
index bdebe38..3ac8d84 100644
--- a/tests/test_init_integration.py
+++ b/tests/test_init_integration.py
@@ -35,6 +35,7 @@ _EXPECTED_SPECFUSE_TREE = {
     "templates/PLAN.template.md",
     "templates/WU.template.md",
     "templates/LEARNINGS-pending.template.md",
+    "templates/DECISIONS.template.md",
     "rules/close-discipline.md",
     "rules/correlation-ids.md",
     "rules/design-for-diagnosis.md",
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
diff --git a/tests/test_scaffold_init.py b/tests/test_scaffold_init.py
index a02ff02..953621e 100644
--- a/tests/test_scaffold_init.py
+++ b/tests/test_scaffold_init.py
@@ -17,6 +17,7 @@ _EXPECTED_TREE = {
     "templates/PLAN.template.md",
     "templates/WU.template.md",
     "templates/LEARNINGS-pending.template.md",
+    "templates/DECISIONS.template.md",
     "rules/close-discipline.md",
     "rules/correlation-ids.md",
     "rules/design-for-diagnosis.md",
diff --git a/tests/test_scaffold_resources.py b/tests/test_scaffold_resources.py
index 1026438..cf7a50b 100644
--- a/tests/test_scaffold_resources.py
+++ b/tests/test_scaffold_resources.py
@@ -23,6 +23,7 @@ _EXPECTED_RELPATHS = {
     "templates/PLAN.template.md",
     "templates/WU.template.md",
     "templates/LEARNINGS-pending.template.md",
+    "templates/DECISIONS.template.md",
     "rules/close-discipline.md",
     "rules/correlation-ids.md",
     "rules/design-for-diagnosis.md",

```
