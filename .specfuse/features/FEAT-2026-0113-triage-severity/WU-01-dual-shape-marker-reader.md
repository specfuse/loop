---
id: FEAT-2026-0113/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - tests/test_marker_dual_shape.py
  - specfuse/loop/triage.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.20.1
started_at: 2026-09-18T00:29:02.882691+00:00
duration_seconds: 34.528
cost_usd: 0.292826
input_tokens: 20
output_tokens: 3485
---

# T01 — the marker reader accepts both shapes

**Context.** `specfuse/loop/triage.py` renders and parses the published triage
marker. `_MARKER_RE` is positionally anchored (`category=(?P<category>\S+)
confidence=(?P<confidence>\S+) -->`), so a marker carrying a third field does not
merely lose that field — **it fails to match at all**, and the issue scans as
untriaged on every subsequent run. This unit is the tracer bullet: it makes the
reader tolerate a `severity=` field end to end so gate 1's `feature_oracle` runs,
and it changes no writer. `render_marker` still emits exactly two fields after this
unit; nothing in the repository produces a three-field marker yet.

`parse_marker`'s `(category, confidence)` return type is a contract with three live
callers (`triage.apply_triage`, `bug_lane_state.triaged_bug_intake`,
`agent/providers/triage.py`) and does not change. Severity is reached through a new
`parse_marker_fields`.

**Acceptance criteria.**

1. `tests/test_marker_dual_shape.py::DualShapeMarker::
   test_a_three_field_marker_parses` fails on HEAD before this unit runs, because
   the anchored regex returns no match for a marker carrying `severity=`.
2. The marker reader parses the fields inside `<!-- specfuse:triage … -->` as
   `key=value` pairs rather than a fixed sequence, so field order and field count
   do not decide whether a marker is seen at all.
3. That same test passes after this unit.
4. `parse_marker(body)` still returns a `(category, confidence)` 2-tuple for a
   two-field marker and `None` for a body carrying no marker — byte-identical
   behaviour, asserted against the existing `tests/test_triage*.py` cases, which
   are not edited by this unit.
5. `parse_marker_fields(body)` returns a `dict` of every field present, or `None`
   for a body carrying no marker. A two-field marker yields exactly
   `{"category": …, "confidence": …}` — no `severity` key invented with a default.
6. `render_marker(category, confidence)` emits the two-field form byte-identically
   to today, asserted by string equality against a literal, not field-wise.
7. No caller of `parse_marker` is edited, and no write path changes.

**Do not touch.** `render_marker`'s output shape. `apply_triage` and every other
write path. `labels.py`. `agent_policy.py`'s severity readers. `LABEL_REGISTRY`.
The `CATEGORIES` / `CONFIDENCES` vocabularies. Any file under
`.specfuse/features/` other than this feature's own folder.

**Verification.** The gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`.

**Escalation triggers.** If making the reader tolerant requires changing
`parse_marker`'s return type or editing any of its three callers, stop and escalate
— that is a wider contract change than this unit's Do-not-touch permits, and it
belongs to a re-scoped unit rather than a quiet widening. Likewise if a marker
shape is found in the wild that neither the old regex nor the new scan parses.
