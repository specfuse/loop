---
gate: 1
status: open
---

# Gate 1 — Driver completeness-guard

## Definition of done

- A 0-input-token attempt is treated as a failed attempt and re-dispatched
  rather than committed as `done` (T01).
- When a WU's RESULT block declares `files_changed: [paths]`, the driver
  verifies each path differs from `HEAD` before squashing; an unchanged path
  triggers re-dispatch (T02).
- When a WU's Verification section names one or more
  `python3 -c "from X import Y"` smoke-import commands, the driver executes
  them post-squash, before advancing dependents; a non-zero exit fails the
  WU (T03).
- All three substantive WUs are `done`.
- `RETROSPECTIVE.md` exists; durable lessons promoted to
  `.specfuse/LEARNINGS.md`; docs and roadmap reconciled; terminal
  feature-arc verdict written.

## Reflection notes

<Written by the human at review time.>
