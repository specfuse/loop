# Retrospective — FEAT-LOOP-2026-0203 gate 1 close

## Measurements

All commands run fresh in this session from the repository root, exit codes read
directly. HEAD was `6fdccb2ed0f167c49bf310f5b9d9faa7f0d6b5cd` with this close's own
working-tree edits (CHANGELOG, this file, `GATE-01-CRITERIA.md`) uncommitted.

### feature_oracle: PASS

Command: `python3 -m unittest tests.test_http_status_regression_end_to_end -v -b`
(exit 0):

```
test_adapter_issues_one_query (...HttpStatusRegressionEndToEnd.test_adapter_issues_one_query) ... ok
test_one_deployment_files_one_finding_per_code (...HttpStatusRegressionEndToEnd.test_one_deployment_files_one_finding_per_code) ... ok
test_same_rows_same_fingerprint (...HttpStatusRegressionEndToEnd.test_same_rows_same_fingerprint) ... ok

Ran 3 tests in 0.003s

OK
```

### One query per check (PLAN.md decision 5)

`HttpStatusRegressionAdapter.fetch_failures` (`specfuse/monitor/providers/azure_app_insights.py`,
class spanning lines 242–317) contains exactly one `run_query` call (line 278); the
other `run_query` sites in the file belong to `ErrorLogsAdapter`, `Http5xxAdapter`,
`InvariantAdapter` and `HeartbeatAdapter`. Measured, not read:

- T01 — `python3 -m unittest tests.test_http_status_regression_end_to_end.HttpStatusRegressionEndToEnd.test_adapter_issues_one_query -v -b`, exit 0:
  `test_adapter_issues_one_query ... ok`. It asserts `len(transport.queries) == 1`
  after one `fetch_failures` call that returns a row carrying the sentinel version
  `9.8.7-sentinel`, and that the sentinel does not appear in the query text.
- T04 — `python3 -m unittest tests.test_http_status_regression_adapter.QueryShape.test_query_is_configuration_only -v -b`, exit 0:
  `test_query_is_configuration_only ... ok`. It asserts one recorded query, that it
  names `AppRequests`, `AppRoleName`, `AppVersion`, `ResultCode` and `TimeGenerated`,
  contains each configured code (`401`, `403`), and contains neither the returned
  version sentinel nor the returned `first_seen` timestamp.

So deployment detection and window counting share one query and no value returned by
a telemetry query is folded into a later one.

### Per-criterion oracles (20 criteria, `GATE-01-CRITERIA.md`)

carried forward: 0 criteria, re-measured: 20

Each criterion's oracle was re-run this attempt; per-entry command, `kind` and
`state` are in `GATE-01-CRITERIA.md`. Results (all exit 0):

| criterion | oracle | result |
| --- | --- | --- |
| T01#1–#3 | the three named `HttpStatusRegressionEndToEnd` tests, one run each | ok |
| T01#4 | the `feature_oracle` above | ok (3 tests) |
| T02#1 | `tests.test_lint_monitoring.TestQueueStalled.test_malformed_stall_after_is_a_lint_error` | ok |
| T02#2 | `tests.test_monitor_durations` (2 tests); `grep -cE "re\.compile" .../azure_service_bus.py` = 3, all of them message-normalisation patterns (`_GUID_RE`, `_TIMESTAMP_RE`, `_NUMBER_RE`), none a duration pattern | ok |
| T02#3 | `tests.test_monitoring_example tests.test_monitoring_fenced_blocks` (14 tests) | ok |
| T02#4 | `grep -n stall_after docs/concepts/monitoring-schema.md` shows the grammar stated; the old "never parsed or bounded" wording is gone from that row | ok |
| T03#1 | `tests.test_lint_monitoring.TestHttpStatusRegression.test_field_rules` | ok |
| T03#2 | `lint_monitoring.py .specfuse/monitoring.yml.example` → `OK — monitoring config is structurally valid`; `cmp` of the two example copies exit 0 | ok |
| T03#3 | `tests.test_monitoring_example tests.test_monitoring_fenced_blocks` | ok |
| T03#4 | `grep -c http-status-regression docs/concepts/monitoring-schema.md` = 2; the doc names `3×` and `at least 10` | ok |
| T04#1–#4 | the four named `RegressionRule` / `QueryShape` tests | 4 ok |
| T04#5 | `tests.test_app_insights_query_schema_check` (9 tests, 1 skipped) | ok |
| T05#1 | `tests.test_derive_monitoring_discovery.TestHttpStatusRegressionProposal.test_proposed_only_with_version_evidence` | ok |
| T05#2 | `tests.test_design_for_diagnosis_rule`; `cmp` of the two design-rule copies exit 0 | ok |
| T05#3 | see below | ok, with a stated substitution |

Two of these are not the criterion's own command, and are stated as such:

