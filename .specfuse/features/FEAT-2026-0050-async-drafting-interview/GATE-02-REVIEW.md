---
gate: 2
open_questions:
  - "Q1: is restating /draft-feature's write rule as 'never writes without answers' acceptable to the humans who rely on it? T05 carries human_only: true. See section 'Open question 1'."
  - "Q2: should T04 change the reply shape the issue instructs, or the shape the parser accepts? See section 'Open question 2'."
---

# Gate 2 review

Gate 2 turns an answered question issue into a drafted feature folder. Four
substantive units are drafted: T04 closes a round-trip gap gate 1 shipped, T05
adds `/draft-feature`'s answers-supplied mode, T06 builds the headless
invocation, T07 wires `FeatureProvider` to dispatch it.

**Do not arm before reading § Runtime probe.** Gate 1's interview cannot
currently be answered in a way its own parser accepts. That is measured, not
suspected, and T04 exists because of it.

## Runtime probe — the reply shape

`GATE-01.md`'s arming discipline requires this section to record the *observed*
shape of a real operator reply, and to say so plainly if none was ever
received.

**No real operator reply was ever received.** Gate 1 never posted an issue: T02
renders a body and a label set and issues no `gh` command, by its own
acceptance criteria, and gate 1 auto-closed (`evaluate_auto_close`,
predicate=v1) without a close session. `RETROSPECTIVE.md` carries the
auto-close stub and the `specfuse:autoclose-debt` marker — it records no reply
shape, because there was none to record. Every reply shape below is therefore
**designed, not observed**, and gate 2's parsing criteria are **unvalidated
against a human**.

What *was* measured is the round-trip between the two halves gate 1 shipped.
Probe run at planning time, in-tree, against a synthetic roadmap entry:

```
python3 -c "from specfuse.agent.drafting_questions import build_question_set, render_question_issue
from specfuse.agent.drafting_answers import parse_reply_answers, evaluate_answer_gate
qs = build_question_set('...roadmap text...', '', ())
body, labels = render_question_issue('FEAT-2026-9999', qs)
ids = [q.id for q in qs]
print(parse_reply_answers('4', ids))          # -> {}
print(evaluate_answer_gate('FEAT-2026-9999', qs, parse_reply_answers('4', ids)).outcome)"
```

Observed:

| Reply shape | Where the operator learns it | `parse_reply_answers` | `evaluate_answer_gate` |
|---|---|---|---|
| `4` (a bare number) | the issue's own `## Reply with a number` section, and every prior `needs-human` issue | `{}` | `fallback` |
| `roadmap-goal: …` lines | nowhere — the issue never asks for it | binds all three elicitation ids | `draft_ready`, two decisions assumed |

**The interview instructs a reply shape its own parser discards.** The rendered
body ends with `Reply with the number of your choice, or prose if none fit:`
followed by five numbered options — all of them decision-question options.
`parse_reply_answers` accepts only lines matching `{question_id}: <answer>`
(`_ANSWER_LINE_RE` in `drafting_answers.py`), and nothing in the issue tells the
operator to write one. Two consequences:

1. An operator following the instruction gets `fallback` every time. D3 holds —
   the fallback *is* the status-quo escalation — so this degrades to today's
   behaviour rather than corrupting a plan. It is a dead round-trip, not a
   correctness hazard.
2. The numbered form cannot express the interview anyway: elicitation questions
   contribute no options, so no number exists for them, and one number selects
   at most one of the two decision questions.

The fail-closed direction is the good news: a mis-shaped reply leaves
elicitation unanswered and D1 falls back, rather than binding an answer to the
wrong question. Gate 1's binding-by-id design is what buys that.

T04 is drafted to close this gap and is the first unit in the gate. Every later
unit consumes what it produces, so **arming gate 2 without T04 arms a path no
operator can feed.**

## Predicate check — `driver_edit.is_driver_module_path`

`PLAN.md`'s Notes flag provider wiring as touched by both gates, and
FEAT-2026-0075 records that a unit editing the driver's importable surface
halts the run for a restart mid-gate. Checked, not assumed — every path in a
gate 2 unit's `produces:` run through the predicate:

```
python3 -c "from specfuse.loop.driver_edit import driver_paths_in; print(driver_paths_in([...]))"
-> []
```

| Path | Driver module? |
|---|---|
| `specfuse/agent/drafting_questions.py` | no |
| `specfuse/agent/drafting_answers.py` | no |
| `specfuse/agent/drafting_invoke.py` | no |
| `specfuse/agent/providers/feature.py` | no |
| `plugins/specfuse/skills/draft-feature/SKILL.md` | no |
| `.specfuse/skills/draft-feature/SKILL.md` | no |
| `tests/*` | no |

