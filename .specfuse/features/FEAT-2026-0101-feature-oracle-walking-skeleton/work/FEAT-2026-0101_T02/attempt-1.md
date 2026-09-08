### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_package_data_matches_canonical (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_data_matches_canonical)
Traceback (most recent call last):
... (4492 line(s) elided) ...
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "Diffs:\n" + "\n".join(f"  {m}" for m in mismatches)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Scaffold data out of sync with canonical sources.
Run: scripts/sync-scaffold.sh

Diffs:
  content differs: rules/close-discipline.md

----------------------------------------------------------------------
Ran 3762 tests in 167.380s

FAILED (failures=1, skipped=3)
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
		Low: 129
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 129
Files skipped (0):
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### coverage: SKIP — dependency 'tests' failed

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

```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 70 events.jsonl file(s), 1798 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
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
evaluable=31 evaluated=31 could_not_evaluate=0 excluded_no_baseline=45
ok: 31 evaluable feature(s) swept clean, no not_evaluable verdicts
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

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_feature_oracle_e2e -q
----------------------------------------------------------------------
Ran 4 tests in 0.057s

OK
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md b/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md
index 0e2f1da..2e9e589 100644
--- a/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md
+++ b/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0101/T02
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 2.50
 oracle_env: macos_local
 produces:
@@ -10,6 +10,11 @@ produces:
   - specfuse/loop/lint_closing.py
   - .specfuse/rules/close-discipline.md
   - tests/test_close_records_feature_oracle.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.16.0
+started_at: 2026-09-07T22:52:23.241280+00:00
 ---
 
 # The close re-runs the gate's oracle and records its verdict
diff --git a/.specfuse/rules/close-discipline.md b/.specfuse/rules/close-discipline.md
index 8074e24..3dce2a7 100644
--- a/.specfuse/rules/close-discipline.md
+++ b/.specfuse/rules/close-discipline.md
@@ -34,6 +34,19 @@ output directory before asserting — stale output satisfies any assertion.
 > catches the composite: all WUs individually green while the feature-level
 > oracle fails.
 
+**The gate's `feature_oracle` is this feature-level re-run, not a
+duplicate of it.** Re-running every producing unit's own oracle is a
+different, narrower question than the one this section asks for —
+`[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]`: fifteen
+oracles re-ran green in one close and none could observe the defect, because
+none asserted on the path the feature was meant to change. When a gate
+declares `feature_oracle` in its `GATE-NN.md` (FEAT-2026-0101/T01), that
+command *is* the composite question the units were each too small to ask,
+`verify()` runs it fresh on every unit's attempt, and the close records its
+PASS/FAIL verdict in `## Measurements` (`specfuse lint --closing`'s `close-n`
+/ `close-intermediate-g`, conditional on the declaration existing) — the
+judge's binary end-to-end signal.
+
 **You measure; the judge concludes (FEAT-2026-0100).** Re-running the oracles
 is your job and it does not change. Deciding what their exit codes *mean* for
 the feature is not: on a terminal gate the driver dispatches a separate judge
diff --git a/specfuse/loop/closing_requirements.py b/specfuse/loop/closing_requirements.py
index 794ef01..1e6506a 100644
--- a/specfuse/loop/closing_requirements.py
+++ b/specfuse/loop/closing_requirements.py
@@ -140,6 +140,19 @@ def gate_section_heading_re(gate_n: int) -> re.Pattern:
     )
 
 
+#: The gate-report name `verify()` gives a declared `feature_oracle`
+#: (FEAT-2026-0101/T01, `loop.verify`'s synthesized gate entry). A close's
+#: `## Measurements` section is expected to carry the same
+#: `### feature_oracle: PASS`/`FAIL` line `_run_gate_set` renders, not a
+#: paraphrase — this is the one place the literal is spelled, so a rename of
+#: the gate name in `loop.py` cannot drift silently out of sync with what the
+#: close lint looks for.
+FEATURE_ORACLE_GATE_NAME = "feature_oracle"
+FEATURE_ORACLE_VERDICT_RE = re.compile(
+    rf"^###\s+{re.escape(FEATURE_ORACLE_GATE_NAME)}:\s*(PASS|FAIL)\s*$",
+    re.MULTILINE,
+)
+
 GATE_REVIEW_FILENAME_TEMPLATE = "GATE-{next_gate:02d}-REVIEW.md"
 
 
@@ -339,6 +352,18 @@ CLOSING_REQUIREMENTS: dict[str, list[Requirement]] = {
             applies_when="criteria_artifact_present",
             enforced_by="check_criteria_state_well_formed",
         ),
