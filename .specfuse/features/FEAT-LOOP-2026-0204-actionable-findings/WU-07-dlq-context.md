---
id: FEAT-LOOP-2026-0204/T07
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - specfuse/monitor/providers/azure_service_bus.py
  - tests/test_monitor_finding_context_end_to_end.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:53:20.571187+00:00
duration_seconds: 59.993
cost_usd: 0.389376
input_tokens: 32
output_tokens: 7599
---

# T07 — a `dlq` finding carries the dead-lettered message's details and recorded exception

**Objective.** A `dlq` finding's body is never empty: it names the message and the
exception the handler recorded, even when the broker's dead-letter reason is blank.

**Context.** `FEAT-LOOP-2026-0204/T07`; T05's `context` model, T03's message id. Today
`ServiceBusDlqAdapter._build_artifact` puts only `dead_letter_error_description` in
`observed_text`, which is empty on Backend#1016 and #1042 because the consumer
dead-letters with custom properties only (Backend#1005). The peeked message already
carries what a diagnosis needs: `message_id`, `sequence_number`, `subject`,
`enqueued_time_utc`, `delivery_count`, `dead_letter_reason`,
`dead_letter_error_description`, and `application_properties`. Add a Message section
(id, sequence number, subject, enqueued UTC, delivery count), a Dead-letter section
(reason and description when present), an Exception section from the
`Exception.Message` / `Exception.StackTrace` application properties when present
(keys may be `bytes`; top frames only, at most 10 lines), a Body shape section (the
JSON body's **top-level keys only**, never values; omitted when the body is not a JSON
object), and a "Peek it" section naming the namespace, topic, subscription and the
sub-queue — text only. When the broker reason is blank but `Exception.Message` exists,
`failure_class` stays as today (`Unknown`); the title uses T05's `in <where>` with the
handler function from the target.

**Acceptance criteria.**

1. `tests/test_monitor_finding_context_end_to_end.py::DlqContext` (skipped by T01,
   naming this unit) has its skip removed and passes: a fixture message modelled on
   Backend#1016 (blank reason, `Exception.Message` and `Exception.StackTrace` as
   `bytes` keys, a JSON body `{restaurantId, companyId, after}`) renders Message,
   Exception (message + top frames), Body shape listing exactly those three keys and
   **no values**, and Peek it.
2. A message with no application properties and a non-JSON body still files, with
   those sections absent.
3. The existing `tests.test_service_bus_dlq_adapter` passes, and the transport still
   only **peeks** (no receive, complete or abandon call appears in the module).

**Do not touch.** The fingerprint. `queue-stalled` (T08). T03's acknowledgement logic.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_service_bus_dlq_adapter tests.test_monitor_finding_lifecycle_end_to_end -b`.

**Escalation triggers.** If a body-shape read would require decoding a body type the
SDK exposes only as a generator of sections, stop and escalate rather than buffering
large bodies.
