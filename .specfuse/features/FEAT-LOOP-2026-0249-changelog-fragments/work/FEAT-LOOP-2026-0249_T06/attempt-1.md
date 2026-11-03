### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_the_baseline_has_not_silently_shrunk (test_caller_check_ratchet.NoNewUnwiredSymbols.test_the_baseline_has_not_silently_shrunk)
Traceback (most recent call last):
... (5745 line(s) elided) ...
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        set(), stale,
        ^^^^^^^^^^^^^
        "these are in BASELINE but now have a caller — remove them from "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        f"BASELINE: {sorted(stale)}")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Items in the second set but not the first:
'append_entry' : these are in BASELINE but now have a caller — remove them from BASELINE: ['append_entry']

----------------------------------------------------------------------
Ran 4975 tests in 295.384s

FAILED (failures=1, skipped=4)
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/tests-20261102T163037098988Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/lint-20261102T163037188967Z.log
```

### changelog-fragments: PASS
```
$ python3 -m specfuse.loop.changelog_fragments check
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/changelog-fragments-20261102T163037237928Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/agent-policy-example-lint-20261102T163037350737Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 89 events.jsonl file(s), 2815 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/event-type-gate-20261102T163037492588Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-LOOP-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-loop-2026-0011)' or '[→ archive](roadmap-archive.md#feat-loop-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/roadmap-link-gate-20261102T163037545869Z.log
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
evaluable=50 evaluated=50 could_not_evaluate=0 excluded_no_baseline=45
ok: 50 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/arm-sweep-gate-20261102T163037991181Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/monitoring-example-lint-20261102T163038040504Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_changelog_fragments -v -b
test_output_is_deterministic_in_filename_order (tests.test_changelog_fragments.TestClause3CollateAtRelease.test_output_is_deterministic_in_filename_order) ... ok
test_release_folds_every_fragment_and_removes_them (tests.test_changelog_fragments.TestClause3CollateAtRelease.test_release_folds_every_fragment_and_removes_them) ... ok
test_absent_directory_passes (tests.test_changelog_fragments.TestClause4CheckGate.test_absent_directory_passes) ... ok
test_bad_trace_fails_naming_file (tests.test_changelog_fragments.TestClause4CheckGate.test_bad_trace_fails_naming_file) ... ok
test_missing_frontmatter_fails_naming_file (tests.test_changelog_fragments.TestClause4CheckGate.test_missing_frontmatter_fails_naming_file) ... ok
test_multi_line_body_fails_naming_file (tests.test_changelog_fragments.TestClause4CheckGate.test_multi_line_body_fails_naming_file) ... ok
test_valid_fragments_pass (tests.test_changelog_fragments.TestClause4CheckGate.test_valid_fragments_pass) ... ok
test_wrong_class_fails_naming_file (tests.test_changelog_fragments.TestClause4CheckGate.test_wrong_class_fails_naming_file) ... ok
test_add_without_mode_edits_changelog_md (tests.test_changelog_fragments.TestClause5NoModeKeyBehavesAsBefore.test_add_without_mode_edits_changelog_md) ... ok
test_release_without_fragments_unchanged (tests.test_changelog_fragments.TestClause5NoModeKeyBehavesAsBefore.test_release_without_fragments_unchanged) ... ok

----------------------------------------------------------------------
Ran 25 tests in 2.055s

OK
full output: .specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/work/gate-logs/feature_oracle-20261102T163040188220Z.log
```

NOTE: narrow_command declared on gate 'tests' did not fire this attempt: the selection resolved to nothing under narrow_selection.test_roots ['tests/'] (produces: offered plugins/specfuse/skills/fix-bug/SKILL.md, .specfuse/skills/fix-bug/SKILL.md, .specfuse/rules/close-discipline.md, specfuse/loop/data/rules/close-discipline.md, docs/lifecycles.md, specfuse/loop/data/docs/lifecycles.md); ran the full command instead. Set `narrow_selection.test_roots` (and `format`) on that gate in .specfuse/verification.yml if this repo's tests live elsewhere.

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/WU-06-prose.md b/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/WU-06-prose.md
index b2642e8..8d7a488 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/WU-06-prose.md
+++ b/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/WU-06-prose.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-LOOP-2026-0249/T06
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 oracle_env: macos_local
 planned_cost_usd: 2.00
 produces:
@@ -15,6 +15,8 @@ produces:
 model: sonnet
 effort: medium
 gate_set: code
+driver_version: 0.31.1
+started_at: 2026-11-02T16:14:45.630912+00:00
 ---
 
 # T06 — skills, rules and docs call the writer
diff --git a/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/events.jsonl b/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/events.jsonl
index 06aa527..581b528 100644
--- a/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/events.jsonl
+++ b/.specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/events.jsonl
@@ -15,3 +15,7 @@
 {"timestamp": "2026-11-02T16:13:55.832123+00:00", "correlation_id": "FEAT-LOOP-2026-0249/T04", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.31.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 33.062, "cost_usd": 0.1824976, "input_tokens": 10, "output_tokens": 2848, "cache_read_input_tokens": 174228, "cache_creation_input_tokens": 29788, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/WU-04-check-gate.md", ".specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/events.jsonl", ".specfuse/verification.yml", "specfuse/loop/changelog_fragments.py", "tests/test_changelog_fragments.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
 {"timestamp": "2026-11-02T16:13:55.832382+00:00", "correlation_id": "FEAT-LOOP-2026-0249/T04", "event_type": "task_completed", "source": "driver", "source_version": "0.31.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 33.062, "cost_usd": 0.1824976, "input_tokens": 10, "output_tokens": 2848, "cache_read_input_tokens": 174228, "cache_creation_input_tokens": 29788}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.182498, "cumulative_cost_usd": 0.182498, "attempts_lifetime": 1, "planned_cost_usd": 1.5}}
 {"timestamp": "2026-11-02T16:13:55.843711+00:00", "correlation_id": "FEAT-LOOP-2026-0249", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.31.1", "payload": {"gate": 1, "wu_id": "FEAT-LOOP-2026-0249/T04", "driver_paths": ["specfuse/loop/changelog_fragments.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "597690f75955647ee91d3fd53aa9c89a37503109", "next_pin_tree": "d0a0df45e5b2d37cad5b0ba14b952e9c0a8b131a"}}
+{"timestamp": "2026-11-02T16:13:55.965907+00:00", "correlation_id": "FEAT-LOOP-2026-0249/T05", "event_type": "task_started", "source": "driver", "source_version": "0.31.1", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-11-02T16:14:45.550043+00:00", "correlation_id": "FEAT-LOOP-2026-0249/T05", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.31.1", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 49.392, "cost_usd": 0.1939224, "input_tokens": 14, "output_tokens": 2843, "cache_read_input_tokens": 259302, "cache_creation_input_tokens": 28401, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/WU-05-ids-migrate.md", ".specfuse/features/FEAT-LOOP-2026-0249-changelog-fragments/events.jsonl", "specfuse/loop/ids.py", "tests/test_ids_migrate_all.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0, "failing_tests": []}}
+{"timestamp": "2026-11-02T16:14:45.550216+00:00", "correlation_id": "FEAT-LOOP-2026-0249/T05", "event_type": "task_completed", "source": "driver", "source_version": "0.31.1", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 49.392, "cost_usd": 0.1939224, "input_tokens": 14, "output_tokens": 2843, "cache_read_input_tokens": 259302, "cache_creation_input_tokens": 28401}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.193922, "cumulative_cost_usd": 0.193922, "attempts_lifetime": 1, "planned_cost_usd": 1.5}}
+{"timestamp": "2026-11-02T16:14:45.558307+00:00", "correlation_id": "FEAT-LOOP-2026-0249", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.31.1", "payload": {"gate": 1, "wu_id": "FEAT-LOOP-2026-0249/T05", "driver_paths": ["specfuse/loop/ids.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "597690f75955647ee91d3fd53aa9c89a37503109", "next_pin_tree": "04b513ee1e26fab0f170c812d9b971b2c05354c4"}}
diff --git a/.specfuse/rules/close-discipline.md b/.specfuse/rules/close-discipline.md
index a2c629c..c77b976 100644
--- a/.specfuse/rules/close-discipline.md
+++ b/.specfuse/rules/close-discipline.md
@@ -137,19 +137,22 @@ fabricate an empty enumeration; the n/a line is the reviewed claim).
 A close carrying this obligation is always load-bearing
 (`auto_close_disabled: true`).
 
-**Also append it to `CHANGELOG.md`'s `Unreleased` section (FEAT-2026-0064).**
+**Also record it in the changelog (FEAT-2026-0064).**
 When this section is a real enumeration — not the `n/a` line — the close
-appends each item to `Unreleased`, classified `added` / `changed` / `fixed` /
-`breaking` and carrying the feature's `FEAT-YYYY-NNNN` ID, via
-`specfuse/loop/changelog.py`'s schema. **This is the same material the
+runs one `python3 -m specfuse.loop.changelog_fragments add --class
+<added|changed|fixed|breaking> --trace FEAT-YYYY-NNNN --summary "<item>"` per
+enumerated item, with the feature's ID as the trace. `add` routes by the
+project's `changelog.mode` (`CHANGELOG.md`'s `Unreleased` section, or a
+`changelog.d/` fragment); do not hand-edit either. Each entry is classified
+and carries the feature's `FEAT-YYYY-NNNN` ID. **This is the same material the
 paragraph above already requires you to write, put where a consumer will
-read it — not a second write.** An author who treats the changelog append as
+read it — not a second write.** An author who treats the changelog entry as
 new work will write the enumeration twice, badly; write it once, in both
 places, from the same understanding. `closing_requirements.py`'s `close-k`
 requirement (enforced by `assert_changelog_entry_for_contract_changes` in
 `loop.py`, and pre-squash by `specfuse lint --closing`) fires when this
-section names a real change and `Unreleased` gained no entry tracing to this
-feature's FEAT-ID.
+section names a real change and no entry tracing to this feature's FEAT-ID
+lives in `CHANGELOG.md` or in a `changelog.d/` fragment.
 
 **An `n/a` close appends nothing to `Unreleased`, and that is correct.** A
 changelog padded with "no user-facing change" entries is noise that trains
diff --git a/.specfuse/skills/fix-bug/SKILL.md b/.specfuse/skills/fix-bug/SKILL.md
index a576e4a..53f7152 100644
--- a/.specfuse/skills/fix-bug/SKILL.md
+++ b/.specfuse/skills/fix-bug/SKILL.md
@@ -198,14 +198,17 @@ predicted. Re-checking here closes that gap.
 
   Co-Authored-By: <as configured>
   ```
-- **Before opening the PR**, append one entry to `CHANGELOG.md`'s
-  `Unreleased` section (FEAT-2026-0064) via `specfuse/loop/changelog.py`'s
-  schema: classified `added` / `changed` / `fixed` / `breaking`, one line
-  derived from the same root-cause/fix understanding the commit message
-  above already captures, carrying `#<issue-number>` as its trace. This is
-  the bug side's collection point — bugs have no close ceremony to collect
-  through, so `fix-bug` is where the entry is written or it is dropped.
-  Include the `CHANGELOG.md` change in the same commit as the fix.
+- **Before opening the PR**, write one changelog entry (FEAT-2026-0064) by
+  running `python3 -m specfuse.loop.changelog_fragments add --class
+  <added|changed|fixed|breaking> --trace '#<issue-number>' --summary "<one
+  line>"`. The summary is derived from the same root-cause/fix understanding
+  the commit message above already captures. The writer picks the target
+  from the project's `changelog.mode` — do not branch on the mode and do not
+  hand-edit `CHANGELOG.md` (`Unreleased` section) or `changelog.d/`. The
+  entry is classified and traces to `#<issue-number>`. This is the bug side's
+  collection point — bugs have no close ceremony to collect through, so
+  `fix-bug` is where the entry is written or it is dropped. Include
+  whatever `add` wrote in the same commit as the fix.
 - `git push -u origin fix/issue-<#>-<short-slug>`.
 - `gh pr create --title "fix(<scope>): <summary>" --body <markdown-body>`.
   PR body sections: Root cause, Fix, Tests, Verification. **The body MUST
diff --git a/docs/lifecycles.md b/docs/lifecycles.md
index 37976ce..5bed7e8 100644
--- a/docs/lifecycles.md
+++ b/docs/lifecycles.md
@@ -172,8 +172,19 @@ and obvious in the diff — a fix that turns out to need a new frontmatter field
 say. So the indicators are re-applied to the actual diff before commit, and a
 hit stops the branch rather than shipping feature-scoped work as a bug fix.
 
-**The `CHANGELOG.md` entry is written here or nowhere.** Bugs have no close
-ceremony to collect through, so `/fix-bug` is the collection point.
+**The changelog entry is written here or nowhere.** Bugs have no close
+ceremony to collect through, so `/fix-bug` is the collection point. It runs
+`python3 -m specfuse.loop.changelog_fragments add --class fixed --trace
+'#<issue>' --summary "..."` and commits what that wrote with the fix.
+
+**Opting in to fragments.** By default `add` appends to `CHANGELOG.md`'s
+`Unreleased` section. Set `changelog.mode: fragments` in `.specfuse/layout.yml`
+and `add` writes one `changelog.d/<trace>-<slug>.md` file per entry instead, so
+parallel branches stop conflicting on `CHANGELOG.md`. Add
+`python3 -m specfuse.loop.changelog_fragments check` as a gate (for example in
+CI) to fail any PR carrying a malformed fragment. A custom release script must
+run `python3 -m specfuse.loop.changelog_fragments collate` before stamping the
+version: it folds the fragments into `Unreleased` and deletes them.
 
 ---
 
diff --git a/plugins/specfuse/skills/fix-bug/SKILL.md b/plugins/specfuse/skills/fix-bug/SKILL.md
index a576e4a..53f7152 100644
--- a/plugins/specfuse/skills/fix-bug/SKILL.md
+++ b/plugins/specfuse/skills/fix-bug/SKILL.md
@@ -198,14 +198,17 @@ predicted. Re-checking here closes that gap.
 
   Co-Authored-By: <as configured>
   ```
-- **Before opening the PR**, append one entry to `CHANGELOG.md`'s
-  `Unreleased` section (FEAT-2026-0064) via `specfuse/loop/changelog.py`'s
-  schema: classified `added` / `changed` / `fixed` / `breaking`, one line
-  derived from the same root-cause/fix understanding the commit message
-  above already captures, carrying `#<issue-number>` as its trace. This is
-  the bug side's collection point — bugs have no close ceremony to collect
-  through, so `fix-bug` is where the entry is written or it is dropped.
-  Include the `CHANGELOG.md` change in the same commit as the fix.
+- **Before opening the PR**, write one changelog entry (FEAT-2026-0064) by
+  running `python3 -m specfuse.loop.changelog_fragments add --class
+  <added|changed|fixed|breaking> --trace '#<issue-number>' --summary "<one
+  line>"`. The summary is derived from the same root-cause/fix understanding
+  the commit message above already captures. The writer picks the target
+  from the project's `changelog.mode` — do not branch on the mode and do not
+  hand-edit `CHANGELOG.md` (`Unreleased` section) or `changelog.d/`. The
+  entry is classified and traces to `#<issue-number>`. This is the bug side's
+  collection point — bugs have no close ceremony to collect through, so
+  `fix-bug` is where the entry is written or it is dropped. Include
+  whatever `add` wrote in the same commit as the fix.
 - `git push -u origin fix/issue-<#>-<short-slug>`.
 - `gh pr create --title "fix(<scope>): <summary>" --body <markdown-body>`.
   PR body sections: Root cause, Fix, Tests, Verification. **The body MUST
diff --git a/specfuse/loop/data/docs/lifecycles.md b/specfuse/loop/data/docs/lifecycles.md
index 37976ce..5bed7e8 100644
--- a/specfuse/loop/data/docs/lifecycles.md
+++ b/specfuse/loop/data/docs/lifecycles.md
@@ -172,8 +172,19 @@ and obvious in the diff — a fix that turns out to need a new frontmatter field
 say. So the indicators are re-applied to the actual diff before commit, and a
 hit stops the branch rather than shipping feature-scoped work as a bug fix.
 
-**The `CHANGELOG.md` entry is written here or nowhere.** Bugs have no close
-ceremony to collect through, so `/fix-bug` is the collection point.
+**The changelog entry is written here or nowhere.** Bugs have no close
+ceremony to collect through, so `/fix-bug` is the collection point. It runs
+`python3 -m specfuse.loop.changelog_fragments add --class fixed --trace
+'#<issue>' --summary "..."` and commits what that wrote with the fix.
+
+**Opting in to fragments.** By default `add` appends to `CHANGELOG.md`'s
+`Unreleased` section. Set `changelog.mode: fragments` in `.specfuse/layout.yml`
+and `add` writes one `changelog.d/<trace>-<slug>.md` file per entry instead, so
+parallel branches stop conflicting on `CHANGELOG.md`. Add
+`python3 -m specfuse.loop.changelog_fragments check` as a gate (for example in
+CI) to fail any PR carrying a malformed fragment. A custom release script must
+run `python3 -m specfuse.loop.changelog_fragments collate` before stamping the
+version: it folds the fragments into `Unreleased` and deletes them.
 
 ---
 
diff --git a/specfuse/loop/data/rules/close-discipline.md b/specfuse/loop/data/rules/close-discipline.md
index a2c629c..c77b976 100644
--- a/specfuse/loop/data/rules/close-discipline.md
+++ b/specfuse/loop/data/rules/close-discipline.md
@@ -137,19 +137,22 @@ fabricate an empty enumeration; the n/a line is the reviewed claim).
 A close carrying this obligation is always load-bearing
 (`auto_close_disabled: true`).
 
