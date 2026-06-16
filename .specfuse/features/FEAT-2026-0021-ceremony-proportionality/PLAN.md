---
feature_id: FEAT-2026-0021
title: Ceremony proportionality + slim WU template
slug: ceremony-proportionality
branch: feat/FEAT-2026-0021-ceremony-proportionality
roadmap_goal: Make closing-ceremony weight proportional to feature size and slim the WU authoring surface — authoring-layer only, driver (loop.py) frozen, with a captured baseline so savings can be measured before any driver hardening.
autonomy_default: review
status: done
planned_cost_usd: 3.50
---

# Plan: Ceremony proportionality + slim WU template

The methodology's cost is not evenly spent. A baseline over 14 features /
129 costed work units showed **43% of spend on closing ceremony** (60 of
129 WUs), worst on small features (FEAT-2026-0004/0005/0006 were 1–2
substantive WUs each paying a 4-WU close). LEARNINGS[FEAT-2026-0005/G1]
already recorded the rule this feature finally encodes: *"closing-ceremony
weight should scale with feature size."*

This feature lands two authoring-layer levers and **does not touch the
driver** (`loop.py`):

- **T01 — slim the WU authoring surface.** `WU.template.md` carries ~141
  lines of frontmatter notes, most documenting fields the driver writes at
  outcome time. Fold the driver-owned/audit-only fields into one collapsed
  note and nudge the acceptance-criteria guidance toward assertion-shaped,
  machine-checkable statements. Pure-markdown: no `lint_plan.py` change —
  recon showed its two absent-warns (`oracle_env`, `produces_driver_helper`)
  are conditional, content-triggered reviewer hints worth keeping, not
  blanket noise.
- **T02 — ceremony proportionality.** Teach `draft-feature` and document in
  `methodology.md`: a feature whose **planned** substantive WU count is ≤4
  drafts as a single gate with a single terminal `close` — no
  `close-intermediate`, no `plan-next`. The existing `gate_eval` predicate
  still forces the full close when a gate goes off-plan, so the safety net
  is unchanged.

**Recursive dogfood.** This feature has 2 substantive WUs — ≤4 — so it is
drafted exactly as T02's rule prescribes: single gate, single terminal
`close`. The feature that adds proportionality demonstrates it.

This file owns the **shape**. WU files own their own status; the GATE file
owns gate status.

## Scope OUT (deferred to follow-up features)

- **Driver hardening.** No change to `loop.py`, `MODEL_BY_TYPE`,
  `EFFORT_BY_TYPE`, or `gate_eval.py`. Prove the authoring-layer levers
  first; harden winners later.
- **Ceremony *execution* optimization** — reducing cost *per* ceremony WU
  (e.g. `close-intermediate` opus→sonnet, effort tiering, trimming mandated
  retro structure, ceremony-content proportionality). Distinct lever from
  this feature's frequency reduction; doing both at once confounds
  measurement. `G1-CLOSE` captures per-ceremony cost data to scope it.
- **#2 single-planning-pass** and **full spec-first WU template** — both
  methodology-positioning changes requiring their own RFC.
- **#3 parallel / serial dispatch** — wall-clock lever, separate work.
- **Model-tiering (#4)** and **batch-hygiene (#6)** — dropped: already
  covered by `authoring-work-units` §21 (Haiku) and §7 (Hygiene WU)
  respectively; the original framings contradicted existing craft.

## Task graph

```yaml
# Single-gate feature (terminal gate 1), drafted per T02's own ≤4 rule:
#   1-WU terminal close (no close-intermediate, no plan-next).
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0021/T01
        file: WU-01-slim-wu-template.md
        depends_on: []
      - id: FEAT-2026-0021/T02
        file: WU-02-ceremony-proportionality.md
        depends_on: []
      # --- closing sequence: 1-WU terminal close ---
      - id: FEAT-2026-0021/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0021/T01
          - FEAT-2026-0021/T02
```

## Notes

- Single-gate, `autonomy: review` — driver runs to the terminal close, then
  the human reviews the close commit. The feature touches `methodology.md`
  and the `draft-feature` drafter, so a human eyeball at close is warranted.
- T01 and T02 are independent (disjoint file sets), `depends_on: []` each.
- Both WUs are documentation-only (no executable code changes anywhere in
  the feature). Their oracle is structural grep ACs + `lint_plan.py`, not the
  vacuous code-gate pass (LEARNINGS[134-141]). Both are Red-test exempt.

## Planned-cost table

| Gate | WU | type | effort | model | planned_cost_usd |
|------|----|------|--------|-------|------------------|
| 1 | T01 | implementation | low | sonnet | 1.00 |
| 1 | T02 | implementation | low | sonnet | 1.00 |
| 1 | G1-CLOSE | close | high | opus | 1.50 |
| **Total** | | | | | **3.50** |
