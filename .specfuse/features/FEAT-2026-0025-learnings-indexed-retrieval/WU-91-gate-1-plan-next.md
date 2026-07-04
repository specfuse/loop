---
id: FEAT-2026-0025/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 1.00
---

# Gate 1 plan-next — draft gate 2 (wire the planning consumers)

**Objective.** Author gate 2's substantive WU files (wiring the planning consumers
to the gate-1 retrieval primitive), add them to `PLAN.md`'s gate-2 `work_units`
graph with `depends_on`, set the terminal `G2-CLOSE` `depends_on`, and write
`GATE-02-REVIEW.md`. Leave every drafted WU `status: draft` (unarmed).

**Context.** This is `FEAT-2026-0025/G1-PLAN`, following G1-CLOSE-INTERMEDIATE. Gate
1 shipped `learnings_query` (`parse_entries` + `rank` + CLI + `should_load_whole`
threshold). Gate 2's job: make the planning consumers load the relevant LEARNINGS
slice via that tool instead of the whole file. Read PLAN.md's `roadmap_goal`, the
gate-1 RETROSPECTIVE, and the four consumer skills
(`.specfuse/skills/{draft-feature,pick-feature,learnings-suggest,authoring-work-units}/SKILL.md`
— note the actual consumers are draft-feature, pick-feature, plan-next dispatch,
and authoring-work-units) to scope the WUs against real files. Reference the binding
rules under `.specfuse/rules/`; honor them.

**Acceptance criteria.**

1. Gate 2's substantive WU files are authored in this feature folder in dispatchable
   form (five sections, `status: draft`, `planned_cost_usd`), each tracing to the
   gate-2 definition of done in `GATE-02.md`. Likely shape (the plan-next author
   refines against the real skill files): one WU per consumer, or one consumer-wiring
   WU plus a `build_query(feature_dir)` helper WU if query assembly belongs
   consumer-side (the gate-1 retro's recommendation decides this).
2. `PLAN.md`'s gate-2 `work_units` list is filled with the drafted WUs' ids/files
   and `depends_on`; the terminal `G2-CLOSE` (`close`) `depends_on` all gate-2
   substantive WUs.
3. **`GATE-02-REVIEW.md`** written — weighted toward doubt: the decisions + rationale
   (which consumers, query-assembly location, threshold value in practice), open
   risks (relevance quality: could slicing drop a lesson the planner needed?), and a
   verification story for each drafted WU.
4. Each gate-2 WU that introduces new behavior carries a red-test-first acceptance
   bullet (or an explicit §12 exemption); the terminal `G2-CLOSE` carries the
   `## Cost analysis` + `## What the loop did NOT verify` AC bullets.
5. **No arming** — gate 2's WUs stay `draft`; the human reviews `GATE-02-REVIEW.md`
   and arms them (flips to `pending`) at the gate boundary.

**Do not touch.** Gate 1's WUs and `GATE-01.md` status (driver owns gate flips);
the consumer skill files themselves (gate 2's WUs edit them — plan-next only DRAFTS
the WUs, it does not implement them); `.git/`, secrets. May create gate-2 WU files,
`GATE-02-REVIEW.md`, and edit `PLAN.md`'s gate-2 graph. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: plan-next`,
plus `assert_next_gate_drafted_or_terminal` (gate 2's WUs exist and are drafted) and
the lint of the updated `PLAN.md` graph.

**Escalation triggers.** If the consumer skills' current LEARNINGS-loading mechanism
cannot be located (so gate-2 WUs cannot name real files to edit), emit
`status: blocked` naming the gap rather than drafting against invented surfaces.
Blocked is respectable (`result-contract.md` rule 4).
