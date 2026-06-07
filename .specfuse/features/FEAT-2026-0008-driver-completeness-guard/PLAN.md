---
feature_id: FEAT-2026-0008
title: Driver completeness-guard
slug: driver-completeness-guard
branch: feat/FEAT-2026-0008-driver-completeness-guard
roadmap_goal: The driver refuses to commit a WU as `done` when the dispatched session produced no real work, so hollow passes (status-flip-only commits) cannot land.
autonomy_default: review
status: done
---

# Plan: Driver completeness-guard

Three driver-side checks that close the hollow-pass gap discovered by
FEAT-2026-0007 (T04, T08H, T08 all reported `status: done` while landing no
production code). Per the FEAT-2026-0007 verdict's mandatory recommendation,
any **one** of the three would have caught all three failures; **all three
together** close the gap structurally.

Agent-side safeguards (smoke-import AC, completeness escalation triggers) were
added to FEAT-2026-0007 LEARNINGS and bypassed entirely when T08H's session
produced 0 tokens. Agent-side rules require an agent session that runs; this
feature is the driver-side enforcement layer that does not.

This file owns the **shape**. WU files own their own status; GATE files own
gate status.

## Scope OUT

- Re-landing the deferred FEAT-2026-0007 work (retry escalation ladder T04,
  telemetry extension T08, original T08H spec). That belongs in
  FEAT-2026-0009 or later, **after** this feature's guards exist so the
  reland cannot hollow-pass a third time.
- Any cost-control lever. FEAT-2026-0007 shipped four; this feature is
  methodology, not cost.
- Verification gate redesign beyond the three named checks. The point is to
  close the documented gap, not to broaden the verification contract.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0008/T01
        file: WU-01-zero-token-attempt-guard.md
        depends_on: []
      - id: FEAT-2026-0008/T02
        file: WU-02-files-changed-diff-guard.md
        depends_on: []
      - id: FEAT-2026-0008/T03
        file: WU-03-verification-smoke-runner.md
        depends_on: []
      - id: FEAT-2026-0008/G1-CLOSE
        file: WU-90-close.md
        depends_on:
          - FEAT-2026-0008/T01
          - FEAT-2026-0008/T02
          - FEAT-2026-0008/T03
```

## Notes

- Single gate, three independent substantive WUs, one `close` ceremony (valid
  for single-gate features per FEAT-2026-0005). Each guard touches a
  different point in the dispatch / squash / advance pipeline and can land in
  any order within Gate 1.
- Dependencies live here, not in WU frontmatter.
- Each substantive WU declares `effort: high` because the changes are in the
  driver's correctness path and a regression there silently breaks every
  future feature.
- Each substantive WU includes explicit existence-check verification AND a
  completeness escalation trigger per FEAT-2026-0007/G1-LESSONS entries
  — belt-and-suspenders, even though this feature's whole point is to make
  those agent-side checks no longer load-bearing.
