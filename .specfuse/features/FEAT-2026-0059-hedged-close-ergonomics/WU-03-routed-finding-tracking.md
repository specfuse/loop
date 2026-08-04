---
id: FEAT-2026-0059/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - plugins/specfuse/skills/accept-hedged-close/SKILL.md
  - .specfuse/skills/accept-hedged-close/SKILL.md
  - tests/test_routed_finding_tracking.py
oracle_env: macos_local
---

# A routed finding gets a queue, not a paragraph

**Objective.** At acceptance, each `routed-finding` entry prompts for a tracking
surface — an existing issue or roadmap row, or an offer to create one — so an
accepted follow-up lands somewhere a human will meet it again.

**Context.** Correlation ID `FEAT-2026-0059/T03`. Read `PLAN.md` and T01's result
first. T01 owns the `kind:` contract; T02 owns the ceiling headline. This WU adds one
prompt to the acceptance step and nothing else.

**Why this entry kind specifically.** `acceptance-discharged` is discharged by the
acceptance itself. `inherent` is never actionable by anyone. `externally-verifiable-later`
already carries its exact re-run condition in the record, which *is* its tracking
surface. A `routed-finding` is the only kind whose whole meaning is *"someone else
owns this now"* — and today that someone is named only in retrospective prose, in a
file nobody opens again. It is the one kind that leaks by construction.

**The blast radius is one prompt.** This does not create issues automatically, does
not decide priority, and does not follow up. It asks where the finding is tracked and
records the answer in the acceptance record next to the entry. An operator who says
"nowhere, deliberately" is recorded as having said that, which is a better artifact
than silence.

**T02 and this WU edit the same two files.** They share `produces` paths by design —
`depends_on` puts T01 before both, and this WU runs after T02 in the graph order.
Read the file as T02 left it; do not revert its step-2 rewrite while adding this
prompt.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `operator-escalation.md`.

**Acceptance criteria.**

1. `tests/test_routed_finding_tracking.py::TestRoutedFindingTracking::test_routed_finding_prompts_for_a_tracking_surface`
   exists and **fails on HEAD before this WU runs** (the skill has no such prompt,
   which counts as red).
2. That test asserts the SKILL.md instructs, for each `routed-finding` entry, a
   prompt for its tracking surface offering an existing issue/roadmap reference or
   `/roadmap-add` / `gh issue create`. It passes after this WU's edits.
3. A test asserts the answer is written into the acceptance record **next to the
   entry it belongs to**, not as a loose appendix — an untracked routed finding and
   its tracking reference must be readable together.
4. A test asserts the other three kinds do **not** trigger the prompt, with the
   reason stated in the skill: they are discharged, inherent, or already carry their
   re-run condition.
5. A test asserts "tracked nowhere, deliberately" is an accepted answer and is
   recorded as such — the prompt must not be a gate that blocks acceptance, since
   `accept-hedged-close` is a single-confirm skill and a mandatory sub-decision would
   change its posture.
6. A test asserts T02's ceiling headline is still present and unmodified — this WU
   adds to the step, it does not rewrite it.
7. Both SKILL.md copies are byte-identical (`diff`, quote the empty output), and
   `tests/test_skill_discovery_links.py` plus the scaffold sync tests pass.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `close-discipline.md` and `closing_requirements.py` — T01's.
T02's ceiling headline and reason scaffolding — additive only, criterion 6 checks it.
Anything that creates issues or roadmap rows automatically: this WU offers the
commands, the operator runs them.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criterion 5 is load-bearing —
a prompt that blocks acceptance turns a single-confirm skill into a multi-step
interrogation, which is the friction this whole feature exists to remove.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
prompt cannot be added without making acceptance multi-step (say so — the posture is
the constraint, not the prompt); T02's edits are absent or conflict, which means the
graph ran out of order and this WU is reading a file it does not expect; or recording
the tracking reference per-entry requires changing the acceptance record's shape in a
way that breaks T01's contract.
