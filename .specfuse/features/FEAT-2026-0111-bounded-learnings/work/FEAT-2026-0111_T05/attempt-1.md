### tests: FAIL
```
$ coverage run --source=specfuse -m unittest discover -s tests -v -b
#207: surefire failures name Class.method, not 'FAIL: test_*' — ... ok
Line 208: valid fixture → main() returns 0 and prints OK. ... ok
FAIL: test_packaged_copy_is_byte_identical (test_result_block_audience.TestContractStatesTheAudienceRule.test_packaged_copy_is_byte_identical)
Traceback (most recent call last):
AssertionError: b'<!-[678 chars] or a\nskill invoked **non-interactively** fro[6559 chars]e.\n' != b'<!-[678 chars] or a skill\ninvoked **non-interactively** fro[6702 chars]e.\n'
FAIL: test_package_data_matches_canonical (test_scaffold_data_in_sync.TestScaffoldDataInSync.test_package_data_matches_canonical)
Traceback (most recent call last):
... (4758 line(s) elided) ...
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Scaffold data out of sync with canonical sources.
Run: scripts/sync-scaffold.sh

Diffs:
  content differs: rules/never-touch.md
  content differs: rules/result-contract.md
  content differs: rules/security-boundaries.md

----------------------------------------------------------------------
Ran 3986 tests in 201.950s

FAILED (failures=2, skipped=3)
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/tests-20260914T152445033780Z.log
```

