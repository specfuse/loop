### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_every_requirement_names_a_real_guard_function (test_closing_requirements.TestRegistryShape.test_every_requirement_names_a_real_guard_function)
Traceback (most recent call last):
... (4486 line(s) elided) ...
    self.assertTrue(
    ~~~~~~~~~~~~~~~^
        hasattr(loop, req.enforced_by) or hasattr(lint_closing, req.enforced_by),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<2 lines>...
        f"lint_closing.py",
        ^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: False is not true : registry requirement close-n names enforced_by='assert_feature_oracle_recorded', which exists in neither loop.py nor lint_closing.py

----------------------------------------------------------------------
Ran 3762 tests in 186.989s

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
ok: no validation errors across 70 events.jsonl file(s), 1800 event(s) checked
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
Ran 4 tests in 0.128s

OK
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md b/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md
index 0e2f1da..960c52b 100644
--- a/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md
+++ b/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-02-close-reruns-and-records.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0101/T02
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 2.50
 oracle_env: macos_local
 produces:
diff --git a/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/events.jsonl b/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/events.jsonl
index aae4d5e..6a33bd1 100644
--- a/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/events.jsonl
@@ -2,3 +2,5 @@
 {"timestamp": "2026-09-07T22:47:59.298604+00:00", "correlation_id": "FEAT-2026-0101/T01", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.16.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 1463.591, "cost_usd": 3.6375757999999996, "input_tokens": 252, "output_tokens": 38843, "cache_read_input_tokens": 13565849, "cache_creation_input_tokens": 133868, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0101-feature-oracle-walking-skeleton/WU-01-declare-read-run-oracle.md", "specfuse/loop/loop.py", "tests/test_feature_oracle_e2e.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-07T22:47:59.298839+00:00", "correlation_id": "FEAT-2026-0101/T01", "event_type": "task_completed", "source": "driver", "source_version": "0.16.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 1463.591, "cost_usd": 3.6375757999999996, "input_tokens": 252, "output_tokens": 38843, "cache_read_input_tokens": 13565849, "cache_creation_input_tokens": 133868}], "type": "implementation", "re_arm_count": 0, "cost_usd": 3.637576, "cumulative_cost_usd": 3.637576, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
 {"timestamp": "2026-09-07T22:47:59.300539+00:00", "correlation_id": "FEAT-2026-0101", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.16.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0101/T01", "driver_paths": ["specfuse/loop/loop.py"], "halted": true, "reason": "driver_restart_required", "remaining_wu_ids": ["FEAT-2026-0101/T02", "FEAT-2026-0101/T03"], "resume_command": "python3 -m specfuse.loop.loop --feature FEAT-2026-0101"}}
+{"timestamp": "2026-09-07T22:52:23.241802+00:00", "correlation_id": "FEAT-2026-0101/T02", "event_type": "task_started", "source": "driver", "source_version": "0.16.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-07T23:10:46.070039+00:00", "correlation_id": "FEAT-2026-0101/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.16.0", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 1102.746, "cost_usd": 1.1766986, "input_tokens": 74, "output_tokens": 15936, "cache_read_input_tokens": 3219373, "cache_creation_input_tokens": 93329, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "test_package_data_matches_canonical", "failure_excerpt": "### tests: FAIL\n#207: surefire failures name Class.method, not 'FAIL: test_*' \u2014 ... ok\nFAIL: test_package_data_matches_canonical (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_data_matches_canonical)\nTraceback (most recent call \n...\nted to the failure. Run the command directly.\nNO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output \u2014 the lines above are the tail only, and may be unrelated to the failure. Run the command directly.", "files_touched": ["tests/test_close_records_feature_oracle.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
diff --git a/.specfuse/rules/close-discipline.md b/.specfuse/rules/close-discipline.md
index 8074e24..e58b278 100644
--- a/.specfuse/rules/close-discipline.md
+++ b/.specfuse/rules/close-discipline.md
@@ -34,6 +34,18 @@ output directory before asserting — stale output satisfies any assertion.
 > catches the composite: all WUs individually green while the feature-level
 > oracle fails.
 
+When the gate declares a `feature_oracle` (FEAT-2026-0101), that command *is*
+the feature-level re-run this section asks for — not a parallel obligation
+beside it. `[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]`:
+re-running every producing unit's own oracle is not this. Fifteen oracles
+re-ran green in one close and none could observe the defect, because none
+asserted on the path the feature was meant to change. `verify()` runs the
+declared `feature_oracle` fresh on every unit's own attempt already; the close
+records that same fresh re-run's verdict in `## Measurements` as `###
+feature_oracle: PASS` or `### feature_oracle: FAIL` — `specfuse lint
+--closing` refuses a close that omits it once the gate has made the
+declaration.
+
 **You measure; the judge concludes (FEAT-2026-0100).** Re-running the oracles
 is your job and it does not change. Deciding what their exit codes *mean* for
 the feature is not: on a terminal gate the driver dispatches a separate judge
diff --git a/specfuse/loop/closing_requirements.py b/specfuse/loop/closing_requirements.py
index 794ef01..de2de78 100644
--- a/specfuse/loop/closing_requirements.py
+++ b/specfuse/loop/closing_requirements.py
@@ -140,6 +140,23 @@ def gate_section_heading_re(gate_n: int) -> re.Pattern:
     )
 
 
+#: The frontmatter key a `GATE-NN.md` declares its feature-level oracle
+#: under, and the synthetic gate name `verify()` runs it as (`loop.py`'s
+#: `read_gate_feature_oracle` / the `gate_set.append` in `verify()`). Reused
+#: here, not re-spelled, so the closing lint's "was it recorded" check can
+#: never drift from the literal the driver actually runs it under.
+FEATURE_ORACLE_KEY = "feature_oracle"
+
+#: A close records a fresh gate re-run as `### <name>: PASS` or `### <name>:
+#: FAIL` (`loop._run_gate_set`'s report format) inside `## Measurements`.
+#: Matches that exact shape for the `feature_oracle` gate name specifically —
+#: FEAT-2026-0101/T02's binary signal that the gate's declared oracle was
+#: re-run and its verdict recorded, not just that some gate passed.
+FEATURE_ORACLE_VERDICT_RE = re.compile(
+    rf"^#{{1,6}}\s*{re.escape(FEATURE_ORACLE_KEY)}:\s*(PASS|FAIL)\b",
+    re.MULTILINE | re.IGNORECASE,
+)
+
 GATE_REVIEW_FILENAME_TEMPLATE = "GATE-{next_gate:02d}-REVIEW.md"
 
 
@@ -327,6 +344,21 @@ CLOSING_REQUIREMENTS: dict[str, list[Requirement]] = {
             applies_when="verdict_not_met",
             enforced_by="assert_followups_recorded",
         ),
+        Requirement(
+            id="close-n", wu_type="close", phase="pre-squash",
+            description=(
+                "When the gate this close closes declares a "
+                f"`{FEATURE_ORACLE_KEY}`, RETROSPECTIVE.md's "
+                "'## Measurements' section records its fresh-re-run verdict "
+                f"as '### {FEATURE_ORACLE_KEY}: PASS' or '### "
+                f"{FEATURE_ORACLE_KEY}: FAIL' — the composite question the "
+                "feature's own units were each too small to ask "
+                "([FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question])"
+            ),
+            file=RETROSPECTIVE_FILENAME,
+            applies_when="feature_oracle_declared",
+            enforced_by="assert_feature_oracle_recorded",
+        ),
         Requirement(
             id="close-l", wu_type="close", phase="pre-squash",
             description=(
@@ -385,6 +417,21 @@ CLOSING_REQUIREMENTS: dict[str, list[Requirement]] = {
             file=LEARNINGS_PATH,
             enforced_by="assert_learnings_staged_under_auto",
         ),
+        Requirement(
+            id="close-intermediate-g", wu_type="close-intermediate", phase="pre-squash",
+            description=(
+                "When the gate this close closes declares a "
+                f"`{FEATURE_ORACLE_KEY}`, RETROSPECTIVE.md's "
+                "'## Measurements' section records its fresh-re-run verdict "
+                f"as '### {FEATURE_ORACLE_KEY}: PASS' or '### "
+                f"{FEATURE_ORACLE_KEY}: FAIL' — the composite question the "
+                "feature's own units were each too small to ask "
+                "([FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question])"
+            ),
+            file=RETROSPECTIVE_FILENAME,
+            applies_when="feature_oracle_declared",
+            enforced_by="assert_feature_oracle_recorded",
+        ),
         Requirement(
             id="close-intermediate-f", wu_type="close-intermediate", phase="pre-squash",
             description=(
diff --git a/specfuse/loop/data/rules/close-discipline.md b/specfuse/loop/data/rules/close-discipline.md
index 8074e24..e58b278 100644
--- a/specfuse/loop/data/rules/close-discipline.md
+++ b/specfuse/loop/data/rules/close-discipline.md
@@ -34,6 +34,18 @@ output directory before asserting — stale output satisfies any assertion.
 > catches the composite: all WUs individually green while the feature-level
 > oracle fails.
 
+When the gate declares a `feature_oracle` (FEAT-2026-0101), that command *is*
+the feature-level re-run this section asks for — not a parallel obligation
+beside it. `[FEAT-2026-0057/G1-CLOSE/feature-oracle-is-a-different-question]`:
+re-running every producing unit's own oracle is not this. Fifteen oracles
+re-ran green in one close and none could observe the defect, because none
+asserted on the path the feature was meant to change. `verify()` runs the
+declared `feature_oracle` fresh on every unit's own attempt already; the close
+records that same fresh re-run's verdict in `## Measurements` as `###
+feature_oracle: PASS` or `### feature_oracle: FAIL` — `specfuse lint
+--closing` refuses a close that omits it once the gate has made the
+declaration.
+
 **You measure; the judge concludes (FEAT-2026-0100).** Re-running the oracles
 is your job and it does not change. Deciding what their exit codes *mean* for
 the feature is not: on a terminal gate the driver dispatches a separate judge
diff --git a/specfuse/loop/lint_closing.py b/specfuse/loop/lint_closing.py
index cb34f4e..9509503 100644
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
@@ -48,6 +54,8 @@ class ClosingContext:
     wbody: str
     _diff_paths: list[str] | None = field(default=None, repr=False)
     _failures_present: bool | None = field(default=None, repr=False)
+    _feature_oracle: str | None = field(default=None, repr=False)
+    _feature_oracle_read: bool = field(default=False, repr=False)
 
     def changed_paths(self) -> list[str]:
         if self._diff_paths is None:
@@ -62,6 +70,25 @@ class ClosingContext:
             self._failures_present = summary != creq.NO_FAILURES_SENTINEL
         return self._failures_present
 
+    def declared_feature_oracle(self) -> str | None:
+        """The current gate's declared `feature_oracle` command, or None.
+
+        Reads the same `GATE-NN.md` frontmatter `verify()` reads via
+        `read_gate_feature_oracle` — never a second parse of the key.
+        Cached: this WU's own gate does not change mid-lint.
+        """
+        if not self._feature_oracle_read:
+            self._feature_oracle_read = True
+            gate = next(
+                (g for g in self.gates if g.get("gate") == self.gate_num), None,
+            )
+            gate_rel = gate.get("file") if gate else None
+            if gate_rel:
+                gate_path = self.feature_dir / gate_rel
+                if gate_path.is_file():
+                    self._feature_oracle = read_gate_feature_oracle(gate_path)
+        return self._feature_oracle
+
 
 def _run_git(repo_root: Path, *args: str) -> str:
     proc = subprocess.run(
@@ -299,6 +326,25 @@ def _check_followups_recorded(req: creq.Requirement, ctx: ClosingContext):
     return True, ""
 
 
+def _check_feature_oracle_recorded(req: creq.Requirement, ctx: ClosingContext):
+    oracle = ctx.declared_feature_oracle()
+    if not oracle:
+        return None  # applies_when already gates this; defensive no-op
+    retro = ctx.feature_dir / creq.RETROSPECTIVE_FILENAME
+    if not retro.exists():
+        return False, (
+            f"gate declares `{creq.FEATURE_ORACLE_KEY}` but "
+            f"{creq.RETROSPECTIVE_FILENAME} is absent"
+        )
+    section = slice_wu_section(retro.read_text(), MEASUREMENTS_SECTION)
+    if not section or not creq.FEATURE_ORACLE_VERDICT_RE.search(section):
+        return False, (
+            f"gate declares `{creq.FEATURE_ORACLE_KEY}` but "
+            f"'## {MEASUREMENTS_SECTION}' records no PASS/FAIL verdict for it"
+        )
+    return True, ""
+
+
 def check_criteria_state_well_formed(req: creq.Requirement, ctx: ClosingContext) -> list[str]:
     """One finding per untrustworthy entry in `GATE-NN-CRITERIA.md`, or none.
 
@@ -368,6 +414,7 @@ _CHECKS = {
     "assert_changelog_entry_for_contract_changes": _check_changelog_entry_for_contract_changes,
     "check_criteria_state_well_formed": check_criteria_state_well_formed,
     "assert_followups_recorded": _check_followups_recorded,
+    "assert_feature_oracle_recorded": _check_feature_oracle_recorded,
 }
 
 
@@ -468,6 +515,9 @@ def lint_closing(feature_dir: Path) -> tuple[list[str], list[str]]:
             artifact_path = ctx.feature_dir / criteria_state.criteria_filename(ctx.gate_num)
             if not artifact_path.is_file():
                 continue
+        elif req.applies_when == "feature_oracle_declared":
+            if ctx.gate_num is None or not ctx.declared_feature_oracle():
+                continue
 
         checker = _CHECKS.get(req.enforced_by)
         if checker is None:

```
