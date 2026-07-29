## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0040
- predicate_version: v1
- gate_total_cost: $2.65
- gate_budget: $26.00
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

This gate auto-closed on-plan; the full close-intermediate ceremony did
not run, so the per-criterion deferred-verification list was **not**
enumerated. Any acceptance criterion whose verification is deferred
(loop-sandbox limit, cross-repo coordination, real-system access) is
unrecorded here. Gate 2's close MUST reconcile these
before the feature's terminal verdict — auto-close cannot enumerate them.

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=32 predicate=v1 -->

- **FEAT-2026-0040/T01** (`WU-01-artifact-model-adapter-protocol.md`)
  - deferred: `tests/test_failure_artifact_model.py::TestArtifactModel::test_artifact_carries_target_coordinates`
  - deferred: `specfuse/monitor/artifact.py` defines `FailureArtifact` carrying at minimum: the
  - deferred: `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/artifact.py specfuse/monitor/adapters.py`
  - deferred: A `FailureArtifact` built from a `dlq` target round-trips both `subscription` and
  - deferred: A `FailureArtifact` built for an `invariant` check carries **no** target
  - deferred: `specfuse/monitor/adapters.py` defines `TelemetryAdapter` and `BrokerAdapter` as
  - deferred: `specfuse/monitor/adapters.py` defines `resolve_telemetry(component, environment)`
  - deferred: A test asserts `resolve_telemetry` is called with the **component** — not only
  - deferred: `specfuse/monitor/artifact.py` contains no cron, schedule, or dialect field:
  - deferred: `python3 -m pytest tests/test_failure_artifact_model.py -q` exits zero after this
  - deferred: `python3 -c "from specfuse.monitor.artifact import FailureArtifact; from specfuse.monitor.adapters import TelemetryAdapter, BrokerAdapter, resolve_telemetry"`
- **FEAT-2026-0040/T02** (`WU-02-fingerprinting.md`)
  - deferred: `tests/test_fingerprint.py::TestFingerprint::test_distinct_targets_produce_distinct_fingerprints`
  - deferred: `specfuse/monitor/fingerprint.py` defines `fingerprint_artifact(artifact)`
  - deferred: A `dlq` artifact's fingerprint incorporates both `subscription` and `function`
  - deferred: A `heartbeat` artifact's fingerprint incorporates the target's `name`.
  - deferred: **Two artifacts identical in every field except their target coordinates produce
  - deferred: An `invariant` artifact's fingerprint is derived from the check's `fingerprint_by`
  - deferred: Two artifacts identical in component, failure class, failure signature, and target
  - deferred: Calling `fingerprint_artifact` twice on the same artifact in **separate Python
  - deferred: The fingerprint is insensitive to the ordering of the target-coordinates mapping.
  - deferred: `python3 -m pytest tests/test_fingerprint.py -q` exits zero after this WU's edits
  - deferred: `python3 -c "from specfuse.monitor.fingerprint import fingerprint_artifact"`
- **FEAT-2026-0040/T03** (`WU-03-redaction.md`)
  - deferred: `tests/test_artifact_redaction.py::TestRedaction::test_planted_secret_is_redacted_at_the_boundary`
  - deferred: `specfuse/monitor/redaction.py` defines `redact_artifact(artifact)` returning a
  - deferred: An artifact whose observed text contains a planted secret yields no occurrence of
  - deferred: A redacted value is replaced by a stable short digest in the `<redacted:sha8>`
  - deferred: **Positive control:** the redaction pattern produces at least one match against a
  - deferred: `grep -n "leak_scan" specfuse/monitor/redaction.py` returns no match — the module
  - deferred: Text containing no secret passes through unchanged — redaction does not mangle an
  - deferred: The failure **signature** used for fingerprinting survives redaction unchanged, or
  - deferred: `python3 -m pytest tests/test_artifact_redaction.py -q` exits zero after this WU's
  - deferred: `python3 -c "from specfuse.monitor.redaction import redact_artifact"` exits zero.

