<!--
`DECISIONS.md` — one feature's decision registry.

Every decision this feature has taken lives here, once. Other artifacts
(PLAN.md, GATE files, WU files) cite a decision by its ID (`D1`, `D2`, ...)
rather than restating its statement — restating is what this registry
replaces (see FEAT-2026-0058). The parser and closed status set live in
`specfuse/loop/decisions_format.py`.

Each entry is a `### D<n>` heading (ID unique within this feature) followed
by these fields, one per line:

- `**statement:**` — the decision itself, one or a few sentences.
- `**owner:**` — who is accountable for this decision (a name or role).
- `**status:**` — one of the closed set in `STATUS_VALUES`:
  `proposed` | `ratified` | `overridden-pending-signoff` | `rejected` |
  `superseded`. A status outside this set is a lint error, not a warning.
- `**provenance:**` — where the decision was taken: a PLAN.md decision
  label (`PLAN.md D2`), a GATE review, an ADR path, or a correlation ID.

An entry whose status is `overridden-pending-signoff`, or which was ever
overridden en route to its current status, additionally carries:

- `**overridden_from:**` — the status the override moved it away from.
- `**signed_off_by:**` — who signed off on the override.
- `**signed_off_at:**` — when (ISO date).

These three fields are what keep "ratified from the start" and "overridden,
then signed off by a named human on a date" distinguishable to a query —
without them, an override that reaches `ratified` is byte-identical to one
that was never overridden.
-->

### D1

- **statement:** <the decision, stated plainly>
- **owner:** <name or role>
- **status:** `ratified`
- **provenance:** PLAN.md D1
