---
feature_id: FEAT-2026-0050
title: Async feature-drafting interview via question issues
slug: async-drafting-interview
branch: feat/FEAT-2026-0050-async-drafting-interview
roadmap_goal: Drafting progresses on the operator's schedule — the agent posts the draft-feature interview as a question issue and drafts from the answers, while planning judgment and the gate-1 checkpoint stay human.
autonomy_default: auto
status: planned
planned_cost_usd: 33.00
---

# Plan: Async feature-drafting interview

An undrafted queue-top feature escalates and waits for an interactive
`/draft-feature` session. That sequencing is correct — planning is where human
judgment adds most — but it is now the throughput bottleneck. Observed
2026-08-15: a run with four `planned` features in `queue:` produced **four
`drafting-needed` escalations and zero units of work** in 0.69 minutes
(issues #2380–#2383). Every subsequent run repeats it until a human sits down
per feature.

The interview itself can move async without surrendering drafting quality. The
agent does the expensive half — reading the roadmap entry, LEARNINGS,
exemplars, and the codebase — and posts the *questions* as a `needs-human`
issue. The operator answers from anywhere. A later run reads the answers and
drafts the folder. Gate-1 review stays human, so the checkpoint that matters
is untouched.

This feature is the decision FEAT-2026-0080 deferred. That PLAN's D1 recorded
agent-side execution of a free-text answer as "a separate decision, not a
deferred slice of this one," to be made "with evidence from real use." That
evidence now exists: nine escalations were dispositioned by hand on
2026-08-14/15, and the pattern was consistent — where the agent could
enumerate options and recommend one, the operator's answer was "go with your
recommendation"; where the question was product intent (which repo a feature
belongs in, whether to burn seventeen IDs to honour a typo), only the human
could answer. D1 below is that observation turned into a rule.

## Decisions taken at draft time

**D1 — an unanswered *elicitation* question forces fallback; an unanswered
*decision* question takes the agent's own recommendation, logged as an explicit
assumption.** `/draft-feature` already classifies every question it asks:
elicitation (only the user knows — asked open, never with manufactured options)
versus decision (the skill enumerates real options and has a basis to
recommend). That classification is reused rather than a new threshold invented,
and it gives silence a principled reading: if the agent could recommend, silence
safely means "your recommendation" — that is what a recommendation is *for*. If
it could not, because the question is the operator's intent, scope boundary, or
definition of done, then silence carries no information and drafting on it is
the assumption-built-plan failure this feature exists to avoid.

Rejected: a count threshold ("four of six answered"), which has no principle
behind it — answering the four easy ones and skipping the goal would pass, and
that is the failure case. Also rejected: letting the agent mark questions
blocking or optional, which puts the same judgment back on the agent and drifts
from the question's actual shape.

A consequence worth having on purpose: the rule makes the *questions* better.
For an answer to be optional the agent must phrase the question as a decision
with real options and a recommendation — which is the better question anyway.

Round two re-asks **only** unanswered elicitation questions. Re-litigating a
decision the operator declined to answer spends their attention on exactly what
they delegated.

**D2 — extend `/draft-feature` rather than build a second drafting path.** The
skill is interactive-only today by its own hard rule, and its RESULT contract
says a headless invocation "can only produce the proposal and must stop before
writing." Gate 2 adds a path where the interview's answers arrive as a file
instead of a conversation.

