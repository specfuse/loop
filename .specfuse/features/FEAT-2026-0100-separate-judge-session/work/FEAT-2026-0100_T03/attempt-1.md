### tests: FAIL
```
$ python3 -m unittest discover -s tests -v -b
AssertionError: True is not false
FAIL: test_doc_set_missing_for_retrospective_fails (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_doc_set_missing_for_retrospective_fails)
Traceback (most recent call last):
AssertionError: True is not false
FAIL: test_empty_list_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_empty_list_for_type_fails_with_config_message)
Traceback (most recent call last):
AssertionError: True is not false : empty 'code' list must fail, not pass
FAIL: test_failing_gate_failure_message_is_distinguishable_from_config_error (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_failing_gate_failure_message_is_distinguishable_from_config_error)
Traceback (most recent call last):
AssertionError: True is not false
FAIL: test_missing_set_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_missing_set_for_type_fails_with_config_message)
Traceback (most recent call last):
AssertionError: True is not false : missing 'code' set must fail, not pass
FAIL: test_null_value_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_null_value_for_type_fails_with_config_message)
Traceback (most recent call last):
... (4607 line(s) elided) ...
AssertionError: True is not false

======================================================================
FAIL: test_passing_gate_with_real_command_still_works (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_passing_gate_with_real_command_still_works)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christian/Specfuse/loop/tests/test_verify_empty_gate_set.py", line 86, in test_passing_gate_with_real_command_still_works
    self.assertIn("PASS", msg)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^
AssertionError: 'PASS' not found in '(stub pass)'

----------------------------------------------------------------------
Ran 3728 tests in 123.785s

FAILED (failures=9, errors=5, skipped=3)
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

### coverage: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
AssertionError: True is not false
FAIL: test_missing_set_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_missing_set_for_type_fails_with_config_message)
Traceback (most recent call last):
AssertionError: True is not false : missing 'code' set must fail, not pass
FAIL: test_null_value_for_type_fails_with_config_message (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_null_value_for_type_fails_with_config_message)
Traceback (most recent call last):
AssertionError: True is not false
FAIL: test_passing_gate_with_real_command_still_works (test_verify_empty_gate_set.TestVerifyEmptyGateSet.test_passing_gate_with_real_command_still_works)
Traceback (most recent call last):
AssertionError: 'PASS' not found in '(stub pass)'
Ran 3728 tests in 127.943s
FAILED (failures=9, errors=5, skipped=3)
   POST-PASS INVARIANT FAILED — archive_anchor_missing: feat-2026-9500
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
... (2910 line(s) elided) ...

[21:13:45] -- FEAT-2026-9301/G1-PLAN [plan-next] model=claude-haiku-4-5-20251001 effort=high
   ↳ G1-PLAN
   [21:13:45] attempt 1/3 model=claude-haiku-4-5-20251001 effort=high — fresh session
   PASS — committed 2ea24ba7593e16e88b8dc2e3495636765ac4e3ce

Gate 1 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: the close recorded verdict `none recorded`, which is not a value the close contract recognises (['met', 'not_met']), so the terminal flips were withheld and there is no follow-up list to read. A close that records no usable verdict has not finished its job. Inspect RETROSPECTIVE.md / events.jsonl before flipping anything by hand.
WARN: WU-01-impl.md: implementation WU declares no 'produces:' deliverable list. See FEAT-2026-0022.
WARN: WU-90-gate-1-close.md: close WU's acceptance criteria are load-bearing (a close-discipline §1-§3 obligation, or a write to a surface outside this feature's folder) but frontmatter lacks 'auto_close_disabled: true' — evaluate_auto_close may skip this WU at attempts: 0 and every criterion in its body would go unfulfilled. See .specfuse/rules/close-discipline.md and #293.
WARN: WU-01-impl.md: missing 'planned_cost_usd' frontmatter (optional but recommended for cost-variance calibration). See PLAN.md roadmap_goal § Planned-cost capture.
WARN: /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp92is_m1s/FEAT-2026-0099-template-render-check/PLAN.md: missing 'planned_cost_usd' frontmatter (optional but recommended for cost-variance calibration). See PLAN.md roadmap_goal § Planned-cost capture.
WARN: /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp92is_m1s/FEAT-2026-0099-template-render-check/PLAN.md: missing 'Existing-mechanism search' section (planning-discipline; write it or an explicit 'n/a' line). See .specfuse/rules/planning-discipline.md.
WARN: /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp92is_m1s/FEAT-2026-0099-template-render-check/PLAN.md: missing 'Escalation-predicate satisfiability' section (planning-discipline; write it or an explicit 'n/a' line). See .specfuse/rules/planning-discipline.md.
WARN: /var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/tmp92is_m1s/FEAT-2026-0099-template-render-check/WU-90-gate-1-close.md: body does not instruct the agent to produce `## Cost analysis` (the heading assert_cost_analysis_section_when_met requires in RETROSPECTIVE.md when verdict is `met`). assert_cost_analysis_section_when_met checks this AFTER dispatch, so the refusal costs a full re-attempt. See close-discipline.md §4.
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