+        Requirement(
+            id="close-n", wu_type="close", phase="pre-squash",
+            description=(
+                "When the gate's GATE-NN.md declares feature_oracle, "
+                "RETROSPECTIVE.md's Measurements section records a PASS/FAIL "
+                "verdict line naming it — the gate's feature_oracle is the "
+                "feature-level re-run close-discipline.md §1 requires "
+                "[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]"
+            ),
+            file=RETROSPECTIVE_FILENAME,
+            enforced_by="check_feature_oracle_verdict_recorded",
+        ),
     ],
     "close-intermediate": [
         Requirement(
@@ -397,6 +422,18 @@ CLOSING_REQUIREMENTS: dict[str, list[Requirement]] = {
             applies_when="criteria_artifact_present",
             enforced_by="check_criteria_state_well_formed",
         ),
+        Requirement(
+            id="close-intermediate-g", wu_type="close-intermediate", phase="pre-squash",
+            description=(
+                "When the gate's GATE-NN.md declares feature_oracle, "
+                "RETROSPECTIVE.md's Measurements section records a PASS/FAIL "
+                "verdict line naming it — the gate's feature_oracle is the "
+                "feature-level re-run close-discipline.md §1 requires "
+                "[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]"
+            ),
+            file=RETROSPECTIVE_FILENAME,
+            enforced_by="check_feature_oracle_verdict_recorded",
+        ),
     ],
     "plan-next": [
         Requirement(
diff --git a/specfuse/loop/lint_closing.py b/specfuse/loop/lint_closing.py
index cb34f4e..7a14c16 100644
--- a/specfuse/loop/lint_closing.py
+++ b/specfuse/loop/lint_closing.py
@@ -27,8 +27,14 @@ from pathlib import Path
 
 from . import closing_requirements as creq
 from . import criteria_state
+from ._wu_sections import slice_wu_section
 from .changelog import parse_changelog
-from .loop import _gate_number_from_wu_id, summarize_attempt_failure_classes
+from .judge import MEASUREMENTS_SECTION
+from .loop import (
+    _gate_number_from_wu_id,
+    read_gate_feature_oracle,
+    summarize_attempt_failure_classes,
+)
 from .lint_plan import _find_task_graph_block, read_frontmatter
 
 _CLOSING_TYPES = frozenset({"close", "close-intermediate", "plan-next"})
@@ -288,6 +294,39 @@ def _check_changelog_entry_for_contract_changes(req: creq.Requirement, ctx: Clos
     )
 
 
+def check_feature_oracle_verdict_recorded(req: creq.Requirement, ctx: ClosingContext):
+    """The gate's declared `feature_oracle`, re-run and recorded (T02).
+
+    Not applicable (returns None) whenever the gate cannot be resolved or
+    declares no `feature_oracle` at all — the scope guard: a gate that never
+    named an oracle imposes no requirement here, and a declared-but-unusable
+    value is `verify()`'s own CONFIGURATION ERROR to catch, not this check's.
+    """
+    if ctx.gate_num is None:
+        return None
+    gate_entry = next((g for g in ctx.gates if g.get("gate") == ctx.gate_num), None)
+    if gate_entry is None or not gate_entry.get("file"):
+        return None
+    gate_file = ctx.feature_dir / gate_entry["file"]
+    if not gate_file.is_file():
+        return None
+    oracle_command = read_gate_feature_oracle(gate_file)
+    if not oracle_command:
+        return None
+    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
+    if not retro.exists():
+        return True, ""  # assert_retrospective_exists already covers this
+    retro_text = retro.read_text()
+    section = slice_wu_section(retro_text, MEASUREMENTS_SECTION) or retro_text
+    if creq.FEATURE_ORACLE_VERDICT_RE.search(section):
+        return True, ""
+    return False, (
+        f"gate {ctx.gate_num} declares feature_oracle but "
+        f"{creq.RETROSPECTIVE_FILENAME}'s '{MEASUREMENTS_SECTION}' section "
+        f"records no '{creq.FEATURE_ORACLE_GATE_NAME}' PASS/FAIL verdict"
+    )
+
+
 def _check_followups_recorded(req: creq.Requirement, ctx: ClosingContext):
     if ctx.wfm.get("verdict") != "not_met":
         return None
@@ -368,6 +407,7 @@ _CHECKS = {
     "assert_changelog_entry_for_contract_changes": _check_changelog_entry_for_contract_changes,
     "check_criteria_state_well_formed": check_criteria_state_well_formed,
     "assert_followups_recorded": _check_followups_recorded,
+    "check_feature_oracle_verdict_recorded": check_feature_oracle_verdict_recorded,
 }
 
 

```