-**Also append it to `CHANGELOG.md`'s `Unreleased` section (FEAT-2026-0064).**
+**Also record it in the changelog (FEAT-2026-0064).**
 When this section is a real enumeration — not the `n/a` line — the close
-appends each item to `Unreleased`, classified `added` / `changed` / `fixed` /
-`breaking` and carrying the feature's `FEAT-YYYY-NNNN` ID, via
-`specfuse/loop/changelog.py`'s schema. **This is the same material the
+runs one `python3 -m specfuse.loop.changelog_fragments add --class
+<added|changed|fixed|breaking> --trace FEAT-YYYY-NNNN --summary "<item>"` per
+enumerated item, with the feature's ID as the trace. `add` routes by the
+project's `changelog.mode` (`CHANGELOG.md`'s `Unreleased` section, or a
+`changelog.d/` fragment); do not hand-edit either. Each entry is classified
+and carries the feature's `FEAT-YYYY-NNNN` ID. **This is the same material the
 paragraph above already requires you to write, put where a consumer will
-read it — not a second write.** An author who treats the changelog append as
+read it — not a second write.** An author who treats the changelog entry as
 new work will write the enumeration twice, badly; write it once, in both
 places, from the same understanding. `closing_requirements.py`'s `close-k`
 requirement (enforced by `assert_changelog_entry_for_contract_changes` in
 `loop.py`, and pre-squash by `specfuse lint --closing`) fires when this
-section names a real change and `Unreleased` gained no entry tracing to this
-feature's FEAT-ID.
+section names a real change and no entry tracing to this feature's FEAT-ID
+lives in `CHANGELOG.md` or in a `changelog.d/` fragment.
 
 **An `n/a` close appends nothing to `Unreleased`, and that is correct.** A
 changelog padded with "no user-facing change" entries is noise that trains

```
