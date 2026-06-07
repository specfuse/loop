---
id: FEAT-2026-0003/G3-PLAN
type: plan-next
model: claude-opus-4-7
status: pending
---

# Gate 3 plan-next — terminal-case handling

**Objective.** Gate 3 is the LAST gate in this feature's
skeleton. There is no further gate to draft. This WU performs
the terminal-case alternative the methodology allows: either
(a) write a **feature-arc retrospective** summarizing the
overall multi-gate proof and explicitly mark the feature ready
for closure, OR (b) if gate 3's retrospective surfaced a clear
follow-on gate (gate 4) needed to make the feature whole, draft
that gate and extend PLAN.md's skeleton — but only if the
follow-on is *required for the roadmap goal*, not merely
*useful*. Choose (a) by default; escalate to (b) only if
gate 3's evidence demands it.

**Context.** Read this feature's `PLAN.md` (especially
`roadmap_goal`), this feature's `RETROSPECTIVE.md` (gate-1,
gate-2, gate-3 sections), the root `.specfuse/LEARNINGS.md`
(all three `[FEAT-2026-0003/...]` entry sets), the gate-3
smoke journal `SMOKE-INIT-2026-0001-F06.md`, and the handoff
brief `docs/handoff-github-feature-pick.md` §6 ("Out of scope
here"). The terminal-case decision the human flagged at gate-3
arming time is in `GATE-03-REVIEW.md` "Terminal-case handling"
— honor it.

The roadmap goal: *"The loop can pick a feature from a target
repo's GitHub issues (specfuse:feature) and grind it through its
gate cycle, alongside today's locally-authored features."* If
the gate-3 smoke proved this, the feature is done. If the smoke
exposed a structural gap (e.g. `GitHubBackend` works but the
adopted-feature dispatch had to be hand-edited to grind, or
report-back labels were observable but the orchestrator's
poller cannot actually consume them), gate 4 might be needed.

**Acceptance criteria — branch A (default; feature closure).**
1. A new top-level section `## Feature-arc retrospective —
   FEAT-2026-0003` is appended to `RETROSPECTIVE.md` (after
   gate 3's section). It synthesizes the full three-gate arc:
   - The read path (gate 1) → write/adopt (gate 2) → report
     back + smoke (gate 3). Did each gate deliver what the
     prior gate's plan-next claimed it would?
   - The multi-gate forward-design move: did `plan-next`
     drafting work? Cite specific examples (a gate-2 review
     question Q4 that became T03 AC 8e; a gate-3 review
     question that became T05/T06/T07's structure).
   - Whether the `roadmap_goal` is met. Cite specific
     evidence from `SMOKE-INIT-2026-0001-F06.md`.
2. PLAN.md's `gates:` graph is unchanged (no new gate
   appended). Gate 3's `work_units` already populated by
   THIS very plan-next WU's earlier write — do not edit
   them here; the graph is settled.
3. A new file `GATE-04-REVIEW.md` is NOT written (branch A
   means no gate 4).
4. The RESULT block's `summary` states "feature-arc
   retrospective written; feature ready for closure" and
   names whether `roadmap_goal` was met.

**Acceptance criteria — branch B (escalation; gate 4 needed).**
Use ONLY if gate-3 retrospective explicitly says the
roadmap goal is not yet met AND a specific bounded gate-4
scope is identifiable.
1. The `## Feature-arc retrospective` section is still written
   (branch-A AC 1 applies) but its `roadmap_goal` verdict is
   "not met; gate 4 follows" with the gap precisely named.
2. A new gate appears in PLAN.md's `gates:` graph: `gate: 4`,
   `file: GATE-04.md`, `work_units: []` (gate 4's own plan-next
   would draft these — recurse the pattern).
3. A new `GATE-04.md` is created (mirroring `GATE-03.md`'s
   shape: gate header, "Definition of done" stub, "Reflection
   notes" stub).
4. A new `GATE-04-REVIEW.md` is created naming the gap and
   the human-decision question: arm gate 4 OR close the
   feature short of the goal.
5. The RESULT block's `summary` states "gate 4 drafted as
   escalation; human decides whether to arm or close short".

**Decision rule.** Branch A unless gate 3's retrospective
contains explicit evidence the roadmap goal is unmet AND a
bounded gate-4 scope is identifiable. Branch B is the
escalation path, not the default; perpetually extending a
feature with new gates corrodes the methodology's "feature
ends" contract.

**Do not touch.** Any prior gate's status (gates 1-2-3 are
settled by this point), source code, secrets, `.git/`. You
write the `## Feature-arc retrospective` section in
`RETROSPECTIVE.md` and — only in branch B — `GATE-04.md`,
`GATE-04-REVIEW.md`, and PLAN.md's graph. Closing-sequence WUs
for gate 4 are NOT drafted here (gate 4's own plan-next would
draft them — same recursive pattern as gates 1-2-3).

**Verification.** The `plannext` gates in
`.specfuse/verification.yml` (run `lint_plan.py` on this
feature). Branch A: no new draft WUs to lint. Branch B: gate
4 must have `work_units: []` (empty list is valid; the linter
admits it since gate-3's empty list was admitted in the
pre-gate-3 plan). Branch A also: verify `RETROSPECTIVE.md`
differs from HEAD via the `doc` gate.

**Escalation triggers.**
- The gate-3 retrospective is silent or contradictory on
  whether the roadmap goal was met. Block — the terminal-case
  decision is the human's, not the agent's, when evidence is
  ambiguous.
- A gate-4 scope is identifiable but is large enough to be its
  own feature (FEAT-2026-0004) rather than a fourth gate of
  this one. Block and propose splitting — a feature with four
  gates the size of gates 1-3 is at the upper bound of what's
  manageable; a fifth gate or sixth is the wrong shape.
- The gate-3 smoke surfaced a methodology-level issue (not a
  feature-level issue) — e.g. `plan-next` itself doesn't work
  when context drift compounds over three gates. Block per
  `[FEAT-2026-0003/G3-LESSONS]`'s methodology-escalation
  posture (if that lesson was promoted).
