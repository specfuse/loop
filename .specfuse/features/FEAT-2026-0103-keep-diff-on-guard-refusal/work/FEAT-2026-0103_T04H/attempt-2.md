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
Ran 3887 tests in 217.377s

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
ok: no validation errors across 73 events.jsonl file(s), 2014 event(s) checked
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
Ran 2 tests in 1.200s
OK
... (21 line(s) elided) ...
== FEAT-2026-9601 — Gate 1 [open] (2 work units) ==

[23:19:20] -- FEAT-2026-9601/T01 [implementation] model=sonnet effort=medium
   ↳ T01
   [23:19:20] attempt 1/2 model=sonnet effort=medium — fresh session
   FILES_CHANGED MISMATCH attempt 1/2 — 1 path(s) unchanged
   [23:19:20] attempt 2/2 model=sonnet effort=medium — fresh session
   retry reason: The RESULT block declared these `files_changed` paths, but each shows NO diff against HEAD before this attempt:
   PASS — committed 6cbd7a3ae0028f2422f0983176b71e9db5235004

[23:19:20] -- FEAT-2026-9601/G1-CLOSE [close] model=opus effort=high
   ↳ Close

   POST-PASS INVARIANT FAILED — roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md
Close WU passed with verdict=met but a terminal flip did not materialize. This is the FEAT-2026-0015/T06 wiring-race regression surface. Inspect events.jsonl and the fire_terminal_flips wiring.
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md b/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md
index 2c7d738..573f1d7 100644
--- a/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md
+++ b/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/WU-04H-canonical-example-mirrored.md
@@ -2,7 +2,7 @@
 id: FEAT-2026-0103/T04H
 type: implementation
 status: pending
-attempts: 0
+attempts: 2
 planned_cost_usd: 1.00
 provenance: "Gate 1 broad run (2026-09-10T02:32Z): test_package_data_matches_canonical — T04 wrote the defaults block into specfuse/loop/data/verification.yml.example, the package mirror, while the canonical .specfuse/verification.yml.example was left untouched; T04's produces: named the mirror, an authoring defect"
 produces:
