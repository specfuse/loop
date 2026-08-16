---
id: FEAT-2026-0050/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - specfuse/agent/drafting_questions.py
  - tests/test_drafting_question_issue.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.12.1
started_at: 2026-08-16T12:32:24.455469+00:00
duration_seconds: 547.812
cost_usd: 1.009557
input_tokens: 38
output_tokens: 14807
---

# Post the interview as a question issue

**Objective.** Render T01's question set into a `needs-human` issue body in the
established six-part escalation format, carrying one machine-readable marker per
question so a later run correlates answers to questions.

**Context.** FEAT-2026-0050/T02, gate 1, depends on T01. This is assembly over
machinery that already exists, per `PLAN.md`'s existing-mechanism search:
`escalation.render_escalation_body` owns the six-part body and the numbered
options, `CATEGORY_LABELS` already contains `drafting-needed`, and
`NEEDS_HUMAN_LABEL` is the parking label. None of that is reimplemented here.

What is new is **per-question markers**. `answers.py` today parses a single
numbered reply for one escalation; this interview asks several questions at
once, so an answer must bind to a question identity rather than to a position
in a list. An operator who answers questions 1 and 3 and skips 2 must not have
answer 3 read as the answer to question 2 — that failure would silently feed D1
a wrong classification, which is the one input D1 cannot tolerate being wrong.

**Acceptance criteria.**

1. `tests/test_drafting_question_issue.py::test_each_question_carries_its_own_marker`
   fails on HEAD before this unit runs and passes after: every question in a
   rendered body carries a distinct marker containing its T01 question `id`,
   following the existing `<!-- specfuse:… -->` idiom.
2. The body is produced by calling `escalation.render_escalation_body` — asserted
   by a test that the six part names appear in the rendered output, so a
   hand-rolled body fails rather than passing on resemblance.
3. The issue carries `needs-human` and `drafting-needed`, and no other category
   label. A test asserts the category is a member of
   `escalation.CATEGORY_LABELS` read from that module, not a string literal.
4. Elicitation questions render open — no numbered options — and decision
   questions render their options with the recommendation named. This is T01's
   classification surviving into what the operator actually reads; a decision
   whose recommendation is missing from the rendered body would strand D1.
5. Rendering issues no `gh` command: the function returns a body and a label
   set, and the caller posts. Asserted structurally, so the render path stays
   testable without network.
6. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`
   exits 0.

**Do not touch.** `escalation.CATEGORY_LABELS` — `drafting-needed` already
exists and `/answer-escalation`'s routing table asserts coverage of that exact
set, so adding a category breaks a test in a different feature's surface.
`answers.py` is T03's to extend.

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed.

**Escalation triggers.** If `render_escalation_body`'s shape cannot carry
multiple questions without changing its signature, stop and report
`status: blocked` naming the collision: that function is consumed by every
escalation path in the agent, and widening it is a change to a shared contract
rather than this unit's business.
