### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [18:17:39] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 5da9c248e7e37efab37a8f5c3998d6e5a076ef35

[18:17:40] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:17:40] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 31dc25f70db5c66db62ec9666c80f888ef05de09

[18:17:40] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:17:40] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed baaff7fc0c2af97241db2e6c3a022fbc12d82c70

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
   [18:18:47] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 5595951f17884c8eebd8ea95f39b569837976efb

[18:18:47] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:18:47] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 9568e4b72e08809fd75e89ec1d8084ebdc174b37

[18:18:47] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:18:47] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed b32fbc5fe96e9472ea73f221522aae08a8d0d177

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
index 19863c4..a542288 100644
--- a/.specfuse/features/FEAT-2026-0053-auto-mode/WU-07-lint-blocking-under-auto.md
+++ b/.specfuse/features/FEAT-2026-0053-auto-mode/WU-07-lint-blocking-under-auto.md
@@ -1,7 +1,7 @@
 ---
 id: FEAT-2026-0053/T07
 type: implementation
-status: pending
+status: in_progress
 attempts: 1
 planned_cost_usd: 3.00
 human_only: true
@@ -10,6 +10,11 @@ produces:
   - specfuse/loop/arm_eval.py
   - tests/test_arm_eval_lint_class.py
 oracle_env: macos_local
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.7.1
+started_at: 2026-07-30T22:13:01.308107+00:00
 ---
 
 # Contract-field lint warns become blocking — under `auto` only
diff --git a/specfuse/loop/arm_eval.py b/specfuse/loop/arm_eval.py
index c920e37..cb835a2 100644
--- a/specfuse/loop/arm_eval.py
+++ b/specfuse/loop/arm_eval.py
@@ -73,9 +73,12 @@ CLASS_NAMES = (
     "drift_caps",
     "missing_provenance",
     "open_questions_human_only",
+    "plan_next_lint",
 )
 
-VETO_CLASSES = frozenset({"missing_provenance", "open_questions_human_only"})
+VETO_CLASSES = frozenset({
+    "missing_provenance", "open_questions_human_only", "plan_next_lint",
+})
 
 
 @dataclass(frozen=True)
@@ -101,8 +104,16 @@ def _parse_frontmatter(text: str) -> tuple[dict, str]:
     end = next((i for i, ln in enumerate(lines[1:], 1) if _FM_DELIM.match(ln)), None)
     if end is None:
         return {}, text
-    fm = _miniyaml.parse("\n".join(lines[1:end])) or {}
     body = "\n".join(lines[end + 1:])
+    try:
+        fm = _miniyaml.parse("\n".join(lines[1:end])) or {}
+    except _miniyaml.MiniYAMLError:
+        # A malformed frontmatter block must not crash arm evaluation — the
+        # dedicated plan_next_lint class (T07) is what surfaces this as a
+        # named finding via lint_plan_next_draft's own parse; every other
+        # class degrades to treating the file as if its frontmatter were
+        # absent, same as the no-delimiter branch above.
+        fm = {}
     return fm, body
 
 
@@ -358,6 +369,26 @@ def evaluate_arm_predicate(feature_dir: Path, just_closed_gate: int) -> ArmDecis
     else:
         classes["open_questions_human_only"] = ClassVerdict("clean", clean_reason)
 
+    # --- Class 8: plan-next contract lint (veto channel, T07) ---
+    # Package-relative + function-local: lint_plan imports `from .loop import
+    # VERDICT_VALUES`, and loop.py imports this module at its own top level,
+    # so a module-top import here would be circular (matches loop.py's
+    # existing plan-next-draft lint hook, FEAT-2026-0018/T07).
+    try:
+        from .lint_plan import lint_plan_next_draft
+        lint_warns = lint_plan_next_draft(feature_dir, just_closed_gate)
+    except Exception as exc:  # noqa: BLE001 - a lint bug must not crash the arm eval
+        classes["plan_next_lint"] = ClassVerdict(
+            "fired", f"lint_plan_next_draft raised {type(exc).__name__}: {exc}"
+        )
+    else:
+        if lint_warns:
+            classes["plan_next_lint"] = ClassVerdict("fired", "; ".join(lint_warns))
+        else:
+            classes["plan_next_lint"] = ClassVerdict(
+                "clean", "plan-next contract lint reported no findings"
+            )
+
     would_arm = all(classes[name].status != "fired" for name in CLASS_NAMES)
 
     return ArmDecision(

```
