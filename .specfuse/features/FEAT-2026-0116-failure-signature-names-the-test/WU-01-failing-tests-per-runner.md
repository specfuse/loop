---
id: FEAT-2026-0116/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
produces_driver_helper:
  - extract_failing_tests
  - signature_from_failing_tests
produces:
  - specfuse/loop/loop.py
  - tests/test_failure_signature_names_the_test.py
---

# Extract the failing test ids per runner and sign the failure with them

**Objective.** For `failure_class: tests`, derive `failure_signature` from the
sorted set of failing test ids, extracted per runner from the gate report and
the persisted full log, and put that set on the `attempt_outcome` as
`failing_tests`.

**Context.** FEAT-2026-0116/T01, this gate's **walking skeleton**: it turns
`GATE-01.md`'s `feature_oracle` green; T02 wires the detector, T03 the docs and
the replay. In `specfuse/loop/loop.py`, add `extract_failing_tests(lines)` that
returns a sorted, de-duplicated list of ids from: unittest
(`^(FAIL|ERROR): (\S+) \(([\w.]+)\)` → `module.Class.name`), pytest
(`^FAILED (\S+)`), surefire (`^\[ERROR\]\s+([\w.$]+\.\w+)(?::\d+)?` — accept a
package-qualified lowercase start, which `_SUREFIRE_FAILING_TEST_RE` rejects
today), vitest/jest (`^\s*[✕×] (.+)$` and `^FAIL (\S+)`), dotnet
(`^\s*Failed (\S+)`), dart (`^.+ \[E\]$`), bats (`^not ok \d+ (.+)$`). Add
`signature_from_failing_tests(ids)`: the ids joined with `, `, capped at 100
characters with an 8-hex stable hash appended when truncated. In
`parse_gate_failure_signature`, for class `tests`, try the extractor over the
report lines first and, when it yields nothing, over the full log named by the
report's `full output: <path>` line (`persist_gate_output`, #3300); only then
fall to today's regex table. The run-level summary (`FAIL: Tests run:`,
`Tests run: … <<< FAILURE!`) is never a signature. `emit_attempt_outcome` gains
`failing_tests` (default `[]`) as an additive payload field; pass it from the
gate-failure emit site. Red test first: the gate's oracle, fixtures inline as in
`tests/test_maven_failure_excerpt.py`.

**Acceptance criteria.**

1. `tests/test_failure_signature_names_the_test.py` fails on HEAD before this
   unit's edits (the module is absent); after,
   `python3 -m unittest tests.test_failure_signature_names_the_test -v -b`
   exits 0.
2. That module asserts, for the #3414 pair of Maven reports, two different
   signatures, neither equal to `Tests`, each naming its test; and for one
   fixture per runner listed above, `extract_failing_tests` returns exactly
   the expected ids.
3. It also asserts that a report whose tail carries only the summary yields
   the ids from the full log when the `full output:` path exists, and the
   existing keyword fallback when it does not.
4. `python3 -m unittest tests.test_attempt_outcome_emission tests.test_attempt_outcome_contract tests.test_surefire_run_level_signature tests.test_failure_signature_fail_prefix tests.test_failure_signature_skips_log_noise tests.test_maven_failure_excerpt -v -b`
   exits 0 with no edit to those modules; if one of them asserts the summary
   line *is* the signature, stop with `status: blocked` naming the test.

**Do not touch.** `detect_spinning_signature_repeat` and the escalation
payloads (T02); `replay_spin.py` and `docs/` (T03); the non-`tests` regex
entries; `.specfuse/verification.yml`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if the report parser has
no access to the full-log path at the call site that feeds the retry note
(name the call site); or if criterion 4 names a test that pins the summary line
as the signature.
