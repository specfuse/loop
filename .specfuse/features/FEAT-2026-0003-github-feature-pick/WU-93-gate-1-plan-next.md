---
id: FEAT-2026-0003/G1-PLAN
type: plan-next
model: claude-opus-4-7
status: done
attempts: 1
cost_usd: 2.920458
input_tokens: 30
output_tokens: 37976
---

# Plan the next gate

**Objective.** Draft gate 2's work units (as `draft`), wire them into PLAN.md's
graph, and write `GATE-02-REVIEW.md` so the human's review is fast and effective.
This is the one act of genuine forward design in the cycle — hence Opus, and hence
it runs last, after retrospective and lessons, so it can consume them.

**Context.** Read, in this order: PLAN.md (especially `roadmap_goal`, the gate
skeleton prose, and the existing graph), this feature's `RETROSPECTIVE.md`, the root
`.specfuse/LEARNINGS.md`, and the brief
[`docs/handoff-github-feature-pick.md`](../../../docs/handoff-github-feature-pick.md)
§3–§4. The next gate is gate 2 ("the write path — adopt"): turn a picked
`specfuse:feature` issue into a dispatchable feature folder seeded from the issue
body's five sections, recording the source issue URL and `initiative:` label, via a
scaffolding **script plus an interactive pick-and-adopt skill** (the human chose
script+skill). You draft; you do not arm. A human reviews and arms.

**Acceptance criteria.**
1. Gate 2's `WU-*.md` files are created with `status: draft`, each with all five
   mandatory sections, a `type`, and a `model`. Include gate 2's own closing
   sequence (retrospective → lessons → docs → plan-next). Apply the per-WU craft in
   `.specfuse/skills/authoring-work-units/SKILL.md`.
2. PLAN.md's graph is updated: gate 2's `work_units` list is populated with the
   drafted units, their files, and dependency edges. Every edge points at a real WU.
   Leave gate 3's `work_units` empty (it is gate 2's plan-next that drafts gate 3).
3. `GATE-02-REVIEW.md` is written for the human, weighted toward DOUBT, with:
   - **Decisions & rationale** — the non-obvious calls (WU boundaries, the
     script/skill split, ordering, model choices) and which retrospective/lessons
     entries drove them.
   - **Flagged for attention** — "if you check only three things, check these":
     where you were least certain, every assumption made to proceed, each WU it maps
     to.
   - **Roadmap anchor** — how gate 2 serves `roadmap_goal`; if the retrospective
     implies the goal itself should change, flag it LOUDLY as an escalation.
   - **Open questions** — what you could not resolve, each mapped to the WU it
     affects.
4. Terminal case does not apply here (gate 3 exists in the skeleton); draft gate 2
   normally.

**Do not touch.** Any non-draft WU, any current/prior gate's status, source code,
secrets, `.git/`. You write gate-2 draft WU files, the PLAN.md graph, and the review
artifact — nothing else. The review artifact is advisory and owns no state; PLAN.md
owns the graph and WU files own status.

**Verification.** The `plannext` gates in `.specfuse/verification.yml`, which run
`lint_plan.py` on this feature (drafted WUs valid and dispatchable, dependency edges
resolve, closing sequence present and ordered). A malformed draft fails HERE, where
the human is already reviewing.

**Escalation triggers.** If the retrospective implies the feature's goal should
change, or if you cannot draft a coherent gate 2 without resolving a genuine design
question, emit `status: blocked` with the question rather than drafting around it.
</content>
