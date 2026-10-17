---
id: FEAT-2026-0204/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - tests/test_monitor_finding_meta.py
  - specfuse/monitor/issues.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.28.2
started_at: 2026-10-17T15:43:52.954243+00:00
duration_seconds: 69.909
cost_usd: 0.317184
input_tokens: 20
output_tokens: 8914
---

# T02 — the finding-meta marker records first seen and seen message ids, and never raises

**Objective.** The `specfuse:finding-meta` marker gains `first_seen` and an optional
`messages` field, and its reader treats anything it cannot fully understand as absent
instead of raising out of a cycle.

**Context.** `FEAT-2026-0204/T02`, gate 1. Today the marker is
`<!-- specfuse:finding-meta occurrences=N last_seen=T -->` and `_parse_meta`
(`specfuse/monitor/issues.py:101`) already scans `key=value` tokens rather than
anchoring positionally — good — but `int(...)` and `float(...)` raise `ValueError` on
a malformed value, and the reader runs on every finding `record_finding` matches. That
is the exact defect `[FEAT-2026-0113/G1-CLOSE-INTERMEDIATE]` records for the triage
marker: tolerance and fail-closed are one edit, and a gate that asks only for
tolerance ships a fail-open sweep.

Add `first_seen=<epoch>` (written on create, preserved on every update and reopen)
and, for `dlq` only, `messages=<id>,<id>,…` (T03 writes it; this unit only reads and
round-trips it, capped so the marker stays one line — keep the most recent 50 ids).
Replace T01's last-seen-only reopen comment with first and last seen in UTC.

**Acceptance criteria.**

1. `tests/test_monitor_finding_meta.py::TestRoundTrip::test_new_fields_round_trip`
   fails on HEAD and passes after: a body rendered with `first_seen` and `messages`
   parses back to the same values, and a body written by HEAD (no new fields) parses
   with `first_seen` and `messages` absent.
2. `TestFailClosed`: each of `occurrences=abc`, `last_seen=`, `first_seen=x`,
   `messages=` with an empty id, a duplicated key, and an unterminated marker yields
   "absent" for the affected field (or `None` for the whole meta when a required field
   is unreadable) and **never raises** — asserted by calling the reader directly, not
   through a caller's `try/except`.
3. `test_cycle_survives_a_malformed_meta`: a `run_cycle` whose `gh` listing returns a
   matching issue with `occurrences=abc` completes, exits 0 and updates that issue as
   occurrence 1, rather than raising.
4. The reopen comment and the updated body name first and last seen as ISO-8601 UTC
   (`…Z`), and `first_seen` is unchanged by an update or a reopen.

**Do not touch.** The `specfuse:finding` fingerprint marker (`_MARKER_TEMPLATE`) —
renaming or reshaping it breaks every existing issue's identity. `has_finding_marker`.
Adapters.

**Verification.** The narrow tier for `implementation`, with `tests` narrowed to this
unit's test module plus
`python3 -m unittest tests.test_monitor_issue_lifecycle tests.test_monitor_finding_lifecycle_end_to_end -b`.

**Escalation triggers.** If an existing consumer issue body carries a meta shape the
new reader would read differently from HEAD (other than the new fields being absent),
stop and escalate with the shape — that is a published-format break, not a detail.
