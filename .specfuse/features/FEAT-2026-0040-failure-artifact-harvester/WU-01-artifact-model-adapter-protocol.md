---
id: FEAT-2026-0040/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
produces:
  - specfuse/monitor/artifact.py
  - specfuse/monitor/adapters.py
  - tests/test_failure_artifact_model.py
produces_driver_helper:
  - FailureArtifact
  - TelemetryAdapter
  - BrokerAdapter
  - resolve_telemetry
---

# Model a failure artifact, and define the adapter protocols that produce one

**Objective.** Ship the neutral `FailureArtifact` the harvester's core reasons
about, plus `TelemetryAdapter` and `BrokerAdapter` protocols, with telemetry
resolved per component through a seam.

**Context.** Correlation ID `FEAT-2026-0040/T01`. The foundation of the whole
feature: T02 fingerprints these artifacts, T03 redacts them, gate 2 writes the
Azure adapters that produce them, and gate 3 turns them into issues.

**The core must never see a provider type.** That is the entire point of the
adapter layer, and it is the property most easily lost by accident — one
`from azure...` import in a core module and the harvester stops being
provider-agnostic. Criterion 3 is a grep, because no type checker catches a string
that happens to name a provider in a field the core reads.

**Telemetry resolves per component, through a seam.** This is the recorded decision
from `PLAN.md`, taken against [#262](https://github.com/specfuse/loop/issues/262).
`environments.<name>.telemetry` is a single binding per environment, so every
component in an environment resolves to the same sink. That is correct for the
motivating project and wrong in general. Expose `resolve_telemetry(component,
environment)` whose **only implementation today** reads the environment's binding.
The seam is the deliverable; the single implementation is expected. When
per-component bindings land they add a resolver rather than reshaping every
adapter — turning #262's *"the adapter interface changes rather than extends"* into
an extension.

**The model carries no schedule semantics.** No cron field, no expected-fire time,
no dialect. That contract lands in gate 2 with the heartbeat adapter, and keeping
it out is what lets this model stay neutral. A heartbeat artifact carries the
target's coordinates and whatever the adapter observed — not a computation the core
would have to understand.

**What a target-derived artifact must carry.** 0069 separated two axes: `component`
is the unit of deployment and attribution, `targets` is the unit of failure-artifact
enumeration. An artifact must therefore record **both** — the component it belongs
to and, when it came from a target, that target's coordinates. T02 fingerprints on
those coordinates; if the model cannot carry them, T02 cannot honour the binding
constraint. This is why criterion 4 exists.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_failure_artifact_model.py::TestArtifactModel::test_artifact_carries_target_coordinates`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/monitor/artifact.py` defines `FailureArtifact` carrying at minimum: the
   component name, the check type, a failure class, a failure signature, the
   observed text, and an optional target-coordinates mapping.
3. `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/artifact.py specfuse/monitor/adapters.py`
   returns no match — no provider identifier is reachable from the core or the
   protocol definitions.
4. A `FailureArtifact` built from a `dlq` target round-trips both `subscription` and
   `function` in its target coordinates; one built from a `heartbeat` target
   round-trips `name`.
5. A `FailureArtifact` built for an `invariant` check carries **no** target
   coordinates — 0069 rejected `targets` on that check type so `fingerprint_by`
   stays its single enumeration key.
6. `specfuse/monitor/adapters.py` defines `TelemetryAdapter` and `BrokerAdapter` as
   protocols (or ABCs) whose declared return type is `FailureArtifact` or a
   collection of them.
7. `specfuse/monitor/adapters.py` defines `resolve_telemetry(component, environment)`
   returning the telemetry binding for that component.
8. A test asserts `resolve_telemetry` is called with the **component** — not only
   the environment — so the seam exists at the component level even though today's
   implementation reads the environment binding.
9. `specfuse/monitor/artifact.py` contains no cron, schedule, or dialect field:
   `grep -niE "cron|schedule|dialect" specfuse/monitor/artifact.py` returns no match.
10. `python3 -m pytest tests/test_failure_artifact_model.py -q` exits zero after this
    WU's edits (the same file named in criterion 1).
11. `python3 -c "from specfuse.monitor.artifact import FailureArtifact; from specfuse.monitor.adapters import TelemetryAdapter, BrokerAdapter, resolve_telemetry"`
    exits zero.

**Do not touch.** `specfuse/loop/lint_monitoring.py` and the monitoring schema —
gate 2 owns the cron-dialect change; this WU reads the schema's shape and changes
nothing. `specfuse/loop/escalation.py` — gate 3 reuses it. Files owned by T02 or
T03. Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run in
criteria 1 and 10, the symbol-existence import in criterion 11, and the two greps in
criteria 3 and 9 — neither provider leakage nor an accidental schedule field is
detectable by any code gate.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
monitoring schema cannot express which target coordinates belong to which check type
without re-reading `lint_monitoring._TARGET_REQUIRED_FIELDS`, and that mapping
disagrees with this WU's Context; a protocol return type cannot name `FailureArtifact`
without a circular import between `artifact.py` and `adapters.py`; or satisfying the
coverage floor would require testing adapter behaviour that does not exist until gate
2. If either module is absent from the files you edited, emit `status: blocked` — do
not claim complete.