```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 68 events.jsonl file(s), 1711 event(s) checked
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
evaluable=29 evaluated=29 could_not_evaluate=0 excluded_no_baseline=45
ok: 29 evaluable feature(s) swept clean, no not_evaluable verdicts
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
diff --git a/.specfuse/features/FEAT-2026-0100-separate-judge-session/WU-03-judge-cost-accounting.md b/.specfuse/features/FEAT-2026-0100-separate-judge-session/WU-03-judge-cost-accounting.md
index cf560ef..96ec4bc 100644
--- a/.specfuse/features/FEAT-2026-0100-separate-judge-session/WU-03-judge-cost-accounting.md
+++ b/.specfuse/features/FEAT-2026-0100-separate-judge-session/WU-03-judge-cost-accounting.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0100/T03
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 model: sonnet
 effort: medium
@@ -11,6 +11,9 @@ produces_driver_helper: fold_judge_usage
 produces:
   - specfuse/loop/loop.py
   - tests/test_judge_cost.py
+gate_set: code
+driver_version: 0.15.0
+started_at: 2026-09-06T00:59:28.732576+00:00
 ---
 
 # The judge's spend is the close's spend
diff --git a/specfuse/loop/loop.py b/specfuse/loop/loop.py
index 4930297..0906650 100644
--- a/specfuse/loop/loop.py
+++ b/specfuse/loop/loop.py
@@ -6456,6 +6456,30 @@ def write_judge_followups(
     return path
 
 
+def fold_judge_usage(attempt_usage: dict, judge_envelope: dict | None) -> dict:
+    """Fold the judge session's usage envelope into a close attempt's usage.
+
+    Pure: returns a new dict, mutating neither argument. `judge_envelope` is
+    the usage dict `run_judge_session` (via `parse_claude_json_output`)
+    returns -- `None` when the judge produced no JSON envelope (a plain-text
+    response, a disabled judge, or a judge that never ran), in which case the
+    close attempt's own usage passes through unchanged. The close's spend is
+    the judge's spend too: cost analysis, the auto-close predicate, and
+    `/gate-status` must all see what the verdict actually cost, not just what
+    the close session cost before a second session re-checked its work.
+    """
+    folded = dict(attempt_usage)
+    if not judge_envelope:
+        return folded
+    folded["cost_usd"] = (float(folded.get("cost_usd", 0.0) or 0.0)
+                          + float(judge_envelope.get("cost_usd", 0.0) or 0.0))
+    for key in ("input_tokens", "output_tokens",
+                "cache_read_input_tokens", "cache_creation_input_tokens"):
+        folded[key] = (int(folded.get(key, 0) or 0)
+                       + int(judge_envelope.get(key, 0) or 0))
+    return folded
+
+
 def _judge_disabled(plan_fm: dict) -> bool:
     """True when PLAN.md frontmatter opts this feature out of the judge."""
     value = plan_fm.get(JUDGE_DISABLED_KEY)
@@ -8086,8 +8110,42 @@ def run(
                                                    f"{type(_exc).__name__}: {_exc}"),
                                     }
                                     print(f"   JUDGE ERROR — {_judged['reason']}")
+                                # The judge's spend is the close's spend
+                                # (FEAT-2026-0100/T03): fold BEFORE the
+                                # `judged` event is built, so `judge_cost_usd`
+                                # on that event and the folded total on the
+                                # close's own attempt_outcome/cost_usd below
+                                # agree on the same number. A judge that
+                                # produced no JSON envelope (disabled, plain
+                                # text, or never ran) folds in nothing.
+                                _judge_usage = _judged.get("usage")
+                                _judged["judge_cost_usd"] = float(
+                                    (_judge_usage or {}).get("cost_usd", 0.0) or 0.0)
                                 wu_events.append(build_event(
                                     "judged", wu.wu_id, _judged))
+                                if _judge_usage:
+                                    attempts_usage[-1] = fold_judge_usage(
+                                        attempts_usage[-1], _judge_usage)
+                                    cum_usage["cost_usd"] += _judged[
+                                        "judge_cost_usd"]
+                                    cum_usage["input_tokens"] += int(
+                                        _judge_usage.get("input_tokens", 0) or 0)
+                                    cum_usage["output_tokens"] += int(
+                                        _judge_usage.get("output_tokens", 0) or 0)
+                                    # wu.file was already squashed with the
+                                    # pre-judge cost; this is a post-squash
+                                    # write and must be committed on its own,
+                                    # same discipline as judge_close's own
+                                    # verdict-lowering commit, or a later
+                                    # reset would silently drop the judge's
+                                    # spend from the WU's frontmatter.
+                                    write_cost_to_wu(backend, wu, cum_usage)
+                                    commit_bookkeeping(
+                                        [wu.file],
+                                        f"chore(loop): {wu.wu_id} fold judge "
+                                        f"usage into close cost"
+                                        f"\n\nFeature: {wu.wu_id}",
+                                    )
                             # Re-read frontmatter post-squash: the agent writes
                             # `verdict:` to the WU file DURING dispatch, but
                             # `wu.verdict` was populated by `load_wu` BEFORE

```
