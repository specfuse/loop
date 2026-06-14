---
id: FEAT-2026-0016/T03
type: implementation
effort: high
status: draft
attempts: 0
planned_cost_usd: 1.50
generated_surfaces: []
produces_driver_helper: []
---

# Unit tests for attempt_outcome emission + re-arm cumulative-fold logic

**Objective.** Cover T01's attempt_outcome emission branches AND
T02's re-arm cumulative-fold logic with unit tests sufficient to
prove the contract before consumers (T04/T05/T06) are wired against
it. Coverage on the new helpers ≥ 90% per-file.

**Context.** This is `FEAT-2026-0016/T03`. Tests for T01 + T02.
This WU does NOT modify the emission helpers or the cumulative-fold
logic; if a test surfaces an edge case requiring a fix, emit
`status: blocked` rather than patching from this WU — emission
correctness is T01's owned surface, cumulative-fold correctness is
T02's.

Reference: `tests/test_terminal_flips.py` and
`tests/test_loop_post_pass_invariant.py` for fixture layout +
mocking patterns. `tests/_workspace.py` for tempdir-git repo setup
(gpgSign-false workaround applies — see
`[FEAT-2026-0017/T01 prior_attempts entry 2]`).

**Acceptance criteria.**

1. **Test file created:** `tests/test_attempt_outcome_emission.py`
   exists. Uses `unittest`.

2. **Per-outcome emission tests:**

   - `test_emit_attempt_outcome_passed_has_all_required_fields` —
     calls `emit_attempt_outcome(wu, 1, "passed", usage)`, asserts
     returned event dict has `event_type`, `correlation_id`,
     `timestamp`, and payload contains `attempt`, `outcome`,
     `duration_seconds`, `cost_usd`, `input_tokens`,
     `output_tokens`, `cache_read_input_tokens`,
     `cache_creation_input_tokens`, `model`, `effort`,
     `failure_class` (null), `failure_signature` (null),
     `failure_excerpt` (null), `files_touched` (list),
     `agent_status` (`complete`), `agent_blocked_reason` (null),
     `re_arm_count` (int).
   - `test_emit_attempt_outcome_failed_carries_failure_metadata` —
     same but with `failure_class`, `failure_signature`,
     `failure_excerpt` non-null and `agent_status == complete`.
   - `test_emit_attempt_outcome_blocked_carries_agent_reason` —
     `agent_status == "blocked"`, `agent_blocked_reason` non-null.
   - `test_emit_attempt_outcome_zero_token_skip_no_failure_class` —
     `outcome == "zero_token"`, `failure_class == None`.
   - `test_emit_attempt_outcome_post_pass_invariant_failed` —
     `outcome == "post_pass_invariant_failed"`, payload contains
     `assertion` field per FEAT-2026-0017 contract.
   - `test_emit_attempt_outcome_closing_deliverable_missing` —
     `outcome == "closing_deliverable_missing"`, payload contains
     `assertion` field.
   - `test_emit_attempt_outcome_files_changed_mismatch` —
     `outcome == "files_changed_mismatch"`, payload contains
     `unchanged_paths` list.
   - `test_emit_attempt_outcome_smoke_import_failed` —
     `outcome == "smoke_import_failed"`, payload contains
     `summary` field.

3. **Failure-signature derivation tests.** Class
   `TestParseGateFailureSignature`:

   - `test_tests_fail_extracts_first_failing_test_name` — input
     stdout `### tests: FAIL\nFAIL: test_foo`, returns
     `("tests", "test_foo")`.
   - `test_lint_fail_extracts_first_ruff_code` — input
     `### lint: FAIL\nfile.py:5:1: E501 line too long`, returns
     `("lint", "E501")`.
   - `test_security_fail_extracts_first_bandit_id` — input
     `### security: FAIL\n...Issue: [B602:subprocess_popen_with_shell_equals_true]`,
     returns `("security", "B602")`.
   - `test_coverage_fail_extracts_first_uncovered_file` — input
     `### coverage: FAIL\nfile.py 100 10  90%`, returns
     `("coverage", "file.py")`.
   - `test_unknown_gate_name_returns_other` — input
     `### custom-gate: FAIL\n...`, returns `("other", ...)`.
   - `test_no_fail_marker_returns_no_gate_marker` — input has
     no `### X: FAIL` line, returns
     `("other", "no_gate_marker")`.

4. **Failure-excerpt extraction tests.** Class
   `TestExtractFailureExcerpt`:

   - `test_extracts_error_lines_when_present` — stdout with
     `Error: foo` line, returns excerpt containing `Error: foo`.
   - `test_truncates_to_max_chars` — long stdout, excerpt ≤ 500
     chars.
   - `test_falls_back_to_last_lines_when_no_error_pattern` —
     stdout with no FAIL/Error/Exception/Traceback, returns last
     500 chars.
   - `test_handles_utf8_safe_boundary` — stdout truncated at
     mid-multibyte char, no UnicodeDecodeError on the excerpt.

