### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_justifying_the_wrong_path_or_nothing_useful_is_still_refused (test_produces_justification.TestProducesJustificationIntegration.test_justifying_the_wrong_path_or_nothing_useful_is_still_refused)
Traceback (most recent call last):
AssertionError: 'produces_unchanged' not found in "declared produces path(s) not in this WU's squash diff: docs/VENDOR-EXTENSIONS.md\n\nEach listed path is a deliverable this WU declared in `produces:` but did not change. Either make the declared change this attempt, or — if the deliverable alread\n...\n - path: docs/VENDOR-EXTENSIONS.md\n    justification: <the command you ran and its output showing the deliverable already holds>\nproduces_amended:\n  - path: docs/VENDOR-EXTENSIONS.md\n    reason: <why this WU no longer needs this produces: path>\n```declared produces path(s) not in this WU's squash diff: docs/VENDOR-EXTENSIONS.md"
Ran 4367 tests in 351.867s
FAILED (failures=1, skipped=3)
... (5153 line(s) elided) ...

Stdout:
Created feature branch 'feat/wrong-path' from 'main'.
== FEAT-2026-0139 — Gate 1 [open] (2 work units) ==

[11:22:14] -- FEAT-2026-0139/T01 [implementation] model=sonnet effort=medium
   ↳ T01
   [11:22:14] attempt 1/3 model=sonnet effort=medium — fresh session
   PRODUCES NOT IN DIFF attempt 1/3 — declared produces path(s) not in this WU's squash diff: docs/VENDOR-EXTENSIONS.md
   [11:22:15] attempt 2/3 model=sonnet effort=medium — fresh session
   retry reason: declared produces path(s) not in this WU's squash diff: docs/VENDOR-EXTENSIONS.md
   PRODUCES NOT IN DIFF attempt 2/3 — declared produces path(s) not in this WU's squash diff: docs/VENDOR-EXTENSIONS.md
   BLOCKED — identical guard refusal on an untouched tree at attempt 2/3; a retry cannot change the inputs. Not dispatching attempt 3.

Gate halted: work unit(s) need human attention.
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/tests-20260926T152312901558Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/lint-20260926T152312979004Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/agent-policy-example-lint-20260926T152313095762Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 78 events.jsonl file(s), 2330 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/event-type-gate-20260926T152313290912Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/roadmap-link-gate-20260926T152313338323Z.log
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
evaluable=39 evaluated=39 could_not_evaluate=0 excluded_no_baseline=48
ok: 39 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/arm-sweep-gate-20260926T152313804218Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/monitoring-example-lint-20260926T152313863125Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_produces_amendment_e2e -v -b
test_amended_path_is_dropped_and_pass_proceeds (tests.test_produces_amendment_e2e.TestProducesAmendmentIntegration.test_amended_path_is_dropped_and_pass_proceeds)
attempt 1 writes only src/a.py, drops src/b.py under ... ok
test_amendment_disabled_by_project_default_is_still_refused (tests.test_produces_amendment_e2e.TestProducesAmendmentIntegration.test_amendment_disabled_by_project_default_is_still_refused)
With `defaults: produces_amendable: false` in verification.yml, ... ok
test_dropping_every_declared_path_is_still_refused (tests.test_produces_amendment_e2e.TestProducesAmendmentIntegration.test_dropping_every_declared_path_is_still_refused)
An amendment that would empty an implementation unit's `produces:` ... ok

----------------------------------------------------------------------
Ran 3 tests in 2.068s