Rejected: a separate agent-side drafting invoker under `specfuse/agent/`. This
repository has now paid twice for one algorithm living in two places — the
roadmap-archive skill/driver split (FEAT-2026-0079, merged 2026-08-14) and the
core-owned rules duplicated into the scaffold (#2270, open). A second
implementation of gate-cutting and WU-authoring would be the same mistake with
a larger surface, and harder to retire later because one copy is prose and the
other code.

The hard rule is restated, not weakened: `/draft-feature` never writes without
**answers**, whatever channel they arrive through.

**D3 — the fallback is the current behaviour, so there is no regression path.**
When D1 says fall back, the agent emits the plain `drafting-needed` escalation
it emits today. Worst case is status quo.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

T03 designs a gating rule, so the search is required.

```
grep -rn "def \|MARKER" specfuse/agent/providers/answers.py
grep -rn "CATEGORY_LABELS\|render_escalation_body" specfuse/loop/escalation.py
```

**Verdict — most of the round-trip already exists and is reused, not rebuilt:**

- `specfuse/loop/escalation.py` owns the six-part body, the numbered-options
  rendering, `CATEGORY_LABELS`, `NEEDS_HUMAN_LABEL`, and the correlation-marker
  template. T02 renders through it.
- `specfuse/agent/providers/answers.py` already parses an operator's numbered
  reply (`_numbered_answers_section`), carries an ack marker, and uses the
  re-derived-from-comments idiom. T03 extends that parsing rather than adding a
  second reader.
- `/answer-escalation` established the `<!-- specfuse:operator-guidance id=… -->`
  convention for locating operator prose mechanically.

**What does not exist, and is this feature's novelty:** question *generation*
classified elicitation/decision (T01), and any answered/unanswered gating rule
(T03). T02 is assembly over existing machinery.

## Escalation-predicate satisfiability

Every escalation trigger in this feature's work units is falsifiable from
inside the session that would fire it, with no external environment:

- **T01** — "an honest question set requires `/draft-feature`'s full interview
  logic rather than a reimplementable subset": checked by attempting the subset
  against a real roadmap entry. The session either produces a classified set or
  cannot.
- **T02** — "`render_escalation_body` cannot carry multiple questions without a
  signature change": checked by calling it. Its signature is in the tree.
- **T03** — "a real operator reply cannot be parsed back to per-question
  answers": checked against the reply shapes the session has; if none exists
  yet, that absence *is* the trigger, and it fires rather than being assumed
  away.

None depends on a deployed component, a credential, or a network round-trip, so
no trigger is unfalsifiable in the environment the loop actually runs in.

## Scope boundary — explicitly OUT

- **Answering the questions.** The operator answers; the agent never supplies a
  value for an elicitation question, in any code path.
- **Gate-1 review.** The human checkpoint after drafting is unchanged and is not
  automated by this feature under any dial.
- **Changing `CATEGORY_LABELS`.** The existing `drafting-needed` category is
  used as-is. Adding one ripples into `/answer-escalation`'s routing table,
  which asserts coverage of that exact set.
- **Triaging or dispositioning the question issue.** `/answer-escalation` owns
  operator dispositions; this feature posts a question and reads its answer.

## Gates

Two gates. Gate 1 delivers the interview round-trip and writes no feature
folder; gate 2 consumes the answers and drafts. The seam is deliberate: the
unknown here is *what operators actually answer*, and gate 2 planned in
ignorance of that is the expensive mistake. `[FEAT-2026-0069/G2-CLOSE]` records
the counter-evidence — an expensive `plan-next` ($16.44) bought a gate that ran
4 WUs, 0 failures, $4.43 against a $12.00 budget, because its hardest WU was
handed an enumerated problem list.

Gate 1 is independently valuable: even if gate 2 never ships, today's bare
`drafting-needed` escalation becomes an issue carrying the actual interview.

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0050/T01
        file: WU-01-question-set-builder.md
        depends_on: []
      - id: FEAT-2026-0050/T02
        file: WU-02-post-question-issue.md
        depends_on: [FEAT-2026-0050/T01]
      - id: FEAT-2026-0050/T03
        file: WU-03-answer-gate.md
        depends_on: [FEAT-2026-0050/T02]
      # --- closing sequence: non-terminal gate ---
      - id: FEAT-2026-0050/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0050/T01
          - FEAT-2026-0050/T02
          - FEAT-2026-0050/T03
      - id: FEAT-2026-0050/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0050/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # Substantive units are drafted by gate 1's plan-next. The terminal
      # close is pre-declared so the linter reads gate 2 — not gate 1 — as
      # this feature's terminal gate.
      - id: FEAT-2026-0050/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on: []
```

## Notes

- T01 → T02 → T03 is a genuine chain, not sequencing by habit: T02 renders what
  T01 produces, and T03 parses what T02 posted. Each depends on the previous
  unit's output shape.
- **Provider wiring is touched by both gates.** Gate 1 needs enough wiring to
  post at all; gate 2 changes what happens once answers arrive. One file across
  two gates is the shape that produced FEAT-2026-0075's driver-staleness hazard
  — worth watching at gate 2's arming review, not worth restructuring around.
- `planned_cost_usd` covers gate 1 plus the pre-declared terminal close.
  Gate 2's substantive units do not exist yet, so they are not in the sum;
  `plan-next` raises it when it drafts them.
- Costs feed `evaluate_auto_close`'s per-WU ratio check. `G1-PLAN` is budgeted
  **$9.00**, above the $5.00 floor, because `[FEAT-2026-0069/G2-CLOSE]` records
  a real `plan-next` at $16.44 and notes the floor is priced as if closing WUs
  pass first try — neither of that feature's did.
