---
id: FEAT-2026-0104/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
---

# Draft gate 2 — the escalation brief's re-plan option

**Objective.** Draft gate 2's substantive work units and its `feature_oracle`,
using gate 1's evidence to settle the question gate 1 deliberately left open.

**Context.** FEAT-2026-0104/G1-PLAN. `GATE-02.md` currently carries a `TBD`
oracle and one `G2-CLOSE` placeholder; this session replaces both with real
work. The open question, stated in `GATE-02.md`: may the brief's re-plan
option **execute** the re-plan on the operator's yes, or only recommend it and
leave the flip manual. Gate 1's retrospective is the first evidence anyone has
about how in-place re-scope behaves on real spins, and this session is the
first that can answer with data instead of taste.

`[FEAT-2026-0069/G2-CLOSE]` is the sizing precedent and the reason this unit's
floor is what it is: an expensive `plan-next` that ran the real oracle and
pasted the actual failure list into the drafted WU bought a gate that ran
4 units, 4 attempts, 0 failures. Probe, don't guess.

**Acceptance criteria.**

- Gate 2's `feature_oracle` is a real command, red on the tree as it stands
  when this session ends, and it exercises the brief end to end rather than
  asserting on a constructed escalation payload —
  `[FEAT-2026-0108/G1-CLOSE]`'s seam rule applies to this gate too.
- Each drafted WU names a scoped red test that fails on HEAD
  (`/authoring-work-units` §12), or carries an explicit exemption with its
  one-line rationale.
- The execute-versus-recommend question is answered in `GATE-02.md` with the
  gate-1 evidence that settles it cited by name — not deferred a second time.
- `GATE-02-REVIEW.md` is written — the review names the gate being **drafted**, not the one being closed: what gate 1 proved, what the drafted gate 2
  assumes, and anything a reviewer should push back on before arming.
- Drafted WUs land `status: draft`. Arming is the human's, at the gate
  boundary.

**Do not touch.** Gate 1's WU files or its retrospective — this session plans
forward, it does not revise the record. `PLAN.md`'s gate-1 graph. Driver code.

**Verification.** Narrow tier for `plan-next`, plus
`specfuse lint .specfuse/features/FEAT-2026-0104-replan-after-two-failures`
over the drafted files.

**Escalation triggers.** Stop with `status: blocked` if gate 1's evidence is
too thin to settle the execute-versus-recommend question — for instance if no
unit re-planned during gate 1 and no probe can produce one. Drafting a gate on
a guess the plan promised would be evidence-based is worse than halting.
