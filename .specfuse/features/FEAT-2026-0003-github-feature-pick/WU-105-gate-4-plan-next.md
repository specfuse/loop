---
id: FEAT-2026-0003/G4-PLAN
type: plan-next
model: claude-opus-4-7
status: pending
attempts: 0
---

# Gate 4 plan-next — terminal-case (feature closure)

**Objective.** Gate 4 is the last gate. There is no further gate to draft. Perform the
terminal-case closure: write a final feature-arc verdict and mark the feature ready for
closure. Draft a gate 5 ONLY if gate-4 evidence shows the roadmap goal is still unmet
AND a bounded gate-5 scope is identifiable (escalation, not default).

**Context.** Read PLAN.md (`roadmap_goal`), `RETROSPECTIVE.md` (all gate sections incl.
gate 4), `SMOKE-INIT-2026-0001-F06.md`, the root `.specfuse/LEARNINGS.md`, and
`GATE-04-REVIEW.md`. Gate 4 fixed the ATX-heading lint gap that was the only mechanism
blocking the roadmap goal at gate-3 close. If T08 landed and the adopted folder now
lints clean, all four pipeline mechanisms (discover / adopt / report-back / lint-clean)
are proven and the feature is done.

**Acceptance criteria — branch A (default; feature closure).**
1. The `## Feature-arc retrospective — FEAT-2026-0003` section in `RETROSPECTIVE.md`
   is updated (or a `## Gate 4 closure` note appended) stating the `roadmap_goal`
   verdict is now MET, citing the gate-4 evidence (adopted folder lints clean; the
   four-mechanism pipeline is whole). If the gate-3 arc retrospective recorded "not
   met; gate 4 follows," update that verdict to "met after gate 4."
2. PLAN.md's `gates:` graph is unchanged (no gate 5 appended).
3. No `GATE-05-REVIEW.md` is written.
4. The RESULT block's `summary` states the feature-arc retrospective is updated and the
   feature is ready for closure, and names that `roadmap_goal` is met.

**Acceptance criteria — branch B (escalation; gate 5 needed).** Use ONLY if gate-4
evidence shows the roadmap goal is still not met AND a bounded gate-5 scope is
identifiable. Then: state the gap precisely in the arc retrospective; append `gate: 5`
(`work_units: []`) to PLAN.md; create `GATE-05.md` and `GATE-05-REVIEW.md` naming the
gap and the human-decision question. A second consecutive escalation gate is a strong
signal the remaining work should be its own feature (`FEAT-2026-0004`) — prefer
proposing that split over a fifth gate unless the scope is genuinely a few WUs.

**Decision rule.** Branch A unless gate-4 evidence explicitly shows the goal unmet AND a
bounded gate-5 scope exists. Perpetually extending a feature corrodes the "feature ends"
contract; gate 4 was already the escalation — a fifth gate needs a very high bar.

**Do not touch.** Any prior gate's status (gates 1-4 settled), source code, secrets,
`.git/`. You write the arc-retrospective update and — only in branch B — `GATE-05.md`,
`GATE-05-REVIEW.md`, and PLAN.md's graph.

**Verification.** The `plannext` gates in `.specfuse/verification.yml` (run
`lint_plan.py` on this feature). Branch A: no new draft WUs to lint; confirm
`RETROSPECTIVE.md` differs from HEAD via the `doc` gate.

**Escalation triggers.** If gate-4 evidence is silent or contradictory on whether the
roadmap goal is met, block — the terminal-case decision is the human's when evidence is
ambiguous. If a gate-5 scope is identifiable but is really its own feature, block and
propose `FEAT-2026-0004` rather than appending a fifth gate.
</content>
