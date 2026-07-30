### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [18:24:41] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed beca5b96fbceab44212c45edad228d0906b9e108

[18:24:41] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:24:41] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 92d333caf285b1a9440077317b16d5ca8b74d08f

[18:24:41] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:24:41] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 65048412d58d8c641c2fba2e8b12d5cf89b1fe28

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
		Low: 89
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 89
Files skipped (0):
```

### coverage: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
   [18:25:44] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed bdf25a4c6a3ed4bb916339362d77c0cf8856ccda

[18:25:44] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:25:44] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed f48d065e4bdcb2207d4f9344ef2769060b7c7e00

[18:25:44] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:25:44] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 4a39b0fe03ab6bd35919cbaac5c08de17bbca294

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`. Inspect RETROSPECTIVE.md / events.jsonl. Likely fix: manually flip PLAN.md `status: active -> done`, then `/wrap-feature`.
```

### leak-scan: PASS
```
$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
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
diff --git a/.specfuse/features/FEAT-2026-0053-auto-mode/WU-07-lint-blocking-under-auto.md b/.specfuse/features/FEAT-2026-0053-auto-mode/WU-07-lint-blocking-under-auto.md
index 19863c4..e157cd9 100644
--- a/.specfuse/features/FEAT-2026-0053-auto-mode/WU-07-lint-blocking-under-auto.md
+++ b/.specfuse/features/FEAT-2026-0053-auto-mode/WU-07-lint-blocking-under-auto.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0053/T07
 type: implementation
 status: pending
-attempts: 1
+attempts: 2
 planned_cost_usd: 3.00
 human_only: true
 provenance: "RETROSPECTIVE.md, Consumer-visible contract changes item 3 — gate 2 flips open_questions to blocking under auto only; that is the severity flip and it needs its own satisfiability answer and runtime probe. AC#5 (a malformed review file must park, not raise) comes from this feature's own G1-PLAN warn census, which hit MiniYAMLError on one of 43 real feature folders."
diff --git a/.specfuse/features/FEAT-2026-0053-auto-mode/events.jsonl b/.specfuse/features/FEAT-2026-0053-auto-mode/events.jsonl
index 64b2bb0..b6fe623 100644
--- a/.specfuse/features/FEAT-2026-0053-auto-mode/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0053-auto-mode/events.jsonl
@@ -32,3 +32,5 @@
 {"timestamp": "2026-07-30T21:58:24.873884+00:00", "correlation_id": "FEAT-2026-0053/T06", "event_type": "task_completed", "source": "driver", "source_version": "0.7.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 1014.622, "cost_usd": 5.0473269, "input_tokens": 2471, "output_tokens": 63848, "cache_read_input_tokens": 9918673, "cache_creation_input_tokens": 184432}], "type": "implementation", "re_arm_count": 0, "cost_usd": 5.047327, "cumulative_cost_usd": 5.047327, "attempts_lifetime": 1, "planned_cost_usd": 3.5}}
 {"timestamp": "2026-07-30T21:58:24.890856+00:00", "correlation_id": "FEAT-2026-0053/T07", "event_type": "task_started", "source": "driver", "source_version": "0.7.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
 {"timestamp": "2026-07-30T22:04:08.562120+00:00", "correlation_id": "FEAT-2026-0053/T07", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.7.1", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 343.62, "cost_usd": 1.6875993000000002, "input_tokens": 60, "output_tokens": 17155, "cache_read_input_tokens": 2894901, "cache_creation_input_tokens": 93604, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "$ python3 -m unittest discover -s tests -v", "failure_excerpt": "### tests: FAIL\n### lint: FAIL\nFound 2 errors.\n### coverage: FAIL\n$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90", "files_touched": ["tests/test_arm_eval_lint_class.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-07-30T22:13:01.308456+00:00", "correlation_id": "FEAT-2026-0053/T07", "event_type": "task_started", "source": "driver", "source_version": "0.7.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-07-30T22:18:59.253997+00:00", "correlation_id": "FEAT-2026-0053/T07", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.7.1", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 357.917, "cost_usd": 1.3786470000000004, "input_tokens": 62, "output_tokens": 19387, "cache_read_input_tokens": 2270320, "cache_creation_input_tokens": 67760, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "$ python3 -m unittest discover -s tests -v", "failure_excerpt": "### tests: FAIL\n### coverage: FAIL\n$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90", "files_touched": ["tests/test_arm_eval_lint_class.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
diff --git a/specfuse/loop/arm_eval.py b/specfuse/loop/arm_eval.py
index c920e37..a1664c8 100644
--- a/specfuse/loop/arm_eval.py
+++ b/specfuse/loop/arm_eval.py
@@ -15,13 +15,13 @@ from `loop.py` (the dependency points the other way: `loop.py` will call
 into this module, T04).
 
 The organizing principle: model-authored signals may only veto; only
-mechanical facts and human-authored constants may approve. Of the seven
-classes below, "missing_provenance" and "open_questions_human_only" are veto
-channels — a clean verdict there withholds nothing, it just declines to
-block; every other class both approves (clean) and blocks (fired) on
-mechanical grounds alone. `would_arm` is True only when all seven classes are
-clean, so the veto classes can only ever pull the decision from True to
-False, never the reverse.
+mechanical facts and human-authored constants may approve. Of the eight
+classes below, "missing_provenance", "open_questions_human_only", and
+"plan_next_lint" are veto channels — a clean verdict there withholds
+nothing, it just declines to block; every other class both approves (clean)
+and blocks (fired) on mechanical grounds alone. `would_arm` is True only when
+all eight classes are clean, so the veto classes can only ever pull the
+decision from True to False, never the reverse.
 
 Honest v1 limit: a draft that weakens an *existing* test's assertions is
 undetectable here. The judge-editing class catches `produces:` paths, not
@@ -73,9 +73,12 @@ CLASS_NAMES = (
     "drift_caps",
     "missing_provenance",
     "open_questions_human_only",
+    "plan_next_lint",
 )
 
-VETO_CLASSES = frozenset({"missing_provenance", "open_questions_human_only"})
+VETO_CLASSES = frozenset(
+    {"missing_provenance", "open_questions_human_only", "plan_next_lint"}
+)
 
 
 @dataclass(frozen=True)
@@ -358,6 +361,27 @@ def evaluate_arm_predicate(feature_dir: Path, just_closed_gate: int) -> ArmDecis
     else:
         classes["open_questions_human_only"] = ClassVerdict("clean", clean_reason)
 
+    # --- Class 8: plan-next contract lint (veto channel, FEAT-2026-0053/T07) ---
+    # Package-relative + function-local: lint_plan imports `from .loop import
+    # VERDICT_VALUES`, and loop.py imports this module at module scope, so a
+    # module-top import here would be circular depending on import order
+    # (matches the precedent at loop.py's plan-next close hook).
+    try:
+        from .lint_plan import lint_plan_next_draft
+
+        lint_warns = lint_plan_next_draft(feature_dir, just_closed_gate)
+    except Exception as exc:  # noqa: BLE001 - a lint-hook bug must veto, not crash
+        classes["plan_next_lint"] = ClassVerdict(
+            "fired", f"lint_plan_next_draft raised: {type(exc).__name__}: {exc}"
+        )
+    else:
+        if lint_warns:
+            classes["plan_next_lint"] = ClassVerdict("fired", "; ".join(lint_warns))
+        else:
+            classes["plan_next_lint"] = ClassVerdict(
+                "clean", "lint_plan_next_draft reported no findings"
+            )
+
     would_arm = all(classes[name].status != "fired" for name in CLASS_NAMES)
 
     return ArmDecision(

```
