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

- **statement:** The lint checks reference integrity and non-restatement
  only; it does not attempt contradiction detection between an artifact's
  prose and a cited decision's statement. Semantic agreement between a cited
  decision and the work done under it stays unguarded by construction.
- **owner:** FEAT-2026-0058 drafter
- **status:** `ratified`
- **provenance:** PLAN.md D1

### D2

- **statement:** The reference-integrity and non-restatement lint runs at
  ERROR severity, not WARN, because measurement (2026-08-15: 66 feature
  folders, 6 carrying decisions-prose, only 2 live) shows an ERROR is
  satisfiable on this tree today. Sequencing condition: FEAT-2026-0050's
  D1–D3 prose is converted to a `DECISIONS.md` in its own PR, landing before
  this feature's gate runs.
- **owner:** FEAT-2026-0058 drafter
- **status:** `ratified`
- **provenance:** PLAN.md D2

### D3

- **statement:** An override carries provenance, not just a status flip: a
  decision moving to `ratified` from `overridden-pending-signoff` records
  `overridden_from`, `signed_off_by`, and `signed_off_at`, so it stays
  distinguishable from one ratified from the start.
- **owner:** FEAT-2026-0058 drafter
- **status:** `ratified`
- **provenance:** PLAN.md D3

### D4

- **statement:** The close ceremony's contract-change enumeration
  (`closing_requirements.py`) is out of scope for this feature. It becomes
  its own roadmap row once the format has survived a feature.
- **owner:** FEAT-2026-0058 drafter
- **status:** `ratified`
- **provenance:** PLAN.md D4
