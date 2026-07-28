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
