### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [18:03:41] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed a4739e8ac3e1ee1589832a9fc62c6e93260341e8

[18:03:41] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:03:41] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 9b131f8b7bd6451064d5338269e1547168507c8e

[18:03:42] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:03:42] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 252a9bb0309461e3f1dc44cbf9a24e6c9e02d3a4

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
		Low: 91
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 91
Files skipped (0):
```

### coverage: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
   [18:05:09] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed cf74f07ae2b692c39b7cbb88507aba02585c3a0f

[18:05:09] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:05:09] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed e566c9aad09154f90812803186efe97c49045b1b

[18:05:09] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:05:09] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 5c088dc29b0c5babfa6db0056282686379587fdd

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
diff --git a/.specfuse/features/FEAT-2026-0060-event-schema-registry/WU-01-driver-event-registry.md b/.specfuse/features/FEAT-2026-0060-event-schema-registry/WU-01-driver-event-registry.md
index dfb1849..7ec744f 100644
--- a/.specfuse/features/FEAT-2026-0060-event-schema-registry/WU-01-driver-event-registry.md
+++ b/.specfuse/features/FEAT-2026-0060-event-schema-registry/WU-01-driver-event-registry.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0060/T01
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 4.50
 produces:
   - specfuse/loop/data/schemas/driver-event.schema.json
@@ -11,6 +11,11 @@ produces:
 produces_driver_helper:
   - load_validator
 oracle_env: macos_local
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.8.0
+started_at: 2026-08-02T21:59:08.121386+00:00
 ---
 
 # A driver-owned registry, resolved by fall-through
diff --git a/specfuse/loop/loop.py b/specfuse/loop/loop.py
index 8252757..47d4166 100644
--- a/specfuse/loop/loop.py
+++ b/specfuse/loop/loop.py
@@ -699,9 +699,10 @@ def build_arm_predicate_event(feature_dir: Path, feature_id: str, gate_number: i
     Pure w.r.t. control flow: evaluation failures degrade to an
     `evaluation_error` payload field rather than propagating, so a defect in
     the predicate (T03) or the baseline reader (T01) can never crash a gate
-    close. Not validated by validate_event.py — see the WU's Verification
-    note; `gate_reached` and `attempt_outcome` are the existing precedent for
-    driver-local event types outside the envelope enum and per-type registry.
+    close. `arm_predicate_evaluated` is sanctioned in the driver-local event
+    registry (specfuse/loop/data/schemas/driver-event.schema.json,
+    FEAT-2026-0060/T01) and validates via validate_event.py's fall-through:
+    the vendored envelope's event_type enum first, this registry second.
     """
     try:
         decision = evaluate_arm_predicate(feature_dir, gate_number)
diff --git a/specfuse/loop/validate_event.py b/specfuse/loop/validate_event.py
index 744f43f..76d124c 100755
--- a/specfuse/loop/validate_event.py
+++ b/specfuse/loop/validate_event.py
@@ -83,6 +83,7 @@ def _resolve_schema_root():
 SCHEMA_ROOT = _resolve_schema_root()
 SCHEMA_PATH = SCHEMA_ROOT / "event.schema.json"
 PER_TYPE_SCHEMA_DIR = SCHEMA_ROOT / "events"
+DRIVER_SCHEMA_PATH = SCHEMA_ROOT / "driver-event.schema.json"
 
 
 def load_validator() -> Draft202012Validator:
@@ -136,6 +137,39 @@ def load_per_type_validator(event_type: str) -> Draft202012Validator | None:
     return validator
 
 
+_DRIVER_LOCAL_TYPES_CACHE: set[str] | None = None
+_DRIVER_LOCAL_TYPES_LOADED = False
+
+
+def load_driver_local_types() -> set[str]:
+    """Return the driver-local event_type registry, or an empty set if absent.
+
+    Mirrors load_per_type_validator's additive contract: a missing or unreadable
+    registry file degrades to "no driver-local types known" rather than raising,
+    so validation falls back to the vendored envelope alone.
+    """
+    global _DRIVER_LOCAL_TYPES_CACHE, _DRIVER_LOCAL_TYPES_LOADED
+    if _DRIVER_LOCAL_TYPES_LOADED:
+        return _DRIVER_LOCAL_TYPES_CACHE
+
+    _DRIVER_LOCAL_TYPES_LOADED = True
+    _DRIVER_LOCAL_TYPES_CACHE = set()
+
+    if not DRIVER_SCHEMA_PATH.is_file():
+        return _DRIVER_LOCAL_TYPES_CACHE
+
+    try:
+        with DRIVER_SCHEMA_PATH.open("r", encoding="utf-8") as f:
+            schema = json.load(f)
+    except (OSError, json.JSONDecodeError):
+        return _DRIVER_LOCAL_TYPES_CACHE
+
+    enum = schema.get("properties", {}).get("event_type", {}).get("enum", [])
+    if isinstance(enum, list):
+        _DRIVER_LOCAL_TYPES_CACHE = {v for v in enum if isinstance(v, str)}
+    return _DRIVER_LOCAL_TYPES_CACHE
+
+
 def format_error(source: str, line_number: int, path: str, message: str) -> str:
     location = f"{source}:{line_number}" if line_number else source
     prefix = f"{location}"
@@ -155,8 +189,21 @@ def validate_line(
     except json.JSONDecodeError as exc:
         return [format_error(source, line_number, "", f"invalid JSON — {exc.msg} (line {exc.lineno}, col {exc.colno})")]
 
+    event_type_for_fallthrough = event.get("event_type") if isinstance(event, dict) else None
+
     errors: list[str] = []
     for err in sorted(validator.iter_errors(event), key=lambda e: list(e.absolute_path)):
+        # Fall-through: the vendored envelope's event_type enum is closed to the
+        # orchestrator's own vocabulary. A driver event whose type is absent there
+        # is not an error as long as it is sanctioned in the driver-local registry
+        # — the resolution order is vendored-first, driver-local-second, never both.
+        if (
+            list(err.absolute_path) == ["event_type"]
+            and err.validator == "enum"
+            and isinstance(event_type_for_fallthrough, str)
+            and event_type_for_fallthrough in load_driver_local_types()
+        ):
+            continue
         path = "/".join(str(p) for p in err.absolute_path) or "(root)"
         errors.append(format_error(source, line_number, path, err.message))
 

```
