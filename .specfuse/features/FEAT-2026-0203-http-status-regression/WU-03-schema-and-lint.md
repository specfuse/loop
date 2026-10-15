---
id: FEAT-2026-0203/T03
type: implementation
status: done
attempts: 3
planned_cost_usd: 2.50
produces:
  - specfuse/loop/lint_monitoring.py
  - tests/test_lint_monitoring.py
  - docs/concepts/monitoring-schema.md
  - .specfuse/monitoring.yml.example
  - specfuse/loop/data/monitoring.yml.example
  - .specfuse/rules/design-for-diagnosis.md
  - specfuse/loop/data/rules/design-for-diagnosis.md
duration_seconds: 163.969
cost_usd: 0.676838
input_tokens: 54
output_tokens: 12524
---

# T03 — the http-status-regression schema is validated and documented

**Objective.** `specfuse-monitor-lint` enforces the new check type's fields, and the
schema doc, both example files and the design rule describe it.

**Context.** `FEAT-2026-0203/T03`, gate 1. T01 added the type to `CHECK_TYPES` and
the targetless sets and nothing else. The field rules come from PLAN.md decisions 1
and 2:

- `deploy_signal` is **required**, a mapping with a required `kind`. The only
  accepted `kind` is `app-version`. Any other value is an error naming the accepted
  set: the field exists for future kinds, and lint is conservative until one ships
  (`[FEAT-2026-0069/G2-CLOSE]`).
- `window_after_deploy` is **required** and must parse under T02's
  `parse_duration_seconds`; do not write a second pattern.
- `codes` is **optional**, a non-empty list of unique integers in 400–499. Absent
  means the documented default `[401, 403, 405, 410, 412, 415, 428]`.
- `targets` is **forbidden** (per-component, like `http-5xx`).

Add the per-type branch beside `queue-stalled`'s in `_check_checks`
(`lint_monitoring.py:212`). The docs follow the existing shape in
`docs/concepts/monitoring-schema.md` §Check types (the count "six" becomes "seven")
and the per-type targets matrix. The 3× / ≥10 thresholds are documented there as
fixed constants, not fields. Both example files gain one `http-status-regression`
check and stay byte-identical. Both design-rule copies list the seventh type.

**Skeleton already in place (operator fix, 2026-10-14).** T01 registered the check
type, which broke `tests/test_monitoring_example.py`'s two invariants (every type in
the example, every type in the doc's check-types table) before this unit could run.
A minimal table row and a minimal `web-api` example check were added on the branch to
restore the baseline. Extend them in place; do not add a second row or example.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::TestHttpStatusRegression::test_field_rules` fails
   on HEAD and passes after: a missing `deploy_signal`, `kind: ci-annotation`, a
   missing or malformed `window_after_deploy` (`30 minutes`), `codes: [500]`,
   `codes: []`, duplicate codes and a `targets` list each produce exactly one error;
   a check with `kind: app-version`, `window_after_deploy: 30m` and no `codes`
   produces none.
2. `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example`
   exits 0, and `cmp .specfuse/monitoring.yml.example specfuse/loop/data/monitoring.yml.example`
   exits 0.
3. `python3 -m unittest tests.test_monitoring_example tests.test_monitoring_fenced_blocks -b`
   exits 0, so every fenced YAML block in the monitoring prose still validates.
4. `grep -c "http-status-regression" docs/concepts/monitoring-schema.md` is at least 2
   (check-types table and targets matrix), and the doc names both thresholds.

**Do not touch.** The adapter and its query (T04). `derive-monitoring` and the design
rule's version-stamping section (T05) — this unit only adds the type to the rule's
list. The `stall_after` rule (T02).

**Verification.** The narrow tier for `implementation`, plus the
`monitoring-example-lint` gate command from `.specfuse/verification.yml`.

**Escalation triggers.** If the default `codes` set cannot be stated without
contradicting #248's decision record (400, 404 and 409 excluded), stop. If the
fenced-block test collects a block this unit cannot make valid without editing
another feature's prose, escalate rather than editing it.
