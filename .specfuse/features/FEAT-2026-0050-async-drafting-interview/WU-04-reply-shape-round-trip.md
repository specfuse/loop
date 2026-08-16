---
id: FEAT-2026-0050/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - specfuse/agent/drafting_questions.py
  - tests/test_drafting_reply_shape.py
model: sonnet
effort: medium
---

# Make the posted interview instruct the reply shape its parser accepts

**Objective.** Add a per-question answer template to the rendered question
issue, so a reply an operator can copy out of the issue is a reply
`parse_reply_answers` binds.

**Context.** FEAT-2026-0050/T04, gate 2, no dependencies — the first unit in
the gate. Everything after it consumes what it produces.

Gate 1 shipped the two halves of the round-trip separately and they do not
meet. `GATE-02-REVIEW.md` § Runtime probe records the measured result: the
rendered body's closing section reads `Reply with the number of your choice, or
prose if none fit:` followed by five numbered options, while
`drafting_answers._ANSWER_LINE_RE` accepts only lines shaped
`{question_id}: <answer>` — a shape the issue never asks for. Measured, not
inferred: `parse_reply_answers("4", ids)` returns `{}` and
`evaluate_answer_gate` returns `fallback`. **No real operator reply exists** —
gate 1 posted no issue and auto-closed without a close session, so
`RETROSPECTIVE.md` records no reply shape. That absence is why this unit is
drafted from the round-trip probe rather than from a human's answer.

Numbers cannot carry the interview in any case: elicitation questions
contribute no options, so no number exists for them, and D1 refuses to default
an elicitation answer.

The fix composes over `escalation.render_escalation_body` from
`drafting_questions.render_question_issue`, the same posture T02 already took.
See `GATE-02-REVIEW.md` § Open question 2 for the direction a reviewer may
revise at arming.

**Acceptance criteria.**

1. `tests/test_drafting_reply_shape.py` names
   `ReplyTemplateRoundTripTests::test_template_block_parses_back_to_every_question`
   and it **fails on HEAD before this unit runs** — the file does not yet exist,
   and `python3 -m unittest tests.test_drafting_reply_shape` exits non-zero on
   an absent module.
2. `render_question_issue` writes a copyable answer-template block naming every
   question id in the set, one line per question, in the shape
   `parse_reply_answers` accepts. Asserted by extracting that block from the
   rendered body, substituting an answer per line, and feeding the result to
   `parse_reply_answers` — every question id binds. This is the criterion above,
   green.
3. `escalation.validate_escalation_body` still returns `[]` on the rendered
   body, and the existing `## Reply with a number` section and its numbered
   decision options are still present — the template is additive, not a
   replacement. `validate_escalation_body` returns `[]` on HEAD's body today, so
   a regression here is this unit's doing.
4. A bare-number reply still yields no bindings and `evaluate_answer_gate`
   still returns `fallback` — asserted directly. Failing closed is the property
   that keeps a mis-shaped reply from binding an answer to the wrong question,
   and it must survive this change.
5. Every question in a set carries a line in the template block, elicitation and
   decision alike, so the block is not a decision-only surface.

**Do not touch.** `specfuse/loop/escalation.py` — it is on the driver's
importable surface (`driver_edit.is_driver_module_path` returns `True`), so a
unit editing it halts the run for a restart (FEAT-2026-0075), and its reply
instruction is shared by every escalation issue in the repo. Do not change
`_ANSWER_LINE_RE` or any other parsing rule in `drafting_answers.py` — this unit
changes what the issue asks for, not what the parser accepts. Do not touch
`/draft-feature`'s SKILL.md (T05), `specfuse/agent/drafting_invoke.py` (T06), or
`specfuse/agent/providers/feature.py` (T07). Do not touch `.git/` or any
secrets file. **The driver owns all git — this session edits files only and
never runs `git`.**

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed; a sandboxed run
hits unrelated network restrictions during pip build-dependency resolution.
Scoped red/green run:
`python3 -m unittest tests.test_drafting_reply_shape -v`. Symbol check:
`python3 -c "from specfuse.agent.drafting_questions import render_question_issue"`.

**Escalation triggers.** If the answer-template block cannot be added without
`escalation.validate_escalation_body` reporting a finding — the six-part shape
has no room for it — stop and report `status: blocked` naming the finding,
rather than editing `escalation.py` to make room. If a reviewer's arming
decision on `GATE-02-REVIEW.md` § Open question 2 contradicts criterion 2 (the
parser is to learn the numbered form instead), report `status: blocked` rather
than implementing both.