OK
full output: .specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/work/gate-logs/feature_oracle-20260926T152316032666Z.log
```

NOTE: narrow_command declared on gate 'tests' did not fire this attempt: the selection resolved to nothing under narrow_selection.test_roots ['tests/'] (produces: offered .specfuse/rules/result-contract.md, specfuse/loop/data/rules/result-contract.md, .specfuse/skills/authoring-work-units/SKILL.md, docs/methodology.md, specfuse/loop/data/docs/methodology.md, .specfuse/verification.yml.example, specfuse/loop/data/verification.yml.example); ran the full command instead. Set `narrow_selection.test_roots` (and `format`) on that gate in .specfuse/verification.yml if this repo's tests live elsewhere.

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/WU-04-document-the-contract.md b/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/WU-04-document-the-contract.md
index 49139ca..8e97c98 100644
--- a/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/WU-04-document-the-contract.md
+++ b/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/WU-04-document-the-contract.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0114/T04
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
+started_at: 2026-09-26T15:12:35.549220+00:00
 ---
 
 # Document `produces_amended:` where the sessions and the authors read
diff --git a/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/events.jsonl b/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/events.jsonl
index c126a70..b8b3994 100644
--- a/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/events.jsonl
@@ -8,3 +8,7 @@
 {"timestamp": "2026-09-26T15:09:46.048592+00:00", "correlation_id": "FEAT-2026-0114/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 384.008, "cost_usd": 1.2296951999999999, "input_tokens": 94, "output_tokens": 23386, "cache_read_input_tokens": 3442156, "cache_creation_input_tokens": 76804, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/WU-02-repair-note-and-refusal-history.md", ".specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/events.jsonl", "specfuse/loop/loop.py", "tests/test_produces_repair_note.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-26T15:09:46.048798+00:00", "correlation_id": "FEAT-2026-0114/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 384.008, "cost_usd": 1.2296951999999999, "input_tokens": 94, "output_tokens": 23386, "cache_read_input_tokens": 3442156, "cache_creation_input_tokens": 76804}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.229695, "cumulative_cost_usd": 1.229695, "attempts_lifetime": 1, "planned_cost_usd": 4.0}}
 {"timestamp": "2026-09-26T15:09:46.056692+00:00", "correlation_id": "FEAT-2026-0114", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0114/T02", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "dcac9d89fae8dc46e0e1e8c0855183d44fdefc81", "next_pin_tree": "dfcabf7d2c8e77b924d1e9c4e0838b8027d08169"}}
+{"timestamp": "2026-09-26T15:09:46.173302+00:00", "correlation_id": "FEAT-2026-0114/T03", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-26T15:12:35.450150+00:00", "correlation_id": "FEAT-2026-0114/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 169.047, "cost_usd": 0.7792426, "input_tokens": 72, "output_tokens": 12002, "cache_read_input_tokens": 2288793, "cache_creation_input_tokens": 50330, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/WU-03-dropped-deliverables-reach-the-judge.md", ".specfuse/features/FEAT-2026-0114-produces-amendable-at-the-guard/events.jsonl", "specfuse/loop/judge.py", "tests/test_judge_sees_dropped_produces.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-26T15:12:35.450351+00:00", "correlation_id": "FEAT-2026-0114/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 169.047, "cost_usd": 0.7792426, "input_tokens": 72, "output_tokens": 12002, "cache_read_input_tokens": 2288793, "cache_creation_input_tokens": 50330}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.779243, "cumulative_cost_usd": 0.779243, "attempts_lifetime": 1, "planned_cost_usd": 4.0}}
+{"timestamp": "2026-09-26T15:12:35.458539+00:00", "correlation_id": "FEAT-2026-0114", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0114/T03", "driver_paths": ["specfuse/loop/judge.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "dcac9d89fae8dc46e0e1e8c0855183d44fdefc81", "next_pin_tree": "112b4c5d251ef6e6465622891871a17d500d234e"}}
diff --git a/.specfuse/rules/result-contract.md b/.specfuse/rules/result-contract.md
index 153fb00..0c4caa2 100644
--- a/.specfuse/rules/result-contract.md
+++ b/.specfuse/rules/result-contract.md
@@ -70,6 +70,9 @@ blocked_reason: <present only when status is blocked>
 produces_unchanged:               # optional — closing obligation 1 below
   - path: <a produces: entry, verbatim>
     justification: <the command you ran and its output showing the deliverable already holds>
+produces_amended:
+  - path: <a produces: entry, verbatim>
+    reason: <why the path was not needed>
 ```
 ````
 