diff --git a/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/events.jsonl b/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/events.jsonl
index b8ac799..3dce40b 100644
--- a/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0103-keep-diff-on-guard-refusal/events.jsonl
@@ -24,3 +24,5 @@
 {"timestamp": "2026-09-10T02:58:11.353300+00:00", "correlation_id": "FEAT-2026-0103", "event_type": "human_escalation", "source": "driver", "source_version": "0.18.0", "payload": {"reason": "preexisting_gate_failure", "gate": 1, "failing_gates": [{"gate": "tests", "failure_class": "tests", "failure_signature": "test_package_data_matches_canonical"}, {"gate": "coverage", "failure_class": "other", "failure_signature": "no_gate_marker"}], "message": "Gate 1 is blocked: the automated checks it depends on are failing, and this gate has ALREADY LANDED WORK.\n\nFailing check(s) found at gate entry:\n  - tests: tests (signature: test_package_data_matches_canonical)\n  - coverage: other (signature: no_gate_marker)\n\n4 work unit(s) in this gate are already `done` and committed, so the baseline these checks measured includes this feature's own work. The failure may well have been introduced by one of them -- do NOT assume it predates the feature:\n  - FEAT-2026-0103/T01\n  - FEAT-2026-0103/T02\n  - FEAT-2026-0103/T03\n  - FEAT-2026-0103/T04\n\nWhat this feature has landed since the integration branch (context, not proof -- the failing check may be in here):\ngit diff main...HEAD --stat:\n.../GATE-01.md                                     |  79 +++++++\n .../PLAN.baseline.json                             |  39 ++++\n .../PLAN.md                                        | 143 ++++++++++++\n .../WU-01-retain-tree-after-refusal.md             |  86 +++++++\n .../WU-02-repair-turn-lead.md                      |  72 ++++++\n .../WU-03-clerical-auto-repair.md                  |  66 ++++++\n .../WU-04-document-the-contract.md                 |  62 +++++\n .../WU-04H-canonical-example-mirrored.md           |  52 +++++\n .../WU-90-gate-1-close.md                          |  60 +++++\n .../events.jsonl                                   |  19 ++\n .specfuse/roadmap.md                               |   4 +-\n docs/methodology.md                                |  22 ++\n specfuse/loop/data/verification.yml.example        |  19 ++\n specfuse/loop/loop.py                              | 235 ++++++++++++++++---\n tests/test_files_changed_auto_repair.py            | 172 ++++++++++++++\n tests/test_guard_repair_e2e.py                     | 259 +++++++++++++++++++++\n tests/test_guard_repair_prompt.py                  |  83 +++++++\n tests/test_retain_on_guard_refusal_docs.py         |  65 ++++++\n 18 files changed, 1508 insertions(+), 29 deletions(-)\n\nWhat to do next:\n  1. Find which of this gate's landed work units introduced the failing check, and fix it ON THIS BRANCH. `git log -S<signature> <base>..HEAD` answers that directly.\n  2. Only if the check also fails on the integration branch is this pre-existing debt \u2014 verify before assuming it.\n\nThere is no way to proceed past this halt in this version. A waiver that lets a feature continue against a red baseline is future work tracked as FEAT-2026-0052; it does not exist yet.", "attributed_to": "FEAT-2026-0103/T04H"}}
 {"timestamp": "2026-09-10T02:58:11.379339+00:00", "correlation_id": "FEAT-2026-0103", "event_type": "arm_predicate_evaluated", "source": "driver", "source_version": "0.18.0", "payload": {"gate": 1, "would_arm": true, "predicate_version": "v1", "classes": {"budget_projection": {"status": "clean", "reason": "projected spend $15.36 within 2.0x baseline planned total $23.00 (cap $46.00)"}, "judge_editing": {"status": "clean", "reason": "no drafted WU touches judge-path surfaces"}, "decision_class_paths": {"status": "clean", "reason": "no drafted WU touches a recognised dependency manifest (pyproject.toml, package.json, pom.xml, build.gradle, build.gradle.kts, Cargo.toml, go.mod, Gemfile, composer.json, requirements*.txt, *.csproj)"}, "retroactive_edits": {"status": "clean", "reason": "no passed-gate baseline WU altered or removed"}, "drift_caps": {"status": "clean", "reason": "added WUs and gates within drift caps"}, "missing_provenance": {"status": "clean", "reason": "every added WU carries a provenance field"}, "open_questions_human_only": {"status": "clean", "reason": "terminal gate: no drafted successor"}, "plan_next_lint": {"status": "clean", "reason": "plan-next lint: no findings"}}}}
 {"timestamp": "2026-09-10T02:58:48.084421+00:00", "correlation_id": "FEAT-2026-0103", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.18.0", "payload": {"tree": "edcc3c840c7c1f292bba81d1de6316f014ae4787", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/edcc3c840c7c1f292bba81d1de6316f014ae4787/specfuse/loop"}}
+{"timestamp": "2026-09-10T02:58:48.266566+00:00", "correlation_id": "FEAT-2026-0103/T04H", "event_type": "task_started", "source": "driver", "source_version": "0.18.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-10T03:15:08.247629+00:00", "correlation_id": "FEAT-2026-0103/T04H", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.18.0", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 979.843, "cost_usd": 0.7776254, "input_tokens": 2, "output_tokens": 34, "cache_read_input_tokens": 77729, "cache_creation_input_tokens": 1192, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "test_package_docs_match_canonical", "failure_excerpt": "### tests: FAIL\n#207: surefire failures name Class.method, not 'FAIL: test_*' \u2014 ... ok\nFAIL: test_package_docs_match_canonical (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_docs_match_canonical)\nTraceback (most recent call last\n...\nnisable pass/fail summary anywhere in its output \u2014 the lines above are the tail only, and may be unrelated to the failure. Run the command directly.\n   POST-PASS INVARIANT FAILED \u2014 roadmap_row_not_done: roadmap.md absent at .specfuse/roadmap.md", "files_touched": [], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
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