> **Reconciled by `FEAT-2026-0040/G2-CLOSE-INTERMEDIATE`.** The list above is the
> auto-close's mechanical dump of every gate-1 criterion, marked `deferred` because
> nothing had looked at them — not because any of them was actually deferred. See
> [`## What the loop did NOT verify`](#what-the-loop-did-not-verify) below, subsection
> **Gate 1's auto-close debt, reconciled**, for the per-criterion disposition. The
> marker line is deliberately left in place: `assert_autoclose_debt_reconciled` fires on
> the terminal `close`, and `G3-CLOSE` must still name `gate 1` literally in its own
> deferred-verification section.

---

## Gate 2 — the Azure adapters produce artifacts, and a schedule declares its dialect

Closed 2026-07-28 by `FEAT-2026-0040/G2-CLOSE-INTERMEDIATE`. Non-terminal gate: no
verdict is recorded here. The feature's terminal verdict belongs to `G3-CLOSE`.

Four substantive work units, all `done`, **all on their first attempt**, no escalations
and no blocked reports:

| WU | shipped |
|---|---|
| `T04` | The `dialect` contract: `CRON_DIALECTS` in `specfuse/loop/lint_monitoring.py`, four ERROR-severity validator rules, both example copies migrated, the `derive-monitoring` reference implementation emitting the field, and a walk-discovered tree-wide sweep |
| `T05` | `specfuse/monitor/providers/azure_service_bus.py` — `ServiceBusDlqAdapter` over a constructor-injected `ServiceBusDlqTransport`, one redacted artifact per dead-lettered message carrying `subscription` + `function` |
| `T06` | `specfuse/monitor/providers/azure_app_insights.py` — `ErrorLogsAdapter`, `Http5xxAdapter`, `InvariantAdapter`, each resolving its binding through `resolve_telemetry(component, environment)` |
| `T07` | `specfuse/monitor/schedule.py` (`most_recent_firing`) plus `HeartbeatAdapter` in the App Insights module — a stdlib-only cron evaluator over both arities, reading the declared dialect and refusing on arity disagreement |

`queue-stalled` still has no adapter. That is a recorded decision, not a gap discovered
here: `GATE-02-REVIEW.md` §2 named it before arming and §6.1 answer 3 placed it in gate
3 alongside the CLI, so gate 2 stayed the adapter-shape gate.

### Failed attempts

None. Every `attempt_outcome` event for `T04`–`T07` in `events.jsonl` reads
`"outcome": "passed"` at `"attempt": 1`. `assert_failure_class_breakdown_when_failures_present`
therefore does not apply, and a `### Failure-class breakdown` heading is absent because
the gate had no failures — not because the section was skipped.

### Which sandbox each gate ran under

Stated per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`: a bare pass/fail count read out of
this environment manufactures a regression. Two distinct environment effects were
observed in this session, and **neither is a defect in gate 2's work**.

| gate | sandbox | result | note |
|---|---|---|---|
| `tests` | default (sandboxed) | **exit 1** — `Ran 1753 tests`, `FAILED (errors=3, skipped=3)` | 3 errors, all in `tests/test_autosync_no_cwd_leak.py`, all `git commit … returned non-zero exit status 128` |
| `tests` | default sandbox, `commit.gpgsign=false` | **exit 0** — `Ran 1753 tests`, `OK (skipped=3)` | the 3 errors are host-config contamination, not a regression |
| `lint` (`ruff`) | default | exit 0 — `All checks passed!` | |
| `security` (`bandit -ll`) | default | exit 0 — Medium: 0, High: 0 | |
| `coverage` (`--fail-under=90`) | default sandbox, `commit.gpgsign=false` | exit 0 — **TOTAL 94%** | `schedule.py` 95%, `azure_app_insights.py` 90%, `azure_service_bus.py` 81% |
| `leak-scan` | default | exit 0 — `leak-scan: clean` (gitleaks 8.30.1) | |
| `monitoring-example-lint` | default | exit 0 — `OK — monitoring config is structurally valid (or absent).` | |
| 6 × `bats` suites | default (sandboxed) | **exit 1**, 21 of 22 cases `not ok` | every failure is `mktemp: mkdtemp failed on …: Operation not permitted` in `setup`, before any assertion runs |
| 6 × `bats` suites | sandbox off | **exit 0 for all six**, 22 `ok` / 0 `not ok` | the real signal |

Two findings about the environment, both worth carrying:

1. **The `bats` failure is the one `T05`/`T06`/`T07`'s Verification sections predicted**,
   and it is already a recorded lesson (`[FEAT-2026-0072/G1-CLOSE]`). Overriding `TMPDIR`
   does not help — `mktemp` still resolves the system temp path. Before re-running with
   the sandbox off, each suite's `setup` was read to confirm every path is rooted in a
   `$TESTDIR` temp directory (`sync_scaffold.bats` overrides `REPO_ROOT`;
   `hookspath_conflict.bats` `cd`s into its own `git init`), so nothing in the real tree
   is touched.
2. **A second, different contamination, not previously in `LEARNINGS.md`.**
   `tests/test_autosync_no_cwd_leak.py`'s `_make_repo` pins `user.name` and `user.email`
   on its throwaway repos but nothing else, so each `git commit` inherits the host
   operator's **global** `commit.gpgsign = true` with `gpg.format = ssh`. The signing
   agent socket is unreachable from the sandbox, and git fails with:

   ```
   error: Couldn't get agent socket?
   fatal: failed to write commit object
   ```

   Confirmed by a controlled re-run rather than inferred:
   `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false python3 -m unittest tests.test_autosync_no_cwd_leak`
   → `Ran 3 tests … OK`. `GATE-02-REVIEW.md` §4's probe-environment note observed the
   same symptom at arming time and flagged the fixture fix as a follow-up; that follow-up
   is still open (see the follow-up list below). The file is `#290`'s driver regression
   test and touches no surface `T04`–`T07` own.

### Oracle re-runs — fresh, in this session

Per `close-discipline.md` §1: exit codes read directly, never inherited from a producing
unit's self-report. Every oracle named by `T04`–`T07`:

| # | oracle | command | exit |
|---|---|---|---|
| 1 | `monitoring-example-lint` (T04 c9) | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** — `OK — monitoring config is structurally valid (or absent).` |
| 2 | T04 c1/c4/c5 | `python3 -m unittest tests.test_monitoring_cron_dialect -v` | **0** — `Ran 9 tests … OK` |
| 3 | T04 c10 | `python3 -m unittest tests.test_monitoring_fenced_blocks -v` | **0** — `Ran 5 tests … OK` |
| 4 | T04 c6/c7b | `python3 -m unittest tests.test_derive_monitoring_discovery` | **0** — `Ran 24 tests … OK` |
| 5 | T05 c11 | `python3 -m unittest tests.test_service_bus_dlq_adapter` | **0** — `Ran 9 tests … OK` |
| 6 | T06 c11 | `python3 -m unittest tests.test_app_insights_adapters` | **0** — `Ran 12 tests … OK` |
| 7 | T07 c12 | `python3 -m unittest tests.test_schedule_dialect` | **0** — `Ran 19 tests … OK` |
| 8 | T07 c12 | `python3 -m unittest tests.test_heartbeat_adapter` | **0** — `Ran 8 tests … OK` |
| 9 | T05 c9 / T06 c10 | `grep -rniE "azure\|appinsights\|servicebus\|kusto" specfuse/monitor/artifact.py specfuse/monitor/adapters.py specfuse/monitor/fingerprint.py specfuse/monitor/redaction.py` | **1** (no match — the passing outcome) |
| 10 | T05 c10 / T06 c10 | `grep -rn "from specfuse.monitor.providers\|import specfuse.monitor.providers" specfuse/monitor/*.py` | **1** (no match) |
| 11 | T07 c11 | `grep -rniE "azure\|appinsights\|servicebus\|kusto" specfuse/monitor/schedule.py specfuse/monitor/artifact.py specfuse/monitor/adapters.py specfuse/monitor/fingerprint.py specfuse/monitor/redaction.py` | **1** (no match) |
| 12 | T07 c11 | `grep -rn "datetime.now\|time.time" specfuse/monitor/schedule.py` | **1** (no match — the reference time is always an argument) |
| 13 | `code` gate set, whole | see the sandbox table above | green in a permitting environment; two environment contaminations named there |

### The sweep, re-run rather than inherited

`T04` criterion 4's tree-wide completeness assertion, executed fresh in this session
rather than read off `T04`'s `done` status. Both halves of the criterion matter — zero
non-conforming instances **and** a non-vacuous collection:

```
$ python3 -m unittest tests.test_monitoring_cron_dialect
Ran 9 tests in 0.320s
OK

$ python3 -c "from tests.test_monitoring_cron_dialect import _collect_cron_carrying_targets; ..."
collected targets: 14
files discovered: 4
non-conforming: 0
```

| file discovered by the walk | cron-carrying targets |
|---|---|
| `.specfuse/monitoring.yml.example` | 2 |
| `specfuse/loop/data/monitoring.yml.example` | 2 |
| `tests/test_derive_monitoring_discovery.py` | 7 |
| `tests/test_heartbeat_adapter.py` | 3 |
| | **14 total**, dialects: 13 × `standard-5`, 1 × `seconds-first-6` |

**Fourteen collected, zero non-conforming.** The sweep is therefore proven to distinguish
"clean" from "empty" — the defect `T04` criterion 5 was written against, and the one
`[FEAT-2026-0069]`'s probe found in two of its own boundary tests.

**The most useful thing the fresh run shows is a file `T04` never saw.**
`tests/test_heartbeat_adapter.py` did not exist when `T04` ran the sweep — `T07` created
it later in the same gate, carrying 3 more cron-declaring targets, including the only
`seconds-first-6` instance in the tree. Because the file list is discovered by walking
`git ls-files` rather than hand-written, the assertion absorbed the new surface with no
edit. A hand-written path tuple would have gone on reporting "zero non-conforming" while
silently not looking at the one file that exercises the second dialect. That is the
`[FEAT-2026-0039/T04]` failure mode `T04` criterion 4 was authored against, caught in the
act one gate later.

### Provider agnosticism as a property of the tree, not only a passing test

`G2-CLOSE-INTERMEDIATE` criterion 7 widens `T05`/`T06`/`T07`'s file-scoped greps to the
whole package:

```
$ grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/
```

**29 matches, every one of them under `specfuse/monitor/providers/`** — 17 in
`azure_service_bus.py`, 12 in `azure_app_insights.py`. **Matches outside `providers/`:
zero.** The core modules `__init__.py`, `adapters.py`, `artifact.py`, `fingerprint.py`,
`redaction.py`, and `schedule.py` contribute no match at all, so the "every match outside
`providers/` is named in the retrospective" clause has an empty list to name — not by
narrowing the grep, but because the property holds.

The dependency arrow is checked in the other direction too (oracle 10): nothing under
`specfuse/monitor/` outside `providers/` imports from `providers/`. Gate 1's and gate 2's
central claim survives a tree-wide test, not just a file-scoped one.

## Cost analysis

Read from `events.jsonl`'s `attempt_outcome` payloads. The **as-drafted** figures are
reported as the honest plan, per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` — the plan is
not re-based onto its own outcome and the result then reported as accuracy.

| WU | planned (as drafted) | actual | delta |
|---|---|---|---|
| `T04` | $4.50 | **$6.25** | **+$1.75 (+39%)** |
| `T05` | $4.00 | **$1.53** | −$2.47 (−62%) |
| `T06` | $4.00 | **$1.18** | −$2.82 (−70%) |
| `T07` | $4.00 | **$4.37** | +$0.37 (+9%) |
| **implementation subtotal** | **$16.50** | **$13.33** | **−$3.17 (−19%)** |
| `G2-CLOSE-INTERMEDIATE` | $4.50 | this session — not yet in `events.jsonl` at write time | — |
| `G2-PLAN` | $6.00 | not yet run | — |
| **gate 2 drafted total** | **$27.00** | **$13.33 spent so far** | $13.67 of drafted budget unspent |

`GATE-02.md` carries `cost_budget_usd: 33.00` — the $27.00 drafted sum plus $6.00 of
defensive padding for one re-attempt of the largest WU. No re-attempt occurred, so that
padding is untouched. **Gate 2 stands at $13.33 against a $33.00 halt threshold (40%),
with two closing units still to run.**

**The delta that matters is not the underrun — it is which unit over-ran.**
`GATE-02-REVIEW.md` §5.3 faced an explicit temptation: gate 1's substantive units came in
at $2.65 against $9.50 (**−72%**, three for three, all first attempt), and scaling gate 2
down by that factor would have priced its six units near $10.00. §5.3 refused, on the
grounds that three observations are not a distribution and that gate 1's units were
unusually clean — new modules, no tree to migrate, no severity flip, no cross-file
assertions to re-aim — while `T04` was none of those things. §6.1 answer 1 recorded the
operator affirming that.

That call is now measured, and it was right in the specific way it predicted. The three
new-module adapter units did land near gate 1's shape (`T05` −62%, `T06` −70%,
`T07` +9%). **The single over-run is `T04` at +39% — precisely the migration-and-severity-flip
unit §5.3 named as the reason not to scale down.** Had the whole gate been priced on gate
1's underrun, `T04` would have been budgeted near $1.25 and actually cost $6.25, and the
budget halt would have landed on the first unit of the gate.

For context across the feature to date:

| gate | planned (drafted units) | actual | note |
|---|---|---|---|
| gate 1 | $20.00 | **$9.34** (−53%) | T01 $1.15, T02 $0.85, T03 $0.65, `G1-CLOSE-INTERMEDIATE` **$0.00** (auto-closed, `attempts: 0`), `G1-PLAN` $6.69 (+11% on $6.00) |
| gate 2 | $27.00 | **$13.33 so far** | two closing units outstanding |
| **feature to date** | | **$22.67** | against `PLAN.md`'s `planned_cost_usd: 52.00`, which is drafted work only and rises again when `G2-PLAN` prices gate 3 |

One honest note on gate 1's $9.34: **$6.69 of it — 72% — was the planning WU**, and the
$4.50 budgeted for gate 1's close was never spent because the close never ran. Gate 1 did
not come in cheap because the work was cheap; it came in cheap partly because a
load-bearing ceremony was skipped, which is the debt the next section settles.

<a id="what-the-loop-did-not-verify"></a>
## What the loop did NOT verify

### Gate 2 — the deferred list, which is not empty

`verification.yml` records that this repository "is a CLI tool with no deployable
components and will never carry a real monitoring.yml." That is not a shortcut taken
here; it is a structural property of the repo, and it bounds what gate 2's evidence can
mean. **Every adapter `T05`, `T06`, and `T07` shipped was exercised only against a stub
transport.**

A stub proves the adapter's shape, its coordinate handling, its redaction boundary, and
its fingerprint behaviour. It proves nothing about the transport underneath. Concretely:

| # | deferred criterion | why the loop could not verify it | where it is actually verified |
|---|---|---|---|
| D-1 | `T05` c2/c11 — `ServiceBusDlqAdapter.fetch_failures()` returns one `FailureArtifact` per dead-lettered message | **No live Service Bus namespace was reached.** The transport is a stub constructed in the test; the real peek API's paging, throttling, and dead-letter metadata field names are unobserved | Operator run against the downstream .NET backend |
| D-2 | `T05` c6 — the adapter issues no settlement call | Verified as a **recorded-call assertion against the stub**, which is strong evidence about the adapter and no evidence about how the real SDK behaves when a peek iterator is exhausted or a lock lapses | Operator run against the downstream .NET backend |
| D-3 | `T05` c7 / `T06` c7 — signature normalization collapses repeat occurrences | The "occurrences" are canned stub rows built to differ only in ID and timestamp. Whether a real dead-lettered message or a real exception row varies only in those fields is unobserved | Operator run against the downstream .NET backend |
| D-4 | `T06` c2/c11 — `ErrorLogsAdapter`, `Http5xxAdapter`, `InvariantAdapter` map rows to artifacts | **No live App Insights workspace was reached.** Whether a real KQL result set carries the columns `_error_logs_query`, `_http_5xx_query`, and the operator-authored `invariant.query` name is unobserved | Operator run against the downstream .NET backend |
| D-5 | `T06` c6 — the `invariant` contract: `failure_signature` is the `fingerprint_by` column's value | The fixture supplies that column by construction. Whether a real workspace returns a column of that name for an operator-authored query is unobserved — this is the criterion whose failure mode is silent, since a missing column yields artifacts that still fingerprint, just wrongly | Operator run against the downstream .NET backend |
| D-6 | `T06` c9 — no query is built from observed data | Verified against a stub returning query-shaped text. Correct and load-bearing as a property of the adapter; says nothing about the real client's query construction | Operator run against the downstream .NET backend |
| D-7 | `T07` c7/c8/c9 — the heartbeat adapter emits exactly one artifact for the silent schedule | The "last observed heartbeat" is a stub value. Whether a real workspace's heartbeat telemetry is complete and timely enough that a silent schedule is distinguishable from a query gap is unobserved, and this is the **false-positive** direction the criterion exists to protect | Operator run against the downstream .NET backend |
| D-8 | `T07` c6 — DST and timezone arithmetic | Asserted against the stdlib's bundled tz database at a pinned reference instant. **No DST transition has been observed in production.** Whether the deployed schedule agrees with the computed instant is an operator observation | Operator run against the downstream .NET backend, observed across a real DST boundary |

**The oracle that discharges D-1 through D-8 is an operator run of the harvester against
the downstream .NET backend** — the same oracle `FEAT-2026-0069` used to discharge its
own FU-1 and FU-3 after its terminal close. `GATE-02-REVIEW.md` §6.1 answer 4 records that
such a run **is planned**, which is what keeps these items a named upgrade condition
rather than a permanent deferral. `G3-CLOSE` should carry that run as the condition that
upgrades the feature's terminal verdict, and should not assume it has happened.

`GATE-02.md`'s definition of done was written so that none of the above is a clause in
it. Nothing in gate 2 claims an adapter works against a live environment. This list is
therefore the gate's honest residue, not a set of missed criteria.

### Gate 1's auto-close debt, reconciled

`RETROSPECTIVE.md` carries `<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=32 predicate=v1 -->`.
Gate 1 auto-closed on-plan at `attempts: 0`, so its close-intermediate ceremony never
ran and its 32 acceptance criteria were dumped as `deferred` without anyone looking at
them. **"Legitimately empty" and "never looked at" are different claims**, and only this
reconciliation distinguishes them.

**Disposition: all 32 criteria were verified in-loop, and 29 of them were re-verified
fresh in this session.** Gate 1 was scoped so that its deferred list is legitimately
empty — every criterion is an assertion over new modules the gate itself wrote, decidable
by a test, a grep, or an import, with no live system anywhere. Re-run here:

```
$ python3 -m pytest tests/test_failure_artifact_model.py -q   →  exit 0   (8 passed)
$ python3 -m pytest tests/test_fingerprint.py -q              →  exit 0   (8 passed)
$ python3 -m pytest tests/test_artifact_redaction.py -q       →  exit 0   (5 passed)
$ grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/artifact.py specfuse/monitor/adapters.py   →  no match
$ grep -niE "cron|schedule|dialect" specfuse/monitor/artifact.py                                              →  no match
$ grep -n "hash(" specfuse/monitor/fingerprint.py                                                             →  no match
$ grep -n "leak_scan" specfuse/monitor/redaction.py                                                           →  no match
$ python3 -c "from specfuse.monitor.artifact import FailureArtifact; from specfuse.monitor.adapters import TelemetryAdapter, BrokerAdapter, resolve_telemetry"   →  exit 0
$ python3 -c "from specfuse.monitor.fingerprint import fingerprint_artifact"   →  exit 0
$ python3 -c "from specfuse.monitor.redaction import redact_artifact"          →  exit 0
```

Per criterion:

**`FEAT-2026-0040/T01` — 11 criteria, 0 deferred.**

| c | disposition |
|---|---|
| 1 | red-before-green on `test_artifact_carries_target_coordinates` — **verified in-loop at the time; not re-runnable now**, the file exists. See the caveat below |
| 2 | verified in-loop; re-verified — `test_artifact_carries_target_coordinates` passes |
| 3 | verified in-loop; **re-run here**, grep returns no match |
| 4 | verified in-loop; re-verified — `test_from_target_round_trips_dlq_coordinates`, `test_from_target_round_trips_heartbeat_coordinates` |
| 5 | verified in-loop; re-verified — `test_invariant_artifact_carries_no_target_coordinates` |
| 6 | verified in-loop; re-verified — `test_adapter_protocols_declare_failure_artifact_return_type` |
| 7 | verified in-loop; re-verified — `test_resolve_telemetry_reads_environment_binding` |
| 8 | verified in-loop; re-verified — `test_resolve_telemetry_receives_component`. Gate 2's `T06`/`T07` are the first real consumers and assert the same thing |
| 9 | verified in-loop; **re-run here**, grep returns no match |
| 10 | verified in-loop; **re-run here**, exit 0 |
| 11 | verified in-loop; **re-run here**, exit 0 |

**`FEAT-2026-0040/T02` — 11 criteria, 0 deferred.**

| c | disposition |
|---|---|
| 1 | red-before-green on `test_distinct_targets_produce_distinct_fingerprints` — verified in-loop at the time; not re-runnable now |
| 2 | verified in-loop; re-verified by the passing suite |
| 3 | verified in-loop; re-verified — `test_dlq_fingerprint_incorporates_subscription_and_function` |
| 4 | verified in-loop; re-verified — `test_heartbeat_fingerprint_incorporates_name` |
| 5 | verified in-loop; re-verified — `test_distinct_targets_produce_distinct_fingerprints`. **This is the binding constraint the whole feature inherits from 0069**, and gate 2's `T05` c5 and `T07` c8 assert it again at the adapter level |
| 6 | verified in-loop; re-verified — `test_invariant_fingerprint_distinguishes_different_fingerprint_by`, `test_invariant_fingerprint_ignores_absent_target_coordinates` |
| 7 | verified in-loop; re-verified — `test_identical_artifacts_produce_the_same_fingerprint` |
| 8 | verified in-loop; **re-run here** — `grep -n "hash("` returns no match, and `test_fingerprint_stable_across_separate_processes` passes |
| 9 | verified in-loop; re-verified — `test_fingerprint_insensitive_to_coordinate_ordering` |
| 10 | verified in-loop; **re-run here**, exit 0 |
| 11 | verified in-loop; **re-run here**, exit 0 |

**`FEAT-2026-0040/T03` — 10 criteria, 0 deferred.**

| c | disposition |
|---|---|
| 1 | red-before-green on `test_planted_secret_is_redacted_at_the_boundary` — verified in-loop at the time; not re-runnable now |
| 2 | verified in-loop; re-verified by the passing suite |
| 3 | verified in-loop; re-verified — `test_planted_secret_is_redacted_at_the_boundary` |
| 4 | verified in-loop; re-verified — `test_same_secret_redacts_to_same_token_different_to_different` |
| 5 | verified in-loop; re-verified — `test_positive_control_pattern_fires_on_planted_secret`. The negative observation `verification-discipline.md` §3 requires |
| 6 | verified in-loop; **re-run here**, grep returns no match — the module does not import repo-internal tooling absent in consumer projects (issue #55) |
| 7 | verified in-loop; re-verified — `test_ordinary_exception_text_passes_through_unchanged` |
| 8 | verified in-loop; re-verified — `test_failure_signature_survives_redaction_unchanged` |
| 9 | verified in-loop; **re-run here**, exit 0 |
| 10 | verified in-loop; **re-run here**, exit 0 |

**The one honest caveat.** Three of the 32 — criterion 1 of each WU — are
*red-before-green* claims about the tree at a commit that no longer exists in the working
state. They were verified by the producing session at the moment they were checkable and
are **not re-runnable at close time by construction**. This reconciliation therefore
rests on the producing sessions' reports for those three, and on fresh re-runs for the
other 29. That is a property of red-before-green criteria in general, not a gap specific
to gate 1, and it is stated rather than papered over.

**Conclusion: gate 1's deferred list is empty, and is now empty as a checked fact rather
than as an untested assumption.** The debt is settled. The marker comment stays in place
so `G3-CLOSE`'s `assert_autoclose_debt_reconciled` still fires and the terminal close
still names `gate 1` literally.

### Follow-ups carried forward, not blocking

- **FU-A — the fixture-signing contamination.** `tests/test_autosync_no_cwd_leak.py`'s
  `_make_repo` should set `commit.gpgsign=false` (and `tag.gpgsign=false`) on its
  throwaway repos alongside `user.name`/`user.email`. Flagged in `GATE-02-REVIEW.md` §4's
  probe-environment note at arming and re-observed here. Not fixed in this session: it is
  a source file no gate-2 WU owns, and this close does not patch work. A one-line fixture
  change for a hygiene WU or a bug branch.
- **FU-B — `queue-stalled` has no adapter.** Decided into gate 3 by `GATE-02-REVIEW.md`
  §6.1 answer 3. Recorded here so it stays a decision.
- **FU-C — `azure_service_bus.py` sits at 81% line coverage** while the package floor is
  90% overall (TOTAL 94%, so the gate is green). The uncovered lines are concentrated in
  `build_azure_transport`, which cannot be exercised without the SDK on the path. Worth
  naming so a future coverage tightening does not read it as neglect.

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3. This section **requires explicit human
acknowledgment before the gate closes**, and the `dialect` entry is why: writing
`n/a — no consumer-visible contract change` here would be false.

### 1. `heartbeat` target `dialect` — **BREAKING**

| | |
|---|---|
| **surface** | `.specfuse/monitoring.yml` — every `checks[].targets[]` entry on a `heartbeat` check |
| **change** | A new `dialect` field, **required whenever the target carries `cron`**. Enum: `standard-5` (5 fields: minute hour day-of-month month day-of-week) and `seconds-first-6` (6 fields: second minute hour day-of-month month day-of-week). Four ERROR-severity validator rules: `cron` without `dialect`; `dialect` outside the enum; field count disagreeing with the declared arity; `dialect` with no `cron` |
| **why breaking** | **A downstream project whose `monitoring.yml` already carries a cron-carrying heartbeat target lints clean today and will not after upgrade.** The finding is ERROR-severity and lands in the same list every other finding does, so `monitoring-example-lint`-equivalent gates in consumer repos turn red on a config nobody edited |
| **blast radius** | Bounded to `heartbeat` targets that carry `cron`. A cron-less `heartbeat` target stays valid and needs no `dialect`; `cron` itself remains optional; no other check type is affected |
| **consumer migration** | For each `heartbeat` target carrying `cron`: count the expression's whitespace-separated fields, add `dialect: standard-5` for 5 fields or `dialect: seconds-first-6` for 6, and re-run the monitoring linter. **This is a mechanical edit and the count is the answer** — the schema is strict at lint time precisely so the ambiguity is settled once, in the config, rather than guessed at every evaluation. Projects that generate the file with `/derive-monitoring` can instead re-run the skill: it now emits `dialect` from the discovered trigger registration |
| **why not inferred instead** | Inference by field count was considered and **rejected by the operator**. It degrades silently the moment a third dialect arrives — the worst possible moment for a monitoring tool to start guessing. A declared dialect turns a mismatch into a validation error at lint time instead of a wrong verdict at 3am. `T07`'s adapter refuses on arity disagreement rather than falling back, so the position holds outside the lint path too |
| **enum names locked** | `GATE-02-REVIEW.md` §6.1 answer 2 records the operator confirming `standard-5` / `seconds-first-6` **before** `T04` was armed, because renaming an enum after ship is a second breaking change to the same field |

### 2–6. Additive, non-breaking

| # | surface | change | consumer impact |
|---|---|---|---|
| 2 | `specfuse.loop.lint_monitoring.CRON_DIALECTS` | new name in `__all__`, mapping dialect → arity | Additive. Nothing previously imported it |
| 3 | `.specfuse/monitoring.yml.example` and the packaged seed `specfuse/loop/data/monitoring.yml.example` | both gain `dialect: standard-5` on their two heartbeat targets; held byte-identical (`cmp` exits 0) | Additive. A newly scaffolded project gets a conforming example. **Does not migrate an existing project's own `monitoring.yml`** — that is entry 1's manual step |
| 4 | the `derive-monitoring` skill | generated `heartbeat` targets now carry the `dialect` the discovered trigger registration implies | Additive, and the reason entry 1's migration is cheap for generated configs. Canonical copies under `plugins/specfuse/skills/` edited and propagated by `scripts/sync-scaffold.sh` |
| 5 | `specfuse.monitor.providers` (new subpackage) | `ServiceBusDlqAdapter`, `ServiceBusDlqTransport`, `DeadLetterMessage`, `build_azure_transport`; `ErrorLogsAdapter`, `Http5xxAdapter`, `InvariantAdapter`, `HeartbeatAdapter`, `AppInsightsTransport`, `build_app_insights_transport` | Additive — new modules, no prior version. **Zero new runtime dependencies**: SDK imports are lazy, inside the `build_*` factory bodies, so `import specfuse.monitor.providers.azure_service_bus` succeeds on a clean checkout with no cloud SDK installed |
| 6 | `specfuse.monitor.schedule` (new module) | `most_recent_firing(expression, dialect, timezone, reference)` | Additive. Stdlib-only. Supports `*`, `*/n`, comma lists, `a-b` ranges, and literals over both arities, and **rejects** `L`, `W`, `#`, and named months/weekdays with an explicit error rather than mis-parsing them |

### Acknowledgment

> **Status: NOT YET ACKNOWLEDGED — this close is blocked on it.**
>
> `close-discipline.md` §3 requires the human to acknowledge this list, and entry 1 is a
> breaking schema change for downstream consumers. This section is left for the operator
> to sign; per `operator-escalation.md`, the acknowledgment text is the human's to write
> and is not drafted here.
>
> _Operator acknowledgment:_

## Lessons

Three entries appended to `.specfuse/LEARNINGS.md`, tagged
`[FEAT-2026-0040/G2-CLOSE-INTERMEDIATE]`: the walk-discovered sweep that absorbed a
later WU's file; the inherited-host-config contamination distinct from the already-recorded
`mktemp` one; and the calibration result that a migration-and-severity-flip WU must not be
priced off a new-module gate's underrun.

Feature-specific observations — the `queue-stalled` deferral, the coverage shape of
`build_azure_transport`, the exact stub cardinalities — stay here and are deliberately
not promoted.

## Docs and roadmap

- `docs/concepts/monitoring-schema.md` — the `dialect` section already matched the four
  validator rules. One behaviour was documented but not recorded: the rules key off
  **truthiness**, so `cron: ""` is treated as absent and reports the *dialect-without-cron*
  finding rather than an empty-expression one. Observed directly, not read off the source:
  `cron: ""` with `dialect: standard-5` → `'dialect' declared without 'cron' — a dialect
  with no expression is not valid`; `cron: "   "` → `'cron' expression has 0 field(s),
  dialect 'standard-5' requires 5`. The doc now states this.
- `.specfuse/roadmap.md` — FEAT-2026-0040's detail section gains gate-1 and gate-2
  shipped notes, and the "two open schema questions" paragraph is updated: the
  cron-dialect ambiguity is now **decided**, and [#262](https://github.com/specfuse/loop/issues/262)
  is deferred **through a seam** rather than left open in the shape it warned about.

---

## Gate 3 — a finding becomes an issue, once, and something runs the cycle

Closed 2026-07-29 by `FEAT-2026-0040/G3-CLOSE`. **Terminal gate.** Verdict:
**`partially_met`** — recorded in this WU's frontmatter, and argued below rather than
asserted. It is not the `met_locally` gate 2 expected, and it is not `met`: the fresh
oracle re-run this close is obliged to perform found a **real, reproducible failure in
the tree at HEAD** that no producing WU could have seen. That finding is the most
valuable thing in this section.

Four substantive work units, all `done`:

| WU | shipped | evidence class |
|---|---|---|
| `T08` | `QueueStalledAdapter` in `specfuse/monitor/providers/azure_service_bus.py` — depth **plus** age-of-oldest over `T01`'s `BrokerAdapter`, a `<int><s\|m\|h\|d>` threshold grammar that **refuses** rather than guesses, and a skip-with-recorded-reason for a target with no `stall_after` | **fully in-loop**, stub transport |
| `T09` | `specfuse/monitor/issues.py` — fingerprint-keyed find-or-create over `escalation.py`'s injected-runner seam, `--search` **replaced** by a client-side filter over an explicitly `--limit`ed listing, occurrence bump under a throttle, quiet annotation, and nothing that closes | **stub-runner only** — D-9 |
| `T10` | `specfuse/monitor/cli.py` + the `specfuse-monitor` entry point — config load, 0069-axis enumeration, registry-driven dispatch, the `resolve_telemetry` seam, watermark fallback, run summary, `--dry-run` | dry-run path in-loop, **write path stub only** — D-10 |
| `T11` | `specfuse/loop/data/workflows/specfuse-monitor.yml`, the `--runner` dial, and `docs/concepts/monitoring-runners.md` | local half in-loop, **workflow asserted structurally and never executed** — D-11 |

### Failure-class breakdown

Gate 3 is the first gate in this feature with failed attempts, so this section is
present rather than absent-with-a-reason. Read from `events.jsonl`'s
`attempt_outcome` payloads, not from prose.

| class | count | WU | what the driver recorded |
|---|---|---|---|
| `tests` | 2 | `FEAT-2026-0040/T10` | attempts 1 and 2, identical `failure_signature` (`$ python3 -m unittest discover -s tests -v`), $5.99 and $5.66 |

`T08`, `T09` and `T11` passed on their first attempt. No other class appears — no
`lint`, no `security`, no `coverage`-only, no `blocked` report from any agent
(`agent_status: complete` on both failed attempts, `agent_blocked_reason: null`).

**What happened, and what is recoverable from the artifacts.** Two identical
signatures tripped the driver's `spinning_signature_repeat` guard and it escalated to
the human rather than spending a third attempt. The recorded `failure_excerpt` on both
attempts is the same four lines:

```
### tests: FAIL
### coverage: FAIL
$ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
### leak-scan: FAIL
```

Of those three red gates, **only `leak-scan`'s cause survives in the artifacts**, and
it is unambiguous: `work/FEAT-2026-0040_T10/attempt-2.md` records the scanner
reporting one finding in `tests/test_monitor_issue_lifecycle.py` — a vendor-shaped
token planted as `T09`'s redaction fixture, of exactly the class the pre-commit
structural form rejects while CI's form tolerates it. `T09` had already passed with
that fixture in place; `T10` inherited the red gate and could not clear it by editing
its own files, because the offending file belonged to a `done` WU it was forbidden to
touch. The fixture was replaced out-of-band (`fix(monitor): drop the vendor-shaped
token from T09's redaction fixture`), `T10` was re-armed, and it passed on the next
attempt at $8.12.

**The `tests`-gate cause is *not* recoverable and this close does not invent one.**
Both attempt notes truncate the `tests` gate's captured output to the tail of an
integration test's own stdout — a nested driver run for an unrelated fixture feature —
so the failing test name never reached the note. What is checkable now is stated
instead: every test module `T10` produces or depends on passes fresh in this session
(rows 18–22 of the oracle table), so whatever the `tests` gate was reporting on
2026-07-29 at 01:10 and 01:36 is not reproducible against those modules today. The
gate is red at HEAD for a **different** reason, diagnosed below, which is not the same
finding and must not be read as one.

**The cost of this class is the single largest variance in the feature.** `T10` was
drafted at $5.00 and cost **$19.77** across three attempts — two failed at $11.65
between them, plus $8.12 on the re-armed pass. See `## Cost analysis`.

### The composite failure the fresh re-run caught

`close-discipline.md` §1 exists for exactly this: *all WUs individually green while the
feature-level oracle fails*. Row 9 of the oracle table:

```
$ python3 -m unittest tests.test_monitoring_cron_dialect
FAIL: test_no_cron_without_a_conforming_dialect_anywhere
AssertionError: Lists differ: [...] != []
  specfuse/loop/data/workflows/specfuse-monitor.yml: cron '0 * * * *' has no
  conforming dialect (got None)
Ran 9 tests in 0.287s
FAILED (failures=1)
```

**`T04`'s tree-wide sweep is now failing on a file `T11` shipped**, and both units were
right by their own lights:

- `T04`'s sweep collects **every mapping in the git-tracked tree that carries a `cron`
  key** — deliberately schema-agnostic, because that is the shape a heartbeat target
  takes whether it lives in a shipped `monitoring.yml`, a discovery fixture, or a test
  assertion. Its own docstring says so.
- `T11`'s workflow template carries `on.schedule: - cron: "0 * * * *"`. That is a
  **GitHub Actions** cron on a surface where `dialect` has no meaning and could not be
  added without shipping an invalid workflow.

So the sweep's predicate now has a false positive, and the `tests` gate — and with it
the `coverage` gate, whose command is `coverage run … && coverage report` — is **red at
HEAD**. Two things follow, and the second is the generalizable one:

1. **This is a defect in the sweep's discovery predicate, not in `T11`'s template.**
   The template is correct GitHub Actions YAML and criterion 5–9's structural
   assertions all pass. The fix is to scope the sweep by *where* a mapping lives rather
   than by the bare presence of a `cron` key. It is **not applied here**: this unit
   closes the feature and does not patch a `done` WU's work, and the file belongs to
   `T04`'s test module. Carried as **FU-E**.
2. **`T11` could not have caught it, and that is a property of the sweep, not of `T11`.**
   The sweep walks `git ls-files`. When `T11`'s own verification ran, the template it
   had just written was **untracked** — invisible to the walk. The driver commits after
   the gate set passes, so the file became visible to the sweep only *after* the unit
   that introduced it was green. **The introducing WU always passes; the failure lands
   on whoever runs the suite next.** Here that was this close, one WU later. Promoted to
   `LEARNINGS.md`.

Gate 2's close already wrote the corollary that caught this — *"re-run the sweep rather
than inheriting the producing WU's pass — the tree it swept is not the tree at close
time"* — as a prediction. This is that prediction being paid out, one gate later, on
the first close obliged to act on it.

### The fingerprint contract, end to end — criterion 6

**The binding constraint inherited from FEAT-2026-0069 holds through the whole
composition.** Exercised in this session against `T10`'s fixture transports plus a
stateful stub of `T09`'s injected runner — a fake repository whose `gh issue list`
returns what its `gh issue create` has filed so far, so the second harvest reads the
first harvest's state rather than a canned answer:

```
run 1 exit code          : 0
gh issue create calls    : 2
distinct fingerprints    : 2
issue titles             : ['[monitor:034ab4830a18] order-worker: MaxDeliveryCountExceeded',
                            '[monitor:bae090a62cd9] order-worker: MaxDeliveryCountExceeded']
run 2 exit code          : 0
create calls after run 2 : 2
issues in fake repo      : 2
```

One component (`order-worker`), one `dlq` check, **two targets** (`orders-sub` /
`ProcessOrder` and `inventory-sub` / `SyncInventory`), whose stub messages carry the
**same** dead-letter reason — so the only thing distinguishing them is the target
coordinate pair, which is precisely the collapse 0069 paid two gates to prevent. Two
create calls, two distinct fingerprint markers in the two bodies, two issues. And the
second cycle over the same two findings creates **nothing**: idempotence and
distinctness proven in the same run, at the surface where losing either is
irreversible.

**What this is worth, stated exactly.** It is proof of the *composition* — that
enumeration, fingerprinting, and the issue lifecycle agree with each other across three
gates' worth of modules that had never run together. It is **not** proof of GitHub:
the runner is a stub, and every `gh` argument list it recorded went nowhere. D-9 and
D-10 remain open exactly as written.

### The duplicate-filing risk inherited from FEAT-2026-0046 — criterion 7

Addressed in `T09`, and the in-loop evidence is recorded here rather than deferred
silently.

| `T09` c | property | fresh evidence in this session |
|---|---|---|
| 4 | the finder never passes the marker to `--search` | `grep -n '"--search"' specfuse/monitor/issues.py` → **exit 1, no match**. `_list_findings` passes `--label`, `--state open`, `--limit`, `--json number,body,title` and nothing else |
| 5 | the `marker in body` re-check is load-bearing | `tests.test_monitor_issue_lifecycle` → exit 0, `Ran 19 tests … OK`, covering both directions (one row matches, no row matches) |
| 6 | a truncated page is never reported as not-found | `find_finding_issue` raises `TruncatedListingError` when the returned row count reaches `--limit` with no match — the chosen behaviour of the two the criterion allowed, asserted rather than assumed |
| 7 | idempotence | the stub suite, **and** the end-to-end run above: a second harvest of two live fingerprints produced zero further create calls |

So 0046's named defect — *a search that returns nothing silently files a duplicate on
every retry* — is structurally out of the code path: there is no search to return
nothing, and the one remaining way to mistake absence for emptiness (a full page) now
raises instead of lying.

**And that is where the in-loop evidence stops.** D-9 — *the same property against a
real repository* — is discharged only by the operator-journal record. **That record
does not exist:** there is no `OPERATOR-JOURNAL.md` in this feature folder at close
time, and `gh` is unusable from this session (invalid `GH_TOKEN`, invalid keyring
token, and a TLS verification failure from inside the sandbox), so nothing here could
have produced one. Stated plainly, per criterion 7, rather than implied by the green
stub suite.

### `stall_after` — the disposition, not an implicit gap — criterion 8

**Disposition: the grammar is settled in the adapter and the validator was deliberately
left permissive.** `T08` accepts `<integer><unit>` with unit in `s`/`m`/`h`/`d` and
raises on everything else — `"15"`, `"15 minutes"`, `"m15"`, `""`, `"-5m"` each observed
rejecting in `tests.test_queue_stalled_adapter` (exit 0, `Ran 14 tests … OK`). It did
**not** tighten `specfuse/loop/lint_monitoring.py`, because making `stall_after`
required and bounded is a severity flip: it needs `planning-discipline.md` §4's runtime
probe, which gate 3 was armed without because it has no other flip, and it would be a
second breaking schema change one release after `dialect`.

**Consequence, stated so it is not rediscovered:** a typo'd `stall_after` lints clean
and fails at **run time**, not at lint time. That is a real gap and it is carried as
**FU-D**, not dropped.

**Its home, and the one thing this close could not confirm.** `GATE-03-REVIEW.md` §6.1
answer 3 records the operator accepting the deferral *on the condition that the
follow-up is filed as a tracked issue, not left in a retrospective*, and requires this
close to confirm the issue exists and cite it. **It could not be confirmed.** `gh` is
unusable here — `gh auth status` reports both the `GH_TOKEN` and keyring tokens
invalid, and `gh issue list` fails before reaching the API with
`tls: failed to verify certificate`. So FU-D is recorded below with its home named as
*a tracked issue the operator files or confirms at the terminal review checkpoint*, and
this close reports the unmet half rather than asserting a citation it never read.

### Which sandbox each gate ran under

Per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`: a bare pass/fail count out of this
environment manufactures a regression. Three effects are separable, and **only the
first is a real defect in the tree**.

| gate | sandbox | result | note |
|---|---|---|---|
| `tests` | default, `commit.gpgsign=false` | **exit 1** — `Ran 1840 tests`, `FAILED (failures=1, skipped=3)` | **The one real failure**: `test_no_cron_without_a_conforming_dialect_anywhere`. Diagnosed above; FU-E |
| `tests` (module) | default, no override | exit 1 — `Ran 3 tests`, `FAILED (errors=3)` on `tests.test_autosync_no_cwd_leak` | Host-config contamination, **reproduced again this session**. FU-A, still open |
| `tests` (module) | default, `commit.gpgsign=false` | exit 0 — `Ran 3 tests … OK` | The controlled re-run that isolates it |
| `lint` (`ruff`) | default | **exit 0** — `All checks passed!` | |
| `security` (`bandit -ll`) | default | **exit 0** — Medium: 0, High: 0 | |
| `coverage` | default, `commit.gpgsign=false` | **exit 1** — the compound command short-circuits on the same single test failure | `coverage report --fail-under=90` on its own: **exit 0, TOTAL 94%**. The threshold is met; the gate is red only because of FU-E |
| `leak-scan` | default | **exit 0** — `leak-scan: clean` (gitleaks 8.30.1) | The `T09` fixture token that blocked `T10` twice is gone |
| `monitoring-example-lint` | default | **exit 0** — `OK — monitoring config is structurally valid (or absent).` | |
| 6 × `bats` | default | **exit 1** on five suites — **21 of 22 cases `not ok`**, every one `mktemp: mkdtemp failed … Operation not permitted` in `setup`, before any assertion. `init_skills_idempotent` (1 case) passes | The recorded environment effect (`[FEAT-2026-0072/G1-CLOSE]`), identical to gate 2's count |
| 6 × `bats` | sandbox off | **exit 0 for all six**, 22 `ok` / 0 `not ok` | The real signal |

### Oracle re-runs — fresh, in this session, gates 1 through 3

Per `close-discipline.md` §1: every oracle the feature's criteria name, re-run here with
exit codes read directly, never inherited from a producing WU's `done`. All rows ran
under the **default sandbox** except the `bats` row noted above. A grep whose passing
outcome is "no match" exits **1**; that is recorded as the passing result, not as a
failure.

| # | gate | oracle (criterion) | command | exit |
|---|---|---|---|---|
| 1 | 1 | `T01` c10 | `python3 -m unittest tests.test_failure_artifact_model` | **0** — `Ran 8 … OK` |
| 2 | 1 | `T02` c10 | `python3 -m unittest tests.test_fingerprint` | **0** — `Ran 8 … OK` |
| 3 | 1 | `T03` c9 | `python3 -m unittest tests.test_artifact_redaction` | **0** — `Ran 5 … OK` |
| 4 | 1 | `T01` c3 | `grep -rniE "azure\|appinsights\|servicebus\|kusto" specfuse/monitor/artifact.py specfuse/monitor/adapters.py` | **1** (no match) |
| 5 | 1 | `T01` c9 | `grep -niE "cron\|schedule\|dialect" specfuse/monitor/artifact.py` | **1** (no match) |
| 6 | 1 | `T02` c8 | `grep -n "hash(" specfuse/monitor/fingerprint.py` | **1** (no match — no salted builtin hash) |
| 7 | 1 | `T03` c6 | `grep -n "leak_scan" specfuse/monitor/redaction.py` | **1** (no match — issue #55 holds) |
| 8 | 1 | `T01`/`T02`/`T03` c11 | three `python3 -c "from specfuse.monitor… import …"` imports | **0**, **0**, **0** |
| 9 | 2 | `T04` c1/c4/c5 | `python3 -m unittest tests.test_monitoring_cron_dialect` | **1** — `Ran 9`, `FAILED (failures=1)` **← the finding** |
| 10 | 2 | `T04` c10 | `python3 -m unittest tests.test_monitoring_fenced_blocks` | **0** — `Ran 5 … OK` |
| 11 | 2 | `T04` c6/c7b | `python3 -m unittest tests.test_derive_monitoring_discovery` | **0** — `Ran 24 … OK` |
| 12 | 2 | `T05` c11 | `python3 -m unittest tests.test_service_bus_dlq_adapter` | **0** — `Ran 9 … OK` |
| 13 | 2 | `T06` c11 | `python3 -m unittest tests.test_app_insights_adapters` | **0** — `Ran 12 … OK` |
| 14 | 2 | `T07` c12 | `python3 -m unittest tests.test_schedule_dialect` | **0** — `Ran 19 … OK` |
| 15 | 2 | `T07` c12 | `python3 -m unittest tests.test_heartbeat_adapter` | **0** — `Ran 8 … OK` |
| 16 | 2 | `T04` c9 | `python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example` | **0** |
| 17 | 2 | `T07` c11/c12 | `grep -rniE "azure\|…" specfuse/monitor/schedule.py`; `grep -rn "datetime.now\|time.time" specfuse/monitor/schedule.py` | **1**, **1** (no match) |
| 18 | 3 | `T08` c13 | `python3 -m unittest tests.test_queue_stalled_adapter` | **0** — `Ran 14 … OK` |
| 19 | 3 | `T09` c13 | `python3 -m unittest tests.test_monitor_issue_lifecycle` | **0** — `Ran 19 … OK` |
| 20 | 3 | `T10` c13 | `python3 -m unittest tests.test_monitor_cli` | **0** — `Ran 40 … OK` |
| 21 | 3 | `T11` c12 | `python3 -m unittest tests.test_monitor_runner_surfaces` | **0** — `Ran 13 … OK` |
| 22 | 3 | `T09` c12 | `python3 -m unittest tests.test_escalation_emit`; `… tests.test_escalation_contract` | **0** — `Ran 6 … OK`; **0** — `Ran 10 … OK` |
| 23 | 3 | `T10` c12 | `grep -rniE "azure\|appinsights\|servicebus\|kusto"` over `cli.py artifact.py adapters.py fingerprint.py redaction.py schedule.py issues.py` | **1** (no match — the core stays provider-agnostic **through the CLI**) |
| 24 | 3 | `T08` c12 | `grep -rn "from specfuse.monitor.providers\|import specfuse.monitor.providers" specfuse/monitor/*.py` | **1** (no match) |
| 25 | 3 | `T08` c10 | `grep -rn "datetime.now\|time.time" specfuse/monitor/providers/azure_service_bus.py` | **1** (no match — the clock is an argument) |
| 26 | 3 | `T09` c4 | `grep -n '"--search"' specfuse/monitor/issues.py` | **1** (no match) |
| 27 | 3 | `T09` c3 | `grep -n "def " specfuse/monitor/issues.py` | **0** — 8 definitions, **none** a re-implementation of the issue-number parse |
| 28 | 3 | `T10` c6 | `grep -n 'environment\["telemetry"\]\|environment.get("telemetry")' specfuse/monitor/cli.py` | **1** (no match — the #262 seam is not bypassed) |
| 29 | 3 | `T11` c10 | `ls .github/workflows` | **0** — `ci.yml`, `leak-scan-content.yml`, `release.yml`: the template is **not** installed here |
| 30 | 3 | `T10` c2 | `python3 -c "from specfuse.monitor.cli import main"`; `python3 -c "from specfuse.monitor.issues import record_finding"` | **0**, **0** — zero-runtime-dependency property holds through the CLI |
| 31 | 1–3 | the whole `code` gate set | see the sandbox table above | **red at HEAD** on `tests` and `coverage`, from one root cause (FU-E); the other seven gates green |

**FU-C, re-measured rather than repeated.** `azure_service_bus.py` is now at **79%**
line coverage, down from gate 2's 81% — `T08` extended the same module and the
uncovered region is still concentrated in the lazy `build_*` transport factories, which
cannot execute without the SDK on the path. `TOTAL` is 94%, so the 90% floor is met with
room. Named again so a future tightening reads it as a known shape, not neglect.

## Cost analysis

Read from `events.jsonl`'s `attempt_outcome` payloads. The **as-drafted** figures are
reported as the honest plan, per `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` — the plan is
not re-based onto its own outcome and the result then reported as accuracy. **The
per-gate split is shown because the feature-wide figure hides where the variance came
from, and here it hides it almost perfectly.**

### Per gate

| gate | planned (as drafted) | actual | delta | note |
|---|---|---|---|---|
| gate 1 | $20.00 | **$9.34** | **−$10.66 (−53%)** | `T01` $1.15, `T02` $0.85, `T03` $0.65, `G1-CLOSE-INTERMEDIATE` **$0.00** (auto-closed at `attempts: 0`), `G1-PLAN` $6.69. $4.50 of the underrun is a ceremony that never ran |
| gate 2 | $27.00 | **$25.68** | −$1.32 (−4.9%) | `T04` $6.25, `T05` $1.53, `T06` $1.18, `T07` $4.37, `G2-CLOSE-INTERMEDIATE` $7.01, `G2-PLAN` $5.34 |
| gate 3 | $23.00 | **$27.15** *(before this close)* | **+$4.15 (+18%)** | `T08` $1.94, `T09` $2.67, `T10` **$19.77**, `T11` $2.77 |
| **feature** | **$70.00** | **$62.19** *(before this close)* | −$7.81 (−11%) | Against `PLAN.md`'s `planned_cost_usd: 70.00`, drafted work only |

### Gate 3 per WU — where the whole variance is

| WU | planned | actual | delta |
|---|---|---|---|
| `T08` | $4.00 | **$1.94** | −$2.06 (−52%) |
| `T09` | $5.00 | **$2.67** | −$2.33 (−47%) |
| `T10` | $5.00 | **$19.77** | **+$14.77 (+295%)** |
| `T11` | $4.00 | **$2.77** | −$1.23 (−31%) |
| implementation subtotal | $18.00 | **$27.15** | +$9.15 (+51%) |
| `G3-CLOSE` | $5.00 | this session — not in `events.jsonl` at write time | — |

**Three of four units under-ran and the gate still blew its plan.** `T08`, `T09` and
`T11` came in at $7.38 against $13.00 (−43%), landing near the shape gate 2's adapter
units took. `T10` alone accounts for **$14.77 of overrun on a $23.00 gate**, and its
$19.77 is three attempts: $5.99 + $5.66 on the two that failed, plus $8.12 on the
re-armed pass. **The two failed attempts cost $11.65 and produced no committed work.**

**The budget consequence, stated because it nearly bit.** `GATE-03.md` carries
`cost_budget_usd: 28.00` — $23.00 drafted plus $5.00 of defensive padding for exactly
one re-attempt of the largest unit. That padding was designed for a single retry and
`T10` needed two plus a re-arm. Gate 3 stood at **$27.15 against the $28.00 halt
threshold — 97% consumed — before the terminal close dispatched at all**, so this close
runs past the threshold. The padding was correctly reasoned and still insufficient,
which is the honest read: it priced the *number* of retries right at one and the *cost*
of a retry at the drafted figure, when a retry on the largest unit cost more than the
unit's whole budget.

**What `GATE-03-REVIEW.md` §5.3 got right, and what it could not see.** §5.3 refused to
re-price gate 3 off gate 2's cheap adapter actuals and priced `T08` at $4.00 rather than
~$2.00. Measured: `T08` cost $1.94, so the trim would have been accurate — and refusing
it cost nothing, exactly as its own "a budget is a halt threshold, not a spend target"
argument predicted. It also priced `T09` and `T10` above the adapters on the grounds
that they cross a package boundary and compose six modules. `T09` did not need it
($2.67). `T10` needed four times it. The signal §5.3 could not price is that **`T10`'s
overrun was not caused by `T10`'s difficulty** — its first two attempts died on a red
`leak-scan` gate seeded by a *different* WU's fixture, which no per-unit estimate can
anticipate. That is a scheduling property, not an estimation error.

## What the loop did NOT verify

**Eleven deferred items, none of them discharged, plus one red gate that is a defect
rather than a deferral.** This section is the terminal one; it supersedes nothing above
it and repeats nothing it can point at.

### Gate 3's deferred list — D-9, D-10, D-11

| # | deferred criterion | why the loop could not verify it | where it is actually verified |
|---|---|---|---|
| D-9 | `T09` — a second harvest of one fingerprint against a **real repository** creates no second issue | The runner is a stub that returns whatever the test hands it. `gh` is unusable from a work-unit session here: `gh auth status` reports the `GH_TOKEN` and keyring tokens invalid, and `gh issue list` fails with `tls: failed to verify certificate` before reaching the API. The end-to-end run above proves the *composition*, against a fake repository | Operator runs the harvester twice against a scratch repository with a planted finding; both invocations and the resulting issue list recorded in `OPERATOR-JOURNAL.md` |
| D-10 | `T10` — `specfuse-monitor run` against a real repository and environment files the issues the dry run predicted | The dry-run path is in-loop and green; the write path terminates in `T09`'s `gh` surface and is stub-evidence only | Same operator run, dry-run output and resulting issue list recorded side by side |
| D-11 | `T11` — the shipped workflow, installed in a consumer repository, completes a scheduled run and files findings | A scheduled GitHub Actions workflow cannot be executed from a work-unit session at all. The template is asserted **structurally only**: it parses, declares `schedule` + `workflow_dispatch`, invokes `specfuse-monitor run`, grants exactly `issues: write` + `contents: read`, and carries no literal secret | Operator installs the template in a scratch repository, triggers it manually, records the run URL, outcome, and issue list |

**The operator journal does not exist.** `GATE-03-REVIEW.md` §6.1 answer 6 named
`OPERATOR-JOURNAL.md` in this feature folder as the proxy for all three. There is no
such file at close time. This close read for it and reports its absence rather than
citing a record it never saw — which is the whole reason D-9, D-10 and D-11 are still
open and the verdict is hedged.

### D-1 … D-8 carry forward unchanged

Gate 2's eight items are unchanged and are **not** restated here: every adapter is still
stub-verified, no live Service Bus namespace or App Insights workspace has been reached,
and no DST transition has been observed in production. The full table is in the gate-2
section above, under *Gate 2 — the deferred list, which is not empty*. Their oracle is
the operator run against the downstream .NET backend, which `GATE-02-REVIEW.md` §6.1
answer 4 records as planned and which has not happened.

### gate 1's auto-close debt — settled, and named literally here

`RETROSPECTIVE.md` carries
`<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=32 predicate=v1 -->`.
**`gate 1` auto-closed on-plan at `attempts: 0`, so its close-intermediate ceremony
never ran and its 32 acceptance criteria were dumped as `deferred` without anyone
looking at them.** That debt was **already reconciled in full** by
`FEAT-2026-0040/G2-CLOSE-INTERMEDIATE` — all 32 criteria dispositioned, 29 re-run fresh,
the remaining 3 identified as red-before-green claims that are not re-runnable at close
time by construction. See *Gate 1's auto-close debt, reconciled* above; this terminal
close does not repeat that work.

What it does do is **re-run gate 1's oracles a second time**, in this session: rows 1–8
of the oracle table, all green. So the claim "`gate 1`'s deferred list is legitimately
empty" now rests on two independent fresh runs a gate apart, not on one. The marker
comment stays in place.

### The red gate at HEAD is a defect, not a deferral

Filed here so it is not mistaken for a deferred item. **`tests` and `coverage` are red
at HEAD** because `T04`'s tree-wide cron sweep flags `T11`'s GitHub Actions template.
It is in-loop verifiable, reproducible in one command, diagnosed above, and **not
fixed** — this unit closes the feature and does not patch a `done` WU's work. It is
**FU-E**, and it is the main reason the verdict is `partially_met` rather than
`met_locally`: `T04` criteria 4 and 5 and `T11` criterion 12 do not hold on the tree as
it stands, which is a stronger statement than "could not be checked here."

### Follow-ups — dispositioned, not dropped

- **FU-A — the fixture-signing contamination. RE-CARRIED, and reproduced again.**
  `tests/test_autosync_no_cwd_leak.py`'s `_make_repo` still pins only `user.name` and
  `user.email`, so each `git commit` inherits the host's global `commit.gpgsign = true`.
  Observed a third time in this session: **exit 1, `Ran 3 tests`, `FAILED (errors=3)`**
  without the override; **exit 0, `OK`** with
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`.
  **Home:** a one-line fixture change on a hygiene WU or a bug branch — no WU in this
  feature owns the file, and this close does not patch work. Flagged at gate 2's arming,
  at gate 2's close, and now here; three sightings is the argument for giving it an owner.
- **FU-B — `queue-stalled` had no adapter. CLOSED.** Discharged by `T08`:
  `tests.test_queue_stalled_adapter` exits 0 with `Ran 14 tests … OK`, the adapter reads
  both broker coordinates, decides on age with depth as evidence, refuses an unparseable
  threshold, and skips a threshold-less target with a recorded reason. The trail
  `GATE-02-REVIEW.md` §2 → §6.1 answer 3 → FU-B → `T08` is unbroken.
- **FU-C — `azure_service_bus.py` line coverage. RE-CARRIED, re-measured at 79%**
  (was 81%; `T08` extended the module). Uncovered lines remain concentrated in the lazy
  SDK transport factories, unexercisable without the SDK on the path. `TOTAL` 94%.
  **Home:** whoever tightens the coverage floor, or the operator run that first
  constructs a real transport — whichever comes first.
- **FU-D — `stall_after` is unbounded at lint time. RE-CARRIED, home named, citation
  NOT confirmed.** A typo'd threshold is a runtime refusal, not a lint error. Deliberately
  out of gate 3 (a severity flip needing `planning-discipline.md` §4's probe, and a second
  breaking schema change one release after `dialect`). **Home:** a tracked issue, per
  `GATE-03-REVIEW.md` §6.1 answer 3, which required this close to confirm the issue exists
  and cite it. **This close could not: `gh` is unusable from this session.** The
  confirmation is an operator action at the terminal review checkpoint, and criterion 8's
  citation half is reported unmet rather than fabricated.
- **FU-E — the cron sweep flags the shipped workflow template. NEW, and it is the red
  gate.** `tests/test_monitoring_cron_dialect.py`'s `_collect_cron_carrying_targets`
  treats *any* mapping carrying a `cron` key as a heartbeat target, and
  `specfuse/loop/data/workflows/specfuse-monitor.yml` carries a GitHub Actions
  `on.schedule` cron where `dialect` has no meaning. **Home:** a bug branch — 1 bug,
  1 branch, 1 PR, test-first. The fix is to scope the sweep's discovery (by config-file
  set, or by requiring the mapping to sit under a `checks[].targets[]` path) while keeping
  its non-vacuity assertion, **not** to add a `dialect` to a workflow file or to
  hand-write an exclusion list — a hand-written exclusion is the failure mode
  `[FEAT-2026-0039/T04]` recorded and the walk exists to avoid.

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3 across **all three gates**. Writing
`n/a — no consumer-visible contract change` here would be false: there are fourteen
entries and one of them is breaking. **This section requires explicit human
acknowledgment; see *Acknowledgment* below, which is still unsigned.**

### 1. `heartbeat` target `dialect` — **BREAKING** (gate 2, unchanged, still in force)

The full entry is in the gate-2 section above and is not restated. In one line: a
`heartbeat` target that carries `cron` must now also carry `dialect`
(`standard-5` / `seconds-first-6`), enforced by four ERROR-severity validator rules, so
a downstream `monitoring.yml` that lints clean today will not after upgrade. Migration
is mechanical (count the fields) or automatic (re-run `/derive-monitoring`). **It stays
in this enumeration because a terminal close's list is the one a consumer reads.**

### 2–6. Gate 2's additive entries

Unchanged, enumerated in the gate-2 section: `CRON_DIALECTS` in `__all__`; both
`monitoring.yml.example` copies gaining `dialect`; the `derive-monitoring` skill
emitting it; the `specfuse.monitor.providers` subpackage; and `specfuse.monitor.schedule`.

### 7–14. Gate 3's entries — all additive

| # | surface | change | consumer impact |
|---|---|---|---|
| 7 | `pyproject.toml` `[project.scripts]` | new entry point **`specfuse-monitor = "specfuse.monitor.cli:main"`**, alongside the four existing ones | Additive. Does **not** collide with the existing `specfuse-monitor-lint`. A new command appears on `PATH` after upgrade |
| 8 | **`specfuse.monitor.issues`** (new module) | `record_finding`, `find_finding_issue`, `annotate_if_quiet`, `TruncatedListingError`, `FINDING_LABEL` | Additive, no prior version. Every entry point takes an injected `runner`, defaulting to `escalation.py`'s |
| 9 | **`specfuse.monitor.cli`** (new module) | `main`, `run_cycle`, `load_monitoring_config`, `MonitorCliError` | Additive. `python3 -c "from specfuse.monitor.cli import main"` exits 0 on a clean checkout with **no cloud SDK installed** — the zero-runtime-dependency property holds through the CLI |
| 10 | **the GitHub label `monitoring-finding`** | Every filed finding carries it, and the finder lists on it | Additive but **visible in a consumer's repository**: the label is created on first use and becomes the fingerprint registry's index. Named here because a label is a contract a consumer's own automation may key on |
| 11 | `queue-stalled` adapter + **the `stall_after` grammar** | `<integer><unit>`, unit in `s`/`m`/`h`/`d`. Anything else **raises**, naming the offending value. A target with no `stall_after` is **skipped and reported**, never defaulted | Additive at lint time — the validator is unchanged, so no existing config becomes invalid. But it is a **new runtime contract**: a config that lints clean can now fail at run time on a typo'd threshold. This is FU-D, disclosed rather than buried |
| 12 | **`specfuse/loop/data/workflows/specfuse-monitor.yml`** (new shipped template) | A scheduled GitHub Actions workflow with `workflow_dispatch`, `permissions: {issues: write, contents: read}` and no literal secret | Additive. Ships in the wheel (`package-data` already globs `data/**/*`, so no packaging change was needed) and is **not** installed into any repository automatically — the consumer copies it |
| 13 | **the `runner` dial is now honoured** | `specfuse-monitor run --runner {local,gh-actions}` enumerates only components whose `runner` matches; the rest are **named in the summary** with the surface they belong to. `in-cluster` is reported as unhandled-by-design with FEAT-2026-0043 named; an unknown value is an error naming the supported set | Additive — the field already existed in the schema and was inert. After upgrade it **routes**, so a component dialed to a surface nobody runs is now visibly unmonitored instead of invisibly so |
| 14 | on-disk state and defaults | `.specfuse/monitor-watermarks/<env>.json` (best-effort cache, falls back to a 24h lookback on missing/unreadable/corrupt), a 6h occurrence-update throttle, a 100-row `gh issue list --limit`, quiet annotation after 5 runs | Additive. A new directory appears under `.specfuse/`; consumers may want it gitignored. Every value is a named parameter, not a magic number |

**`docs/concepts/monitoring-runners.md`** documents entries 12 and 13, including — per
`GATE-03-REVIEW.md` §6.1 answer 2 — the one sentence stating that `--dry-run` **performs
the read-only `fetch_failures()` calls** and gates only the writes. It is not `--offline`.

### Acknowledgment

> **Status: NOT YET ACKNOWLEDGED — and this is the single human action gating the
> feature's terminal flip.**
>
> `close-discipline.md` §3 requires explicit human acknowledgment of this list, and
> entry 1 is a breaking schema change for downstream consumers. Gate 2's close left the
> same block unsigned; this terminal enumeration supersedes it and is the one to sign.
> Per `operator-escalation.md` the acknowledgment text is the human's to write and is
> not drafted here. FEAT-2026-0069's precedent is the path: its list was acknowledged by
> the operator at the terminal review checkpoint, after which the verdict was upgraded.
>
> _Operator acknowledgment:_

## Lessons

Three entries appended to `.specfuse/LEARNINGS.md`, tagged `[FEAT-2026-0040/G3-CLOSE]`:
the `git ls-files` sweep that cannot see the introducing WU's own new file; the
schema-agnostic structural predicate that collides with a foreign surface sharing its
key; and the gate budget whose one-retry padding was priced at the drafted figure rather
than at what a retry on the largest unit actually costs.

Feature-specific observations stay here and are deliberately not promoted: the exact
stub cardinalities, `azure_service_bus.py`'s coverage shape, the `monitoring-finding`
label name, and the specific fingerprints the end-to-end run produced.

## Docs and roadmap

- `docs/concepts/monitoring-runners.md` — shipped by `T11`; documents both runner
  surfaces, the dial, the template's secrets, `in-cluster` as FEAT-2026-0043's, and the
  `--dry-run` scope sentence. Not edited here.
- `.specfuse/roadmap.md` — FEAT-2026-0040's detail section gains a gate-3 shipped note
  that says which surfaces were **never executed**, the terminal verdict and what would
  upgrade it, and names the four features this feature unblocks: FEAT-2026-0038,
  FEAT-2026-0041, FEAT-2026-0042, FEAT-2026-0043. The status row and `PLAN.md`'s
  `status` field are **not** touched — the driver owns the terminal flip and it is gated
  on the verdict.

## Hedged verdict accepted

**Accepted verdict:** `partially_met`

**Operator reason (verbatim):** Accepting that this ships incomplete: D-1 through D-11 are open, both operator runs are planned, and the verdict gets revisited once they're recorded.

**Recorded:** 2026-07-29T16:44:07Z

**Acknowledgment.** The operator confirmed explicitly: *"yes I accept shipping with
D-1 through D-11 open."* All eleven are carried forward below by reference to the
tables that define them — `## What the loop did NOT verify` for D-1 … D-8 and gate
3's list for D-9 … D-11 — verbatim and undischarged. Accepting a hedge means shipping
with known-open items, not pretending they are done.

`partially_met` is a stronger admission than `met_locally` and the reason line says
so. It is the honest grade: the close's fresh-oracle obligation found a real red gate
at HEAD, not merely something it could not check.

### What changed between the close and this acceptance

Recorded because carrying it forward verbatim would now be false, and an acceptance
record that misstates the tree is worse than none.

**FU-E is fixed.** It was the close's *main stated reason* for grading
`partially_met` rather than `met_locally`: `T04`'s tree-wide cron sweep flagged
`T11`'s GitHub Actions workflow, whose `on.schedule.cron` is POSIX 5-field by
GitHub's definition and has no dialect to declare. `tests` and `coverage` were red at
HEAD. Fixed in `1341fe9` by scoping the sweep to dicts carrying `name` — mandatory
for heartbeat targets, never present on a bare Actions schedule entry — with the
exclusion asserted by a test so a future widening cannot silently reintroduce it.
**HEAD is green: 1841 tests, ruff, bandit, coverage 94%, leak-scan clean.**

The verdict is **not** upgraded on that basis. FU-E was one reason among several; D-1
… D-11 are untouched by it, and they are what `partially_met` now rests on.

**The follow-ups gained owners.** FU-A is [#296](https://github.com/specfuse/loop/issues/296),
FU-D is [#295](https://github.com/specfuse/loop/issues/295) — the latter discharging
`GATE-03-REVIEW.md` §6.1 answer 3's condition, which the close itself could not
satisfy because `gh` is unusable from a work-unit session. FU-B was closed by `T08`.
FU-C is recorded with a home.

**The operator journal now exists.** `OPERATOR-JOURNAL.md`, cited by D-9, D-10 and
D-11 as their verification proxy, did not exist when the close ran — the close
recorded exactly that. It is now committed as a structured stub with a runbook.

### A constraint found after the close, which changes how D-9/D-10 get discharged

Writing that runbook against the shipped code surfaced something drafting missed and
the close could not have known. `_load_provider_module` resolves a provider only by
importing `specfuse.monitor.providers.<name>` — no plugin path, no override — so
**a scratch repository cannot manufacture a finding on its own.**
`GATE-03-REVIEW.md` §6.1 answer 5 recorded run 2 as an independent oracle, "a scratch
repository, not the .NET backend." That holds for D-11 and does not hold for D-9 or
D-10.

The seam that makes it workable: `run_cycle()` takes `transport_resolver` and
`gh_runner` separately, so a fake transport plants the finding while the real `gh`
files it. `plant-finding.py` in this folder does that. It discharges **D-9 in full**
— the fingerprint-keyed find-or-create against the real GitHub index, the
highest-risk item and the one `T09` replaced `escalation.py`'s `--search` finder to
get right — and **D-10 only partially**, because the CLI is not the entry point. A
journal entry must not tick D-10 on that evidence.

The missing extension point is filed as
[#298](https://github.com/specfuse/loop/issues/298).

### Carried forward — D-1 … D-11, all OPEN

None is discharged by this acceptance. D-1 … D-8 need the Azure run against the
downstream .NET backend; D-9 … D-11 need the scratch GitHub repository. Both are
planned, both are the named upgrade conditions, and their exact re-run conditions are
in the tables above and as checkboxes in `OPERATOR-JOURNAL.md`. When they are
recorded there, re-evaluate with `--recheck-verdict`.
