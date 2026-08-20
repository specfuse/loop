### tests: FAIL
```
$ python3 -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_no_orphan_files_in_package_data (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_no_orphan_files_in_package_data)
Traceback (most recent call last):
... (4143 line(s) elided) ...
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "Add them to scripts/sync-scaffold.sh and the TRACKED set here:\n"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        + "\n".join(f"  {p}" for p in sorted(orphans))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Unexpected files in specfuse/loop/data/ not in sync manifest.
Add them to scripts/sync-scaffold.sh and the TRACKED set here:
  templates/DECISIONS.template.md

----------------------------------------------------------------------
Ran 3447 tests in 123.709s

FAILED (failures=1, skipped=1)
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
[13:14:41] bug-1 failed after 0s — RuntimeError: boom on bug-1
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
FAIL: test_no_orphan_files_in_package_data (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_no_orphan_files_in_package_data)
Traceback (most recent call last):
AssertionError: Unexpected files in specfuse/loop/data/ not in sync manifest.
Ran 3447 tests in 134.202s
FAILED (failures=1, skipped=1)
   POST-PASS INVARIANT FAILED — archive_anchor_missing: feat-2026-9500
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
... (2360 line(s) elided) ...
   [13:16:49] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed c328e102631ef277bea86b27269d3ba927f48ece

[13:16:49] -- FEAT-2026-9301/G1-DOCS [docs] model=claude-haiku-4-5-20251001 effort=low
   ↳ G1-DOCS
   [13:16:49] attempt 1/3 model=claude-haiku-4-5-20251001 effort=low — fresh session
   PASS — committed 90b8a449ae129695dd79e13e8e55a45e51ad8445

[13:16:49] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [13:16:49] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 1cabc76bbdf2def5b6a3f1808d8bc58a50845667

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
ok: no validation errors across 64 events.jsonl file(s), 1577 event(s) checked
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
index 38c9f06..09e0e64 100644
--- a/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
+++ b/.specfuse/features/FEAT-2026-0058-decision-registry/WU-01-decisions-format.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0058/T01
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 4.00
 oracle_env: macos_local
 produces:
diff --git a/specfuse/loop/arm_eval.py b/specfuse/loop/arm_eval.py
index 10d645e..1aed6f1 100644
--- a/specfuse/loop/arm_eval.py
+++ b/specfuse/loop/arm_eval.py
@@ -137,6 +137,8 @@ NON_JUDGE_MODULES = {
     "build_provenance.py": "warns when the running build is not the working "
         "tree's; prints a diagnostic and changes no verdict",
     "changelog.py": "parses and stamps CHANGELOG.md; no gate reads it",
+    "decisions_format.py": "parses/formats DECISIONS.md; no arm/close/merge "
+        "verdict reads it",
     "driver_edit.py": "applies operator edits to a feature folder",
     "escalation.py": "renders and files needs-human records after a halt",
     "events_stats.py": "aggregates the event trail for reporting",
diff --git a/tests/test_init_integration.py b/tests/test_init_integration.py
index bdebe38..c8902cc 100644
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
@@ -121,6 +122,7 @@ class TestInitFullLayout(unittest.TestCase):
             "templates/PLAN.template.md",
             "templates/WU.template.md",
             "templates/LEARNINGS-pending.template.md",
+            "templates/DECISIONS.template.md",
         ):
             self.assertTrue((self.sf / rel).exists(), f"{rel} not written")
             self.assertEqual(
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
