---
feature_id: FEAT-2026-0015
title: Closing-ceremony restructure + hollow-pass guard
slug: closing-ceremony-restructure
branch: feat/FEAT-2026-0015-closing-ceremony-restructure
roadmap_goal: Restructure the closing-WU contract from 4-WU sequence to 1+2-WU patterns + ship type-keyed hollow-pass guard for the new taxonomy; verdict-state ↔ PLAN-flip coupling, oracle env-parity declaration, state-flip ownership consolidation, and planned-vs-actual cost capture all enforced driver-side. Recursive dogfood: this feature's own terminal close uses the new contract.
autonomy_default: review
status: active
planned_cost_usd: 12.00
---

# Plan: Closing-ceremony restructure + hollow-pass guard

**Subsumes FEAT-2026-0012.** Live evidence from this session
(FEAT-2026-0010 4-WU close = 52% of feature cost; FEAT-2026-0013
$13.50 across 5 dispatches with re-arm rework; FEAT-2026-0014 G1-CLOSE
single combined session = $0.83) showed the 4-WU sequence is wasteful
and the hollow-pass surface for closing WUs is open.

Gate 1 lands MECHANICS (new WU types + driver dispatch + lint +
templates). Gate 2 lands SEMANTICS + AUDIT (verdict-coupling, oracle
env-parity, state-flip consolidation, planned-cost capture, hollow-pass
guard). Recursive dogfood: gate 1's own close uses the OLD 4-WU
sequence (lint grandfathers it with warning); gate 2's terminal close
uses the NEW `close` contract — first production exercise.

This file owns the **shape**. WU files own their own status; GATE files
own gate status.

## Scope OUT

- Backfilling already-closed features (their 4-WU closes stay as
  precedent).
- Changing `plan-next`'s shape — keep its dedicated session.
- Cross-feature cost aggregation / heuristic calibration — that's
  the future analysis path (file as FEAT-2026-0017 or fold into 0011).
- Hard-removing the 4-WU sequence — grandfather it with warnings.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0015/T01
        file: WU-01-driver-wu-types-and-dispatch.md
        depends_on: []
      - id: FEAT-2026-0015/T02
        file: WU-02-lint-new-shapes.md
        depends_on:
          - FEAT-2026-0015/T01
      - id: FEAT-2026-0015/T02H
        file: WU-02H-correlation-id-grammar.md
        depends_on:
          - FEAT-2026-0015/T02
      - id: FEAT-2026-0015/T03
        file: WU-03-templates-and-draft-feature.md
        depends_on:
          - FEAT-2026-0015/T01
          - FEAT-2026-0015/T02
          - FEAT-2026-0015/T02H
      - id: FEAT-2026-0015/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on:
          - FEAT-2026-0015/T01
          - FEAT-2026-0015/T02
          - FEAT-2026-0015/T02H
          - FEAT-2026-0015/T03
      - id: FEAT-2026-0015/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on:
          - FEAT-2026-0015/G1-RETRO
      - id: FEAT-2026-0015/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on:
          - FEAT-2026-0015/G1-LESSONS
      - id: FEAT-2026-0015/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on:
          - FEAT-2026-0015/G1-DOCS
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0015/T04
        file: WU-04-verdict-coupling.md
        depends_on: []
      - id: FEAT-2026-0015/T05
        file: WU-05-oracle-env-parity.md
        depends_on: []
      - id: FEAT-2026-0015/T06
        file: WU-06-state-flip-consolidation.md
        depends_on:
          - FEAT-2026-0015/T04
      - id: FEAT-2026-0015/T07
        file: WU-07-hollow-pass-guard.md
        depends_on:
          - FEAT-2026-0015/T04
          - FEAT-2026-0015/T05
      - id: FEAT-2026-0015/T08
        file: WU-08-planned-cost-capture.md
        depends_on: []
      - id: FEAT-2026-0015/G2-CLOSE
        file: WU-94-gate-2-close.md
        depends_on:
          - FEAT-2026-0015/T04
          - FEAT-2026-0015/T05
          - FEAT-2026-0015/T06
          - FEAT-2026-0015/T07
          - FEAT-2026-0015/T08
```

## Notes

- Multi-gate, `autonomy: review` — driver halts at gate 1 boundary for
  `/arm-gate` to review G2 drafts.
- Gate 1 close: OLD 4-WU sequence (G1-RETRO/LESSONS/DOCS/PLAN). Last
  feature to pay full close tax on this branch.
- Gate 2 close (drafted by G1-PLAN): NEW `close` WU using the contract
  T01-T08 establish. First production dogfood of the new shape.
- Planned-cost field MUST appear in every WU's frontmatter at draft
  time (this feature is the first to dogfood it). Lint doesn't enforce
  yet (T08 ships that); operator writes it manually per the table
  surfaced at /draft-feature time.

## Planned-cost table (dogfood snapshot)

| Gate | WU | type | effort | planned_cost_usd |
|------|----|------|--------|------------------|
| 1 | T01 | implementation | medium | 1.00 |
| 1 | T02 | implementation | medium | 1.00 |
| 1 | T03 | implementation | low | 0.50 |
| 1 | G1-RETRO | retrospective | low | 0.30 |
| 1 | G1-LESSONS | lessons | low | 0.20 |
| 1 | G1-DOCS | docs | low | 0.30 |
| 1 | G1-PLAN | plan-next | high | 1.50 |
| 2 | T04 | implementation | medium | 1.20 |
| 2 | T05 | implementation | medium | 1.00 |
| 2 | T06 | implementation | medium | 1.50 |
| 2 | T07 | implementation | high | 1.50 |
| 2 | T08 | implementation | low | 0.50 |
| 2 | G2-CLOSE | close (new) | high | 1.50 |
| **Total** | | | | **12.00** |
