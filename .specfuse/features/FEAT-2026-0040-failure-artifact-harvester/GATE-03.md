---
gate: 3
status: open
---

# Gate 3 — drafted by the previous gate's plan-next

## Definition of done

<Written by gate 2's `plan-next` work unit, from that gate's
retrospective and lessons. The methodology's forward-design move: a gate is
detailed only once the gate before it has actually run.>

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Written by gate 2's `plan-next` when it drafts this gate. One requirement is
already known:

- **This gate's central surface cannot be verified in-loop.**
  `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` records that `gh` returns auth errors
  inside `claude -p`, so work units touching the real GitHub issue surface produce
  zero in-loop evidence. Gate 3 was isolated for exactly that reason. At arming,
  confirm each such unit is either designated out-of-loop with an operator-journal
  artifact as its verification proxy, or scoped to a stubbed runner with the real
  invocation named as a deferred criterion. A hedged verdict here is expected; an
  unhedged one claimed on stub evidence is not.
- **Runtime probe (§4) / flag-scope table (§3).** Assess when the gate is drafted —
  neither is knowable before gate 2's plan-next writes the work units.

## Reflection notes

<Written by the human at review time.>
