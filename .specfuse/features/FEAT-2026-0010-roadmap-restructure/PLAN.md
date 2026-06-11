---
feature_id: FEAT-2026-0010
title: Roadmap restructure - add and archive
slug: roadmap-restructure
branch: feat/FEAT-2026-0010-roadmap-restructure
roadmap_goal: .specfuse/roadmap.md carries detail sections only for planned/active features; done/abandoned details live in .specfuse/roadmap-archive.md; roadmap-add and roadmap-archive skills exist; current done features (0003..0008) migrated.
autonomy_default: review
status: planned
---

# Plan: Roadmap restructure - add and archive

Split the roadmap so the hot file carries only `planned` and `active` detail
sections; done and abandoned detail sections live in a new
`.specfuse/roadmap-archive.md` and are reached from the main table via a new
`Detail` back-link column. Two new skills (`roadmap-add`,
`roadmap-archive`) replace today's hand-edit-only flow. Dogfood by migrating
FEAT-2026-0003..0008 in the same gate.

This is the structural foundation for FEAT-2026-0011 (scoring framework),
which adds new columns and rich per-feature scoring data the table cannot
carry while it is still hand-edited.

This file owns the **shape**. WU files own their own status; GATE files own
gate status.

## Scope OUT

- New roadmap columns (CI / BV / TF / R / Budget / Score) — those belong to
  FEAT-2026-0011.
- `scoring-criteria.md`, `priorities/<period>.yml`, weighting, scoring
  formula, `roadmap-rank` skill, `roadmap-estimate` skill — all FEAT-2026-0011.
- Auto-archive hook in `loop.py` at PLAN status flip — manual-first cut;
  auto follow-up after this feature lands.
- Orchestrator-level cross-repo aggregation — deferred to a future feature
  once the orchestrator exists.
- Rewriting the prose content of any feature's detail section (Why, Goal,
  Benefits, Verification) — only split, never re-author.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0010/T01
        file: WU-01-archive-scaffold.md
        depends_on: []
      - id: FEAT-2026-0010/T02
        file: WU-02-roadmap-archive-skill.md
        depends_on:
          - FEAT-2026-0010/T01
      - id: FEAT-2026-0010/T03
        file: WU-03-roadmap-add-skill.md
        depends_on:
          - FEAT-2026-0010/T01
      - id: FEAT-2026-0010/T04
        file: WU-04-migrate-done-features.md
        depends_on:
          - FEAT-2026-0010/T02
      - id: FEAT-2026-0010/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on:
          - FEAT-2026-0010/T01
          - FEAT-2026-0010/T02
          - FEAT-2026-0010/T03
          - FEAT-2026-0010/T04
      - id: FEAT-2026-0010/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on:
          - FEAT-2026-0010/G1-RETRO
      - id: FEAT-2026-0010/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on:
          - FEAT-2026-0010/G1-LESSONS
      - id: FEAT-2026-0010/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on:
          - FEAT-2026-0010/G1-DOCS
  - gate: 2
    file: GATE-02.md
    work_units: []
```

## Notes

- Gate 1 lands the mechanics (archive file, table schema, two skills) and
  migrates the existing 6 done features as the first dogfood pass. Gate 2 is
  reserved for the driver auto-archive hook and any back-link rendering
  polish that Gate 1's retrospective surfaces; its WUs are detailed by
  `G1-PLAN`. Gate 2 may collapse to nothing if Gate 1 closes everything
  required — that is a legitimate plan-next outcome.
- Dependencies live here, not in WU frontmatter.
- T01 is intentionally low-effort — pure file creation and a table-schema
  column add. T02 and T03 are medium because both ship interactive skills
  with self-tests. T04 is low again because the work is mechanical
  invocation of the T02 skill against six known IDs.
- `Detail` column convention: cell is `—` for `planned`/`active` rows and
  for any `done`/`abandoned` row whose detail still lives inline; cell
  becomes `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)` once the section
  has been moved to the archive. T01 documents this in the archive file's
  `## Conventions` section.