### lint: PASS
```
$ ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/lint-20260914T152445093815Z.log
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/agent-policy-example-lint-20260914T152445177265Z.log
```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 76 events.jsonl file(s), 2167 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/event-type-gate-20260914T152445297512Z.log
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/roadmap-link-gate-20260914T152445336077Z.log
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
evaluable=37 evaluated=37 could_not_evaluate=0 excluded_no_baseline=45
ok: 37 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/arm-sweep-gate-20260914T152445661043Z.log
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/monitoring-example-lint-20260914T152445705983Z.log
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_binding_block_budget -v -b
test_cap_is_exposed_on_the_result (tests.test_binding_block_budget.BindingBlockWordCountTests.test_cap_is_exposed_on_the_result) ... ok
test_every_referenced_file_resolves_under_repo_root (tests.test_binding_block_budget.BindingBlockWordCountTests.test_every_referenced_file_resolves_under_repo_root) ... ok
test_reads_actual_at_references_not_a_hardcoded_list (tests.test_binding_block_budget.BindingBlockWordCountTests.test_reads_actual_at_references_not_a_hardcoded_list) ... ok
test_rules_local_distilled_file_is_wired_and_counted (tests.test_binding_block_budget.BindingBlockWordCountTests.test_rules_local_distilled_file_is_wired_and_counted) ... ok
test_total_is_sum_of_per_file_counts (tests.test_binding_block_budget.BindingBlockWordCountTests.test_total_is_sum_of_per_file_counts) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
full output: .specfuse/features/FEAT-2026-0111-bounded-learnings/work/gate-logs/feature_oracle-20260914T152445782310Z.log
```

NOTE: narrow_command declared on gate 'tests' did not fire this attempt: the selection resolved to nothing under narrow_selection.test_roots ['tests/'] (produces: offered docs/methodology.md, .specfuse/rules-local/README.md); ran the full command instead. Set `narrow_selection.test_roots` (and `format`) on that gate in .specfuse/verification.yml if this repo's tests live elsewhere.

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0111-bounded-learnings/WU-05-document-the-budget.md b/.specfuse/features/FEAT-2026-0111-bounded-learnings/WU-05-document-the-budget.md
index d6d0200..0d528b0 100644
--- a/.specfuse/features/FEAT-2026-0111-bounded-learnings/WU-05-document-the-budget.md
+++ b/.specfuse/features/FEAT-2026-0111-bounded-learnings/WU-05-document-the-budget.md
@@ -1,12 +1,17 @@
 ---
 id: FEAT-2026-0111/T05
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 2.50
 produces:
   - docs/methodology.md
   - .specfuse/rules-local/README.md
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.19.0
+started_at: 2026-09-14T15:03:52.643725+00:00
 ---
 
 # Document the budget, the accept step, and what the weights do not mean
diff --git a/.specfuse/features/FEAT-2026-0111-bounded-learnings/events.jsonl b/.specfuse/features/FEAT-2026-0111-bounded-learnings/events.jsonl
index 2f7d1f3..9f30ff9 100644
--- a/.specfuse/features/FEAT-2026-0111-bounded-learnings/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0111-bounded-learnings/events.jsonl
@@ -11,3 +11,7 @@
 {"timestamp": "2026-09-14T15:01:34.347119+00:00", "correlation_id": "FEAT-2026-0111/T04", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.19.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 592.108, "cost_usd": 1.3682622, "input_tokens": 98, "output_tokens": 26750, "cache_read_input_tokens": 3912871, "cache_creation_input_tokens": 79007, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0111-bounded-learnings/WU-04-budget-allocation.md", ".specfuse/features/FEAT-2026-0111-bounded-learnings/events.jsonl", ".specfuse/rules/never-touch.md", ".specfuse/rules/result-contract.md", ".specfuse/rules/security-boundaries.md", "specfuse/loop/loop.py", "tests/test_binding_block_allocation.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-14T15:01:34.347288+00:00", "correlation_id": "FEAT-2026-0111/T04", "event_type": "task_completed", "source": "driver", "source_version": "0.19.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 592.108, "cost_usd": 1.3682622, "input_tokens": 98, "output_tokens": 26750, "cache_read_input_tokens": 3912871, "cache_creation_input_tokens": 79007}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.368262, "cumulative_cost_usd": 1.368262, "attempts_lifetime": 1, "planned_cost_usd": 5.0}}
 {"timestamp": "2026-09-14T15:01:34.353438+00:00", "correlation_id": "FEAT-2026-0111", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.19.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0111/T04", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "a9374296c87d08d0bca80995b849a02b1d13accf", "next_pin_tree": "ccde7a431725d6f66f9cc5e6460207b4eb372eeb"}}
+{"timestamp": "2026-09-14T15:01:34.373269+00:00", "correlation_id": "FEAT-2026-0111/T03", "event_type": "task_started", "source": "driver", "source_version": "0.19.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-14T15:03:52.620982+00:00", "correlation_id": "FEAT-2026-0111/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.19.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 138.13, "cost_usd": 0.48637620000000004, "input_tokens": 28, "output_tokens": 12150, "cache_read_input_tokens": 807021, "cache_creation_input_tokens": 50376, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0111-bounded-learnings/WU-03-accept-step.md", ".specfuse/features/FEAT-2026-0111-bounded-learnings/events.jsonl", "specfuse/loop/loop.py", "tests/test_distilled_accept_step.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-14T15:03:52.621181+00:00", "correlation_id": "FEAT-2026-0111/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.19.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 138.13, "cost_usd": 0.48637620000000004, "input_tokens": 28, "output_tokens": 12150, "cache_read_input_tokens": 807021, "cache_creation_input_tokens": 50376}], "type": "implementation", "re_arm_count": 0, "cost_usd": 0.486376, "cumulative_cost_usd": 0.486376, "attempts_lifetime": 1, "planned_cost_usd": 4.5}}
+{"timestamp": "2026-09-14T15:03:52.627307+00:00", "correlation_id": "FEAT-2026-0111", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.19.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0111/T03", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "a9374296c87d08d0bca80995b849a02b1d13accf", "next_pin_tree": "b5b67d4e07f4edab762c303bea88cb8e5c72cd60"}}
diff --git a/.specfuse/rules-local/README.md b/.specfuse/rules-local/README.md
index a3101fd..192e210 100644
--- a/.specfuse/rules-local/README.md
+++ b/.specfuse/rules-local/README.md
@@ -40,4 +40,29 @@ Follow the shipped rules' format: one failure mode per rule, the check stated
 imperatively, provenance recorded so the reasoning survives the rule (see
 `.specfuse/rules/planning-discipline.md` for the model).
 
+## The shared word budget
+
+Rules included here are summed into the same dispatch-path binding block as
+`.specfuse/rules/`, capped at 2,500 words total (`BINDING_BLOCK_WORD_CAP`,
+`specfuse/loop/loop.py`; enforced by `check_binding_block_budget`, blocking —
+it fails the build if exceeded). Adding a rule here spends from that shared
+allowance, not a budget of its own — check `docs/methodology.md`'s
+"The binding-block word budget" section before authoring one, and note
+whether headroom exists.
+
+The one exception is `learnings-distilled.md`: it has its own 500-word
+sub-budget (`LEARNINGS_DISTILLED_WORD_CAP`) within the 2,500-word total, and
+is written only through the accept step — see `docs/methodology.md`
+§8 and FEAT-2026-0111/T03. That accept step ranks candidates by cost and by
+citation `reach`, and `reach` is a **tiebreaker with an age bias, not a
+ranking**: older entries accumulate citations from being visible longer, not
+from being more valuable, and neither weight measures whether a rule actually
+improves a future session's work.
+
+Before adding any rule here — hand-authored or distilled — check whether a
+guard or lint already enforces it. An entry already enforced mechanically
+does not belong in the binding block; it is dispatch-path cost with no
+marginal effect, and the words are better spent on a rule nothing else
+catches.
+
 This README is seeded once and never overwritten — edit it freely.
diff --git a/docs/methodology.md b/docs/methodology.md
index 48b5656..ac97f81 100644
--- a/docs/methodology.md
+++ b/docs/methodology.md
@@ -654,6 +654,38 @@ feature's `RETROSPECTIVE.md`; only rules that would change how a *future* WU is
 written or executed graduate to `LEARNINGS.md`. This is the human-scale analogue
 of the Ralph loop feeding errors back into the prompt.
 
+### The binding-block word budget
+
+Every dispatch loads a fixed set of rules — `.claude/CLAUDE.md`'s `@`-referenced
+files under `.specfuse/rules/` plus any project-authored `.specfuse/rules-local/`
+files — and that block is capped at `BINDING_BLOCK_WORD_CAP` (2,500 words,
+`specfuse/loop/loop.py`). `check_binding_block_budget` enforces the cap: it is
+**blocking**, not advisory — it raises if the resolved block's total word count
+exceeds the cap.
+
+A project's own `.specfuse/rules-local/` entries are summed into that same
+total (see `.specfuse/rules-local/README.md`), so a project adding a local rule
+is spending from the same shared allowance every other included rule draws
+from, not a separate budget. `LEARNINGS.md` itself is never dispatched whole;
+what can enter the binding block is only its distilled subset,
+`.specfuse/rules-local/learnings-distilled.md`, landed through the accept step
+below and held to its own `LEARNINGS_DISTILLED_WORD_CAP` sub-budget (500
+words) within the total.
+
+Candidate entries for that distilled file are ranked by `score_learnings_entries`
+on two signals: `failure_signature` attempt cost (primary — what the failure
+the entry describes actually cost, from `events.jsonl`) and citation `reach`
+(secondary). **`reach` is a tiebreaker with an age bias, not a ranking**: it
+counts citations in planning documents, and planning agents cite what they
+already read in `LEARNINGS.md`, so an older entry accumulates citations partly
+because it has been visible longer, not because it is more valuable. Neither
+signal — cost or reach — measures whether a rule actually improves a future
+session's work; establishing that would need a before/after on failure rates
+that nothing in this repo computes today. The ranking is a proposal, and
+nothing reaches `learnings-distilled.md` without an explicit per-entry human
+accept (FEAT-2026-0111/T03) — the same propose-and-confirm posture as
+`/arm-gate` and `/pick-feature`.
+
 ## 9. Autonomy
 
 Three levels — `auto`, `review`, `supervised` — set once as a feature default
diff --git a/specfuse/loop/data/docs/methodology.md b/specfuse/loop/data/docs/methodology.md
index 48b5656..ac97f81 100644
--- a/specfuse/loop/data/docs/methodology.md
+++ b/specfuse/loop/data/docs/methodology.md
@@ -654,6 +654,38 @@ feature's `RETROSPECTIVE.md`; only rules that would change how a *future* WU is
 written or executed graduate to `LEARNINGS.md`. This is the human-scale analogue
 of the Ralph loop feeding errors back into the prompt.
 
+### The binding-block word budget
+
+Every dispatch loads a fixed set of rules — `.claude/CLAUDE.md`'s `@`-referenced
+files under `.specfuse/rules/` plus any project-authored `.specfuse/rules-local/`
+files — and that block is capped at `BINDING_BLOCK_WORD_CAP` (2,500 words,
+`specfuse/loop/loop.py`). `check_binding_block_budget` enforces the cap: it is
+**blocking**, not advisory — it raises if the resolved block's total word count
+exceeds the cap.
+
+A project's own `.specfuse/rules-local/` entries are summed into that same
+total (see `.specfuse/rules-local/README.md`), so a project adding a local rule
+is spending from the same shared allowance every other included rule draws
+from, not a separate budget. `LEARNINGS.md` itself is never dispatched whole;
+what can enter the binding block is only its distilled subset,
+`.specfuse/rules-local/learnings-distilled.md`, landed through the accept step
+below and held to its own `LEARNINGS_DISTILLED_WORD_CAP` sub-budget (500
+words) within the total.
+
+Candidate entries for that distilled file are ranked by `score_learnings_entries`
+on two signals: `failure_signature` attempt cost (primary — what the failure
+the entry describes actually cost, from `events.jsonl`) and citation `reach`
+(secondary). **`reach` is a tiebreaker with an age bias, not a ranking**: it
+counts citations in planning documents, and planning agents cite what they
+already read in `LEARNINGS.md`, so an older entry accumulates citations partly
+because it has been visible longer, not because it is more valuable. Neither
+signal — cost or reach — measures whether a rule actually improves a future
+session's work; establishing that would need a before/after on failure rates
+that nothing in this repo computes today. The ranking is a proposal, and
+nothing reaches `learnings-distilled.md` without an explicit per-entry human
+accept (FEAT-2026-0111/T03) — the same propose-and-confirm posture as
+`/arm-gate` and `/pick-feature`.
+
 ## 9. Autonomy
 
 Three levels — `auto`, `review`, `supervised` — set once as a feature default
diff --git a/specfuse/loop/data/rules-local/README.md b/specfuse/loop/data/rules-local/README.md
index a3101fd..192e210 100644
--- a/specfuse/loop/data/rules-local/README.md
+++ b/specfuse/loop/data/rules-local/README.md
@@ -40,4 +40,29 @@ Follow the shipped rules' format: one failure mode per rule, the check stated
 imperatively, provenance recorded so the reasoning survives the rule (see
 `.specfuse/rules/planning-discipline.md` for the model).
 
+## The shared word budget
+
+Rules included here are summed into the same dispatch-path binding block as
+`.specfuse/rules/`, capped at 2,500 words total (`BINDING_BLOCK_WORD_CAP`,
+`specfuse/loop/loop.py`; enforced by `check_binding_block_budget`, blocking —
+it fails the build if exceeded). Adding a rule here spends from that shared
+allowance, not a budget of its own — check `docs/methodology.md`'s
+"The binding-block word budget" section before authoring one, and note
+whether headroom exists.
+
+The one exception is `learnings-distilled.md`: it has its own 500-word
+sub-budget (`LEARNINGS_DISTILLED_WORD_CAP`) within the 2,500-word total, and
+is written only through the accept step — see `docs/methodology.md`
+§8 and FEAT-2026-0111/T03. That accept step ranks candidates by cost and by
+citation `reach`, and `reach` is a **tiebreaker with an age bias, not a
+ranking**: older entries accumulate citations from being visible longer, not
+from being more valuable, and neither weight measures whether a rule actually
+improves a future session's work.
+
+Before adding any rule here — hand-authored or distilled — check whether a
+guard or lint already enforces it. An entry already enforced mechanically
+does not belong in the binding block; it is dispatch-path cost with no
+marginal effect, and the words are better spent on a rule nothing else
+catches.
+
 This README is seeded once and never overwritten — edit it freely.

```
