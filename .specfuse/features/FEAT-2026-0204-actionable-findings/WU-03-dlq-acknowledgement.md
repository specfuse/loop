---
id: FEAT-2026-0204/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/monitor/providers/azure_service_bus.py
  - specfuse/monitor/artifact.py
  - specfuse/monitor/issues.py
  - tests/test_monitor_finding_lifecycle_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:46:21.789052+00:00
duration_seconds: 151.473
cost_usd: 0.52299
input_tokens: 38
output_tokens: 11000
---

# T03 — closing a `dlq` finding acknowledges it until a new message arrives

**Objective.** A closed `dlq` issue stays closed while every dead-lettered message in
the queue is one it has already recorded, and a new message id reopens it with a
comment naming that message.

**Context.** `FEAT-2026-0204/T03`, gate 1; PLAN.md decision 2. A dead-lettered
message sits in the queue until it is resubmitted or purged, so the `dlq` check sees
it on every run; with T01 alone, closing a `dlq` issue would just reopen it on the
next run. Backend#1016 is the live case: one `Restaurant.Created` message from
2026-10-10, closed with a diagnosis that says "replay after the release".

The adapter (`ServiceBusDlqAdapter._build_artifact`,
`specfuse/monitor/providers/azure_service_bus.py`) already reads each peeked message;
the transport's message object carries `message_id` and `sequence_number`
(`azure_service_bus.py:78-79`). Carry the message id on the artifact — a new optional
field on `FailureArtifact` that the fingerprint does **not** include (the fingerprint
stays per subscription and exception signature, so one issue per failure kind, not
per message). In `record_finding`, for a `dlq` artifact matched to a **closed** issue:
if its message id is already in the meta's `messages` (T02), do nothing — no `gh`
write at all; otherwise reopen with a comment naming the new message id and append it
to `messages`. For an open `dlq` issue, append unseen ids on the normal update path.

**Acceptance criteria.**

1. `tests/test_monitor_finding_lifecycle_end_to_end.py::DlqAcknowledgement`, skipped
   by T01 with a reason naming this unit, has its skip removed and passes:
   - a closed `dlq` issue whose `messages` contains the only peeked message id → no
     `gh` call after the listing;
   - the same issue, with one additional unseen message id peeked → one reopen, one
     comment naming that id, and the id appended to `messages`.
2. `test_fingerprint_ignores_message_id`: two artifacts differing only in message id
   share a fingerprint (`fingerprint_artifact`).
3. A non-`dlq` artifact never carries a message id, and its path is unchanged
   (T01's tests still pass).
4. The existing `tests.test_service_bus_dlq_adapter` passes unchanged except where a
   test asserts the artifact's full field set.

**Do not touch.** `fingerprint.py`'s fingerprint model. `queue-stalled`. T07's DLQ
diagnostic context (subject, delivery count, `Exception.*` properties) — this unit
carries the id only.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_service_bus_dlq_adapter tests.test_monitor_finding_meta tests.test_monitor_issue_lifecycle -b`.

**Escalation triggers.** If a peeked message can arrive with no `message_id` (the SDK
allows `None`), stop and decide the fallback with evidence (sequence number is
per-entity and survives) rather than inventing an id.