5. **Cumulative-fold tests.** Class
   `TestCumulativeFoldOnRearm`:

   - `test_first_dispatch_no_fold` — `re_arm_count == 0`,
     `detect_rearm_dispatch` returns False, `fold_cumulative_on_rearm`
     is not called.
   - `test_rearm_dispatch_folds_prior_cycle` — WU has
     `re_arm_count: 1`, `cost_usd: 5.0`, `cumulative_cost_usd: 0`.
     After `fold_cumulative_on_rearm`: `cost_usd: 0`,
     `cumulative_cost_usd: 5.0`. Same shape for the other three
     usage fields.
   - `test_rearm_dispatch_preserves_cumulative_from_earlier_rearms` —
     WU has `re_arm_count: 2`, `cost_usd: 3.0`,
     `cumulative_cost_usd: 5.0`. After fold:
     `cumulative_cost_usd: 8.0`, `cost_usd: 0`.
   - `test_missing_fields_default_zero` — WU lacks
     `cumulative_*` fields entirely. Fold treats them as 0;
     no KeyError.
   - `test_re_arm_dispatched_event_emitted` — fold path also
     emits `re_arm_dispatched` event with correct payload.

6. **Coverage gate:**

   ```bash
   coverage run -m unittest discover tests
   coverage report --include=.specfuse/scripts/loop.py --fail-under=90
   ```

   The `--include` filter is on `loop.py` (T01 and T02 both land
   helpers there). If coverage drops below 90% specifically because
   of the new emit_attempt_outcome / parse_gate_failure_signature /
   extract_failure_excerpt / fold_cumulative_on_rearm /
   detect_rearm_dispatch code paths, add tests for the uncovered
   branches. Coverage padding without exercising real behavior is
   hollow-pass bait.

7. **Symbol-existence checks** before declaring complete:

   ```bash
   # a. Test file exists with expected class count
   test "$(grep -cE '^class (TestEmitAttemptOutcome|TestParseGateFailureSignature|TestExtractFailureExcerpt|TestCumulativeFoldOnRearm)' tests/test_attempt_outcome_emission.py)" -ge "4"

   # b. All required test methods present (spot-check)
   grep -qE 'def test_emit_attempt_outcome_passed' tests/test_attempt_outcome_emission.py
   grep -qE 'def test_emit_attempt_outcome_failed' tests/test_attempt_outcome_emission.py
   grep -qE 'def test_emit_attempt_outcome_blocked' tests/test_attempt_outcome_emission.py
   grep -qE 'def test_rearm_dispatch_folds_prior_cycle' tests/test_attempt_outcome_emission.py

   # c. All tests pass
   python3 -m unittest tests.test_attempt_outcome_emission -v

   # d. Coverage ≥ 90%
   coverage run -m unittest discover tests && coverage report --include=.specfuse/scripts/loop.py --fail-under=90

   # e. Working-tree diff touches the test file
   git diff --name-only HEAD | grep -qx 'tests/test_attempt_outcome_emission.py'
   ```

   Any check failing → `status: blocked`. Do NOT flip frontmatter
   as substitute.

**Do not touch.** Files this WU may create:
- `tests/test_attempt_outcome_emission.py` (new file)

No edits to: `.specfuse/scripts/loop.py` (T01 + T02 own; tests are
read-only on the production code), `validate-event.py`,
`gate_eval.py`, `lint_plan.py`, other features, secrets, `.git/`.
If a test surfaces a bug in T01/T02's code, emit `status: blocked`
naming the bug + the failing test; operator re-arms T01 or T02
with revised spec.

**Verification.** The `code` gate set + AC6 coverage gate + AC7
existence checks.

**Tempdir-git setup pattern (precautionary).** If any test creates
a tempdir git repo (the cumulative-fold tests likely will, since
the fold writes WU frontmatter via the driver's write helpers), it
MUST run `git config commit.gpgSign false` immediately after
`git init` per `[FEAT-2026-0017/T01 prior_attempts entry 2]`.
Pattern reference: `tests/_workspace.py:36`.

**Escalation triggers.**

1. **Completeness.** AC7 commands any failing → `status: blocked`.
2. **Coverage shortfall** that can't be addressed without touching
   T01/T02 code → name the uncovered branches in RESULT and emit
   `status: blocked` — operator decides whether to re-arm T01/T02
   with new tests-required ACs or accept the shortfall.
3. **Helper-signature drift.** If T01 or T02 ship helpers with
   different signatures than this WU's spec assumes (e.g.
   keyword arguments named differently), name the drift and emit
   `status: blocked` — tests should match the SHIPPED helper, not
   the planned signature; emitting blocked surfaces the spec/code
   divergence for operator resolution.
