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
