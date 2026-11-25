### tests: PASS
```
$ python3 -m unittest tests.test_gate_timings -v -b
test_ok_skipped_and_durations (tests.test_gate_timings.TestAttemptGateEvents.test_ok_skipped_and_durations) ... ok
test_one_gate_result_per_gate_with_payload (tests.test_gate_timings.TestAttemptGateEvents.test_one_gate_result_per_gate_with_payload) ... ok
test_stub_verify_without_gate_results_emits_nothing (tests.test_gate_timings.TestAttemptGateEvents.test_stub_verify_without_gate_results_emits_nothing) ... ok
test_split (tests.test_gate_timings.TestAttemptSplit.test_split) ... skipped 'T02 owns the agent_seconds/verify_seconds split'
test_phases (tests.test_gate_timings.TestBaselineAndBroadPhases.test_phases) ... skipped 'T03 owns baseline and broad gate_result phases'
test_every_emitted_event_type_validates (tests.test_gate_timings.TestNothingExistingChanges.test_every_emitted_event_type_validates) ... skipped 'T02-T04 own the remaining clause-5 checks'
test_gate_result_in_schema_event_types (tests.test_gate_timings.TestNothingExistingChanges.test_gate_result_in_schema_event_types) ... ok
test_stats (tests.test_gate_timings.TestStatsReport.test_stats) ... skipped 'T04 owns the specfuse stats report'

----------------------------------------------------------------------
Ran 8 tests in 1.286s

OK (skipped=4)
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/tests-20261125T152018611236Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/lint-20261125T152018695313Z.log
```

### changelog-fragments: PASS
```
$ python3 -m specfuse.loop.changelog_fragments check
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/changelog-fragments-20261125T152018780185Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/agent-policy-example-lint-20261125T152018961483Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 90 events.jsonl file(s), 2845 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/event-type-gate-20261125T152019230269Z.log
```

