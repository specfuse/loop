---
feature_id: FEAT-2026-0007
title: Dispatch cost controls
slug: dispatch-cost-controls
branch: feat/FEAT-2026-0007-dispatch-cost-controls
roadmap_goal: Cut loop dispatch cost via per-WU model alias, effort tier, terseness, and per-gate budget.
autonomy_default: auto
status: active
---

# Plan: Dispatch cost controls

Reduce per-feature dispatch cost without changing the verification-as-oracle
property. Four levers, layered on top of the existing fresh-context-per-attempt
design:

1. **Model family aliases** in WU frontmatter (`sonnet` / `opus` / `haiku`) so
   features inherit the latest model without WU rewrites.
2. **Per-WU effort tier** (`low` … `max`) wired to `claude -p --effort`, with
   tier-gated terseness directive (caveman preamble) on the cheap end.
3. **Retry escalation ladder** — cheap-first; each retry bumps effort one tier
   and loosens the terseness directive. Failure signal = need more compute or
   more reasoning-out-loud, not the same attempt again.
4. **Guardrails** — per-gate cost budget that halts to `blocked_human` mirroring
   `MAX_ATTEMPTS`; failure-note size cap so the retry ladder does not compound
   into runaway prompts.

The mechanics ship in Gate 1; defaults-by-WU-type policy and telemetry + budget
guardrails ship in Gate 2 (drafted by Gate 1's plan-next from real telemetry of
Gate 1's own run).

This file owns the **shape**. WU files own their own status; GATE files own
gate status.

## Scope OUT

- Prompt-caching SDK migration (`cache_control` breakpoints). Gated on a
  separate measurement spike of the `claude -p` CLI's built-in caching.
- Parallel / concurrent WU dispatch. Race conditions on `git`,
  `events.jsonl`, and the working tree need their own design.
- Context pruning / per-WU file allowlist. Needs an agent-contract change.
- Ceremony-WU adaptive strategy (planned vs actual). Depends on telemetry
  from this feature; separate future feature.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0007/T01
        file: WU-01-model-family-alias.md
        depends_on: []
      - id: FEAT-2026-0007/T02
        file: WU-02-effort-field.md
        depends_on: [FEAT-2026-0007/T01]
      - id: FEAT-2026-0007/T03
        file: WU-03-caveman-preamble.md
        depends_on: [FEAT-2026-0007/T02]
      - id: FEAT-2026-0007/T04
        file: WU-04-retry-ladder.md
        depends_on: [FEAT-2026-0007/T02, FEAT-2026-0007/T03]
      - id: FEAT-2026-0007/T05
        file: WU-05-failure-note-cap.md
        depends_on: []
      # --- mandatory closing sequence ---
      - id: FEAT-2026-0007/G1-RETRO
        file: WU-90-gate-1-retrospective.md
        depends_on:
          - FEAT-2026-0007/T01
          - FEAT-2026-0007/T02
          - FEAT-2026-0007/T03
          - FEAT-2026-0007/T04
          - FEAT-2026-0007/T05
      - id: FEAT-2026-0007/G1-LESSONS
        file: WU-91-gate-1-lessons.md
        depends_on: [FEAT-2026-0007/G1-RETRO]
      - id: FEAT-2026-0007/G1-DOCS
        file: WU-92-gate-1-docs.md
        depends_on: [FEAT-2026-0007/G1-LESSONS]
      - id: FEAT-2026-0007/G1-PLAN
        file: WU-93-gate-1-plan-next.md
        depends_on: [FEAT-2026-0007/G1-DOCS]
  - gate: 2
    file: GATE-02.md
    work_units: []     # drafted by Gate 1's plan-next from Gate 1 telemetry
```

## Notes

- Dependencies live here, not in WU frontmatter.
- Gate 1 substantive WUs ship without their own `effort:` declaration — they
  run under current dispatch (no `--effort`) since the mechanic does not exist
  until T02 lands. Gate 2's drafts will declare `effort:` from the outset.
- T05 is independent of T01–T04 and may run in any order within Gate 1.
- Closing-WU numbering follows the 90+ convention so they sort last.