@@ -117,7 +120,9 @@ never required by any guard. Omit it and nothing changes: the driver's
    reads that list: a justified entry passes and is recorded on the attempt as
    `produces_justified`; an unjustified one, or a blank justification, is
    refused (#198, #3268, outcome `produces_not_in_diff`). Silence on an
-   unchanged deliverable is not a valid close.
+   unchanged deliverable is not a valid close. `produces_unchanged:` is for a
+   deliverable already holding; `produces_amended:` is for a plan-named path
+   not needed — dropped under `produces_dropped:`, never added.
 2. **A plan-level contradiction is `blocked`, not `complete`.** Put the
    finding in `blocked_reason`; never write it into a gate document and close
    `complete`.
diff --git a/.specfuse/skills/authoring-work-units/SKILL.md b/.specfuse/skills/authoring-work-units/SKILL.md
index 91bba6b..6524142 100644
--- a/.specfuse/skills/authoring-work-units/SKILL.md
+++ b/.specfuse/skills/authoring-work-units/SKILL.md
@@ -254,6 +254,14 @@ empty, recording `deliverable_missing`; a body-level `test -s` is advisory.
 *Prevents:* the zero-deliverable and partial-bundle hollow passes the
 no-code-written guard left open (`[FEAT-2026-0020/G2/hollow-pass-presence-gates]`).
 
+A verified attempt may drop a declared path at close time under
+`produces_amended:` when the plan named it but the solution did not need it
+(`result-contract.md`). That escape hatch exists for the plan being wrong, not
+for a hedged declaration: an author unsure whether a path will change should
+not declare it in the first place — list only what you are confident the
+solution will touch, and let a genuine planning miss go through the runtime
+amendment instead of padding `produces:` against your own uncertainty.
+
 ## 14. Tracer bullet — stubs permitted only in the unit that turns the oracle green
 
 A gate's `feature_oracle` (`docs/methodology.md` §2.1) is red on the tree until
diff --git a/.specfuse/verification.yml.example b/.specfuse/verification.yml.example
index d12a835..30ec259 100644
--- a/.specfuse/verification.yml.example
+++ b/.specfuse/verification.yml.example
@@ -129,11 +129,18 @@
 #                               # Defaults to false (#3424): the checklist is
 #                               # appended under the feature's archived detail
 #                               # section in roadmap-archive.md instead.
+#   produces_amendable: true    # whether a verified attempt's RESULT may drop
+#                               # a `produces:` path via `produces_amended:`
+#                               # (result-contract.md) — the plan named a path
+#                               # the solution did not need. Defaults to true.
+#                               # Set to false to require every declared path
+#                               # stay in force for the WU's lifetime.
 # defaults:
 #   max_attempts: 3
 #   retain_on_guard_refusal: true
 #   dispatch_skills: false
 #   post_merge_issue: false
+#   produces_amendable: true
 #
 # The re-plan-after-two-failures behaviour (FEAT-2026-0104) reads this same
 # `max_attempts` resolution and adds no config key of its own — a unit's
diff --git a/docs/methodology.md b/docs/methodology.md
index 734c0f2..45061d4 100644
--- a/docs/methodology.md
+++ b/docs/methodology.md
@@ -99,7 +99,10 @@ it mostly does not need. Author-set unless marked driver-owned.
   `/draft-feature` refuses to draft a gate without one
   (`.specfuse/rules/close-discipline.md` §5, FEAT-2026-0101).
 - `produces` — OPTIONAL. Path(s) or glob(s) this unit must yield; the driver's
-  presence gate refuses `complete` when one is missing or empty.
+  presence gate refuses `complete` when one is missing or empty. A verified
+  attempt may drop a path here via the RESULT's `produces_amended:`
+  (`result-contract.md`), gated by `verification.yml`'s
+  `defaults.produces_amendable` (default true; `.specfuse/verification.yml.example`).
 - `produces_driver_helper` — OPTIONAL. Symbol(s) this unit adds to the driver.
   Lint WARNs when the body mentions driver wiring and the field is absent.
 - `prep` — OPTIONAL. A `verification.yml` set run **before dispatch**, fail-fast:
@@ -126,7 +129,10 @@ it mostly does not need. Author-set unless marked driver-owned.
 - Driver-owned, written at dispatch and outcome time (authors leave them absent):
   `attempts`, `cost_usd`, `input_tokens`, `output_tokens`, `duration_seconds`,
   `cumulative_*`, `re_arm_count`, `re_arm_history`, `folded_through_re_arm`,
-  `model`/`effort` as resolved, `gate_set`, `driver_version`, `started_at`.
+  `model`/`effort` as resolved, `gate_set`, `driver_version`, `started_at`,
+  `produces_dropped` (written when a RESULT's `produces_amended:` drops a
+  `produces:` path — result-contract.md — recording the path and stated
+  reason, FEAT-2026-0114/T01).
 
 ## 3. Work unit types
 
diff --git a/plugins/specfuse/skills/authoring-work-units/SKILL.md b/plugins/specfuse/skills/authoring-work-units/SKILL.md
index 91bba6b..6524142 100644
--- a/plugins/specfuse/skills/authoring-work-units/SKILL.md
+++ b/plugins/specfuse/skills/authoring-work-units/SKILL.md
@@ -254,6 +254,14 @@ empty, recording `deliverable_missing`; a body-level `test -s` is advisory.
 *Prevents:* the zero-deliverable and partial-bundle hollow passes the
 no-code-written guard left open (`[FEAT-2026-0020/G2/hollow-pass-presence-gates]`).
 
+A verified attempt may drop a declared path at close time under
+`produces_amended:` when the plan named it but the solution did not need it
+(`result-contract.md`). That escape hatch exists for the plan being wrong, not
+for a hedged declaration: an author unsure whether a path will change should
+not declare it in the first place — list only what you are confident the
+solution will touch, and let a genuine planning miss go through the runtime
+amendment instead of padding `produces:` against your own uncertainty.
+
 ## 14. Tracer bullet — stubs permitted only in the unit that turns the oracle green
 
 A gate's `feature_oracle` (`docs/methodology.md` §2.1) is red on the tree until
diff --git a/specfuse/loop/data/docs/methodology.md b/specfuse/loop/data/docs/methodology.md
index 734c0f2..45061d4 100644
--- a/specfuse/loop/data/docs/methodology.md
+++ b/specfuse/loop/data/docs/methodology.md
@@ -99,7 +99,10 @@ it mostly does not need. Author-set unless marked driver-owned.
   `/draft-feature` refuses to draft a gate without one
   (`.specfuse/rules/close-discipline.md` §5, FEAT-2026-0101).
 - `produces` — OPTIONAL. Path(s) or glob(s) this unit must yield; the driver's
-  presence gate refuses `complete` when one is missing or empty.
+  presence gate refuses `complete` when one is missing or empty. A verified
+  attempt may drop a path here via the RESULT's `produces_amended:`
+  (`result-contract.md`), gated by `verification.yml`'s
+  `defaults.produces_amendable` (default true; `.specfuse/verification.yml.example`).
 - `produces_driver_helper` — OPTIONAL. Symbol(s) this unit adds to the driver.
   Lint WARNs when the body mentions driver wiring and the field is absent.
 - `prep` — OPTIONAL. A `verification.yml` set run **before dispatch**, fail-fast:
@@ -126,7 +129,10 @@ it mostly does not need. Author-set unless marked driver-owned.
 - Driver-owned, written at dispatch and outcome time (authors leave them absent):
   `attempts`, `cost_usd`, `input_tokens`, `output_tokens`, `duration_seconds`,
   `cumulative_*`, `re_arm_count`, `re_arm_history`, `folded_through_re_arm`,
-  `model`/`effort` as resolved, `gate_set`, `driver_version`, `started_at`.
+  `model`/`effort` as resolved, `gate_set`, `driver_version`, `started_at`,
+  `produces_dropped` (written when a RESULT's `produces_amended:` drops a
+  `produces:` path — result-contract.md — recording the path and stated
+  reason, FEAT-2026-0114/T01).
 
 ## 3. Work unit types
 
diff --git a/specfuse/loop/data/rules/result-contract.md b/specfuse/loop/data/rules/result-contract.md
index 153fb00..0c4caa2 100644
--- a/specfuse/loop/data/rules/result-contract.md
+++ b/specfuse/loop/data/rules/result-contract.md
@@ -70,6 +70,9 @@ blocked_reason: <present only when status is blocked>
 produces_unchanged:               # optional — closing obligation 1 below
   - path: <a produces: entry, verbatim>
     justification: <the command you ran and its output showing the deliverable already holds>
+produces_amended:
+  - path: <a produces: entry, verbatim>
+    reason: <why the path was not needed>
 ```
 ````
 
@@ -117,7 +120,9 @@ never required by any guard. Omit it and nothing changes: the driver's
    reads that list: a justified entry passes and is recorded on the attempt as
    `produces_justified`; an unjustified one, or a blank justification, is
    refused (#198, #3268, outcome `produces_not_in_diff`). Silence on an
-   unchanged deliverable is not a valid close.
+   unchanged deliverable is not a valid close. `produces_unchanged:` is for a
+   deliverable already holding; `produces_amended:` is for a plan-named path
+   not needed — dropped under `produces_dropped:`, never added.
 2. **A plan-level contradiction is `blocked`, not `complete`.** Put the
    finding in `blocked_reason`; never write it into a gate document and close
    `complete`.
diff --git a/specfuse/loop/data/verification.yml.example b/specfuse/loop/data/verification.yml.example
index d12a835..30ec259 100644
--- a/specfuse/loop/data/verification.yml.example
+++ b/specfuse/loop/data/verification.yml.example
@@ -129,11 +129,18 @@
 #                               # Defaults to false (#3424): the checklist is
 #                               # appended under the feature's archived detail
 #                               # section in roadmap-archive.md instead.
+#   produces_amendable: true    # whether a verified attempt's RESULT may drop
+#                               # a `produces:` path via `produces_amended:`
+#                               # (result-contract.md) — the plan named a path
+#                               # the solution did not need. Defaults to true.
+#                               # Set to false to require every declared path
+#                               # stay in force for the WU's lifetime.
 # defaults:
 #   max_attempts: 3
 #   retain_on_guard_refusal: true
 #   dispatch_skills: false
 #   post_merge_issue: false
+#   produces_amendable: true
 #
 # The re-plan-after-two-failures behaviour (FEAT-2026-0104) reads this same
 # `max_attempts` resolution and adds no config key of its own — a unit's

```
