---
id: FEAT-2026-0007/G1-PLAN
type: plan-next
model: claude-opus-4-7
status: pending
attempts: 0
---

# Plan the next gate

**Objective.** Draft Gate 2's work units (as `draft`), wire them into PLAN.md's graph,
and write `GATE-02-REVIEW.md` so the human's review is fast and effective. Gate 2's
scope is fixed: defaults-by-WU-type policy (with Haiku guidance), per-gate cost budget,
and telemetry extension. The forward-design work here is the per-WU shape, model
selection, dependency edges, and acceptance criteria — informed by Gate 1's
retrospective and lessons.

**Context.** Read, in this order: PLAN.md (especially `roadmap_goal`, the Scope OUT
section, and Gate 2's empty `work_units` list), this feature's `RETROSPECTIVE.md`, and
the root `.specfuse/LEARNINGS.md`. The next gate is Gate 2 (already declared empty in
the graph). You draft; you do not arm. A human reviews and arms.

**Acceptance criteria.**
1. Gate 2's three substantive WU files are created with `status: draft`, each with all
   five mandatory sections, a `type`, a `model`, and an `effort:` declaration (Gate 2
   ships after the effort mechanic, so it must use it). Suggested IDs: `T06`
   (defaults + Haiku policy), `T07` (per-gate cost budget), `T08` (telemetry extension
   incl. `cache_hit_rate`). Include Gate 2's own closing sequence (retrospective →
   lessons → docs → plan-next) with WU-94 through WU-97 (the next available numbers in
   the 90+ range).
2. PLAN.md's graph is updated: Gate 2's `work_units` list is populated with the drafted
   units, their files, and dependency edges. Every edge points at a real WU.
3. `GATE-02-REVIEW.md` is written for the human, weighted toward DOUBT, with:
   - **Decisions & rationale** — the non-obvious calls (T06 default tables, T07 budget
     semantics on overshoot, T08 cache_hit_rate denominator) and which retrospective /
     lessons entries drove them.
   - **Flagged for attention** — "if you check only three things, check these": where
     you were least certain (e.g. mid-gate halt vs finish-current-WU on budget
     overshoot), every assumption you made, each WU it maps to.
   - **Roadmap anchor** — how Gate 2 serves `roadmap_goal`; if the retrospective
     implies the goal itself should change, flag it LOUDLY as escalation.
   - **Open questions** — what you could not resolve, each mapped to the WU it affects
     (e.g. cache_hit_rate formula needs first-telemetry data to confirm denominator).
4. Terminal case: not applicable — Gate 2 exists. Do not write the terminal feature-arc
   verdict here; that's Gate 2's plan-next concern.

**Do not touch.** Any non-draft WU, any current/prior gate's status, source code,
secrets, `.git/`. You write Gate 2 draft WU files, the PLAN.md graph, and the review
artifact — nothing else.

**Verification.** The `plannext` gates in `.specfuse/verification.yml`, which run
`lint_plan.py` on this feature (drafted WUs valid and dispatchable, dependency edges
resolve, closing sequence present and ordered) and confirm `GATE-02-REVIEW.md` exists.

**Escalation triggers.** If Gate 1's retrospective surfaces a fundamental flaw in Gate
2's stated scope (e.g. telemetry shape must change before defaults-by-type can be
applied, forcing a re-ordering of T06/T08), draft what is coherent and flag the
ordering question loudly in `GATE-02-REVIEW.md` rather than silently reshaping scope.
