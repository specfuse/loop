---
id: FEAT-2026-0113/T08
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/loop/triage.py
  - tests/test_severity_backfill_marker.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.20.1
started_at: 2026-09-18T11:09:04.697210+00:00
duration_seconds: 104.236
cost_usd: 0.523399
input_tokens: 42
output_tokens: 7321
---

# T08 — which issues a backfill may touch, and how a marker is amended

**Objective.** `list_severity_backfill_candidates` selects the already-marked,
severity-less issues a backfill run is allowed to touch, and
`amend_marker_severity` rewrites one such marker in place.

**Context.** `FEAT-2026-0113/T08`, gate 3. Two pure additions to
`specfuse/loop/triage.py`, beside the marker functions they extend. This unit
issues no write and is not a tracer bullet: T07 landed the skeleton, so a stub
here is the hollow pass `/authoring-work-units` §9 exists to catch.

**This is where the blast radius is set.** A backfill amends markers in bulk, so
what it may touch is a property of this selection and nowhere else. The predicate
is the inverse of the one that strands the measured 31 issues: `list_untriaged`
(`specfuse/loop/triage.py:308`) *excludes* a marked issue whose labels are
complete, which is why nothing revisits them.

The exclusions are the ones the normal triage path already applies, reused rather
than re-derived: `has_finding_marker` (`specfuse/monitor/issues.py:72`) for a
harvester finding, and `escalation.CATEGORY_LABELS`
(`specfuse/loop/escalation.py:29`) for an agent-authored escalation, which
`TriageProvider._is_agent_escalation` (`specfuse/agent/providers/triage.py:146`)
keys on.

The stop condition is the marker itself: an issue whose marker already carries a
`severity=` field is not a candidate, so a second run over the same repository
selects nothing. That is the same idempotency the two-field marker already has,
read one field deeper.

**Acceptance criteria.**

1. `tests/test_severity_backfill_marker.py::BackfillSelection::test_marked_issue_without_severity_is_a_candidate`
   fails on HEAD before this unit runs and passes after:
   `list_severity_backfill_candidates(runner, repo, limit=...)` returns a row for
   an open issue whose marker parses and carries no `severity` field, and returns
   nothing for an otherwise identical issue whose marker carries `severity=high`.
2. Each exclusion is asserted on its own row, not as a bundle: an issue carrying
   a harvester finding marker, an issue carrying any label in
   `escalation.CATEGORY_LABELS`, an issue whose marker names a category outside
   `CATEGORIES`, and an issue carrying no marker at all are each absent from the
   result.
3. `limit` bounds both the fetch and the result: the listing argv carries
   `--limit <n>` and at most `n` rows are returned, and the listing is issued
   through the module's existing `_list_open_issues` —
   `grep -c '"issue", "list"' specfuse/loop/triage.py` still reports `1`.
4. `amend_marker_severity(body, severity)` replaces the body's existing marker in
   place: `category=` and `confidence=` keep their values byte-for-byte, the
   result carries exactly one `specfuse:triage` marker, and the new marker is
   rendered through the existing `render_marker` rather than a fourth literal —
   `grep -c "specfuse:triage" specfuse/loop/triage.py` still reports `3`.
5. `amend_marker_severity` returns its input unchanged, by string equality, for a
   body carrying no marker and for a body whose marker already carries a
   `severity=` field.

**Do not touch.** `parse_marker`'s `(category, confidence)` return type and
`parse_marker_fields`, `render_marker`, `apply_triage`, `list_untriaged` — this
unit adds two functions beside them and edits none of their bodies; gate 2's
tests over them must stay green unedited. `specfuse/agent/severity_backfill.py`
(T09 switches the call site over and deletes T07's `_amend_marker` stub; this
unit does not reach into it). `specfuse/loop/labels.py` and
`specfuse/agent/triage_invoke.py` (gate 2's). `_MARKER_TEMPLATE` and
`_MARKER_TEMPLATE_WITH_SEVERITY` — every marker in the wild is read against those
strings.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_triage tests.test_triage_apply tests.test_triage_severity_write tests.test_marker_dual_shape -b`,
and `python3 -c "from specfuse.loop.triage import amend_marker_severity, list_severity_backfill_candidates"`.

**Escalation triggers.** If the selection cannot be written without a second
`gh issue list` — a different limit, a different field set — stop and escalate
rather than adding one: `GATE-03.md`'s arming discipline names the
existing-mechanism search explicitly, and a second listing is the shape it
forbids. If amending in place requires changing either marker template, stop:
gate 1's whole proof rests on those two strings, and a template change orphans
every marker already written under it.