- **T05#3** names `bash scripts/sync-scaffold.sh` leaving `git status --porcelain`
  unchanged. This session may not run git, so that command was not run. The
  oracle recorded instead is `tests.test_scaffold_data_in_sync
  tests.test_skills_vendored_in_sync` (13 tests with `test_design_for_diagnosis_rule`,
  OK) plus `cmp` of both `derive-monitoring` `SKILL.md` and `PROMPT.md` pairs
  (identical) and `grep -c` showing both `SKILL.md` copies name
  `http-status-regression` (1 each) and `version-stamping` (2 each). That is the
  same "copies already in sync" property by a different route; the driver's broad
  `sync-scaffold-bats` gate is what runs the script itself.
- **T02#2's** `grep -cE "re\.compile"` prints 3, not 0: the criterion's intent
  ("no longer counts a duration pattern") holds, the literal count does not go to
  zero because the file keeps three unrelated normalisation patterns.

### Other gates run this attempt

- `ruff check specfuse .specfuse/scripts tests scripts` → `All checks passed!`
- `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` → exit 0.
- The close's own `lint_plan.py --closing` is recorded in the report that ends this
  session, after the deliverables below were in place.

The gate's `broad_run` (driver, 2026-10-15T03:50:38Z, `GATE-01.md` frontmatter):
`ok: true`, `failing: []`. The driver's `broad_run_result` event is the record; it
was not re-run here (`tier: broad` gates are the driver's).

## Cost analysis

`planned_cost_usd` from each WU's frontmatter (and `PLAN.md`: 14.50 substantive +
5.00 close = 19.50) against the sum of `cost_usd` over that WU's `attempt_outcome`
events in `events.jsonl`:

| WU | planned_cost_usd | attempt_outcome events | actual cost_usd (sum) | delta |
| --- | ---: | --- | ---: | ---: |
| T01 | 3.00 | 2 (1 failed 0.262969, 1 passed 0.335449) | 0.598418 | -2.401582 (-80.1%) |
| T02 | 2.50 | 1 (passed) | 0.250054 | -2.249946 (-90.0%) |
| T03 | 2.50 | 4 (failed 0.234930, failed 0.258873, produces_not_in_diff 0.308750, passed 0.109215) | 0.911768 | -1.588232 (-63.5%) |
| T04 | 3.50 | 1 (passed) | 0.537765 | -2.962235 (-84.6%) |
| T05 | 3.00 | 1 (passed) | 0.334600 | -2.665400 (-88.8%) |
| **substantive total** | **14.50** | 9 | **2.632604** | **-11.867396 (-81.8%)** |
| G1-CLOSE | 5.00 | none yet | not recorded | its own `attempt_outcome` is written after this session ends, so it cannot be quoted from inside it |

Every substantive WU landed under plan; the gate's `cost_budget_usd` is 30.00. The
plan's estimates were 5–10x the real spend on every unit, which makes this feature's
budget numbers uninformative as a calibration point rather than a success: the
spread is the finding, not the sum. T03's four events carry `attempt` values 1, 1, 2,
3 because the first failed attempt was re-run after the operator re-armed it from
the `preexisting_gate_failure` escalation (see below); the WU's frontmatter reads
`attempts: 3`.

### Failure-class breakdown

- **T01, attempt 1 — class `other`, gate `roadmap-link-gate`.** The gate-entry
  probe failed on `roadmap.md:1089: FEAT-LOOP-2026-0203's detail section says… active.**'
  and keep any prose after it`, alongside `tests` (`failures=3`) and `coverage`
  (`no_gate_marker`); the driver attributed it to T01 and raised
  `preexisting_gate_failure`. The roadmap row and detail section for this feature
  were left in an inconsistent `planned` state by drafting, not by T01's code. The
  working tree now has the row at `active` and a `**Status: active.**` line in the
  detail section; T01 attempt 2 passed with no further failure.
