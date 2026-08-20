---
id: FEAT-2026-0050/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
oracle_env: macos_local
produces:
  - specfuse/agent/drafting_questions.py
  - tests/test_drafting_questions.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.12.1
started_at: 2026-08-16T12:21:48.285565+00:00
duration_seconds: 636.001
cost_usd: 1.396823
input_tokens: 235
output_tokens: 15044
---

# Build the drafting interview's question set

**Objective.** Produce, from a `drafting-needed` roadmap entry, the set of
questions `/draft-feature`'s interview would ask — each classified `elicitation`
or `decision`, with options and a recommendation on decisions and neither on
elicitation.

**Context.** FEAT-2026-0050/T01, gate 1. This is the "agent studies" half of the
async interview: the expensive reading — roadmap entry, a LEARNINGS slice via
`python3 -m specfuse.loop.learnings_query`, one or two exemplar `PLAN.md` files,
and a light codebase probe — moves off the operator's session so only the
*questions* need their attention.

The elicitation/decision split is not new vocabulary. `/draft-feature`'s own
interview rules define it: elicitation is "only the user knows the answer",
asked open, and manufacturing options for one "reads as a phone tree and buries
the real question"; a decision is one where the skill "can enumerate real
options and have a basis to recommend". This unit makes that classification a
data structure instead of a prose instruction, because **D1 in `PLAN.md` reads
it** — the whole draft-or-fallback rule rests on the classification being
honest.

New module `specfuse/agent/drafting_questions.py`. Pure: it reads files and
returns a question set. It posts nothing, writes no issue, and runs no `gh`
command — T02 owns the posting.

**Acceptance criteria.**

1. `tests/test_drafting_questions.py::TestBuildQuestionSet::test_elicitation_questions_carry_no_options`
   fails on HEAD before this unit runs (the module does not exist), and passes
   after. The assertion is a **negative observation**: an elicitation question
   must carry no options and no recommendation, because a fake multiple-choice
   on the user's own intent is the failure `/draft-feature` names.
2. Every question in a built set carries `kind` ∈ {`elicitation`, `decision`},
   a stable `id` usable as a marker, and its question text.
3. Every `decision` question carries at least two options **and** a
   recommendation naming one of them. A decision the agent cannot recommend on
   is an elicitation question misfiled — asserted directly, because D1 defaults
   unanswered decisions to the recommendation and a missing one would default to
   nothing.
4. The builder reads the roadmap entry, a LEARNINGS slice, and at least one
   exemplar `PLAN.md`, and a test asserts a question set built for a roadmap
   entry naming a surface mentions that surface — the "trace every proposal to
   evidence" rule made checkable rather than asserted.
5. The module issues no `gh` and no `git` subprocess — asserted structurally
   against its own source, the same guarantee `driver_invoke.py` carries.
6. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`
   exits 0.

**Do not touch.** `specfuse/loop/escalation.py` (T02 renders through it
unchanged), `plugins/specfuse/skills/draft-feature/SKILL.md` (gate 2 owns the
skill change), and `escalation.CATEGORY_LABELS`.

**Verification.** `./scripts/smoke-test.sh` — the full gate set, run
unsandboxed; a sandboxed run hits unrelated network restrictions during pip
build-dependency resolution.

**Escalation triggers.** If building an honest question set turns out to require
`/draft-feature`'s full interview logic rather than a reimplementable subset,
stop and report `status: blocked` naming that — it would mean D2's "one
implementation" argument applies to gate 1 as well, which is a planning decision
this unit must not take on its own.
