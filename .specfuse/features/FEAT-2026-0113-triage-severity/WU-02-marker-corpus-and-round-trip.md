---
id: FEAT-2026-0113/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
produces:
  - tests/test_marker_dual_shape.py
duration_seconds: 125.878
cost_usd: 0.529971
input_tokens: 30
output_tokens: 13410
---

# T02 — prove the reader against every marker shape that exists

**Context.** T01 makes the reader tolerant. This unit is the evidence that it is
tolerant *of what is actually out there*, which is the property the published-marker
contract cares about: "once an issue in any repository carries one, changing this
format orphans that issue." A reader that parses the shapes we imagined is not the
same as one that parses the shapes we wrote.

**Acceptance criteria.**

1. `tests/test_marker_dual_shape.py::MarkerCorpus::
   test_every_shipped_marker_shape_parses` fails on HEAD before this unit runs.
2. The corpus is assembled from the repository's own marker literals rather than
   hand-typed: `render_marker`'s output across the full cross-product of
   `CATEGORIES` × `CONFIDENCES`, plus the literal marker strings already present in
   `tests/` and in `CHANGELOG.md`'s published-contract entries. Each parses to the
   category and confidence it names.
3. A marker embedded in a realistic issue body — surrounded by prose, preceded and
   followed by blank lines, and with other HTML comments nearby — parses, and a
   second unrelated HTML comment is never mistaken for a marker.
4. Round trip: for every `(category, confidence)` pair,
   `parse_marker(render_marker(c, f)) == (c, f)`.
5. A malformed marker (missing a field, an empty value, an unterminated comment)
   returns `None` rather than a partial tuple or a raised exception — a marker the
   reader cannot fully understand must read as absent, which is the fail-closed
   direction.
6. The three-field forward-compatible shape parses through `parse_marker_fields`
   and still yields a correct 2-tuple through `parse_matcher`'s two-field contract.

**Do not touch.** Everything named in T01's Do-not-touch. Additionally: T01's
implementation — if this unit's corpus proves T01 wrong, escalate rather than
patching T01's reader from here, so the failure is recorded against the unit that
owns the code.

**Verification.** The gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`.

**Escalation triggers.** If the corpus surfaces a marker shape in the wild that the
old regex parsed and the new scan does not, stop — that is an orphaning regression
and the reader is wrong. If assembling the corpus requires a network call or a live
`gh` query, stop: the corpus is built from this repository's own literals, and a
test that needs the network is not the oracle this gate wants.
