---
feature_id: FEAT-2026-0025
title: LEARNINGS indexed retrieval (bound planning-context load)
slug: learnings-indexed-retrieval
branch: feat/FEAT-2026-0025-learnings-indexed-retrieval
roadmap_goal: Indexed retrieval over .specfuse/LEARNINGS.md so planning consumers load only the entries relevant to the feature being planned, instead of the whole (now ~1700-line) file — bounding planning-context cost as the repo scales.
autonomy_default: review
status: active
planned_cost_usd: 8.95
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: LEARNINGS indexed retrieval

`.specfuse/LEARNINGS.md` is loaded **whole** into every planning session
(`/draft-feature`, `/pick-feature`, `plan-next`, `/authoring-work-units`). It is
append-only and now ~1700 lines / ~100 entries, growing ~4 entries per feature.
Every planning session pays that full token cost even though only a handful of
entries are relevant to the feature at hand.

**Scope — this feature builds only goal (4) of roadmap FEAT-2026-0025.** Goals
(1)–(3) — the `/learnings-curate` skill, retirement into `LEARNINGS-archive.md`,
and rule promotion into `.specfuse/rules/*.md` — are **already shipped** (the
`learnings-curate` skill exists and executes merge / retire / promote). Curation
*compacts* the file; it does not make consumers load a *slice*. This feature adds
the missing retrieval half: given the feature being planned, return only the
relevant LEARNINGS entries.

**Decisions (set at draft time):**
- **BM25 / tf-idf ranking, stdlib-only.** Deterministic keyword-relevance over
  entry text; no external dependency, no persisted index to go stale. The query
  is assembled from the feature's goal + slug + touched paths (assembled on the
  consumer side, gate 2).
- **Threshold fallback.** Below a configurable entry-count threshold the tool
  emits a `load-whole` signal, so small projects and early-stage repos are
  unaffected — slicing only kicks in once the file is big enough to matter.
- **Two gates.** Gate 1 builds and tests the retrieval primitive in isolation
  (fully in-loop verifiable). Gate 2 wires the four planning consumers to use it
  — the cross-cutting "change how every planning session loads context" milestone,
  which gets its own human review-and-arm checkpoint (autonomy `review`).
- **Out of scope:** re-building any of goals (1)–(3); a persisted/on-disk index
  (recompute per query — the file is small enough); semantic-embedding retrieval
  (stdlib BM25 only); actually running `/learnings-curate` to compact the file
  (an operator action, orthogonal to retrieval).

This file owns the **shape**. Only gate 1 is detailed; gate 2 is drafted by gate 1's
`plan-next` when gate 1 completes.

## Forward arc (gate 2 drafted by plan-next)

- **Gate 2 — wire the planning consumers (terminal).** Update `/draft-feature`,
  `/pick-feature`, `plan-next`, and `/authoring-work-units` to build a query from
  the feature context and load the relevant LEARNINGS slice via `learnings_query`
  instead of the whole file, honoring the load-whole threshold fallback. Includes
  the query-assembly helper (`build_query(feature_dir)`) if gate 1's retro shows
  it belongs consumer-side.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0025/T01
        file: WU-01-entry-parser-bm25-ranker.md
        depends_on: []
      - id: FEAT-2026-0025/T02
        file: WU-02-cli-and-threshold.md
        depends_on: [FEAT-2026-0025/T01]
      - id: FEAT-2026-0025/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0025/T01
          - FEAT-2026-0025/T02
      - id: FEAT-2026-0025/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0025/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    # Gate 2 wires the planning consumers to the gate-1 primitive. Drafted by
    # gate 1's plan-next (G1-PLAN); left `draft` for human review-and-arm.
    # Scope correction (see GATE-02-REVIEW.md): of the four consumers named in
    # roadmap_goal, only draft-feature and pick-feature actually load
    # LEARNINGS.md WHOLE at runtime. authoring-work-units is a static
    # DISTILLATION of LEARNINGS (no runtime load); plan-next has no durable
    # skill file (its LEARNINGS reads are authored per-WU). So gate 2 wires the
    # two real load-whole consumers; the other two are documented as out of
    # scope rather than drafted against invented surfaces.
    work_units:
      - id: FEAT-2026-0025/T03
        file: WU-03-wire-draft-feature.md
        depends_on: []
      - id: FEAT-2026-0025/T04
        file: WU-04-wire-pick-feature.md
        depends_on: []
      - id: FEAT-2026-0025/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on:
          - FEAT-2026-0025/T03
          - FEAT-2026-0025/T04
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- Gate 1 is fully in-loop verifiable: the parser + ranker + CLI + threshold are
  pure-Python with unit tests; no cross-repo or real-system dependency.
