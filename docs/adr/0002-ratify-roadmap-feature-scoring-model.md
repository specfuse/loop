# ADR-0002: Ratify the roadmap feature-scoring model

- **Status:** Proposed
- **Date:** 2026-07-22
- **Blocks:** FEAT-2026-0011 (Scoring framework for roadmap features)

## Context

FEAT-2026-0011 will land a reusable scoring stack — `scoring-criteria.md`,
per-quarter `priorities/YYYY-QN.yml` weights, and a rendered
`roadmap-ranked.md` — so every repo inherits the same prioritization discipline.
The build is gated on one decision that must be settled *before* code, not
discovered during it: the exact scoring model. Implementing the artifacts, then
changing the formula or the criteria set, would invalidate every estimate
already captured under the old rubric. FEAT-2026-0011 therefore sits at
`status: blocked` on this ADR until the model is accepted.

The candidate model, carried forward from the feature's roadmap detail:

- **Formula:** `Score = (WCI·CI) + (WBV·BV) + (WTF·TF) − (WCOI·COI) − (WR·R)`,
  normalized to 0–100.
- **Stable per-feature criteria** (objective, data-backed): CI, BV, TF, COI, R.
- **Time-varying weights** (WCI…WR): set per quarter in a `priorities` file,
  decoupled from the per-feature criteria so a strategy shift re-weights the
  backlog without re-rating every feature.

## Decision (proposed)

Adopt the formula above and the five-criterion schema as the ratified scoring
model, with the stable-criteria / time-varying-weights split as a hard
boundary. Criterion *definitions* evolve through a revision log in
`scoring-criteria.md`; the *formula shape* and the *criteria set* change only by
a superseding ADR.

## Consequences

- Once `Accepted`, FEAT-2026-0011 unblocks — a human flips it via
  `/block-feature FEAT-2026-0011 --unblock` (or by editing the roadmap row and
  removing its `**Blocked by.**` block).
- Estimates captured under this model stay comparable across quarters, because
  only weights move; the criteria set is fixed until a superseding ADR.
- If the model is rejected, FEAT-2026-0011's artifacts are redesigned before any
  are built — the cost the `blocked` status exists to avoid.

## Open questions (resolve before accepting)

- Do CI/BV/TF/COI/R each need project-specific sub-criteria in
  `scoring-criteria.md`, or is a single per-criterion definition enough?
- Normalization: linear 0–100, or a percentile against the current backlog?