- **T03, attempt 1 (first dispatch) — class `other`, test
  `test_one_deployment_files_one_finding_per_code`.** T03's new lint rule rejected
  the end-to-end oracle's own config: `AssertionError: Lists differ:
  ["component 'order-api': checks[0]: 'http-status-regression' check requires
  'deploy_signal' — a mapping with a 'kind' (one of ['app-version'])"] != []`. The
  walking-skeleton oracle and the lint it was meant to exercise disagreed about the
  shape of one field. The driver again escalated `preexisting_gate_failure` at
  gate entry (`tests`, `failures=2`).
- **T03, attempt 1 (second dispatch) — class `other`, same test, a different lint
  message** ("`… requires … nd'`" in the excerpt, truncated by the driver). Same
  root: the oracle's config and the new lint rule were out of step. By the
  `baseline_attribution` event at 03:36:22Z `failing` was `[]`.
- **T03, attempt 2 — class `produces_not_in_diff`.** Declared `produces:` paths
  `.specfuse/monitoring.yml.example` and `specfuse/loop/data/monitoring.yml.example`
  were not in the attempt's diff. Attempt 3 added the `codes:` example to both files
  and passed at $0.109215.

No failure here was a defect in the shipped feature: three of the four non-passing
attempts were an interface mismatch between two units written to agree, and the
fourth was the driver's produces-vs-diff guard doing its job.

## What the loop did NOT verify

1. **A live run against a real workspace.**
   - **Criterion:** the `http-status-regression` KQL query runs, without a schema
     resolution error, against a real Log Analytics workspace whose component stamps
     `AppVersion` (`PLAN.md` § Post-merge checklist).
   - **Reason not verified here:** every in-loop oracle runs over a stub transport,
     and `tests.test_app_insights_query_schema_check` checks the query only against
     the checked-in workspace-schema reference (from #3471), not against Azure.
     No consumer stamps a version today, so it also cannot be a pre-close human unit.
     The live test's own skip was visible in the run above (`OK (skipped=1)`).
   - **Where it gets checked:** the opt-in live check
     (`SPECFUSE_LIVE_TESTS=1 SPECFUSE_LIVE_WORKSPACE_ID=<id>`) once the new query is
     in its list, filed as one `specfuse:post-merge` issue at close.

2. **Re-sighting after a closed finding (decision 8's residual).**
   - **Criterion:** a spike re-observed after its finding's issue was closed does
     not open a second issue for the same (component, code, deployment).
   - **Reason not verified here:** it is not true and not meant to be.
     `issues.record_finding` searches open issues only, so a re-observation after
     close opens a new one; decision 6 (evaluate only a fully elapsed window) makes
     it rare but does not remove it. The in-loop oracles prove the fingerprint is
     stable across cycles (`test_same_rows_same_fingerprint`), which is a different
     property from deduplication across an issue's close.
   - **Where it gets checked:** nowhere yet by design. It is accepted and recorded
     here; it surfaces the first time a deployment's finding is closed while that
     deployment's window is still within the harvester's lookback. A consumer
     adopting the check is where it would be seen, and a bug or follow-up issue is
     the right place to engineer around it then.

Also not measured, and not a criterion: the first consumer's services do not stamp
a version, so no real telemetry has ever been fed through the check's
deployment-detection clause.

## Consumer-visible contract changes

Enumerated across T01–T05 for acknowledgment; each is also in `CHANGELOG.md`
`Unreleased` (`Added`: FEAT-LOOP-2026-0203; `Breaking`: #295).

- **Added — check type `http-status-regression`** accepted by `monitoring.yml` and
  `specfuse-monitor-lint`, with new fields `deploy_signal` (mapping, `kind`
  required, only `app-version` accepted), `window_after_deploy` (duration) and
  optional `codes` (non-empty list of unique integers in 400–499, default
  `401, 403, 405, 410, 412, 415, 428`). `targets` is forbidden on it.
- **Added — fixed thresholds** documented as constants, not fields: after-share at
  least 3× before-share and at least 10 occurrences.
- **Added — a finding per (component, status code, deployment version)** whose
  `failure_signature` carries the version, so a code's finding is filed once per
  deployment.
- **Added — `derive-monitoring` proposes the check** only with version-stamping
  evidence, and otherwise reports a single `version-stamping` finding; the
  design-for-diagnosis rule (both copies) gains the version-stamping contract.
- **Changed, breaking — `queue-stalled` `stall_after` is now validated.** A value
  outside `<integer><unit>` with unit `s`/`m`/`h`/`d` is a lint error where it was
  accepted and refused only at harvester runtime. Migration: rewrite to the grammar.
  Every value shipped in this repo (examples, fenced blocks) was already `15m`;
  `GATE-01-REVIEW.md` records the full-suite probe with exactly one expected failure.
- **Changed, internal — the duration grammar moved** from
  `parse_stall_after_seconds` in `azure_service_bus.py` to
  `specfuse/monitor/durations.py` (`parse_duration_seconds`); the old name is kept
  and agrees with it (`tests.test_monitor_durations`).

Awaiting human acknowledgment of this list, per `close-discipline.md` §3.

#295 is closed by reference: its CHANGELOG entry traces to it and the PR that
carries this branch should say `Closes #295` and `Refs #248`. This session did not
close the issue itself: closing is outward-facing and belongs to the PR that merges
the branch.

## Retrospective

**What went well.** The walking skeleton did its job: T01's oracle module existed
before anything else, so no unit failed on `ModuleNotFoundError`, and the e2e oracle
caught T03's lint disagreeing with the skeleton's config before the adapter work
built on it. Folding #295 in via one shared grammar meant `window_after_deploy`
and `stall_after` could not drift, and the §4 runtime probe in `GATE-01-REVIEW.md`
predicted the one expected failure exactly. Decision 5 was forced by a binding rule
and held: a single query, measured twice.

**What didn't.** Drafting left the roadmap row and detail section for this feature
at `planned` while the plan was `active`, which tripped `roadmap-link-gate` at the
first gate entry and was attributed to T01 and escalated; the driver attributed a drafting-time
roadmap defect to the first unit it dispatched. T03's two failures
were an interface mismatch between a skeleton's literal config and the lint it was
supposed to anticipate; the skeleton pinned its config before the schema unit had
settled how `deploy_signal` was parsed.

**Open follow-ups (not blockers).** The decision-8 residual; the live run; and
`HttpStatusRegressionAdapter`'s row contract (`version`, `code`, `first_seen`,
`after`, `before`, `after_total`, `before_total`) is held only by the adapter's test
and its one query, with no schema for it outside the code.
