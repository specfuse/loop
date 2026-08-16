---
id: FEAT-2026-0050/T06
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - specfuse/agent/drafting_invoke.py
  - tests/test_drafting_invoke.py
model: sonnet
effort: medium
---

# Build the headless drafting invocation

**Objective.** Turn a `draft_ready` answer-gate result into the argv and prompt
for one headless `/draft-feature` session, and read that session's result back.
Build nothing; run nothing.

**Context.** FEAT-2026-0050/T06, gate 2, depends on T04 (the reply shape that
produces a bindable answer set) and T05 (the skill mode this invocation
targets).

The module idiom is already established three times over —
`specfuse/agent/triage_invoke.py`, `specfuse/agent/diagnose_invoke.py`, and
`specfuse/monitor/autofix_invoke.py` all expose `build_invocation(...) ->
(argv, prompt)` and a `read_result(result_text)`, and none of them runs a
subprocess. Follow that shape rather than inventing a fourth.

The input is `drafting_answers.AnswerGateResult`: `outcome` is
`OUTCOME_DRAFT_READY` or `OUTCOME_FALLBACK`, `answers` maps question id to
effective answer, and `assumptions` is a tuple of `Assumption(question_id,
assumed_value)` naming every decision D1 defaulted. `GATE-02-REVIEW.md`
§ Runtime probe records the measured behaviour of that gate, including that no
real operator reply has ever been observed — this unit consumes the parsed
answers and must not re-parse reply text itself.

D1's rule is the boundary this unit enforces mechanically: a `fallback` result
means the agent may not draft, and there is no code path here that supplies a
value for an unanswered elicitation question.

**Acceptance criteria.**

1. `tests/test_drafting_invoke.py` names
   `RefusesFallbackTests::test_build_invocation_refuses_a_fallback_result` and
   it **fails on HEAD before this unit runs** — the file does not yet exist, and
   `python3 -m unittest tests.test_drafting_invoke` exits non-zero on an absent
   module.
2. `build_invocation` raises on an `AnswerGateResult` whose `outcome` is
   `OUTCOME_FALLBACK`, rather than returning a prompt built from partial
   answers. This is the criterion above, green.
3. `build_invocation` returns a `(argv, prompt)` tuple and runs no subprocess —
   asserted structurally, by the same means `tests/test_drafting_answer_gate.py`
   asserts T03's module issues no `gh` or `git`.
4. The prompt names every question id and its effective answer, and names every
   `Assumption` verbatim with its `question_id` and `assumed_value`, so the
   drafted `PLAN.md` can record each defaulted decision as an explicit
   assumption (T05 criterion 2). Asserted per assumption, not by a count.
5. `read_result` parses the session's RESULT block and raises on any status
   other than `complete` — a `blocked` drafting session must not be read as a
   drafted folder. The RESULT block's shape is
   `.specfuse/rules/result-contract.md`'s; do not restate it in the module.

**Do not touch.** `specfuse/agent/drafting_answers.py` and
`specfuse/agent/drafting_questions.py` — this unit consumes their output and
adds no second parser (T04 owns the render side). `specfuse/loop/*.py` — the
driver's importable surface; a unit editing it halts the run for a restart
(FEAT-2026-0075). `specfuse/agent/providers/feature.py` — T07 owns the wiring.
`/draft-feature`'s SKILL.md — T05 owns it. Do not touch `.git/` or any secrets
file. **The driver owns all git — this session edits files only and never runs
`git`.**

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed; a sandboxed run
hits unrelated network restrictions during pip build-dependency resolution.
Scoped red/green run: `python3 -m unittest tests.test_drafting_invoke -v`.
Symbol check:
`python3 -c "from specfuse.agent.drafting_invoke import build_invocation, read_result"`.

**Escalation triggers.** If `build_invocation` cannot name every assumption in
the prompt without exceeding a prompt-size limit the session actually hits,
report `status: blocked` with the observed limit rather than silently truncating
the assumptions list — an unstated default is the failure `PLAN.md`'s
`roadmap_goal` names. If `read_result` cannot distinguish a `complete` RESULT
from a `blocked` one against the shapes in the tree, report `status: blocked`
with the ambiguous shape rather than defaulting to `complete`.
