---
id: FEAT-2026-0113/G3-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
---

# G3-CLOSE — terminal close

**Context.** Placeholder, scaffolded at draft time so the linter reads gate 3 as
the terminal gate and gate 1 as non-terminal. Gate 2's `plan-next` inserts gate 3's
substantive work units ahead of this entry and sets its real `depends_on`.

**Acceptance criteria.** Drafted by gate 2's `plan-next`. Two hold regardless of
what it drafts:

1. `RETROSPECTIVE.md` carries a `## Cost analysis` heading reconciling the
   feature's spend against `planned_cost_usd` and `events.jsonl`.
2. The terminal verdict answers the question the feature was opened on: whether
   the measured 31 stranded issues are routable after this feature, not merely
   whether new issues carry a severity.

**Do not touch.** To be drafted.

**Verification.** `specfuse lint --closing` exits 0.

**Escalation triggers.** To be drafted.
