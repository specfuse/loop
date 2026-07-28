---
id: FEAT-2026-0040/T05
type: implementation
status: draft
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/monitor/providers/__init__.py
  - specfuse/monitor/providers/azure_service_bus.py
  - tests/test_service_bus_dlq_adapter.py
model: sonnet
effort: medium
gate_set: code
---

# Peek the dead-letter queue — the Service Bus broker adapter

**Objective.** Ship the first `BrokerAdapter` implementation: a Service Bus adapter
that **peeks** a subscription's dead-letter queue and returns one redacted
`FailureArtifact` per dead-lettered message, carrying that target's coordinates.

**Context.** Correlation ID `FEAT-2026-0040/T05`. Gate 2, no dependencies — T01's
`BrokerAdapter` protocol and `FailureArtifact` model are `done` and shipped. This is
the adapter the `dlq` check type has been waiting for since the schema shipped in
0039; T02's fingerprints and T03's redaction are both properties this unit must
actually exercise rather than assume.

**Peek means peek.** `harvest_mode: peek` is in the schema for a reason and this is
the unit that makes it true. The adapter may **only** read: no receive, no complete,
no abandon, no dead-letter move, no message settlement of any kind. All environment
access in this feature is read-only (`PLAN.md`'s scope boundary), and a monitoring
tool that consumes the evidence it is reporting on destroys the thing a human needs to
diagnose. DLQ *quarantine* harvesting — the mode that does move messages — is
FEAT-2026-0038's, deliberately out of scope here. Criterion 6 is a recorded-call
assertion rather than a code review, because "we didn't call settle" is exactly the
kind of claim that stays true until someone adds a retry loop.

**No provider type may become reachable from the core.** That is the whole point of
T01's adapter layer and the property most easily lost by accident — one import in the
wrong direction and the harvester stops being provider-agnostic. Provider code lives
under `specfuse/monitor/providers/`; the dependency arrow points from `providers/` to
the core and never back. Criterion 9 is a grep, because no type checker catches a
string that happens to name a provider in a field the core reads.

**The package has zero runtime dependencies, and this unit does not change that.**
`lint_monitoring.py`'s docstring records it as a property of the package, and the
`code` gate set has no install step that would put an Azure SDK on the path. So the
transport is **injected at construction** — the adapter takes an object exposing the
peek operation it needs, the real SDK client is built by a factory that imports lazily
inside the function body, and every test in this unit runs against a stub. An adapter
that imports an SDK at module scope fails `tests` on a clean checkout, and that
failure looks like a broken test rather than a broken design.

**What the artifact must carry.** One artifact per dead-lettered message, built
through `FailureArtifact.from_target` so the `dlq` coordinates — `subscription` and
`function` — round-trip into `target_coordinates`. That is the binding constraint this
whole feature inherits from 0069: without those coordinates, twenty DLQ targets
collapse into one issue with every gate green. `failure_class` comes from the
dead-letter reason the broker recorded; `failure_signature` is derived from the
exception type plus a **normalized** message — no message ID, no timestamp, no GUID,
no sequence number — because the signature is what makes a thousand occurrences of one
poison message into one issue.

**Redaction happens at the adapter boundary, before anything can leave the process.**
T03 shipped `redact_artifact` for this. A dead-lettered message body is arbitrary
production payload: it is the single most likely place in this feature for a live
credential to enter the process, and the boundary is here, not at the issue writer.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_service_bus_dlq_adapter.py::TestDlqPeekAdapter::test_distinct_subscriptions_yield_distinct_fingerprints`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. `specfuse/monitor/providers/azure_service_bus.py` defines a DLQ peek adapter class
   whose `fetch_failures()` returns an iterable of `FailureArtifact` — structurally a
   `BrokerAdapter` per T01's protocol. A test asserts the instance satisfies the
   protocol (`isinstance` against a `runtime_checkable` protocol, or an explicit
   structural assertion if the protocol is not runtime-checkable).
3. The adapter's transport is supplied at construction. A test constructs it with a
   stub and no Azure SDK is importable in the test environment:
   `python3 -c "import specfuse.monitor.providers.azure_service_bus"` exits zero on a
   clean checkout with no cloud SDK installed.
4. **Cardinality the failure needs.** The stub carries **at least 2 subscriptions**,
   each with **at least 2 dead-lettered messages**, and at least two of those messages
   share an exception type. A fixture with one subscription cannot express the bug this
   feature exists to prevent — `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`: a fixture with
   cardinality 1 where the failure needs N is testing a different question.
5. Each returned artifact's `target_coordinates` carries the **`subscription` and
   `function`** of the target it came from, and
   `fingerprint_artifact` over two artifacts identical in every field except their
   subscription returns **two different digests**. This is the binding constraint from
   `PLAN.md`, asserted rather than assumed.
6. **Read-only, proven by recorded calls.** The stub transport records every method
   invoked on it. A test asserts the recorded set contains only peek/read operations
   and **no** `receive`, `complete`, `abandon`, `dead_letter`, `defer`, or
   `renew_lock` call — a negative observation, not an inspection of the source.
7. Two occurrences of the same poison message — differing only in message ID,
   enqueued timestamp, and sequence number — produce the **same** `failure_signature`
   and therefore the same fingerprint. Two messages with different exception types
   produce different signatures.
8. **Redaction at the boundary.** A stubbed dead-lettered message whose body carries a
   planted secret yields an artifact in which no occurrence of that secret's value
   survives, and the redacted span reads as `<redacted:` + a short digest. Use a
   synthetic value that is not a real credential and not a denylisted token; see
   `security-boundaries.md` and note that the `leak-scan` pre-commit form is stricter
   than its CI form.
9. `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/artifact.py
   specfuse/monitor/adapters.py specfuse/monitor/fingerprint.py
   specfuse/monitor/redaction.py` returns no match — no provider identifier is
   reachable from the core. The grep is scoped to the core files by name, not to
   `specfuse/monitor/` as a whole, because `providers/` is where the provider name
   belongs.
10. Nothing under `specfuse/monitor/` outside `providers/` imports anything from
    `providers/`: `grep -rn "from specfuse.monitor.providers\|import specfuse.monitor.providers"
    specfuse/monitor/*.py` returns no match. The arrow points one way.
11. `python3 -m unittest tests.test_service_bus_dlq_adapter -v` exits zero after this
    WU's edits, and the `code` gate set passes in full — `tests`, `lint`, `security`,
    `coverage` (≥90%), `leak-scan`, `monitoring-example-lint`, and the five `bats`
    suites.

**Do not touch.** `specfuse/monitor/artifact.py`, `fingerprint.py`, `redaction.py` —
T01–T03 own them and they are `done`; this unit **consumes** them. If one of them
cannot express what this adapter needs, that is an escalation, not an edit.
`specfuse/loop/lint_monitoring.py` and the monitoring examples — T04 owns the schema.
`specfuse/monitor/providers/azure_app_insights.py` — T06 and T07 own it.
`escalation.py` — gate 3 reuses it. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 11, the two greps in criteria 9
and 10 — provider leakage is detectable by no code gate — the recorded-call negative
observation in criterion 6, and the planted-secret negative observation in criterion 8.
Note that three of this repo's `code` gates are `bats` suites whose `setup` calls
`mktemp -d`; under the agent session's default sandbox that returns
`Operation not permitted` and every case fails before an assertion runs. Report which
sandbox each gate ran under rather than reporting a manufactured regression
(`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: T01's
`BrokerAdapter` protocol cannot express a Service Bus peek without a provider type
appearing in `adapters.py` — that is a finding about gate 1's central claim and it is
worth more as a blocked report than as a quiet edit to the protocol; `FailureArtifact`
cannot carry what a dead-lettered message needs without a new field, which is T01's
model and not this unit's to widen; the coverage floor cannot be met without asserting
behaviour that only a live broker exhibits; or satisfying criterion 6 requires the
stub to model an SDK surface precisely enough that the test becomes a test of the SDK
rather than of the adapter.
