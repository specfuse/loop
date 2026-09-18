---
id: FEAT-2026-0113/T01H
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.00
produces:
  - specfuse/loop/triage.py
  - tests/test_marker_dual_shape.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.20.1
started_at: 2026-09-18T00:40:04.120128+00:00
duration_seconds: 48.918
cost_usd: 0.293139
input_tokens: 26
output_tokens: 2632
---

# T01H — `parse_marker` fails closed on a marker missing a field

**Context.** Hygiene unit, inserted after T02 escalated
(`agent_reported_blocked`) rather than patch a sibling unit's code from inside
its own Do-not-touch boundary. T02 was correct to stop; this unit exists so the
fix is dispatched and verified like any other change.

T01 replaced an anchored regex with a marker shell plus a `key=value` field
scan. Before it, a marker missing `confidence` did not match at all and
`parse_marker` returned `None`. After it, the shell matches, the scan yields
`{'category': 'bug'}`, and `fields["confidence"]` at `specfuse/loop/triage.py`
raises `KeyError`. Reproduced directly:

```
'<!-- specfuse:triage category=bug -->'              parse_marker RAISED KeyError 'confidence'
'<!-- specfuse:triage category=bug confidence= -->'  parse_marker RAISED KeyError 'confidence'
```

That is a regression against T01's own criterion 4 ("byte-identical behaviour"),
and it is not hypothetical: the first literal is already in the tree at
`tests/test_agent_invoke_usage.py:83`. It matters beyond tidiness because
`parse_marker`'s three live callers — `triage.apply_triage`,
`bug_lane_state.triaged_bug_intake`, `agent/providers/triage.py` — sweep every
open issue, so one malformed marker raises out of the whole sweep. A marker the
reader cannot fully understand must read as **absent**; that is the fail-closed
direction the feature depends on.

**Incremental edit to already-delivered paths.** Both `produces` entries were
delivered by `FEAT-2026-0113/T01` and this unit edits them rather than creating
them. In `specfuse/loop/triage.py` the edit is confined to `parse_marker`'s
field lookup — no other function is touched. In
`tests/test_marker_dual_shape.py` the edit is purely additive: one new
`FailsClosed` case class; T01's existing cases are not modified, per criterion 5.

**Acceptance criteria.**

1. `tests/test_marker_dual_shape.py::FailsClosed::
   test_a_marker_missing_a_required_field_reads_as_absent` fails on HEAD before
   this unit runs, raising `KeyError` rather than returning `None`.
2. `parse_marker(body)` returns `None` — never raises — when the marker is
   present but carries no `category`, no `confidence`, or an empty value for
   either. Written as a lookup that cannot raise, not a `try/except KeyError`
   around the existing indexing: an exception swallowed is a different
   contract from a value that was never there.
3. That same test passes after this unit, and it covers all four shapes:
   missing `confidence`, missing `category`, `confidence=` empty, `category=`
   empty.
4. `parse_marker_fields` is **unchanged** and still reports exactly the fields
   present — it is the raw reader, and a caller wanting to know that a field is
   missing needs it to keep saying so.
5. Every existing assertion in `tests/test_marker_dual_shape.py` and
   `tests/test_triage*.py` passes unmodified. A test edited to accommodate this
   change is a signal the change is wrong.
6. The literal at `tests/test_agent_invoke_usage.py:83` is left alone — it is a
   fixture for a different subject, and this unit fixes the reader rather than
   the corpus.

**Do not touch.** `parse_marker`'s `(category, confidence)` return type for a
well-formed marker, and its three callers. `render_marker`'s output. Any write
path, `apply_triage` included. `_MARKER_RE` / `_MARKER_FIELD_RE` shell matching
— T01's tolerance is correct and is not what regressed. T02's file. Any file
under `.specfuse/features/` other than this feature's folder.

**Verification.** The gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`.

**Escalation triggers.** If making `parse_marker` fail closed turns out to
require changing its return type or editing a caller, stop — that is the wider
contract change T01's Do-not-touch already refused, and it belongs to a
re-scoped unit. If any existing test must be edited to pass, stop and report
which one: criterion 5 treats that as evidence the fix is wrong.
