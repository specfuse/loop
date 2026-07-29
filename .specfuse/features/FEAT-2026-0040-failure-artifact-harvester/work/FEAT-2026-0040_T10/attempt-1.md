### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [21:09:21] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 18229dd8b7542a4dc445ac07d073b94acb55fd51

[21:09:21] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [21:09:21] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 885ca0a6fcc778970fe5495b27badcc46c6b75aa

[21:09:21] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [21:09:21] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 66028d845b2f0739bd4f87c66e6aaa23efbc6a8e

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
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
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 6

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 83
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 83
Files skipped (0):
```

### coverage: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
   [21:10:30] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 36798fdbd7dae8ab5a4df46de2dca6e6d7fdeeb4

[21:10:30] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [21:10:30] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 0cd5ecb778038ccd7027e374125282692c3fae1a

[21:10:30] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [21:10:30] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 5721b713a1513b8ca31c6a85a614976c11abc5df

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

### leak-scan: FAIL
```
$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: FINDINGS
  secret:stripe-access-token (/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp_kytq5y8/tests/test_monitor_issue_lifecycle.py)
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
```

### sync-scaffold-bats: PASS
```
$ bats tests/sync_scaffold.bats
1..5
ok 1 sync copies all canonical files to specfuse/loop/data/
ok 2 sync copies file contents correctly
ok 3 sync is idempotent (second run exits 0 and reports unchanged)
ok 4 sync updates a stale file and reports it
ok 5 sync exits non-zero if canonical source dir is missing
```

### sync-scaffold-symlinks-bats: PASS
```
$ bats tests/sync_scaffold_symlinks.bats
1..4
ok 1 sync creates a missing discovery link for a skill with no .claude/skills entry
ok 2 sync leaves an existing discovery link byte-identical
ok 3 sync does not modify or remove an entry resolving outside .specfuse/skills/
ok 4 sync is idempotent for discovery links (second run creates nothing)
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
```

### init-skills-bats: PASS
```
$ bats tests/init_skills_idempotent.bats
1..1
ok 1 source repo holds skill content in .specfuse (real), not .claude
```

### hookspath-conflict-bats: PASS
```
$ bats tests/hookspath_conflict.bats
1..4
ok 1 install-hooks.sh then setup.sh: both hooks active under hooksPath
ok 2 setup.sh then install-hooks.sh: both hooks active under hooksPath
ok 3 install-hooks.sh alone: both hooks active under hooksPath
ok 4 setup.sh alone: both hooks active under hooksPath
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/WU-10-specfuse-monitor-run-cli.md b/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/WU-10-specfuse-monitor-run-cli.md
index 4d2acc7..cb5750b 100644
--- a/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/WU-10-specfuse-monitor-run-cli.md
+++ b/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/WU-10-specfuse-monitor-run-cli.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0040/T10
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 5.00
 oracle_env: macos_local
 produces:
@@ -12,6 +12,8 @@ produces:
 model: sonnet
 effort: high
 gate_set: code
+driver_version: 0.6.0
+started_at: 2026-07-29T00:47:13.807446+00:00
 ---
 
 # One polling cycle, end to end — the `specfuse-monitor run` CLI
diff --git a/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/events.jsonl b/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/events.jsonl
index f5ae528..27afa30 100644
--- a/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0040-failure-artifact-harvester/events.jsonl
@@ -34,3 +34,6 @@
 {"timestamp": "2026-07-29T00:22:58.267716+00:00", "correlation_id": "FEAT-2026-0040/T08", "event_type": "task_started", "source": "driver", "source_version": "0.6.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
 {"timestamp": "2026-07-29T00:34:25.943251+00:00", "correlation_id": "FEAT-2026-0040/T08", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.6.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 687.631, "cost_usd": 1.9414535999999996, "input_tokens": 70, "output_tokens": 22666, "cache_read_input_tokens": 3104292, "cache_creation_input_tokens": 111661, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0040-failure-artifact-harvester/WU-08-queue-stalled-broker-adapter.md", "specfuse/monitor/providers/azure_service_bus.py", "tests/test_queue_stalled_adapter.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-07-29T00:34:25.943499+00:00", "correlation_id": "FEAT-2026-0040/T08", "event_type": "task_completed", "source": "driver", "source_version": "0.6.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 687.631, "cost_usd": 1.9414535999999996, "input_tokens": 70, "output_tokens": 22666, "cache_read_input_tokens": 3104292, "cache_creation_input_tokens": 111661}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.941454, "cumulative_cost_usd": 1.941454, "attempts_lifetime": 1, "planned_cost_usd": 4.0}}
+{"timestamp": "2026-07-29T00:34:25.961626+00:00", "correlation_id": "FEAT-2026-0040/T09", "event_type": "task_started", "source": "driver", "source_version": "0.6.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-07-29T00:47:13.790359+00:00", "correlation_id": "FEAT-2026-0040/T09", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.6.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 767.742, "cost_usd": 2.672889600000001, "input_tokens": 90, "output_tokens": 32727, "cache_read_input_tokens": 4658322, "cache_creation_input_tokens": 130703, "model": "sonnet", "effort": "high", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0040-failure-artifact-harvester/WU-09-fingerprint-keyed-issue-lifecycle.md", ".specfuse/features/FEAT-2026-0040-failure-artifact-harvester/events.jsonl", "specfuse/monitor/issues.py", "tests/test_monitor_issue_lifecycle.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-07-29T00:47:13.790571+00:00", "correlation_id": "FEAT-2026-0040/T09", "event_type": "task_completed", "source": "driver", "source_version": "0.6.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 767.742, "cost_usd": 2.672889600000001, "input_tokens": 90, "output_tokens": 32727, "cache_read_input_tokens": 4658322, "cache_creation_input_tokens": 130703}], "type": "implementation", "re_arm_count": 0, "cost_usd": 2.67289, "cumulative_cost_usd": 2.67289, "attempts_lifetime": 1, "planned_cost_usd": 5.0}}
diff --git a/pyproject.toml b/pyproject.toml
index 7aae7e4..30e0868 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -64,6 +64,7 @@ select = ["E4", "E7", "E9", "F", "PLW1510", "B", "BLE001", "S110", "TRY004"]
 specfuse-loop = "specfuse.loop.loop:main"
 specfuse-lint = "specfuse.loop.lint_plan:main"
 specfuse-monitor-lint = "specfuse.loop.lint_monitoring:main"
+specfuse-monitor = "specfuse.monitor.cli:main"
 specfuse-stats = "specfuse.loop.events_stats:main"
 
 [tool.setuptools.packages.find]

```
