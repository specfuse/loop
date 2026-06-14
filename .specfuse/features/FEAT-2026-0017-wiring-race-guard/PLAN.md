---
feature_id: FEAT-2026-0017
title: Close-WU wiring-race guard
slug: wiring-race-guard
branch: feat/FEAT-2026-0017-wiring-race-guard
roadmap_goal: Add post-pass driver-state invariant guard for close-type WUs so wiring-race hollow-passes (close passed with `verdict: met` but `fire_terminal_flips` never ran) are caught + retried, not silently shipped.
autonomy_default: auto
status: done
planned_cost_usd: 3.20
---

# Plan: Close-WU wiring-race guard

FEAT-2026-0015/T06 hollow-passed: shipped `fire_terminal_flips` helper +
wired it into the close path, all tests passed, but the driver checked
in-memory `wu.verdict` (loaded by `load_wu` BEFORE dispatch, value
`None`) against agent's `verdict: met` frontmatter write (made DURING
dispatch). Race meant `verdict_permits_terminal_flips` returned False
→ `close_wu_for_terminal` stayed `None` → flips never fired despite
G2-CLOSE passing cleanly with `verdict: met`.

None of today's guards catch this surface:
- Zero-token / files_changed / smoke-import (FEAT-2026-0008): T06 ran
  productively.
- Closing-deliverable guards (FEAT-2026-0015/T07): assert file shape
  post-pass, not driver-state invariants that should fire as
  CONSEQUENCE of the WU.

This file owns the **shape**. WU files own their own status; GATE file
owns gate status.

## Scope OUT

- Re-architecting `WorkUnit` in-memory ↔ frontmatter sync. T06's
  fix (re-read frontmatter post-squash) suffices for the verdict path.
- Wiring-race detection beyond the close path — only `close` WUs
  exhibit the load-vs-dispatch verdict-write gap.
- Detecting agent-introduced bugs unrelated to driver wiring.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0017/T01
        file: WU-01-post-pass-invariant-guard.md
        depends_on: []
      - id: FEAT-2026-0017/T02
        file: WU-02-helper-declaration-field.md
        depends_on: []
      - id: FEAT-2026-0017/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0017/T01
          - FEAT-2026-0017/T02
```

## Notes

- Single-gate terminal feature. Closing shape: new 1-WU `close`
  (per FEAT-2026-0015 contract).
- Recursive dogfood: G1-CLOSE's own pass exercises T01's
  `assert_terminal_flips_fired` against itself. T01 wiring failure
  → guard fires → G1-CLOSE blocks. Closes the wiring-race surface
  recursively.

## Planned-cost table

| Gate | WU | type | effort | planned_cost_usd |
|------|----|------|--------|------------------|
| 1 | T01 | implementation | high | 1.50 |
| 1 | T02 | implementation | low | 0.50 |
| 1 | G1-CLOSE | close | high | 1.20 |
| **Total** | | | | **3.20** |
