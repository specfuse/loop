---
id: FEAT-2026-0001/G1-PLAN
type: plan-next
model: claude-opus-4-7
status: pending
attempts: 0
---

# Plan the next gate

**Objective.** Draft the next gate's work units (as `draft`), wire them into PLAN.md's
graph, and write `GATE-NN-REVIEW.md` so the human's review is fast and effective. This
is the one act of genuine forward design in the cycle — hence Opus, and hence it runs
last, after retrospective and lessons, so it can consume them.

**Context.** Read, in this order: PLAN.md (especially `roadmap_goal` and the existing
graph), this feature's `RETROSPECTIVE.md`, and the root `.specfuse/LEARNINGS.md`. The
next gate is the lowest-numbered gate in the graph with an empty `work_units` list.
You draft; you do not arm. A human reviews and arms.

**Acceptance criteria.**
1. The next gate's `WU-*.md` files are created with `status: draft`, each with all five
   mandatory sections, a `type`, and a `model`. Include that gate's own closing
   sequence (retrospective → lessons → docs → plan-next).
2. PLAN.md's graph is updated: the next gate's `work_units` list is populated with the
   drafted units, their files, and dependency edges. Every edge points at a real WU.
3. `GATE-NN-REVIEW.md` is written for the human, weighted toward DOUBT, with:
   - **Decisions & rationale** — the non-obvious calls (WU boundaries, ordering, model
     choices) and which retrospective/lessons entries drove them.
   - **Flagged for attention** — "if you check only three things, check these": where
     you were least certain, every assumption you made to proceed, each WU it maps to.
   - **Roadmap anchor** — how this gate serves `roadmap_goal`; if the retrospective
     implies the goal itself should change, flag it LOUDLY as an escalation rather than
     silently steering toward a new target.
   - **Open questions** — what you could not resolve, each mapped to the WU it affects.
4. Terminal case: if there is NO empty future gate (this was the last gate), draft
   nothing, write a short `GATE-NN-REVIEW.md` stating the feature is complete, set
   PLAN.md `status: done`, update the roadmap row, and emit `feature_complete` in the
   RESULT block.

**Do not touch.** Any non-draft WU, any current/prior gate's status, source code,
secrets, `.git/`. You write next-gate draft WU files, the PLAN.md graph, and the review
artifact — nothing else. The review artifact is advisory and owns no state; PLAN.md owns
the graph and WU files own status.

**Verification.** The `plannext` gates in `.specfuse/verification.yml`, which run
`lint_plan.py` on this feature (drafted WUs valid and dispatchable, dependency edges
resolve, closing sequence present and ordered) and confirm `GATE-NN-REVIEW.md` exists.
A malformed draft fails HERE, where the human is already reviewing.

**Escalation triggers.** If the retrospective implies the feature's goal should change,
or if you cannot draft a coherent next gate without resolving a genuine design question,
emit `status: blocked` with the question rather than drafting around it.
