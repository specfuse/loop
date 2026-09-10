### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_package_docs_match_canonical (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_docs_match_canonical)
Traceback (most recent call last):
... (4645 line(s) elided) ...
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "Diffs:\n" + "\n".join(f"  {m}" for m in mismatches)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Docs seed out of sync with canonical docs/.
Run: scripts/sync-scaffold.sh

Diffs:
  content differs: docs/methodology.md

----------------------------------------------------------------------
Ran 3887 tests in 204.442s

FAILED (failures=1, skipped=3)
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml

```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 73 events.jsonl file(s), 2012 event(s) checked
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
  decision_class_paths       observed=[clean, fired]; NEVER not_evaluable
  retroactive_edits          observed=[clean, fired]; NEVER not_evaluable
  drift_caps                 observed=[clean, fired]; NEVER not_evaluable
  missing_provenance         observed=[clean, fired]; NEVER not_evaluable
  open_questions_human_only  observed=[clean, fired]; NEVER not_evaluable
  plan_next_lint             observed=[clean]; NEVER fired, NEVER not_evaluable
evaluable=34 evaluated=34 could_not_evaluate=0 excluded_no_baseline=45
ok: 34 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_guard_repair_e2e -v
Ran 2 tests in 1.442s
OK
... (21 line(s) elided) ...
== FEAT-2026-9601 — Gate 1 [open] (2 work units) ==

[23:15:07] -- FEAT-2026-9601/T01 [implementation] model=sonnet effort=medium
   ↳ T01
   [23:15:07] attempt 1/2 model=sonnet effort=medium — fresh session
   FILES_CHANGED MISMATCH attempt 1/2 — 1 path(s) unchanged
   [23:15:07] attempt 2/2 model=sonnet effort=medium — fresh session
   retry reason: The RESULT block declared these `files_changed` paths, but each shows NO diff against HEAD before this attempt:
   PASS — committed 4b2353c17755b25c34cf408b58f29840e546ae74

[23:15:07] -- FEAT-2026-9601/G1-CLOSE [close] model=opus effort=high
   ↳ Close

   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
Close WU passed with verdict=met but a terminal flip did not materialize. This is the FEAT-2026-0015/T06 wiring-race regression surface. Inspect events.jsonl and the fire_terminal_flips wiring.
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md b/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md
index 2c7d738..70b3b01 100644
--- a/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md
+++ b/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0103/T04H
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 1.00
 provenance: "Gate 1 broad run (2026-09-10T02:32Z): test_package_data_matches_canonical — T04 wrote the defaults block into specfuse/loop/data/verification.yml.example, the package mirror, while the canonical .specfuse/verification.yml.example was left untouched; T04's produces: named the mirror, an authoring defect"
 produces:
@@ -12,6 +12,10 @@ duration_seconds: 276.73
 cost_usd: 0.241148
 input_tokens: 24
 output_tokens: 2446
+effort: medium
+gate_set: code
+driver_version: 0.18.0
+started_at: 2026-09-10T02:58:48.266335+00:00
 ---
 
 # Hygiene: the `defaults:` block lives in the canonical example, mirrored by sync-scaffold
diff --git a/.specfuse/verification.yml.example b/.specfuse/verification.yml.example
index ae42f5b..ca4b1ba 100644
--- a/.specfuse/verification.yml.example
+++ b/.specfuse/verification.yml.example
@@ -103,6 +103,25 @@
 #       test_roots: ["src/test/java/"]
 #       format: class_name
 #       separator: ","
+
+# TOP-LEVEL `defaults:` block (optional). Project-wide fallbacks a work unit's
+# own frontmatter can override.
+#   max_attempts: 3            # attempt ceiling when a WU declares none of
+#                               # its own; the constant MAX_ATTEMPTS is the
+#                               # fallback when this key is also absent.
+#   retain_on_guard_refusal: true  # whether a bookkeeping-guard refusal keeps
+#                               # the working tree instead of uncommitting it
+#                               # back to a blank slate. Covers four outcomes:
+#                               # `deliverable_missing`, `no_deliverable_files`,
+#                               # `produces_not_in_diff`, `files_changed_mismatch`
+#                               # (FEAT-2026-0103). Defaults to true: the next
+#                               # attempt repairs the retained tree in place
+#                               # instead of re-authoring from scratch. Set to
+#                               # false to restore the pre-0.18 discard behaviour.
+# defaults:
+#   max_attempts: 3
+#   retain_on_guard_refusal: true
+
 code:
   - name: tests
     # Run the suite UNDER `coverage run` so the `coverage` gate below can reuse

```
