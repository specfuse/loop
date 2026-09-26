### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_distilled_file_is_under_its_own_sub_budget (test_binding_block_allocation.BindingBlockAllocationTests.test_distilled_file_is_under_its_own_sub_budget)
Traceback (most recent call last):
    raise AssertionError(
AssertionError: binding block is 2640 words, over its 2500-word cap
FAIL: test_tree_passes_the_blocking_check (test_binding_block_allocation.BindingBlockAllocationTests.test_tree_passes_the_blocking_check)
... (5152 line(s) elided) ...
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christian/Specfuse/loop/tests/test_binding_block_allocation.py", line 22, in test_tree_passes_the_blocking_check
    check_binding_block_budget()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/christian/Specfuse/loop/specfuse/loop/loop.py", line 238, in check_binding_block_budget
    raise AssertionError(
    ...<2 lines>...
    )
AssertionError: binding block is 2640 words, over its 2500-word cap

----------------------------------------------------------------------
Ran 4381 tests in 210.774s

FAILED (failures=2, skipped=3)
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/tests-20260926T165305141484Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/lint-20260926T165305188026Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/agent-policy-example-lint-20260926T165305269428Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 79 events.jsonl file(s), 2372 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/event-type-gate-20260926T165305391389Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/roadmap-link-gate-20260926T165305434905Z.log
```

### arm-sweep-gate: PASS
```
$ python3 .specfuse/scripts/arm_sweep_gate.py
branch-observation table:
  budget_projection          observed=[clean, fired]; NEVER not_evaluable
  judge_editing              observed=[clean, fired]; NEVER not_evaluable
  decision_class_paths       observed=[clean, fired]; NEVER not_evaluable
  retroactive_edits          observed=[clean, fired]; NEVER not_evaluable
  drift_caps                 observed=[clean, fired]; NEVER not_evaluable
  missing_provenance         observed=[clean, fired]; NEVER not_evaluable
  open_questions_human_only  observed=[clean, fired]; NEVER not_evaluable
  plan_next_lint             observed=[clean, fired]; NEVER not_evaluable
evaluable=40 evaluated=40 could_not_evaluate=0 excluded_no_baseline=47
ok: 40 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/arm-sweep-gate-20260926T165305769472Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/monitoring-example-lint-20260926T165305813849Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b
test_blocked_with_blocked_next_under_review_autonomy_escalates (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_with_blocked_next_under_review_autonomy_escalates) ... ok
test_blocked_with_valid_blocked_next_inserts_and_continues (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_with_valid_blocked_next_inserts_and_continues) ... ok
test_blocked_without_blocked_next_escalates_unchanged (tests.test_fix_unit_insertion_e2e.FixUnitInsertionEndToEndTest.test_blocked_without_blocked_next_escalates_unchanged) ... ok

----------------------------------------------------------------------
Ran 3 tests in 1.172s

OK
full output: .specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/work/gate-logs/feature_oracle-20260926T165307064417Z.log
```

NOTE: narrow_command declared on gate 'tests' did not fire this attempt: the selection resolved to nothing under narrow_selection.test_roots ['tests/'] (produces: offered .specfuse/rules/result-contract.md, specfuse/loop/data/rules/result-contract.md, .specfuse/skills/authoring-work-units/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example); ran the full command instead. Set `narrow_selection.test_roots` (and `format`) on that gate in .specfuse/verification.yml if this repo's tests live elsewhere.

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md
index 157b11a..17f4c42 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0115/T04
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 3.00
 produces:
   - .specfuse/rules/result-contract.md
@@ -12,6 +12,11 @@ produces:
   - specfuse/loop/data/docs/methodology.md
   - .specfuse/verification.yml.example
   - specfuse/loop/data/verification.yml.example
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.25.0
+started_at: 2026-09-26T16:46:31.895526+00:00
 ---
 
 # Document `blocked_next:` where the sessions and the authors read
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
index bc8ed95..5bc8559 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
@@ -13,3 +13,8 @@
 {"timestamp": "2026-09-26T16:33:29.997845+00:00", "correlation_id": "FEAT-2026-0115/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 225.451, "cost_usd": 1.3358510000000003, "input_tokens": 96, "output_tokens": 23777, "cache_read_input_tokens": 3862865, "cache_creation_input_tokens": 81329, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-03-auto-close-and-brief.md", "specfuse/loop/gate_eval.py", "specfuse/loop/loop.py", "tests/test_fix_unit_insertion_bookkeeping.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-26T16:33:29.997999+00:00", "correlation_id": "FEAT-2026-0115/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 225.451, "cost_usd": 1.3358510000000003, "input_tokens": 96, "output_tokens": 23777, "cache_read_input_tokens": 3862865, "cache_creation_input_tokens": 81329}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.335851, "cumulative_cost_usd": 1.335851, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
 {"timestamp": "2026-09-26T16:35:05.871522+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.25.0", "payload": {"tree": "cda5ba7aadd38d0fa6d7dc7a9c6273975bc961dd", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/cda5ba7aadd38d0fa6d7dc7a9c6273975bc961dd/specfuse/loop"}}
+{"timestamp": "2026-09-26T16:35:06.003036+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 1}}
+{"timestamp": "2026-09-26T16:35:06.003040+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "re_arm_dispatched", "source": "driver", "source_version": "0.25.0", "payload": {"re_arm_count": 1, "reason": "Both sessions reported status: blocked with a real reason (the unit forbade the edits its own design needed); the driver read the block-scalar RESULT as complete (#3436) and escalated as a spin. Unit re-scoped to write-then-evaluate; override because the escalated signature is the parse defect, not the unit."}}
+{"timestamp": "2026-09-26T16:46:31.815626+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 685.709, "cost_usd": 3.124198799999999, "input_tokens": 156, "output_tokens": 58420, "cache_read_input_tokens": 9614814, "cache_creation_input_tokens": 154181, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md", "specfuse/loop/loop.py", "tests/test_fix_unit_insertion_e2e.py", "tests/test_fix_unit_insertion_refused.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:46:31.815869+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 685.709, "cost_usd": 3.124198799999999, "input_tokens": 156, "output_tokens": 58420, "cache_read_input_tokens": 9614814, "cache_creation_input_tokens": 154181}], "type": "implementation", "re_arm_count": 1, "cost_usd": 3.124199, "cumulative_cost_usd": 3.124199, "attempts_lifetime": 3, "planned_cost_usd": 5.0}}
+{"timestamp": "2026-09-26T16:46:31.822496+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0115/T02", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "cda5ba7aadd38d0fa6d7dc7a9c6273975bc961dd", "next_pin_tree": "e00d97b42e626f00a759afaf791e209a592ead49"}}
diff --git a/.specfuse/rules/result-contract.md b/.specfuse/rules/result-contract.md
index 5425926..bda5869 100644
--- a/.specfuse/rules/result-contract.md
+++ b/.specfuse/rules/result-contract.md
@@ -67,6 +67,10 @@ acceptance_criteria:
     met: true | false
     evidence: <how you know — a test name, a behavior, a line reference>
 blocked_reason: <present only when status is blocked>
+blocked_next:                     # optional — present only when status is blocked
+  kind: fix_unit
+  file: <path to the drafted fix-unit WU file, relative to the feature dir>
+  id: <the drafted unit's own correlation ID, e.g. FEAT-YYYY-NNNN/T05>
 produces_unchanged:                # optional — obligation 1 below
   - path: <a produces: entry, verbatim>
     justification: <the command you ran and its output showing the deliverable already holds>
@@ -111,6 +115,16 @@ never required by any guard. Omit it and nothing changes: the driver's
    unresolvable build dependencies) reports where the suite ran, not the
    repository (#2075).
 
+8. **`blocked_next:` names a drafted fix unit, not a wish.** When a `blocked`
+   session has already written the fix as a new work-unit file inside the
+   feature dir, name it in `blocked_next:` instead of leaving the block to a
+   human. The driver inserts that draft ahead of the blocked unit when the
+   feature runs `auto` and the draft passes its arm checks — the same
+   predicate a gate arm runs, plus the insertion caps. The draft file itself
+   must already carry `provenance: agent`, `status: draft`, and the work
+   unit's five sections before you name it; an insertion the checks refuse
+   falls back to today's escalation, unchanged.
+
 ## Closing obligations for implementation WUs (FEAT-2026-0049)
 
 1. **Diff against `produces:` first.** Every path in the WU's `produces:` list
diff --git a/.specfuse/skills/authoring-work-units/SKILL.md b/.specfuse/skills/authoring-work-units/SKILL.md
index 9856dc4..5ab46d1 100644
--- a/.specfuse/skills/authoring-work-units/SKILL.md
+++ b/.specfuse/skills/authoring-work-units/SKILL.md
@@ -69,6 +69,12 @@ pre-existing unrelated state, a reasoned `status: blocked` with the evidence is
 right move ([`../../rules/result-contract.md`](../../rules/result-contract.md)).
 *Prevents:* a doubtful pass that spends the gate's trust budget.
 
+When a trigger is of the form "block; the fix is a new unit," the session should
+draft that fix unit itself and name it in the RESULT's `blocked_next: {kind:
+fix_unit, file, id}` field
+([`../../rules/result-contract.md`](../../rules/result-contract.md)) rather than
+leaving the gap for a human to fill — the block then costs no wait.
+
 ## 6. Sizing — one WU = one focused session's work
 
 A WU is crafted to land in a single fresh-session pass; the Ralph property (fresh
diff --git a/.specfuse/verification.yml.example b/.specfuse/verification.yml.example
index dd0ec10..f5fda7c 100644
--- a/.specfuse/verification.yml.example
+++ b/.specfuse/verification.yml.example
@@ -136,12 +136,20 @@
 #                               # ignored and the path is judged as an
 #                               # unjustified unchanged deliverable instead
 #                               # (FEAT-2026-0114).
+#   fix_unit_insertion: true    # whether a blocked RESULT's `blocked_next:`
+#                               # may insert its drafted fix unit instead of
+#                               # escalating to a human. Defaults to true.
+#   max_fix_units_per_unit: 2  # cap on `fix_unit_inserted` insertions per
+#                               # blocked unit, before insertion refuses and
+#                               # falls back to escalation. Defaults to 2.
 # defaults:
 #   max_attempts: 3
 #   retain_on_guard_refusal: true
 #   dispatch_skills: false
 #   post_merge_issue: false
 #   produces_amendable: false
+#   fix_unit_insertion: true
+#   max_fix_units_per_unit: 2
 #
 # The re-plan-after-two-failures behaviour (FEAT-2026-0104) reads this same
 # `max_attempts` resolution and adds no config key of its own — a unit's
diff --git a/docs/methodology.md b/docs/methodology.md
index f2dc699..620ec75 100644
--- a/docs/methodology.md
+++ b/docs/methodology.md
@@ -131,6 +131,13 @@ it mostly does not need. Author-set unless marked driver-owned.
   entries are accepted (`defaults.produces_amendable: true`): the paths dropped
   from this unit's recorded `produces:` (`.specfuse/rules/result-contract.md`).
 
+A blocked RESULT's `blocked_next:` (`.specfuse/rules/result-contract.md`) can
+name a drafted fix unit; a successful insertion emits a `fix_unit_inserted`
+event to `events.jsonl` and re-arms the blocked unit. Two `defaults:` keys in
+`verification.yml` govern it: `fix_unit_insertion` (default true) turns the
+whole mechanism on or off, and `max_fix_units_per_unit` (default 2) caps how
+many insertions one blocked unit accepts before falling back to escalation.
+
 ## 3. Work unit types
 
 Nine types share one state machine; type affects only who handles the unit and
diff --git a/plugins/specfuse/skills/authoring-work-units/SKILL.md b/plugins/specfuse/skills/authoring-work-units/SKILL.md
index 9856dc4..5ab46d1 100644
--- a/plugins/specfuse/skills/authoring-work-units/SKILL.md
+++ b/plugins/specfuse/skills/authoring-work-units/SKILL.md
@@ -69,6 +69,12 @@ pre-existing unrelated state, a reasoned `status: blocked` with the evidence is
 right move ([`../../rules/result-contract.md`](../../rules/result-contract.md)).
 *Prevents:* a doubtful pass that spends the gate's trust budget.
 
+When a trigger is of the form "block; the fix is a new unit," the session should
+draft that fix unit itself and name it in the RESULT's `blocked_next: {kind:
+fix_unit, file, id}` field
+([`../../rules/result-contract.md`](../../rules/result-contract.md)) rather than
+leaving the gap for a human to fill — the block then costs no wait.
+
 ## 6. Sizing — one WU = one focused session's work
 
 A WU is crafted to land in a single fresh-session pass; the Ralph property (fresh
diff --git a/specfuse/loop/data/docs/methodology.md b/specfuse/loop/data/docs/methodology.md
index f2dc699..620ec75 100644
--- a/specfuse/loop/data/docs/methodology.md
+++ b/specfuse/loop/data/docs/methodology.md
@@ -131,6 +131,13 @@ it mostly does not need. Author-set unless marked driver-owned.
   entries are accepted (`defaults.produces_amendable: true`): the paths dropped
   from this unit's recorded `produces:` (`.specfuse/rules/result-contract.md`).
 
+A blocked RESULT's `blocked_next:` (`.specfuse/rules/result-contract.md`) can
+name a drafted fix unit; a successful insertion emits a `fix_unit_inserted`
+event to `events.jsonl` and re-arms the blocked unit. Two `defaults:` keys in
+`verification.yml` govern it: `fix_unit_insertion` (default true) turns the
+whole mechanism on or off, and `max_fix_units_per_unit` (default 2) caps how
+many insertions one blocked unit accepts before falling back to escalation.
+
 ## 3. Work unit types
 
 Nine types share one state machine; type affects only who handles the unit and
diff --git a/specfuse/loop/data/rules/result-contract.md b/specfuse/loop/data/rules/result-contract.md
index 5425926..bda5869 100644
--- a/specfuse/loop/data/rules/result-contract.md
+++ b/specfuse/loop/data/rules/result-contract.md
@@ -67,6 +67,10 @@ acceptance_criteria:
     met: true | false
     evidence: <how you know — a test name, a behavior, a line reference>
 blocked_reason: <present only when status is blocked>
+blocked_next:                     # optional — present only when status is blocked
+  kind: fix_unit
+  file: <path to the drafted fix-unit WU file, relative to the feature dir>
+  id: <the drafted unit's own correlation ID, e.g. FEAT-YYYY-NNNN/T05>
 produces_unchanged:                # optional — obligation 1 below
   - path: <a produces: entry, verbatim>
     justification: <the command you ran and its output showing the deliverable already holds>
@@ -111,6 +115,16 @@ never required by any guard. Omit it and nothing changes: the driver's
    unresolvable build dependencies) reports where the suite ran, not the
    repository (#2075).
 
+8. **`blocked_next:` names a drafted fix unit, not a wish.** When a `blocked`
+   session has already written the fix as a new work-unit file inside the
+   feature dir, name it in `blocked_next:` instead of leaving the block to a
+   human. The driver inserts that draft ahead of the blocked unit when the
+   feature runs `auto` and the draft passes its arm checks — the same
+   predicate a gate arm runs, plus the insertion caps. The draft file itself
+   must already carry `provenance: agent`, `status: draft`, and the work
+   unit's five sections before you name it; an insertion the checks refuse
+   falls back to today's escalation, unchanged.
+
 ## Closing obligations for implementation WUs (FEAT-2026-0049)
 
 1. **Diff against `produces:` first.** Every path in the WU's `produces:` list
diff --git a/specfuse/loop/data/verification.yml.example b/specfuse/loop/data/verification.yml.example
index dd0ec10..f5fda7c 100644
--- a/specfuse/loop/data/verification.yml.example
+++ b/specfuse/loop/data/verification.yml.example
@@ -136,12 +136,20 @@
 #                               # ignored and the path is judged as an
 #                               # unjustified unchanged deliverable instead
 #                               # (FEAT-2026-0114).
+#   fix_unit_insertion: true    # whether a blocked RESULT's `blocked_next:`
+#                               # may insert its drafted fix unit instead of
+#                               # escalating to a human. Defaults to true.
+#   max_fix_units_per_unit: 2  # cap on `fix_unit_inserted` insertions per
+#                               # blocked unit, before insertion refuses and
+#                               # falls back to escalation. Defaults to 2.
 # defaults:
 #   max_attempts: 3
 #   retain_on_guard_refusal: true
 #   dispatch_skills: false
 #   post_merge_issue: false
 #   produces_amendable: false
+#   fix_unit_insertion: true
+#   max_fix_units_per_unit: 2
 #
 # The re-plan-after-two-failures behaviour (FEAT-2026-0104) reads this same
 # `max_attempts` resolution and adds no config key of its own — a unit's

```
