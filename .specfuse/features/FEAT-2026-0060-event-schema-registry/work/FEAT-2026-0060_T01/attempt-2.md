### tests: FAIL
```
$ python3 -m unittest discover -s tests -v
   [18:19:58] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed b6e27bb2e26a5590d3fe1122711931360f5b3b40

[18:19:58] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:19:58] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 8743307829ac96fa023a4d1e12f8adf01ce488a2

[18:19:58] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:19:58] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed b48f0c60f8de4d2e3bdbbbfb9a1df14162d34b6f

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
   [18:21:24] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed daa685ad02c652d7c6141bdb5528aa1a32ee062c

[18:21:24] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [18:21:24] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 2cfcfc0b20f437be349cab82417e3c395894b5f5

[18:21:24] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [18:21:24] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed e307b19920a94f7c5cfa72e740b9685eaffe0a62

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
index dfb1849..f101de8 100644
--- a/.specfuse/features/FEAT-2026-0060-event-schema-registry/WU-01-driver-event-registry.md
+++ b/.specfuse/features/FEAT-2026-0060-event-schema-registry/WU-01-driver-event-registry.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0060/T01
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 4.50
 produces:
   - specfuse/loop/data/schemas/driver-event.schema.json
diff --git a/specfuse/loop/loop.py b/specfuse/loop/loop.py
index 8252757..231e901 100644
--- a/specfuse/loop/loop.py
+++ b/specfuse/loop/loop.py
@@ -699,9 +699,11 @@ def build_arm_predicate_event(feature_dir: Path, feature_id: str, gate_number: i
     Pure w.r.t. control flow: evaluation failures degrade to an
     `evaluation_error` payload field rather than propagating, so a defect in
     the predicate (T03) or the baseline reader (T01) can never crash a gate
-    close. Not validated by validate_event.py — see the WU's Verification
-    note; `gate_reached` and `attempt_outcome` are the existing precedent for
-    driver-local event types outside the envelope enum and per-type registry.
+    close. Not validated at emit time (runtime validation was declined,
+    FEAT-2026-0060/PLAN.md) — `arm_predicate_evaluated` is sanctioned in the
+    driver-local registry (specfuse/loop/data/schemas/driver-event.schema.json)
+    that validate_event.py falls through to for driver-sourced event types
+    outside the vendored envelope enum.
     """
     try:
         decision = evaluate_arm_predicate(feature_dir, gate_number)
diff --git a/specfuse/loop/validate_event.py b/specfuse/loop/validate_event.py
index 744f43f..ab5a1f1 100755
--- a/specfuse/loop/validate_event.py
+++ b/specfuse/loop/validate_event.py
@@ -83,6 +83,7 @@ def _resolve_schema_root():
 SCHEMA_ROOT = _resolve_schema_root()
 SCHEMA_PATH = SCHEMA_ROOT / "event.schema.json"
 PER_TYPE_SCHEMA_DIR = SCHEMA_ROOT / "events"
+DRIVER_SCHEMA_PATH = SCHEMA_ROOT / "driver-event.schema.json"
 
 
 def load_validator() -> Draft202012Validator:
@@ -136,6 +137,40 @@ def load_per_type_validator(event_type: str) -> Draft202012Validator | None:
     return validator
 
 
+_DRIVER_TYPES_LOADED = False
+_DRIVER_TYPES: frozenset[str] | None = None
+
+
+def load_driver_event_types() -> frozenset[str] | None:
+    """Return the driver-local event_type registry, or None if unavailable.
+
+    Additive fall-through, mirroring load_per_type_validator's contract: a
+    missing or unreadable driver-event.schema.json degrades to vendored-envelope-
+    only validation rather than raising. Sanctions event_type values the driver
+    emits with source: "driver" that are outside the vendored envelope enum.
+    """
+    global _DRIVER_TYPES_LOADED, _DRIVER_TYPES
+    if _DRIVER_TYPES_LOADED:
+        return _DRIVER_TYPES
+
+    _DRIVER_TYPES_LOADED = True
+    _DRIVER_TYPES = None
+
+    if not DRIVER_SCHEMA_PATH.is_file():
+        return None
+
+    try:
+        with DRIVER_SCHEMA_PATH.open("r", encoding="utf-8") as f:
+            schema = json.load(f)
+        types = schema.get("properties", {}).get("event_type", {}).get("enum")
+        if isinstance(types, list):
+            _DRIVER_TYPES = frozenset(types)
+    except (OSError, json.JSONDecodeError):
+        _DRIVER_TYPES = None
+
+    return _DRIVER_TYPES
+
+
 def format_error(source: str, line_number: int, path: str, message: str) -> str:
     location = f"{source}:{line_number}" if line_number else source
     prefix = f"{location}"
@@ -155,15 +190,33 @@ def validate_line(
     except json.JSONDecodeError as exc:
         return [format_error(source, line_number, "", f"invalid JSON — {exc.msg} (line {exc.lineno}, col {exc.colno})")]
 
+    # Fall-through resolution for source: "driver" events: the vendored
+    # envelope's event_type enum is tried first; only an event_type it rejects
+    # falls through to the driver-local registry (load_driver_event_types()).
+    # Already-sanctioned types (task_started, task_completed, human_escalation)
+    # validate against the vendored enum directly and never reach this path.
+    event_type = event.get("event_type") if isinstance(event, dict) else None
+    driver_sanctioned = (
+        isinstance(event, dict)
+        and event.get("source") == "driver"
+        and isinstance(event_type, str)
+        and event_type in (load_driver_event_types() or frozenset())
+    )
+
     errors: list[str] = []
     for err in sorted(validator.iter_errors(event), key=lambda e: list(e.absolute_path)):
+        if (
+            driver_sanctioned
+            and list(err.absolute_path) == ["event_type"]
+            and "is not one of" in err.message
+        ):
+            continue
         path = "/".join(str(p) for p in err.absolute_path) or "(root)"
         errors.append(format_error(source, line_number, path, err.message))
 
     # Per-type payload validation. Applied only when the top-level envelope
     # is valid enough to name the event_type and the payload is a dict;
     # otherwise the top-level errors above are the signal.
-    event_type = event.get("event_type") if isinstance(event, dict) else None
     payload = event.get("payload") if isinstance(event, dict) else None
     if isinstance(event_type, str) and isinstance(payload, dict):
         per_type = load_per_type_validator(event_type)
diff --git a/tests/test_init_integration.py b/tests/test_init_integration.py
index db601f9..9dc2968 100644
--- a/tests/test_init_integration.py
+++ b/tests/test_init_integration.py
@@ -46,6 +46,7 @@ _EXPECTED_SPECFUSE_TREE = {
     "rules/verification-discipline.md",
     "rules/operator-escalation.md",
     "schemas/event.schema.json",
+    "schemas/driver-event.schema.json",
     "schemas/events/initiative_created.schema.json",
     "schemas/events/spec_validated.schema.json",
     "schemas/events/spec_issue_resolved.schema.json",
diff --git a/tests/test_scaffold_data_in_sync.py b/tests/test_scaffold_data_in_sync.py
index 08bd777..2ed91ee 100644
--- a/tests/test_scaffold_data_in_sync.py
+++ b/tests/test_scaffold_data_in_sync.py
@@ -61,8 +61,12 @@ DOCS_TRACKED = {
 # (FEAT-2026-0040/T11): this repository never installs it into its own
 # .github/workflows/ (see test_monitor_runner_surfaces.py), so there is no
 # canonical copy for it to drift from. Existence-only, checked below.
+# `schemas/driver-event.schema.json` (FEAT-2026-0060/T01) is this repository's
+# own driver-local event type registry — not vendored from core, so there is
+# no .specfuse/schemas/ canonical counterpart to byte-match.
 UNMIRRORED_TRACKED = {
     "workflows/specfuse-monitor.yml",
+    "schemas/driver-event.schema.json",
 }
 
 
diff --git a/tests/test_scaffold_init.py b/tests/test_scaffold_init.py
index c5bc4e0..363069b 100644
--- a/tests/test_scaffold_init.py
+++ b/tests/test_scaffold_init.py
@@ -28,6 +28,7 @@ _EXPECTED_TREE = {
     "rules/verification-discipline.md",
     "rules/operator-escalation.md",
     "schemas/event.schema.json",
+    "schemas/driver-event.schema.json",
     "schemas/events/initiative_created.schema.json",
     "schemas/events/spec_validated.schema.json",
     "schemas/events/spec_issue_resolved.schema.json",
diff --git a/tests/test_scaffold_resources.py b/tests/test_scaffold_resources.py
index b40a027..2be6302 100644
--- a/tests/test_scaffold_resources.py
+++ b/tests/test_scaffold_resources.py
@@ -33,6 +33,7 @@ _EXPECTED_RELPATHS = {
     "rules/verification-discipline.md",
     "rules/operator-escalation.md",
     "schemas/event.schema.json",
+    "schemas/driver-event.schema.json",
     "schemas/events/initiative_created.schema.json",
     "schemas/events/spec_validated.schema.json",
     "schemas/events/spec_issue_resolved.schema.json",

```
