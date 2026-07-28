---
id: FEAT-2026-0040/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/monitor/providers/azure_app_insights.py
  - tests/test_app_insights_adapters.py
model: sonnet
effort: medium
gate_set: code
---

# Query the telemetry backend — the App Insights KQL adapters

**Objective.** Ship the `TelemetryAdapter` implementations for the three
telemetry-keyed check types that do not involve a schedule — `error-logs`,
`http-5xx`, and `invariant` — resolving the telemetry binding through T01's
per-component seam.

**Context.** Correlation ID `FEAT-2026-0040/T06`. Gate 2, no dependencies — T01's
`TelemetryAdapter` protocol, `FailureArtifact`, and `resolve_telemetry` are `done`
and shipped. T07 adds the fourth telemetry-keyed type, `heartbeat`, in a separate
unit because it consumes T04's cron dialect and computes an expected firing time —
different work, different failure mode, and bundling it here would let a red-to-green
proof pass on the three easy types while the schedule half stayed silently
unimplemented. That is exactly what `[FEAT-2026-0069]` split `T07` out of `T06` to
avoid.

**Resolve telemetry through the seam, with the component.** T01 shipped
`resolve_telemetry(component, environment)` whose only implementation today reads the
environment's single binding — the recorded decision against
[#262](https://github.com/specfuse/loop/issues/262). Every adapter here obtains its
binding by calling that function **with the component**, never by reaching into
`environment["telemetry"]` directly. The seam is worthless if its first three
consumers bypass it: when per-component bindings land they add a resolver
implementation, and #262's *"the adapter interface changes rather than extends"* only
stays false if the call sites go through the seam.

**These three check types carry no target coordinates, and that is enforced.**
`_TARGETLESS_CHECK_TYPES` in both the validator and the artifact model rejects
`targets` on `error-logs`, `http-5xx`, and `invariant` — 0069's decision, so that
`fingerprint_by` remains `invariant`'s single enumeration key and the role-name-keyed
types stay genuinely component-scoped. `FailureArtifact.from_target` **raises** for
these types by construction; build artifacts directly and assert
`target_coordinates is None`.

**`invariant` is the one with a real contract.** Its fingerprint derives from
`failure_signature` alone (see `fingerprint.py`'s module docstring), and the check's
`fingerprint_by` names the column whose value identifies the violating row. So the
adapter must put **that column's value** into `failure_signature` — not the query
text, not the row index, not a hash of the whole row. Get this wrong and every
invariant violation on a component collapses into one issue, or every row becomes its
own issue forever; criterion 6 pins it.

**Queries are built from configuration, never from observed text.** The
`invariant.query` is operator-authored and lives in the repository's own
`monitoring.yml`; it is executed as written, which is the schema's recorded position
that its contents are opaque. What must never happen is the reverse direction: no
value returned by a telemetry query, and no field of an artifact, may be interpolated
back into a subsequent query. That closes the loop an attacker would need. See
`security-boundaries.md`.

**Zero runtime dependencies, same as T05.** The transport is injected at construction,
any real SDK client is built by a factory that imports lazily inside the function
body, and every test runs against a stub returning canned result rows.

**Redaction at the boundary.** Every artifact this unit returns passes through T03's
`redact_artifact` before it leaves the adapter. Exception messages and log lines are
the second-most-likely place in this feature for a live credential to enter the
process, after a dead-lettered message body.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_app_insights_adapters.py::TestTelemetryAdapters::test_resolve_telemetry_is_called_with_the_component`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `specfuse/monitor/providers/azure_app_insights.py` defines an adapter for each of
   `error-logs`, `http-5xx`, and `invariant`, each of whose `fetch_failures()` returns
   an iterable of `FailureArtifact` — structurally a `TelemetryAdapter` per T01's
   protocol, asserted for all three.
3. Each adapter obtains its telemetry binding by calling
   `resolve_telemetry(component, environment)` **with the component**. A test asserts
   the recorded call argument is the component name, for all three adapters — the
   assertion T01's criterion 8 established and this unit is the first real consumer of.
4. The transport is supplied at construction and
   `python3 -c "import specfuse.monitor.providers.azure_app_insights"` exits zero on a
   clean checkout with no cloud SDK installed.
5. Every artifact these three adapters return has `target_coordinates is None`, and a
   test asserts that calling `FailureArtifact.from_target` for any of the three check
   types raises — a negative observation against the 0069 position, not a comment.
6. **The `invariant` contract.** Given a check with `fingerprint_by: <column>` and a
   stubbed result set of **at least 3 rows with at least 2 distinct values** in that
   column, the adapter yields one artifact per row whose `failure_signature` is that
   row's value in the named column, and `fingerprint_artifact` over the set yields
   exactly **2 distinct** digests. Cardinality is specified because a 1-row fixture
   cannot express the collapse this criterion guards.
7. **Signatures are stable across occurrences.** For `error-logs` and `http-5xx`, two
   stubbed rows differing only in timestamp, operation ID, and request ID produce the
   same `failure_signature`; two rows with different exception types or different
   failing routes produce different ones.
8. **Redaction at the boundary.** A stubbed row whose message field carries a planted
   secret yields an artifact in which no occurrence of that value survives, and the
   redacted span reads as `<redacted:` + a short digest. Use a synthetic value that is
   not a real credential and not a denylisted token.
9. **No query is built from observed data.** A test drives an adapter with a stub whose
   returned rows contain query-shaped text and asserts the transport recorded exactly
   the queries the configuration implies — the returned text appears in no subsequent
   query.
10. `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/artifact.py
    specfuse/monitor/adapters.py specfuse/monitor/fingerprint.py
    specfuse/monitor/redaction.py` returns no match, and
    `grep -rn "from specfuse.monitor.providers\|import specfuse.monitor.providers"
    specfuse/monitor/*.py` returns no match — the core neither names a provider nor
    imports one.
11. `python3 -m unittest tests.test_app_insights_adapters -v` exits zero after this
    WU's edits, and the `code` gate set passes in full — `tests`, `lint`, `security`,
    `coverage` (≥90%), `leak-scan`, `monitoring-example-lint`, and the five `bats`
    suites.

**Do not touch.** `specfuse/monitor/artifact.py`, `fingerprint.py`, `redaction.py`,
`adapters.py` — T01–T03 own them and they are `done`; this unit consumes them. If
`resolve_telemetry`'s signature does not fit, that is an escalation, not an edit —
reshaping the seam is the one thing #262's decision exists to prevent.
`specfuse/loop/lint_monitoring.py` and the monitoring examples — T04's. The
`heartbeat` adapter, the cron dialect, and anything computing an expected firing time
— T07's, and a `heartbeat` adapter written here would collide with it. `escalation.py`
— gate 3's. Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 11, the two greps in criterion
10, the raise-assertion in criterion 5, the planted-secret negative observation in
criterion 8, and the recorded-query assertion in criterion 9. Report which sandbox each
gate ran under — the `bats` suites fail under the session's default sandbox for
`mktemp -d` reasons that have nothing to do with this unit.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: T01's
`TelemetryAdapter` protocol cannot express a KQL query without a provider type
appearing in `adapters.py`; `resolve_telemetry`'s two-argument signature cannot supply
what an App Insights client needs to be constructed, which is a finding about the seam
and belongs in a report rather than in a signature change; the `invariant` contract in
criterion 6 cannot be satisfied because `fingerprint_by` does not name something a
result row carries, which would be a schema finding for T04's surface; or the coverage
floor requires asserting behaviour only a live workspace exhibits.