**No gate 2 unit edits the driver's importable surface**, so no mid-gate
restart is expected. The predicate keys on `specfuse/loop/*.py`; every gate 2
path is under `specfuse/agent/`, which is dispatched-process code, not the
driver's own modules. The overlap `PLAN.md` flagged is real —
`providers/feature.py` is touched by both gates — but it is not the
FEAT-2026-0075 hazard.

**One adjacent path is on that surface: `specfuse/loop/escalation.py`
(`is_driver_module_path` → `True`).** T04's obvious-looking fix is to change
`render_escalation_body`'s reply instruction there. Its `Do not touch` forbids
that, and T04 is drafted to compose over it from `drafting_questions.py`
instead — the same posture T02 already took. If a reviewer decides the fix
belongs in `escalation.py` after all, that unit must be re-drafted knowing it
will restart the driver mid-gate, and it changes every escalation issue in the
repo, not just this one.

## Flag scope

No gate 2 unit introduces, gates on, or flips a behavior flag. T07 changes a
dispatch branch on an existing disposition (`DISPOSITION_NEEDS_DRAFTING`), not
a flag. No flag-scope table is required. If a reviewer adds one at arming, the
introducing WU carries the table
(`.specfuse/rules/planning-discipline.md` §3).

## Cross-repo contracts

`/authoring-work-units` §8 requires a `plan-next` draft to table every value it
could have invented, with its authoritative source. Every value below was read
from the tree during this planning session, not inferred:

| Value | Authoritative source | Checked |
|---|---|---|
| `needs-human`, `drafting-needed` | `specfuse/loop/escalation.py` (`NEEDS_HUMAN_LABEL`, `CATEGORY_LABELS`) | yes — unchanged by gate 2 |
| `<!-- specfuse:question id=… -->` | `drafting_questions._QUESTION_MARKER_TEMPLATE` | yes |
| `{question_id}: <answer>` | `drafting_answers._ANSWER_LINE_RE` | yes — and see § Runtime probe |
| `draft_ready` / `fallback` | `drafting_answers.OUTCOME_*` | yes |
| `MAX_ROUNDS = 2` | `drafting_answers.MAX_ROUNDS` | yes |
| `DISPOSITION_NEEDS_DRAFTING` | `specfuse/agent/queue_read.py` | yes |
| `## Headless mode` shape, three named outcomes | `plugins/specfuse/skills/fix-bug/SKILL.md` + `tests/test_fix_bug_headless.py` (FEAT-2026-0042/T03) | yes — cited as the precedent T05 follows |

No value in a gate 2 unit's acceptance criteria comes from another repository.

## Open question 1 — restating `/draft-feature`'s hard rule (T05)

**The question.** D2 asserts the hard rule is *restated, not weakened*:
`/draft-feature` never writes without **answers**, whatever channel they arrive
through. T05 writes that restatement. Is it acceptable to the humans who rely
on the current rule?

**What the rule actually says today.** Worth settling before the debate, because
`PLAN.md`'s D2 quotes a sentence that is not in the tree. D2 says the skill's
RESULT contract states a headless invocation "can only produce the proposal and
must stop before writing." `grep -r "stop before writing" --include="*.md"`
returns nothing. What `SKILL.md` actually carries is weaker:

- a `**Run interactively.**` paragraph whose stated reason is mechanical —
  `claude -p` with stdin redirected consumes the channel the interview asks
  through;
- a RESULT section that already contemplates non-interactive dispatch and
  defines `status: complete` as "the user accepted, files are written, and lint
  passes."

So the skill today does **not** forbid a headless write. It assumes a live
channel and defines completion in terms of a user's accept. D2's framing
("restated, not weakened") is defensible on that reading — but it is defending
against a sentence nobody wrote, and the reviewer should judge the real text.

**What T05 would change.** The written-in rule becomes: answers, not presence,
authorize a write. The safety property that survives is D1's — an unanswered
elicitation question falls back and nothing is written. The property that does
not survive is *a human being in the loop at write time*.

**Precedent.** FEAT-2026-0042/T03 did this exact thing to `/fix-bug`, also a
skill titled "interactive", also one that halts for humans: it added a
`## Headless mode` section, named three outcomes, and asserted the interactive
Method was untouched. T05 is drafted to follow that shape, including the
additive-only assertion against HEAD. The disanalogy a reviewer should weigh:
`/fix-bug` headless produces a fix that a PR and a test suite judge;
`/draft-feature` headless produces the *plan* everything downstream is judged
against, and its cheapest failure mode is a plausible plan built on a defaulted
decision nobody read.

