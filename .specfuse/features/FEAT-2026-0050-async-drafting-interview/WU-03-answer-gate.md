---
id: FEAT-2026-0050/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.50
oracle_env: macos_local
produces:
  - specfuse/agent/drafting_answers.py
  - tests/test_drafting_answer_gate.py
---

# Read the answers and apply the D1 gate

**Objective.** Parse an operator's reply back to per-question answers, then
decide by D1 whether the answer set supports drafting or the run falls back to a
plain `drafting-needed` escalation — recording every defaulted decision as an
explicit assumption.

**Context.** FEAT-2026-0050/T03, gate 1, depends on T02. This unit is the
feature's judgment: everything else moves text around, and this decides whether
a plan gets built on what came back.

D1, from `PLAN.md`: **any unanswered elicitation question forces fallback; an
unanswered decision question takes the agent's own recommendation, logged as an
explicit assumption.** The rule reuses T01's classification rather than inventing
a threshold, because if the agent could enumerate options and recommend one,
silence safely means "your recommendation" — that is what a recommendation is
for — and if it could not, silence carries no information at all.

Extends `answers.py`'s existing parsing rather than adding a second reader; that
module already owns the numbered-reply idiom and the ack marker.

**Acceptance criteria.**

1. `tests/test_drafting_answer_gate.py::test_unanswered_elicitation_forces_fallback`
   fails on HEAD before this unit runs and passes after: an answer set missing
   any elicitation answer returns the fallback outcome and no draft-ready set.
2. An unanswered **decision** question yields the agent's recommendation as the
   effective answer **and** appends an entry to an assumptions list naming the
   question and the value assumed. A test asserts the assumptions list is
   non-empty whenever any decision defaulted — a plan must never rest on an
   unstated default, which is the failure mode `PLAN.md`'s `roadmap_goal`
   names.
3. Answers bind by T02's per-question marker, not by position: a reply answering
   questions 1 and 3 while skipping 2 leaves question 2 unanswered. Asserted
   directly, because a mis-binding here feeds D1 a wrong classification.
4. Round two re-asks **only** unanswered elicitation questions; answered
   questions and unanswered decisions are not re-asked. A test asserts a
   second-round question set contains no `decision` entries.
5. A hard cap of two rounds: a third round is never posted, and reaching the cap
   with elicitation still unanswered produces the fallback outcome.
6. The fallback outcome is the **existing** `drafting-needed` escalation, not a
   new shape — asserted by comparing against what `FeatureProvider`'s
   `needs_drafting` branch produces today, so D3's "worst case is status quo"
   holds mechanically rather than by intention.
7. `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0050-async-drafting-interview`
   exits 0.

**Do not touch.** `/draft-feature`'s SKILL.md and any feature-folder write path
— gate 2 owns those. This unit decides *whether* to draft; it never drafts.

**Verification.** `./scripts/smoke-test.sh` — run unsandboxed.

**Escalation triggers.** If a real operator reply cannot be parsed back to
per-question answers reliably — free prose that answers three questions in one
paragraph, say — stop and report `status: blocked` with the observed reply
shape. A parser that guesses which question a sentence answers would corrupt
D1's input, and a wrong classification is worse than a fallback.
