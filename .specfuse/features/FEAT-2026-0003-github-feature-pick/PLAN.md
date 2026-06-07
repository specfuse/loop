---
feature_id: FEAT-2026-0003
title: GitHub feature-pick for the loop
slug: github-feature-pick
branch: feat/FEAT-2026-0003-github-feature-pick
roadmap_goal: The loop can pick a feature from a target repo's GitHub issues (specfuse:feature) and grind it through its gate cycle, alongside today's locally-authored features.
autonomy_default: review
status: active
---

# Plan: GitHub feature-pick for the loop

Teach the loop to adopt a *feature* from GitHub issues — so an orchestrator can
dispatch a feature to a component repo and that component's loop grinds it —
in addition to today's locally-authored `.specfuse/features/` flow. An
orchestrator-dispatched feature *is* a loop feature; only the ID namespace
differs (`INIT-…/FNN` orchestrated vs `FEAT-…` component-local). The full
brief is [`docs/handoff-github-feature-pick.md`](../../../docs/handoff-github-feature-pick.md).

This build is itself the loop's **first real multi-gate feature** — run through
the gate cycle to dogfood the methodology and prove `plan-next` drafts a real
next gate. Only gate 1 is detailed here; gate 1's `plan-next` drafts gate 2,
gate 2's drafts gate 3 — that forward-design move is the thing being proven.

This file owns the **shape**: gate order, WU membership, dependency edges. WU
files own their own status; GATE files own gate status.

## Gate skeleton (human-facing; the graph below is authoritative)

- **Gate 1 — the read path.** The ID grammar admits orchestrated
  `INIT-…/FNN[/TNN]` IDs (rule + linter + tests), and a discovery script lists a
  target repo's `specfuse:feature` issues as feature candidates, unit-tested
  against a stubbed `gh`. Foundational, fully offline-testable.
- **Gate 2 — the write path (adopt).** A picked issue becomes a dispatchable
  feature folder seeded from the issue body's five sections, recording the
  source issue URL and the `initiative:` label. A scaffolding script plus an
  interactive pick-and-adopt skill. *(Drafted by gate 1's plan-next.)*
- **Gate 3 — report back + smoke.** A `GitHubBackend(Backend)` emits feature
  start/complete signals the orchestrator can observe (issue label transitions),
  selected behind the existing `Backend` seam without forking the driver; then
  one real orchestrated feature (`INIT-2026-0001/F06`, RestoManagerApp/Backend
  #287, autonomy `review`) is dispatched end-to-end as the smoke test.
  *(Drafted by gate 2's plan-next.)*

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0003/T01
        file: WU-01-correlation-id-grammar.md
        depends_on: []
      - id: FEAT-2026-0003/T02
        file: WU-02-gh-feature-discovery.md
        depends_on: []
      - id: FEAT-2026-0003/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on: [FEAT-2026-0003/T01, FEAT-2026-0003/T02]
      - id: FEAT-2026-0003/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [FEAT-2026-0003/G1-RETRO]
      - id: FEAT-2026-0003/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [FEAT-2026-0003/G1-LESSONS]
      - id: FEAT-2026-0003/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [FEAT-2026-0003/G1-DOCS]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0003/T03
        file: WU-03-adopt-script.md
        depends_on: []
      - id: FEAT-2026-0003/T04
        file: WU-04-adopt-skill.md
        depends_on: [FEAT-2026-0003/T03]
      - id: FEAT-2026-0003/G2-RETRO
        file: WU-94-gate-2-retrospective.md
        depends_on: [FEAT-2026-0003/T03, FEAT-2026-0003/T04]
      - id: FEAT-2026-0003/G2-LESSONS
        file: WU-95-gate-2-lessons.md
        depends_on: [FEAT-2026-0003/G2-RETRO]
      - id: FEAT-2026-0003/G2-DOCS
        file: WU-96-gate-2-docs.md
        depends_on: [FEAT-2026-0003/G2-LESSONS]
      - id: FEAT-2026-0003/G2-PLAN
        file: WU-97-gate-2-plan-next.md
        depends_on: [FEAT-2026-0003/G2-DOCS]
  - gate: 3
    file: GATE-03.md
    work_units:
      - id: FEAT-2026-0003/T05
        file: WU-05-backend-lifecycle-hooks.md
        depends_on: []
      - id: FEAT-2026-0003/T06
        file: WU-06-github-backend.md
        depends_on: [FEAT-2026-0003/T05]
      - id: FEAT-2026-0003/T07
        file: WU-07-smoke-end-to-end.md
        depends_on: [FEAT-2026-0003/T06]
      - id: FEAT-2026-0003/G3-RETRO
        file: WU-98-gate-3-retrospective.md
        depends_on: [FEAT-2026-0003/T05, FEAT-2026-0003/T06, FEAT-2026-0003/T07]
      - id: FEAT-2026-0003/G3-LESSONS
        file: WU-99-gate-3-lessons.md
        depends_on: [FEAT-2026-0003/G3-RETRO]
      - id: FEAT-2026-0003/G3-DOCS
        file: WU-100-gate-3-docs.md
        depends_on: [FEAT-2026-0003/G3-LESSONS]
      - id: FEAT-2026-0003/G3-PLAN
        file: WU-101-gate-3-plan-next.md
        depends_on: [FEAT-2026-0003/G3-DOCS]
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- T01 and T02 have no edge between them: the grammar change and the discovery
  script are independent and may run in either order (the driver runs them
  sequentially in v1, but neither blocks the other).
- WU file numbers track the correlation sub-ID (`WU-01` ↔ `/T01`); closing units
  use the reserved 90+ range so they sort last.
</content>
</invoke>