### roadmap-link-gate: FAIL
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-LOOP-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-loop-2026-0011)' or '[→ archive](roadmap-archive.md#feat-loop-2026-0011)'
ERROR: roadmap.md:131: ref '#feat-loop-2026-0250' in roadmap.md does not resolve — no anchor 'feat-loop-2026-0250' found in roadmap.md or roadmap-archive.md
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 1 error(s), 1 warning(s)

1 roadmap-link error(s).
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/roadmap-link-gate-20261125T152019309405Z.log
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
evaluable=51 evaluated=51 could_not_evaluate=0 excluded_no_baseline=45
ok: 51 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/arm-sweep-gate-20261125T152019943949Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/monitoring-example-lint-20261125T152020003773Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_gate_timings -v -b
test_ok_skipped_and_durations (tests.test_gate_timings.TestAttemptGateEvents.test_ok_skipped_and_durations) ... ok
test_one_gate_result_per_gate_with_payload (tests.test_gate_timings.TestAttemptGateEvents.test_one_gate_result_per_gate_with_payload) ... ok
test_stub_verify_without_gate_results_emits_nothing (tests.test_gate_timings.TestAttemptGateEvents.test_stub_verify_without_gate_results_emits_nothing) ... ok
test_split (tests.test_gate_timings.TestAttemptSplit.test_split) ... skipped 'T02 owns the agent_seconds/verify_seconds split'
test_phases (tests.test_gate_timings.TestBaselineAndBroadPhases.test_phases) ... skipped 'T03 owns baseline and broad gate_result phases'
test_every_emitted_event_type_validates (tests.test_gate_timings.TestNothingExistingChanges.test_every_emitted_event_type_validates) ... skipped 'T02-T04 own the remaining clause-5 checks'
test_gate_result_in_schema_event_types (tests.test_gate_timings.TestNothingExistingChanges.test_gate_result_in_schema_event_types) ... ok
test_stats (tests.test_gate_timings.TestStatsReport.test_stats) ... skipped 'T04 owns the specfuse stats report'

----------------------------------------------------------------------
Ran 8 tests in 1.283s

OK (skipped=4)
full output: .specfuse/features/FEAT-LOOP-2026-0250-gate-timings/work/gate-logs/feature_oracle-20261125T152021386511Z.log
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-LOOP-2026-0250-gate-timings/WU-01-attempt-gate-events.md b/.specfuse/features/FEAT-LOOP-2026-0250-gate-timings/WU-01-attempt-gate-events.md
index bcfb5a7..18533d2 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0250-gate-timings/WU-01-attempt-gate-events.md
+++ b/.specfuse/features/FEAT-LOOP-2026-0250-gate-timings/WU-01-attempt-gate-events.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-LOOP-2026-0250/T01
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 oracle_env: macos_local
 planned_cost_usd: 4.00
 produces:
@@ -13,6 +13,9 @@ produces_driver_helper:
   - _run_gate_set
 model: sonnet
 effort: medium
+gate_set: code
+driver_version: 0.33.2
+started_at: 2026-11-25T15:15:30.163148+00:00
 ---
 
 # T01 — walking skeleton: attempt-phase `gate_result` events
diff --git a/specfuse/loop/data/schemas/driver-event.schema.json b/specfuse/loop/data/schemas/driver-event.schema.json
index 7a1c356..12c4037 100644
--- a/specfuse/loop/data/schemas/driver-event.schema.json
+++ b/specfuse/loop/data/schemas/driver-event.schema.json
@@ -3,9 +3,10 @@
   "$id": "https://specfuse.dev/loop/schemas/driver-event.schema.json",
   "title": "Driver-local envelope registry",
   "description": "Additive to the vendored orchestrator envelope (event.schema.json): shapes the loop driver emits with no orchestrator-side counterpart. validate_event.py resolves each shape against the vendored envelope first; only when absent there does it fall through to this registry. `event_types` (FEAT-2026-0060) widens the event_type enum; task_started, task_completed, and human_escalation are already sanctioned in the vendored enum and must not be duplicated here. `correlation_id` (FEAT-2026-0073) widens the correlation_id pattern to admit the closing-sequence and hygiene shapes `.specfuse/rules/correlation-ids.md` documents; `closing_names` and `hygiene_suffix_pattern` here must state the same set of shapes as that rules file's combined pattern (and as specfuse/loop/lint_plan.py's CORRELATION_ID_RE, which independently enforces the same contract on PLAN.md graphs).",
-  "$comment": "FEAT-2026-0060/T01: event_types derived from the union of every build_event(...) call site in specfuse/loop/loop.py and a corpus sweep of every .specfuse/features/*/events.jsonl, subtracting the vendored envelope enum. attempt_outcome and gate_reached were already-known precedent (loop.py's build_arm_predicate_event docstring); auto_close_decision, arm_predicate_evaluated, re_arm_dispatched, plan_next_draft_lint, and unsandboxed_dispatch are additional driver-local mechanics the orchestrator has no concept of. gate_auto_armed (loop.py build_event call under gate_events.append) and re_arm_rejected (loop.py build_event call under the spinning_reproduction_missing re-arm check) are emitted by real code paths that have never fired in a recorded run, so a corpus-only sweep cannot see them; they are included because call-site derivation does. FEAT-2026-0073/T01: correlation_id added — closing_names and hygiene_suffix_pattern mirror correlation-ids.md's documented shapes and lint_plan.py's CORRELATION_ID_RE verbatim, so the envelope, the rules file, and the PLAN-graph linter state one contract. FEAT-2026-0075/T03: driver_staleness_detected added — emitted at gate completion when a work unit's squash diff touched the driver's own importable surface, naming the editing unit, the driver paths it touched, and the IDs of units this process dispatched afterward (which ran the pre-edit module). FEAT-2026-0100/T02: judged added — emitted once per terminal close after the closing-deliverable guards, carrying the close's own verdict, the judge session's verdict (null when the judge was disabled, timed out, or returned nothing parseable, with the reason beside it), and whether the judge lowered it. FEAT-2026-0109/T01: baseline_attribution added — emitted when the retroactive per-attempt-failure baseline probe (attribute_failure_to_baseline) runs fresh, carrying the gate, the failing-gate set, and the unit whose failed attempt triggered the probe. FEAT-2026-0109/T06: broad_run_result added — emitted whenever the once-per-gate broad verification pass (gate_broad_run_check) actually runs (never on a tree-unchanged dedup skip), carrying the gate, the tree it was measured on, and its pass/fail outcome; a failing broad run additionally raises the existing human_escalation event type with reason: broad_run_gate_failure, which needs no schema addition since human_escalation is already sanctioned in the vendored envelope enum. FEAT-2026-0109/T08: driver_build_pinned added — emitted once per process, before any work unit is dispatched, when this process is itself a materialized pin (`_reexec_pinned`); carries the pin's tree hash and its path so an operator or test can read what build actually ran without inferring it from `ps` output. `driver_staleness_detected` needed no addition here: this unit reuses it with `halted: false` for the pinned, non-halting case (the registry constrains the type list, not the payload), adding `pinned_tree` / `next_pin_tree` fields alongside the existing `halted: true` shape. FEAT-2026-0104/T04: replan added — emitted once a re-plan turn (T03's run_replan_turn) rewrites a unit's body ahead of its last permitted attempt, so gate_eval.py's evaluate_auto_close (check 2, already reading this event_type since FEAT-2026-0018/T02) can disable auto-close for a gate that needed one. FEAT-2026-0115/T01: fix_unit_inserted added — emitted once a blocked RESULT's `blocked_next:` names a drafted fix unit that `insert_fix_unit` validated and inserted ahead of the blocked unit, carrying the fix unit's id, its file, the gate, and the insertion count; the blocked unit's own re-arm (an existing `re_arm_dispatched`, reason `fix_unit_inserted`) rides alongside it, so this is the only genuinely new event_type the mechanic needs. FEAT-2026-0246/T01: terminal_judge_editing_evaluated added — emitted on every terminal gate immediately before the close (auto or dispatched), carrying the gate, the `arm_eval.evaluate_terminal_judge_editing` verdict status and reason; a `fired` verdict additionally raises the existing human_escalation event type with reason: judge_editing_terminal, which needs no schema addition. FEAT-2026-0246/T02: terminal_judge_editing_acknowledged added — emitted when that check is clean only because the close unit carries an operator-authored judge_edit_acknowledged field covering every hit, carrying the gate, close unit id, acknowledged paths, and the operator's reason. FEAT-2026-0247/T06: the correlation-ID shape (legacy FEAT-YYYY-NNNN and the keyed FEAT-<KEY>-YYYY-NNNN form) now comes from specfuse.loop.ids.",
+  "$comment": "FEAT-2026-0060/T01: event_types derived from the union of every build_event(...) call site in specfuse/loop/loop.py and a corpus sweep of every .specfuse/features/*/events.jsonl, subtracting the vendored envelope enum. attempt_outcome and gate_reached were already-known precedent (loop.py's build_arm_predicate_event docstring); auto_close_decision, arm_predicate_evaluated, re_arm_dispatched, plan_next_draft_lint, and unsandboxed_dispatch are additional driver-local mechanics the orchestrator has no concept of. gate_auto_armed (loop.py build_event call under gate_events.append) and re_arm_rejected (loop.py build_event call under the spinning_reproduction_missing re-arm check) are emitted by real code paths that have never fired in a recorded run, so a corpus-only sweep cannot see them; they are included because call-site derivation does. FEAT-2026-0073/T01: correlation_id added — closing_names and hygiene_suffix_pattern mirror correlation-ids.md's documented shapes and lint_plan.py's CORRELATION_ID_RE verbatim, so the envelope, the rules file, and the PLAN-graph linter state one contract. FEAT-2026-0075/T03: driver_staleness_detected added — emitted at gate completion when a work unit's squash diff touched the driver's own importable surface, naming the editing unit, the driver paths it touched, and the IDs of units this process dispatched afterward (which ran the pre-edit module). FEAT-2026-0100/T02: judged added — emitted once per terminal close after the closing-deliverable guards, carrying the close's own verdict, the judge session's verdict (null when the judge was disabled, timed out, or returned nothing parseable, with the reason beside it), and whether the judge lowered it. FEAT-2026-0109/T01: baseline_attribution added — emitted when the retroactive per-attempt-failure baseline probe (attribute_failure_to_baseline) runs fresh, carrying the gate, the failing-gate set, and the unit whose failed attempt triggered the probe. FEAT-2026-0109/T06: broad_run_result added — emitted whenever the once-per-gate broad verification pass (gate_broad_run_check) actually runs (never on a tree-unchanged dedup skip), carrying the gate, the tree it was measured on, and its pass/fail outcome; a failing broad run additionally raises the existing human_escalation event type with reason: broad_run_gate_failure, which needs no schema addition since human_escalation is already sanctioned in the vendored envelope enum. FEAT-2026-0109/T08: driver_build_pinned added — emitted once per process, before any work unit is dispatched, when this process is itself a materialized pin (`_reexec_pinned`); carries the pin's tree hash and its path so an operator or test can read what build actually ran without inferring it from `ps` output. `driver_staleness_detected` needed no addition here: this unit reuses it with `halted: false` for the pinned, non-halting case (the registry constrains the type list, not the payload), adding `pinned_tree` / `next_pin_tree` fields alongside the existing `halted: true` shape. FEAT-2026-0104/T04: replan added — emitted once a re-plan turn (T03's run_replan_turn) rewrites a unit's body ahead of its last permitted attempt, so gate_eval.py's evaluate_auto_close (check 2, already reading this event_type since FEAT-2026-0018/T02) can disable auto-close for a gate that needed one. FEAT-2026-0115/T01: fix_unit_inserted added — emitted once a blocked RESULT's `blocked_next:` names a drafted fix unit that `insert_fix_unit` validated and inserted ahead of the blocked unit, carrying the fix unit's id, its file, the gate, and the insertion count; the blocked unit's own re-arm (an existing `re_arm_dispatched`, reason `fix_unit_inserted`) rides alongside it, so this is the only genuinely new event_type the mechanic needs. FEAT-2026-0246/T01: terminal_judge_editing_evaluated added — emitted on every terminal gate immediately before the close (auto or dispatched), carrying the gate, the `arm_eval.evaluate_terminal_judge_editing` verdict status and reason; a `fired` verdict additionally raises the existing human_escalation event type with reason: judge_editing_terminal, which needs no schema addition. FEAT-2026-0246/T02: terminal_judge_editing_acknowledged added — emitted when that check is clean only because the close unit carries an operator-authored judge_edit_acknowledged field covering every hit, carrying the gate, close unit id, acknowledged paths, and the operator's reason. FEAT-2026-0247/T06: the correlation-ID shape (legacy FEAT-YYYY-NNNN and the keyed FEAT-<KEY>-YYYY-NNNN form) now comes from specfuse.loop.ids. FEAT-LOOP-2026-0250/T01: gate_result added — emitted once per gate per attempt (phase: attempt) alongside attempt_outcome, carrying the attempt, gate, ok, skipped, duration_seconds and phase, so per-gate wall-clock time is recorded instead of only the attempt total.",
   "event_types": [
     "attempt_outcome",
+    "gate_result",
     "gate_reached",
     "auto_close_decision",
     "arm_predicate_evaluated",
diff --git a/specfuse/loop/loop.py b/specfuse/loop/loop.py
index 17e32d9..4408b28 100644
--- a/specfuse/loop/loop.py
+++ b/specfuse/loop/loop.py
@@ -928,6 +928,12 @@ class WorkUnit:
     # attempt's RESULT named untouched paths outside `produces:` that got
     # silently dropped from files_changed. None on every other attempt.
     auto_repaired_files_changed: "list[str] | None" = None
+    # INTERNAL, never frontmatter (FEAT-LOOP-2026-0250/T01): the per-gate
+    # result dicts of the attempt's most recent `verify()` call, reset by
+    # `execute_unit_attempt` before each verification so the dispatch loop can
+    # emit one `gate_result` event per gate without changing `verify_fn`'s
+    # `(passed, evidence)` return contract. Empty when verify never ran.
+    last_gate_results: "list[dict]" = field(default_factory=list)
     # VESTIGIAL tracer-bullet opt-in (FEAT-2026-0104/T01). Parsed for
     # backward compatibility with fixtures that still declare it, but no
     # longer read by the dispatch loop — T02's `should_replan_instead_of_retry`
@@ -6759,7 +6765,10 @@ def _run_gate_set(
 ) -> list[dict]:
     """Run every gate in *gate_set* and return one result dict per gate.
 
-    Each dict is {"name": str, "ok": bool, "report": str} where "report" is
+    Each dict is {"name": str, "ok": bool, "report": str, "duration_seconds":
+    float, "skipped": bool} (the last two FEAT-LOOP-2026-0250/T01: wall-clock
+    seconds of a spawned gate; 0 and True for a gate skipped on a failed
+    dependency) where "report" is
     the same PASS/FAIL fenced block `verify()` has always produced. Factored
     out of `verify()` (FEAT-2026-0051/T01) so `probe_baseline()`
     can run the `code` set independent of any work unit without duplicating the
@@ -6795,6 +6804,8 @@ def _run_gate_set(
                     f"### {gate['name']}: SKIP — dependency "
                     f"'{failed_dep}' failed"
                 ),
+                "duration_seconds": 0,
+                "skipped": True,
             })
             continue
         command = gate["command"].replace("{feature_dir}", str(feature_dir))
@@ -6837,6 +6848,8 @@ def _run_gate_set(
                         f"(https://git-scm.com/download/win) so gate commands can "
                         f"run through bash.exe.\n```"
              
… (diff truncated)
--- /dev/null
+++ b/tests/test_gate_timings.py
+#
+# Copyright 2026 Specfuse contributors
+# Licensed under the Apache License, Version 2.0. See LICENSE.
+#
+"""FEAT-LOOP-2026-0250 — per-gate timings are recorded, and `specfuse stats` reads them.
+
+One class per Definition-of-done clause in GATE-01.md. T01 (walking skeleton)
+implements clause 1 and the schema half of clause 5; the other classes are
+skipped here and owned by T02, T03 and T04.
+"""
+
+from __future__ import annotations
+
+import json
+import tempfile
+import unittest
+from pathlib import Path
+
+from tests._loop_loader import REPO_ROOT, load_loop
+
+loop = load_loop()
+
+SCHEMA_PATH = (
+    REPO_ROOT / "specfuse" / "loop" / "data" / "schemas" / "driver-event.schema.json"
+)
+
+PASS_SLEEP = 0.4
+ORACLE_SLEEP = 0.2
+
+
+def _make_wu(feature_dir: Path) -> "loop.WorkUnit":
+    wu_file = feature_dir / "WU-01-gate-timings.md"
+    wu_file.write_text("---\nstatus: pending\n---\n")
+    return loop.WorkUnit(
+        wu_id="FEAT-LOOP-2026-9999/T01",
+        file=wu_file,
+        depends_on=[],
+        type="implementation",
+        model="sonnet",
+        status="pending",
+        attempts=1,
+        title="T01",
+        body="**Objective.** test",
+    )
+
+
+class TestAttemptGateEvents(unittest.TestCase):
+    """Clause 1 — one `gate_result` per gate per attempt, oracle included."""
+
+    def setUp(self):
+        self._tmp = tempfile.TemporaryDirectory()
+        self.addCleanup(self._tmp.cleanup)
+        self.feature_dir = Path(self._tmp.name)
+        (self.feature_dir / "work").mkdir()
+        self.gate_file = self.feature_dir / "GATE-01.md"
+        self.gate_file.write_text(
+            f'---\ngate: 1\nfeature_oracle: "sleep {ORACLE_SLEEP}"\n---\n'
+        )
+        self.cfg = {
+            "code": [
+                {"name": "slow_pass", "command": f"sleep {PASS_SLEEP}"},
+                {"name": "boom", "command": "exit 1"},
+                {"name": "after_boom", "command": "exit 0", "needs": ["boom"]},
+            ]
+        }
+
+    def _attempt(self):
+        wu = _make_wu(self.feature_dir)
+
+        def verify_fn(w, fd, gate_file=None):
+            return loop.verify(w, fd, cfg=self.cfg, gate_file=gate_file)
+
+        outcome, _payload, _usage = loop.execute_unit_attempt(
+            wu, self.feature_dir, None,
+            dispatch_fn=lambda w, note: "agent did things",
+            verify_fn=verify_fn,
+            prerun_cfg=self.cfg,
+            gate_file=self.gate_file,
+        )
+        events = loop.emit_gate_result_events(wu, 1, wu.last_gate_results)
+        return wu, outcome, events
+
+    def test_one_gate_result_per_gate_with_payload(self):
+        wu, outcome, events = self._attempt()
+        self.assertEqual(outcome, "failed")
+        self.assertEqual(
+            [e["payload"]["gate"] for e in events],
+            ["slow_pass", "boom", "after_boom", "feature_oracle"],
+        )
+        for e in events:
+            self.assertEqual(e["event_type"], "gate_result")
+            self.assertEqual(e["correlation_id"], wu.wu_id)
+            self.assertEqual(
+                set(e["payload"]),
+                {"attempt", "gate", "ok", "skipped", "duration_seconds", "phase"},
+            )
+            self.assertEqual(e["payload"]["attempt"], 1)
+            self.assertEqual(e["payload"]["phase"], "attempt")
+
+    def test_ok_skipped_and_durations(self):
+        _wu, _outcome, events = self._attempt()
+        by_gate = {e["payload"]["gate"]: e["payload"] for e in events}
+        self.assertTrue(by_gate["slow_pass"]["ok"])
+        self.assertFalse(by_gate["slow_pass"]["skipped"])
+        self.assertGreaterEqual(by_gate["slow_pass"]["duration_seconds"], PASS_SLEEP)
+        self.assertFalse(by_gate["boom"]["ok"])
+        self.assertFalse(by_gate["boom"]["skipped"])
+        self.assertGreater(by_gate["boom"]["duration_seconds"], 0)
+        self.assertFalse(by_gate["after_boom"]["ok"])
+        self.assertTrue(by_gate["after_boom"]["skipped"])
+        self.assertEqual(by_gate["after_boom"]["duration_seconds"], 0)
+        self.assertTrue(by_gate["feature_oracle"]["ok"])
+        self.assertGreaterEqual(
+            by_gate["feature_oracle"]["duration_seconds"], ORACLE_SLEEP
+        )
+
+    def test_stub_verify_without_gate_results_emits_nothing(self):
+        wu = _make_wu(self.feature_dir)
+        outcome, _p, _u = loop.execute_unit_attempt(
+            wu, self.feature_dir, None,
+            dispatch_fn=lambda w, note: "agent did things",
+            verify_fn=lambda w, fd: (True, "ok"),
+            prerun_cfg=self.cfg,
+        )
+        self.assertEqual(outcome, "passed")
+        self.assertEqual(wu.last_gate_results, [])
+        self.assertEqual(loop.emit_gate_result_events(wu, 1, wu.last_gate_results), [])
+
+
+class TestAttemptSplit(unittest.TestCase):
+    """Clause 2 — owned by T02."""
+
+    @unittest.skip("T02 owns the agent_seconds/verify_seconds split")
+    def test_split(self):
+        pass
+
+
+class TestBaselineAndBroadPhases(unittest.TestCase):
+    """Clause 3 — owned by T03."""
+
+    @unittest.skip("T03 owns baseline and broad gate_result phases")
+    def test_phases(self):
+        pass
+
+
+class TestStatsReport(unittest.TestCase):
+    """Clause 4 — owned by T04."""
+
+    @unittest.skip("T04 owns the specfuse stats report")
+    def test_stats(self):
+        pass
+
+
+class TestNothingExistingChanges(unittest.TestCase):
+    """Clause 5 — schema half implemented in T01; the rest owned by T02-T04."""
+
+    def test_gate_result_in_schema_event_types(self):
+        schema = json.loads(SCHEMA_PATH.read_text())
+        self.assertIn("gate_result", schema["event_types"])
+
+    @unittest.skip("T02-T04 own the remaining clause-5 checks")
+    def test_every_emitted_event_type_validates(self):
+        pass
+
+
+if __name__ == "__main__":
+    unittest.main()

```
