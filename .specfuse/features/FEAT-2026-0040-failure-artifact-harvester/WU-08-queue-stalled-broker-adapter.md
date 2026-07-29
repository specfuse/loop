---
id: FEAT-2026-0040/T08
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/monitor/providers/azure_service_bus.py
  - tests/test_queue_stalled_adapter.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.6.0
started_at: 2026-07-29T00:22:58.267426+00:00
duration_seconds: 687.631
cost_usd: 1.941454
input_tokens: 70
output_tokens: 22666
---

# The wedged consumer — the `queue-stalled` broker adapter

**Objective.** Ship the sixth and last check type's adapter: a `queue-stalled`
adapter that reads a subscription's **queue depth** and **age of the oldest
message** and emits one `FailureArtifact` per target whose backlog has been
sitting longer than that target's declared stall threshold.

**Context.** Correlation ID `FEAT-2026-0040/T08`. Gate 3, no dependencies —
`T01`'s `BrokerAdapter` protocol and `FailureArtifact` model and `T05`'s Service
Bus transport seam are all `done` and shipped. This unit is **not** a gap
discovered at gate 3's drafting: `GATE-02-REVIEW.md` §2 named it before gate 2 was
armed and §6.1 answer 3 records the operator placing it here, so gate 2 stayed the
adapter-*shape* gate. `RETROSPECTIVE.md`'s follow-up **FU-B** carries the same
decision forward.

**It is a broker check, not a telemetry one — and that is the whole reason the
check type exists.** `docs/concepts/monitoring-schema.md` states it plainly: a
wedged consumer produces no dead-lettered message (so `dlq` sees nothing), leaves
the host alive (so `heartbeat` sees nothing), and its symptom is a **broker
coordinate — queue depth and age of the oldest message — not a telemetry query**,
so `invariant` cannot reach it either. This unit therefore extends `T05`'s
`BrokerAdapter` surface in `specfuse/monitor/providers/azure_service_bus.py`. It
does **not** touch the App Insights telemetry adapters; a `queue-stalled` adapter
built as a KQL query would be answering a different question with a worse
instrument.

**The threshold's units are opaque in the schema, and this unit is where that
stops being free.** The shipped example carries `stall_after: 15m` and
`docs/concepts/monitoring-schema.md` records the value as "accepted but never
parsed or bounded here, exactly like `invariant.query`" — a deliberate 0069
position at the *lint* layer. The adapter cannot share that position: it has to
compare the threshold against an observed age, so it must know what `15m` means.
Three sub-decisions, all of which this unit settles explicitly rather than by
default:

1. **The grammar is settled here, in the adapter, and is refused rather than
   guessed.** Accept `<integer><unit>` with `unit` in `s` / `m` / `h` / `d`, and
   **raise on anything else** — no coercion, no "assume minutes", no silent zero.
   This is the same posture `T07` took on the cron dialect and for the same reason:
   a monitoring tool that guesses degrades silently at the exact moment a new
   spelling arrives.
2. **A `queue-stalled` target with no `stall_after` is skipped with a recorded
   reason, not defaulted and not crashed.** The schema makes the coordinate
   optional, so a config with no threshold is *valid* — inventing a default would
   fabricate an alerting policy the operator never wrote, and raising would make a
   schema-valid config fail at runtime. The adapter records the skip so `T10`'s run
   summary can surface it and the operator learns from one dry run.
3. **The validator is NOT tightened in this unit.** Making `stall_after` required,
   or bounding its grammar at lint time, is a severity flip; `planning-discipline.md`
   §4 requires a runtime probe before arming one, and gate 3 was armed with no such
   probe because it has no other flip. It is named as a follow-up in
   `GATE-03-REVIEW.md` §7, deliberately, rather than smuggled in here.

**Zero runtime dependencies, still.** Same shape as `T05`: the transport is
injected at construction, the real SDK client is built by a factory whose import is
lazy inside the function body, and every test runs against a stub. An adapter that
imports an SDK at module scope fails `tests` on a clean checkout, and that failure
reads as a broken test rather than a broken design.

