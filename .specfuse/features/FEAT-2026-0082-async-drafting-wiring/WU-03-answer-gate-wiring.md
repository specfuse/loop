---
id: FEAT-2026-0082/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.00
oracle_env: macos_local
produces_driver_helper: read_reply_answers, default_answer_gate
produces:
  - specfuse/agent/drafting_answers.py
  - specfuse/agent/run.py
  - tests/test_answer_gate_wiring.py
model: sonnet
effort: medium
---

# Read the operator's reply back, and inject the gate that was never injected

**Objective.** Close seam 2: build an `answer_gate` that reads a reply from the
question issue's comments, binds it through `parse_reply_answers`, evaluates it
with `evaluate_answer_gate`, and — the part 0050 missed — **pass it to
`FeatureProvider` in `default_providers`**, so `_dispatch_drafting` stops taking
the fallback branch on every real run.

**Context.** Third WU of FEAT-2026-0082; read `PLAN.md` for the scope boundary
and `GATE-01.md` for what this gate must not claim. Depends on T02, which posts
the issue this unit reads.

**The seam, exactly — and note how small it is.**

```
specfuse/agent/providers/feature.py:79   answer_gate: Optional[...]        <- the parameter exists
specfuse/agent/providers/feature.py:90   self._answer_gate = answer_gate or self._fallback_answer_gate
specfuse/agent/run.py:640                FeatureProvider(repo=..., runner=..., policy_path=...,
                                                         features_root=..., stream_driver_output=True,
                                                         reporter=...)     <- no answer_gate passed
```

The provider was **built** to take an injected gate. `default_providers` simply
never passes one, so `self._answer_gate` is `_fallback_answer_gate` on every
production run and `_dispatch_drafting` (`feature.py:223`) escalates
unconditionally. 0050's retrospective calls this out verbatim. **Do not
restructure `FeatureProvider`** — the injection point is already correct; supply
an argument.

`evaluate_answer_gate(feature_id, questions, answers)`
(`drafting_answers.py:177`) already implements D1: any unanswered *elicitation*
question forces `OUTCOME_FALLBACK`; unanswered *decisions* default to their
recommendation and are recorded as `Assumption`s. That semantics is 0050's and
ships unchanged — this WU feeds it, it does not redesign it.

What is missing between the issue and that function is the read: fetch the
issue's comments, pick the reply, hand its text to `parse_reply_answers`. The
`<!-- specfuse:question id=... -->` markers T02 preserved are what bind an answer
to its question, so an operator who answers questions 1 and 3 and skips 2 does
not have answer 3 read as the answer to question 2 — the failure
`render_question_issue`'s docstring says it exists to prevent.

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_answer_gate_wiring.py::test_default_providers_injects_an_answer_gate`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). `default_providers(repo=...)` returns a `FeatureProvider` whose
  `_answer_gate` is **not** `_fallback_answer_gate`. This is the one-line
  omission that cost 0050 its verdict; assert it directly.
- After this WU's edits that same test passes, and so does
  `tests/test_answer_gate_wiring.py::test_reply_with_every_answer_reaches_draft_ready`
  — a synthetic comment answering every question binds through
  `parse_reply_answers` and `evaluate_answer_gate` returns
  `OUTCOME_DRAFT_READY`, driven through an injected runner with no live `gh`.
- `tests/test_answer_gate_wiring.py::test_missing_elicitation_answer_falls_back`
  passes: a reply that skips an elicitation question yields `OUTCOME_FALLBACK`,
  and the run escalates rather than drafting from a guess. D1's rule, asserted
  at the wiring layer rather than only in 0050's unit tests.
- **An unanswered decision defaults and is recorded.** A test asserts the
  resulting `assumptions` tuple names the defaulted question — a drafted folder
  whose choices nobody made must say which ones those were.
- **No reply yet is not an error.** A test drives an issue with zero comments and
  asserts the gate returns fallback quietly, with no exception and no second
  question issue posted. This is the common state between two agent runs.
- **Out-of-order answers bind correctly.** A test supplies a reply answering
  question 3 then question 1, omitting 2, and asserts each answer binds to its
  own question id. The marker discipline is the point of the whole design.
- `read_reply_answers` and `default_answer_gate` are importable: `python3 -c
  "from specfuse.agent.drafting_answers import read_reply_answers,
  default_answer_gate"` exits 0.
- `FeatureProvider`'s constructor signature is unchanged. Assert mechanically:
  `git diff HEAD -- specfuse/agent/providers/feature.py` shows no edit to
  `__init__`, and the existing provider tests pass untouched.
- Every new `subprocess.run` declares `check=` explicitly (`PLW1510`).

**Do not touch.** `evaluate_answer_gate`'s D1 semantics, `parse_reply_answers`'
grammar, and `build_invocation` — all 0050's, all shipped, all out of scope per
PLAN.md; `FeatureProvider.__init__` and `_dispatch_drafting`'s branch structure
(supply the argument, do not restructure the provider); T02's poster; T01's
emitter. `.git/`, secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check above, plus T01's and T02's test modules still green. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if `parse_reply_answers` cannot
bind a reply shaped the way `render_question_issue`'s answer-template block asks
for — that would mean the renderer and the parser disagree, which is a 0050
defect this feature is explicitly scoped **not** to fix, and a human must decide
whether to widen scope. Record the exact shapes that failed. Also block if
injecting the gate requires changing `FeatureProvider`'s constructor: the
parameter already exists, and needing to change it means the diagnosis in
PLAN.md is wrong. If `default_providers` still constructs `FeatureProvider`
without an `answer_gate` in the files you edited, emit `status: blocked` — that
is the entire point of this unit; do not claim complete. Blocked is respectable
(`result-contract.md` rule 4).
