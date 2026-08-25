---
id: FEAT-2026-0082/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
oracle_env: macos_local
produces_driver_helper: post_question_issue
produces:
  - specfuse/agent/drafting_questions.py
  - specfuse/agent/providers/feature.py
  - tests/test_post_question_issue.py
model: sonnet
effort: medium
---

# Actually post the question issue, and stop filing the escalation it replaces

**Objective.** Close seam 1: give `render_question_issue` a production caller, so
a `needs_drafting` queue entry posts one real question issue carrying
`needs-human` + `drafting-needed` — and suppress the old `fallback_escalation`
when that post succeeds, so one human gets one issue rather than two.

**Context.** Second WU of FEAT-2026-0082; read `PLAN.md` in this folder first,
and `GATE-01.md` for what this gate must not claim. Depends on T01, which ships
`escalation.emit_issue_with_body`.

**The seam, exactly.** `render_question_issue(correlation_id, questions)`
(`specfuse/agent/drafting_questions.py:264`) returns `(body, labels)` and has
**no production caller** — that is the whole defect. Its docstring records that
it *"composes over `escalation.render_escalation_body` rather than
reimplementing it"*, so what it returns is already an escalation body in the
six-part shape, with a `<!-- specfuse:question id=... -->` marker per question
and an answer-template block appended. It is ready to post; nothing posts it.

The call site is `FeatureProvider._dispatch_drafting`
(`specfuse/agent/providers/feature.py:215`). Today its fallback branch returns
`STATUS_ESCALATED` with `drafting_answers.fallback_escalation(feature_id)`. That
escalation is what produced #2381 and #2383 in this repository.

**Two exits, and both are yours.** This is the WU's one real hazard, called out
in PLAN.md:

1. **The question issue posts successfully** — it *is* the escalation. Do not
   also file `fallback_escalation`; two issues asking one human the same thing is
   how an inbox gets ignored.
2. **Posting fails** (no `gh`, no auth, API refusal) — fall back to today's
   escalation exactly as it behaves now. A feature waiting on a human with
   nothing in the `needs-human` queue is invisible, and that is strictly worse
   than a duplicate.

If the split between these two proves ambiguous while you are in it, that is a
block, not a judgement call.

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**

- `tests/test_post_question_issue.py::test_needs_drafting_posts_one_question_issue`
  exists and **fails on HEAD before this WU's edits** (the module does not yet
  exist). A `needs_drafting` disposition drives `render_question_issue` and files
  its body through `emit_issue_with_body`, with an injected runner and no live
  `gh`.
- After this WU's edits that same test passes, and so does
  `tests/test_post_question_issue.py::test_successful_post_suppresses_the_fallback_escalation`
  — when the post succeeds, `fallback_escalation` is **not** called and the
  outcome carries the question issue's identifier.
- `tests/test_post_question_issue.py::test_failed_post_falls_back_to_todays_escalation`
  passes: an injected runner reporting failure produces exactly the escalation
  the code produces today, unchanged. Assert the `category` is still
  `drafting-needed` so `/attention`'s category routing is unaffected.
- **A second run posts no second issue.** A test invokes the path twice against a
  runner whose search reports the first issue present, and asserts one create
  call total. This is the criterion that keeps a four-entry queue from filing
  four issues per invocation.
- **A drafted queue entry posts nothing.** A test drives a `workable`
  disposition and asserts zero `gh` calls — PLAN.md's §2 no-op answer, made
  executable.
- The posted issue carries **both** `needs-human` and `drafting-needed`. A test
  asserts both appear in the runner's argv. The first puts it in the inbox
  `/attention` sweeps; the second is what `/answer-escalation` routes on.
- The body posted is `render_question_issue`'s output **unmodified** — a test
  asserts the `<!-- specfuse:question id=... -->` markers survive to the argv.
  T03 binds a reply to a question by those markers; a rewritten body breaks it.
- `post_question_issue` is importable: `python3 -c "from
  specfuse.agent.drafting_questions import post_question_issue"` exits 0.
- Every new `subprocess.run` declares `check=` explicitly (`PLW1510`).

**Do not touch.** `render_question_issue`'s rendering (0050's, unchanged — this
WU calls it); `escalation.emit_issue_with_body` (T01 owns it — call it, do not
edit it); `parse_reply_answers`, `evaluate_answer_gate` and the `answer_gate`
injection (T03); the `blocked` / `unreadable` escalation branches at
`feature.py:178-206`, which keep behaving as they do. `.git/`, secrets. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
symbol-import check above, plus T01's test module still green. See
`.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** Emit `status: blocked` if suppressing
`fallback_escalation` on the success path cannot be done without changing what
the `blocked` or `unreadable` dispositions file — those are unrelated queue
states and silently altering them while fixing `needs_drafting` is out of scope.
Also block if the two exits above cannot be told apart reliably from the
emitter's return value: an ambiguous "did it post?" means the run either
double-files or goes silent, and both are worse than stopping here. If
`post_question_issue` is absent from the files you edited, emit `status: blocked`
— do not claim complete. Blocked is respectable (`result-contract.md` rule 4).