**Read-only, still.** All environment access in this feature is read-only
(`PLAN.md`'s scope boundary). Reading queue depth and age-of-oldest is a
management/metadata read; it must not peek, receive, settle, or otherwise consume
the backlog it is measuring. As in `T05`, that is asserted by a recorded-call
negative observation rather than by code review.

**The binding constraint applies here too.** A `queue-stalled` artifact carries the
target's `subscription` and `function` — `artifact.py`'s
`_TARGET_COORDINATE_FIELDS` already maps the check type to exactly those two — so
two stalled subscriptions on one component fingerprint apart. Without it, this
adapter reintroduces at gate 3 the collapse 0069 paid two gates to prevent.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_queue_stalled_adapter.py::TestQueueStalledAdapter::test_distinct_subscriptions_yield_distinct_fingerprints`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/monitor/providers/azure_service_bus.py` gains a queue-stalled adapter
   class whose `fetch_failures()` returns an iterable of `FailureArtifact` —
   structurally a `BrokerAdapter` per `T01`'s protocol, asserted the same way
   `T05`'s is.
3. The adapter reads **both** broker coordinates: queue depth (active message
   count) and age of the oldest message. A test asserts the transport is asked for
   both, and that the emitted artifact's `observed_text` names both values.
4. **The stall decision is the age, and the depth is evidence.** A target whose
   oldest message is younger than `stall_after` yields **no** artifact even when the
   depth is large — a deep queue that is draining is not stalled. A target whose
   oldest message is older than `stall_after` yields exactly one artifact. Both
   directions asserted; the negative case is the one that keeps this from being a
   depth alarm with extra steps.
5. **Cardinality the failure needs.** The stub carries **at least 2 subscriptions**,
   at least one stalled and at least one not. A single-subscription fixture cannot
   express the bug this feature exists to prevent
   (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
6. Each artifact's `target_coordinates` carries the target's **`subscription` and
   `function`**, and `fingerprint_artifact` over two artifacts identical in every
   field except their subscription returns **two different digests**.
7. **Threshold grammar, settled and refused rather than guessed.**
   `stall_after` values `30s`, `15m`, `2h`, and `1d` parse to the expected number
   of seconds. **Negative observation:** each of `"15"`, `"15 minutes"`, `"m15"`,
   `""`, and `"-5m"` raises an explicit error naming the offending value — no
   coercion and no silent default. `verification-discipline.md` §3 requires the
   rejection to be observed, not asserted in prose.
8. **A target with no `stall_after` is skipped, with the reason recorded.** The
   adapter emits no artifact for it and exposes the skip (target coordinates plus
   reason) on a public attribute or return value that `T10`'s run summary can read.
   A test asserts both halves: no artifact, and one recorded skip naming the target.
9. **Read-only, proven by recorded calls.** The stub transport records every method
   invoked. A test asserts the recorded set contains only metadata/read operations
   and **no** `receive`, `complete`, `abandon`, `dead_letter`, `defer`,
   `renew_lock`, or `peek` call.
10. **The clock is an argument, never read.** `grep -rn "datetime.now\|time.time"`
    over the queue-stalled code path returns no match; the reference instant is
    passed in, exactly as `T07`'s `most_recent_firing` takes it. A test pins two
    different reference instants against one stub and gets stalled / not-stalled.
11. **Redaction at the boundary.** If any observed broker text reaches
    `observed_text`, it passes through `redact_artifact` first. A stub whose
    oldest-message metadata carries a planted synthetic secret yields an artifact in
    which no occurrence of that value survives, and the redacted span reads as
    `<redacted:` + a short digest. Use a synthetic value that is not a real
    credential and not a denylisted token; see `security-boundaries.md`.
12. **No provider identifier reaches the core**:
    `grep -rniE "azure|appinsights|servicebus|kusto" specfuse/monitor/artifact.py
    specfuse/monitor/adapters.py specfuse/monitor/fingerprint.py
    specfuse/monitor/redaction.py specfuse/monitor/schedule.py` returns no match, and
    `grep -rn "from specfuse.monitor.providers\|import specfuse.monitor.providers"
    specfuse/monitor/*.py` returns no match.
13. `python3 -m unittest tests.test_queue_stalled_adapter -v` exits zero after this
    WU's edits, `python3 -m unittest tests.test_service_bus_dlq_adapter` still exits
    zero (this unit extends `T05`'s module and must not regress it), and the `code`
    gate set passes in full — `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`, `monitoring-example-lint`, and the `bats` suites.

**In-loop evidence.** This unit produces **real in-loop evidence**. It touches no
`gh` surface and needs no live environment: every criterion is decidable by a test,
a grep, or an import against a stub transport. It is the unit that keeps gate 3
from being wholly out-of-loop. What a stub cannot prove — that a real Service Bus
management API reports these two coordinates under these names, with this
freshness — is deferred to the operator run against the downstream .NET backend
that `GATE-02-REVIEW.md` §6.1 answer 4 records as planned, and belongs in
`G3-CLOSE`'s deferred list alongside `RETROSPECTIVE.md`'s D-1 … D-8.

**Do not touch.** `specfuse/monitor/artifact.py`, `fingerprint.py`, `redaction.py`,
`schedule.py`, `adapters.py` — gates 1 and 2 own them and they are `done`; this unit
**consumes** them. If one cannot express what this adapter needs, that is an
escalation, not an edit. `specfuse/monitor/providers/azure_app_insights.py` — the
telemetry adapters, and not where a broker check belongs.
`specfuse/loop/lint_monitoring.py` and both `monitoring.yml.example` copies — the
validator stays as it is; tightening it is the follow-up named above, not this
unit's. `specfuse/loop/escalation.py` — `T09` owns it. Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, in declared
order. Plus the scoped red/green run in criteria 1 and 13, the negative
observations in criteria 4, 7, 9, and 11, and the two greps in criteria 10 and 12 —
provider leakage and a hidden clock read are detectable by no code gate. Note that
several of this repo's `code` gates are `bats` suites whose `setup` calls
`mktemp -d`; under the agent session's default sandbox that returns
`Operation not permitted` and every case fails before an assertion runs. Report
which sandbox each gate ran under rather than reporting a manufactured regression
(`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`, `[FEAT-2026-0072/G1-CLOSE]`).

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`T01`'s `BrokerAdapter` protocol cannot express a depth-plus-age read without a
provider type appearing in `adapters.py` — that is a finding about gate 1's central
claim and is worth more as a blocked report than as a quiet edit to the protocol;
`FailureArtifact` cannot carry what a stall finding needs without a new field, which
is `T01`'s model and not this unit's to widen; criterion 8's skip-with-recorded-reason
cannot be exposed without changing `BrokerAdapter`'s public shape, which is a
cross-gate contract question; or the only way to satisfy criterion 4 is to model the
Service Bus management SDK precisely enough that the test becomes a test of the SDK
rather than of the adapter.
