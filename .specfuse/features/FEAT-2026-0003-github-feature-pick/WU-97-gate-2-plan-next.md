---
id: FEAT-2026-0003/G2-PLAN
type: plan-next
model: claude-opus-4-7
status: done
attempts: 1
cost_usd: 2.818453
input_tokens: 31
output_tokens: 35861
---

# Plan the next gate (gate 3)

**Objective.** Draft gate 3's work units (as `draft`), wire them into PLAN.md's
graph, and write `GATE-03-REVIEW.md` so the human's review of the final gate is
fast and effective. This is the forward-design move that closes the multi-gate
proof — hence Opus, and hence it runs last, after gate-2 retrospective and
lessons, so it can consume them.

**Context.** Read, in this order: this feature's `PLAN.md` (especially
`roadmap_goal`, the gate skeleton prose on gate 3, and the existing graph), this
feature's `RETROSPECTIVE.md` (both gate-1 and gate-2 sections), the root
`.specfuse/LEARNINGS.md`, and the handoff brief
[`docs/handoff-github-feature-pick.md`](../../../docs/handoff-github-feature-pick.md)
§3–§5. The next gate is gate 3 ("report back + smoke"): a `GitHubBackend(Backend)`
that emits feature start/complete signals the orchestrator can observe (issue
label transitions), selected behind the existing `Backend` seam in
`.specfuse/scripts/loop.py` without forking the driver; then one real
orchestrated feature (`INIT-2026-0001/F06` — example-org/example-app issue #287,
autonomy `review`) is dispatched end-to-end as the smoke test. You draft; you
do not arm.

**Acceptance criteria.**
1. Gate 3's `WU-*.md` files are created with `status: draft`, each with all
   five mandatory sections, a `type`, and a `model`. Include gate 3's own
   closing sequence (retrospective → lessons → docs → plan-next). Apply the
   per-WU craft in `.specfuse/skills/authoring-work-units/SKILL.md`. The smoke
   WU must be a separable WU (offline backend wiring vs live `gh` smoke is the
   right cut, mirroring gate 1's offline-first principle in
   `[FEAT-2026-0003/G1-LESSONS]`).
2. PLAN.md's graph is updated: gate 3's `work_units` list is populated with the
   drafted units, their files, and dependency edges. Every edge points at a
   real WU.
3. `GATE-03-REVIEW.md` is written for the human, weighted toward DOUBT, with:
   - **Decisions & rationale** — the non-obvious calls (Backend seam choice,
     how `gh` labels are transitioned and at what loop event, whether the
     smoke is a separate gate or a final WU in gate 3, model choices) and
     which retrospective/lessons entries drove them.
   - **Flagged for attention** — "if you check only three things, check
     these": where you were least certain, every assumption made to proceed,
     each WU it maps to.
   - **Roadmap anchor** — how gate 3 serves `roadmap_goal` (the loop grinds
     an orchestrator-dispatched feature end-to-end); if the retrospective
     implies the goal itself should change, flag it LOUDLY as an
     escalation.
   - **Open questions** — what you could not resolve, each mapped to the
     WU it affects (e.g. is the smoke target still `INIT-2026-0001/F06` or
     did `example-org/example-app#287` change?).
4. Terminal case: gate 3 is the LAST gate in the skeleton. Gate 3's
   `plan-next` will therefore have no further gate to draft — the WU may
   summarize the feature's overall arc instead, or this PLAN may be extended
   if a follow-on gate is identified. Document the chosen terminal-case
   handling in `GATE-03-REVIEW.md` so the human can decide.

**Do not touch.** Any non-draft WU, any current/prior gate's status, source
code, secrets, `.git/`. You write gate-3 draft WU files, the PLAN.md graph,
and the review artifact — nothing else. The review artifact is advisory and
owns no state; PLAN.md owns the graph and WU files own status.

**Verification.** The `plannext` gates in `.specfuse/verification.yml`, which
run `lint_plan.py` on this feature (drafted WUs valid and dispatchable,
dependency edges resolve, closing sequence present and ordered).

**Escalation triggers.** If the gate-2 retrospective implies the feature's
roadmap goal should change, or if you cannot draft a coherent gate 3 without
resolving a genuine design question (e.g. the `Backend` seam in `loop.py`
turns out to be too narrow for what gate 3 needs to emit), emit `status:
blocked` with the question rather than drafting around it.