**Mitigation already in the draft.** T06 refuses to build an invocation from a
`fallback` result, and T05 requires the assumptions list to be written into the
drafted `PLAN.md` — so a defaulted decision is visible to the gate-1 reviewer
rather than silent. Gate-1 review stays human under every dial; that checkpoint
is `PLAN.md`'s explicit out-of-scope line.

**Options.**

- *Accept as drafted.* Gate 2 delivers what the feature was funded for. Cost:
  the skill can write a feature folder with no human present, and the first
  such folder is reviewed at gate 1 rather than at write time.
- *Accept, but require the drafted folder to land `status: planned` and
  unarmed.* This is already the skill's behaviour ("Does not flip status to
  `active`"), so it costs nothing to make explicit in T05's criteria and closes
  most of the blast radius.
- *Reject the restatement; keep the write interactive.* The agent posts the
  interview and reads the answers, and a human still runs the write. Gate 1's
  value survives intact; the bottleneck the feature was filed for does not
  move. This is a legitimate outcome, not a failure — it makes gate 2 a
  different, smaller gate, and T05/T06/T07 would need re-drafting.

**Recommendation: accept with the second option's constraint** — the drafted
folder stays `planned` and unarmed, stated as an explicit T05 acceptance
criterion. It wins here because it preserves the one checkpoint that actually
catches a bad plan (human gate-1 review) while removing the one that only
catches a bad *typist* (a human watching the write). The reviewer is being
asked to approve unattended writing, not unattended arming.

**Recorded answer (arming, 2026-08-16).** Accepted as drafted — the
recommendation, i.e. the second option's constraint. T05's criterion 3 already
carries it (the drafted folder lands `status: planned` and unarmed), so the
unit's acceptance criteria are armed unchanged. The `human_only: true`
precondition is satisfied by this record; T05 may dispatch.

## Open question 2 — which side of the round-trip T04 should change

**The question.** § Runtime probe shows the instructed reply shape and the
accepted reply shape disagree. T04 is drafted to make the issue instruct the
shape the parser accepts (add a per-question answer template to the body). The
reverse is also available: teach the parser the numbered form.

- *Instruct the parseable shape (as drafted).* One file changes,
  `escalation.py` stays untouched, no driver restart. Cost: the operator learns
  a second reply convention — `qid: answer` lines here, a bare number on every
  other `needs-human` issue.
- *Teach the parser the numbered form.* The operator's existing habit keeps
  working. Cost: numbers cannot express elicitation answers at all, so it
  solves at most the two decision questions and the elicitation half still needs
  a prose convention. It does not actually close the gap.
- *Both.* Accept numbers for decisions and `qid:` lines for elicitation. Widest
  operator surface, most parser ambiguity, and the largest T04.

**Recommendation: as drafted (instruct the parseable shape).** The second
option cannot answer an elicitation question, which is the half D1 refuses to
default — so it does not close the gap it is proposed for.

**Recorded answer (arming, 2026-08-16).** Accepted as drafted — instruct the
parseable shape. T04's criterion 2 stands unchanged, and its escalation trigger
on a contradicting arming decision does not fire.

## One standing lint WARN, expected

`python3 -m specfuse.loop.lint_plan <feature-dir> --just-closed-gate 1` exits 0
with one advisory:

```
WARN: WU-04-reply-shape-round-trip.md: FEAT-2026-0050/T04 declares produces
path 'specfuse/agent/drafting_questions.py', but done WU FEAT-2026-0050/T01
already delivered it.
```

Correct and expected: T04 edits T01's module rather than creating a new one,
and its body states the incremental edit. The path is kept in `produces:`
deliberately — dropping it to silence the WARN would also drop the driver's
produces-vs-diff guard, which is what stops T04 closing without touching the
file.

## What a reviewer should check before arming

1. Answer § Open question 1. T05 carries `human_only: true` and should not be
   armed on a silent read.
2. Confirm T04 is armed **first** — the gate's later units consume its output,
   and without it the interview cannot be answered at all.
3. Accept or revise the § Open question 2 direction; T04's criteria change with
   it.
4. Note that gate 2's parser criteria remain unvalidated against a real
   operator. The first real reply is evidence gate 2's close should record, and
   `WU-92`'s criterion 3 already asks whether a queue entry reached a drafted
   folder without an interactive session.

More on request: the full probe transcript, the per-unit cost estimates, the
`is_driver_module_path` output for any additional path.
