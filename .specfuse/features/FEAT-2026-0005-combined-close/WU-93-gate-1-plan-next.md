---
id: FEAT-2026-0005/G1-PLAN
type: plan-next
model: claude-opus-4-7
status: pending
attempts: 0
---

# Gate 1 plan-next — terminal case (single-gate feature closure)

**Objective.** Single-gate feature: no next gate to draft. Write the feature-arc verdict
and mark the feature ready for closure. Draft a gate 2 ONLY if gate-1 evidence shows the
roadmap goal is unmet AND a bounded gate-2 scope is identifiable (escalation, not default).

**Context.** Read PLAN.md (`roadmap_goal`), this feature's `RETROSPECTIVE.md`, the root
`.specfuse/LEARNINGS.md`. The roadmap goal: *"A single-gate feature may close with one
`close` work unit instead of the four-WU sequence."* If T01 landed (the `close` type
implemented, lint accepts single-gate / rejects multi-gate, tests green), the goal is met.

**Acceptance criteria — branch A (default; closure).**
1. A `## Feature-arc retrospective — FEAT-2026-0005` section is appended to
   `RETROSPECTIVE.md` stating whether `roadmap_goal` is met, citing T01's evidence.
2. PLAN.md's `gates:` graph is unchanged (no gate 2 appended).
3. No `GATE-02-REVIEW.md` is written.
4. The RESULT block `summary` states the feature is ready for closure and whether the goal
   is met.

**Acceptance criteria — branch B (escalation; gate 2 needed).** Use ONLY if gate-1
evidence shows the goal unmet AND a bounded gate-2 scope exists. Then: state the gap in the
arc retrospective; append `gate: 2` (`work_units: []`) to PLAN.md; create `GATE-02.md` and
`GATE-02-REVIEW.md` naming the gap and the human-decision question.

**Decision rule.** Branch A unless gate-1 evidence explicitly shows the goal unmet AND a
bounded gate-2 scope exists.

**Do not touch.** Any prior gate's status, source code, secrets, `.git/`. Write the
arc-retrospective update and — only in branch B — `GATE-02.md`, `GATE-02-REVIEW.md`, and
PLAN.md's graph.

**Verification.** The `plannext` gates (`lint_plan.py` on this feature). Branch A: confirm
`RETROSPECTIVE.md` differs from HEAD via the `doc` gate.

**Escalation triggers.** If gate-1 evidence is silent or contradictory on whether the goal
is met, block — the terminal decision is the human's when evidence is ambiguous.
</content>
