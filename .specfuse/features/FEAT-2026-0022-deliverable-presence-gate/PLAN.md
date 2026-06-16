---
feature_id: FEAT-2026-0022
title: Deliverable-presence gate
slug: deliverable-presence-gate
branch: feat/FEAT-2026-0022-deliverable-presence-gate
roadmap_goal: The driver refuses to commit an implementation WU as `done` when a declared deliverable is absent or empty, or when the WU touched zero files — closing the zero/partial-deliverable hollow-pass class FEAT-2026-0008/0015 left open.
autonomy_default: auto
status: active
planned_cost_usd: 7.00
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Deliverable-presence gate

The direct sequel to FEAT-2026-0008 (driver completeness-guard). That feature
closed the **no-code-written** hollow pass (status-flip-only commits). It did
not close two adjacent shapes, both observed live in FEAT-2026-0020 gate 2
(see LEARNINGS `[FEAT-2026-0020/G2/hollow-pass-presence-gates]`):

- **Zero-deliverable** — T16 (leak-scan-wiring) passed `done` having touched
  zero deliverable files (`files_touched` was just the WU file + events.jsonl),
  at ~$1.48 cost. Its body listed presence checks; none were machine-run.
- **Partial-bundle** — T12 (security-and-conduct) created `SECURITY.md` but not
  the bundled `CODE_OF_CONDUCT.md`, despite its own `test -s` gate. The driver
  accepted because the repo-global `code` gates pass regardless of whether a
  specific WU's files exist.

Both were caught only by a manual `/gate-status` sweep before gate close, then
finished out-of-loop. Filed as loop bug (GitHub issue #41).

Root cause: WU-body Verification/Acceptance presence checks are **advisory** —
the agent self-attests `complete` and the driver accepts after the repo-global
`code` gates pass. This feature makes per-WU deliverable presence a
**machine-enforced** gate the driver runs before accepting `complete`, and adds
a hard escalation when an implementation WU touches zero files.

This file owns the **shape** of the feature: the gate order, which work units
belong to each gate, and the dependency edges between them. It does **not** own
status — each WU file owns its own status, and each GATE file owns its gate's
status.

## Scope OUT

- **Symbol-level presence** (`grep -q <symbol>` inside a produced file).
  v1 enforces file existence + non-empty (`test -s`) only — the two real
  failures (T16, T12) are both file-level. Symbol presence overlaps the
  existing `produces_driver_helper` field (FEAT-2026-0017) and adds parse
  surface for no proven case. A clean follow-up if a symbol-level hollow pass
  is ever observed.
- **Retrofitting `produces:` onto existing WUs.** The 18 existing features'
  WUs and the worked example stay as-is; `produces:` is opt-in. The only hard
  rule applied to all implementation WUs is the empty-files escalation, which
  fires on a signal (`files_touched`) those WUs already produce.
- **Broadening the verification contract** beyond presence. The point is to
  close the documented gap, not redesign `verification.yml`.
- **Cost levers.** This is methodology, not cost control.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0022/T01
        file: WU-01-produces-frontmatter-field.md
        depends_on: []
      - id: FEAT-2026-0022/T02
        file: WU-02-deliverable-presence-gate.md
        depends_on: [FEAT-2026-0022/T01]
      - id: FEAT-2026-0022/T03
        file: WU-03-empty-files-escalation.md
        depends_on: []
      - id: FEAT-2026-0022/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0022/T01
          - FEAT-2026-0022/T02
          - FEAT-2026-0022/T03
```

## Notes

- **Single terminal gate, three independent driver-side guards, one `close`
  ceremony** — same shape as FEAT-2026-0008 (valid for single-gate features
  per FEAT-2026-0005). Each guard touches a different point in the
  parse → squash → advance pipeline.
- **T01** introduces the `produces:` frontmatter field (parse + `WorkUnit`
  field + advisory lint WARN + `WU.template.md` reference). **T02** is the
  presence gate that reads it (depends on T01). **T03** is the empty-files
  escalation, which depends only on `files_touched` and is independent of T01.
- Dependencies live here, not in WU frontmatter.
- Each substantive WU declares `effort: high` and `model: opus`: the changes
  are in the driver's correctness path, and LEARNINGS
  `[FEAT-2026-0017/G1-CLOSE]` documents Sonnet 4.6 hollow-passing this exact
  guard-authoring shape three times. A regression here silently breaks every
  future feature.
- Each substantive WU is red-test-first (`/authoring-work-units` §12): the
  regression named in issue #41 point 3 — "a WU declaring a deliverable but
  producing nothing must NOT reach `done`" — is itself the red test for T02,
  and the zero-files variant the red test for T03.
- **Autonomy `auto`**: the driver runs the gate unattended to a terminal
  outcome. The three red→green tests plus the `code` gate set are the safety
  net on the correctness-path change.
