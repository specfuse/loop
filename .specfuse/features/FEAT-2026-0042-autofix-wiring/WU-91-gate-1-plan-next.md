---
id: FEAT-2026-0042/G1-PLAN
type: plan-next
status: pending
attempts: 0
planned_cost_usd: 6.00
---

# Draft gate 2 — the dial goes live, verified end to end

**Objective.** Draft gate 2's substantive work units: the firing wiring that turns
gate 1's decision layer into an actual automated fix, and the live end-to-end run that
proves it. Insert them into `PLAN.md`'s graph **before** the pre-declared `G2-CLOSE`,
and set gate 2's cost budget.

**Context.** Correlation ID `FEAT-2026-0042/G1-PLAN`. Read `PLAN.md`, `GATE-01.md`,
`GATE-02.md`, and gate 1's `RETROSPECTIVE.md` first. `GATE-02.md` records the intended
shape at draft time; you may revise it after reading the retrospective, but the
constraints below are not yours to revise.

Binding rules apply by reference: `planning-discipline.md`, `authoring-work-units`,
`close-discipline.md`, `result-contract.md`, `never-touch.md`, `correlation-ids.md`,
`operator-escalation.md`.

## Constraints that are not re-decidable at drafting time

**The safety floor.** Auto-merge belongs to
[FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is impossible in this feature.
No drafted work unit may merge a pull request, enable auto-merge, or push to a
protected branch. The ceiling is an unwanted PR on a branch. A draft that widens this
is an escalation to the operator, not a judgement call.

**The live run targets a scratch issue, not a real finding.** Gate 2's end-to-end WU
plants a trivial bug in a scratch issue it creates in this repository, fires against
*that*, and cleans up — so the pull request it produces is disposable by construction.
Firing against a real finding is not gate 2's job.

**`FEAT-2026-0041/T04` is the posture to copy** for the live WU: `unsandboxed: true`
with a real rationale in the frontmatter (the driver refuses the flag without one),
raw stdout+stderr dumped between unforgeable markers rather than classified
(`LEARNINGS [preflight-must-dump-raw]`), cleanup as an explicit acceptance criterion,
and residue from a killed prior attempt reported rather than silently removed.
**Confine the sandbox escape to the single WU that needs it** — every other gate-2 WU
stays sandboxed and forbidden from writing `gh` calls.

**Fix correctness stays unassertable.** Do not draft an acceptance criterion of the
form "the automated fix produces a correct patch." Gate 2 asserts that the *mechanism*
runs and produces a PR, and that the *decision* to run was right. Quality is inherent
and belongs in the close's `## What the loop did NOT verify`.

## Arming discipline — answer, do not inherit

**§4 runtime probe is REQUIRED for gate 2.** Gate 1 answered "not applicable" because
nothing fired and no default changed. Gate 2 introduces firing behaviour behind a dial
that is currently inert, which is precisely the case `planning-discipline.md` §4
exists for. Run the probe and record it in `GATE-02-REVIEW.md` before the gate is
armed. Inheriting gate 1's answer is a defect.

**§2 satisfiability must be re-answered.** Gate 1 was satisfiable by construction
because nothing fired; gate 2's criteria meet a real repository. Check every drafted
criterion against what a dispatched session can actually verify — including that `gh`
works only unsandboxed (`LEARNINGS [gh-claudeP-broken]`, corrected 2026-08-03 by
FEAT-2026-0041/G1-CLOSE).

**Acceptance criteria.**

1. Gate 2's substantive work units are drafted as files in this feature folder and
   listed in `PLAN.md`'s gates graph **before** `FEAT-2026-0042/G2-CLOSE`, with
   `depends_on` edges that reflect real ordering.
2. `G2-CLOSE`'s `depends_on` is updated to name every substantive WU inserted.
3. Each drafted WU carries the five required sections, a `planned_cost_usd`, and —
   for implementation WUs introducing behaviour — a named red test that fails on HEAD
   (`authoring-work-units` §12).
4. Exactly **one** drafted WU carries `unsandboxed: true`, with a rationale naming
   why the sandbox escape is needed. Every other drafted WU is forbidden from writing
   `gh` calls, stated in its escalation triggers.
5. No drafted WU merges a pull request, enables auto-merge, or pushes to a protected
   branch. The safety floor is restated verbatim in `GATE-02.md`.
6. `GATE-02.md` gains its Definition of Done, its `cost_budget_usd` (the sum of
   drafted WU estimates plus one re-attempt of the largest), and the §4 probe result
   or an explicit statement that it is recorded in `GATE-02-REVIEW.md`.
7. `GATE-02-REVIEW.md` exists carrying `open_questions` — a **required explicit
   list**; `[]` means nothing blocks execution, and a missing field is not an empty
   list.
8. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0042-autofix-wiring`
   exits 0 after the drafts land. Quote the output.

**Do not touch.** Gate 1's work units and their deliverables — they are `done`.
`PLAN.md`'s `status` field. `GATE-01.md`. Source files under `specfuse/` — this WU
drafts plans, it does not implement.

**Verification.** The `plannext` gate set for closing WUs, plus criterion 8's lint
run quoted in the result. A drafted gate that does not lint is not armed, it is
blocked.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
firing wiring cannot be drafted without widening the safety floor; the §4 probe shows
the dial's behaviour change reaches surfaces beyond this feature's scope; the live
end-to-end run cannot be bounded to a scratch target (say why — do not draft it
against a real finding); or gate 1's retrospective records something that invalidates
`GATE-02.md`'s intended shape, in which case name the conflict rather than quietly
drafting around it.
