---
id: FEAT-2026-0049/T08
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.50
produces:
  - specfuse/agent/providers/answers.py
  - tests/test_agent_provider_answers.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.11.0
started_at: 2026-08-11T03:40:03.853026+00:00
duration_seconds: 802.802
cost_usd: 1.543806
input_tokens: 1004
output_tokens: 20222
---

# T08 — the answered-escalation provider

**Context.** An action class in its own right, ranked first by T05: an operator's
answer may cancel or redirect work already queued, so reading answers before
spending on anything else is the whole point of the ordering.

Unlike the other providers, this one composes no single shipped function —
nothing in the repo parses an escalation answer today. What *is* shipped is the
contract to parse against, all of it in `specfuse/loop/escalation.py`:

- `NEEDS_HUMAN_LABEL` — the label every escalation issue carries.
- The correlation marker `<!-- specfuse:escalation id=... -->`
  (`_CORRELATION_MARKER_TEMPLATE`, `escalation.py:44`), which threads the issue
  back to the unit that raised it.
- The numbered-answers section `render_escalation_body` writes
  (`escalation.py:97-103`): a `Reply with a number` heading followed by the same
  numbered option labels as the options section. `validate_escalation_body`
  is the shipped reader of that shape and states the invariant — at least two
  numbered options plus the marker.
- `specfuse/loop/notify_sla.py`'s `PARKED_LABEL`, added to escalations past the
  SLA window. Parked is a label, not a close; a parked escalation is still
  awaiting a human and is still answerable.

**Scope: this unit records an answer; it does not execute the chosen option.**
What option *N* means is free text written by whichever unit raised the
escalation, so executing it is not a general capability the agent can have. The
provider parses the choice and leaves a durable acknowledgment — and **leaves the
issue in the human inbox**. `GATE-02-REVIEW.md`'s OQ-2 was resolved at the
`/arm-gate` checkpoint in favour of the label staying until the chosen option is
executed: an inbox that overstates outstanding work is safer than one that drops
an answered-but-unacted item silently. Since no gate-2 provider executes an
option, that means answered escalations accumulate `needs-human` until a later
gate can act — a consequence the operator accepted explicitly. If the answer is
unanswerable-in-place, the issue is left exactly as it was.

**The snapshot does not carry comments.** `state._read_issues` requests
`number,title,labels,body` only. This provider reads comments itself through the
injected runner (`gh issue view --json comments`), the same read-only shape
`autofix_run._read_finding_issue` uses. Extending T02's snapshot is a gate-1
surface change and is out of bounds here.

**Acceptance criteria.**

1. `tests/test_agent_provider_answers.py::TestAnsweredEscalations::test_numbered_reply_is_parsed_and_acknowledged`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_provider_answers.TestAnsweredEscalations.test_numbered_reply_is_parsed_and_acknowledged`.
2. `specfuse/agent/providers/answers.py` implements T05's protocol, advertising
   `kind="escalation-answer"` items for open issues that carry
   `NEEDS_HUMAN_LABEL` **and** the escalation correlation marker **and** at least
   one comment selecting one of the body's numbered options.
3. The same test passes after this WU's edits.
4. The label name, the marker pattern, and the numbered-answers shape are read
   from `specfuse.loop.escalation`'s own constants and renderer output — this
   module contains no literal copy of the marker string, the label string, or the
   `Reply with a number` heading (§8).
5. An acknowledged answer produces exactly one `gh issue comment` naming the
   parsed option and the correlation ID. **`NEEDS_HUMAN_LABEL` is NOT removed** —
   the label stays until the chosen option is actually executed, which no gate-2
   provider does. A test asserts the injected runner receives no
   `gh issue edit --remove-label needs-human` for an acknowledged issue. The
   write is idempotent: a second pass over an issue that already carries the
   acknowledgment writes nothing at all. Three tests.

   *Operator's decision at the `/arm-gate` checkpoint, resolving
   `GATE-02-REVIEW.md`'s OQ-2 — see that file's "Open questions — resolved at
   arming" section for their words and the consequence they accepted.*
6. An issue whose comments match no numbered option is left untouched — no
   comment, no label change — and is not advertised twice in the same run.
   `PARKED_LABEL` is never removed by this provider.
7. The provider is registered in `default_providers()` and performs no git
   mutation of its own; a test asserts the injected runner receives no `git`
   command and no `gh issue close`.

**Do not touch.** `specfuse/loop/` entirely — `escalation.py` and `notify_sla.py`
are read for their constants and consumed unmodified; a needed change there is a
plan change. `specfuse/monitor/`. `specfuse/agent/state.py` (in particular, do
not add comments to the snapshot) and `specfuse/agent/budget.py`.
`specfuse/agent/run.py` **except** the one-line registration in
`default_providers()`. The sibling gate-2 WU files (`WU-05`, `WU-06`, `WU-07`)
and their modules. The driver owns all git; this session edits files only and
runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.providers.answers import AnsweredEscalationProvider; print(AnsweredEscalationProvider)"`
and a negative observation for criterion 4:
`python3 -c "import specfuse.agent.providers.answers as m, inspect; src=inspect.getsource(m); assert 'specfuse:escalation' not in src and 'needs-human' not in src, 'contract literal copied into the provider'"`.

**Escalation triggers.** If the acknowledgment cannot be written without a new
label or a new marker format, stop and name it: minting a cross-surface value is
exactly what §8 forbids a drafted-ahead WU to do, and the existing comment-marker
convention (`notify_sla`'s re-ping marker) is the precedent to reuse or to
explicitly reject. If `GATE-02-REVIEW.md`'s open question on the `needs-human`
lifecycle is still unanswered when this unit is dispatched, stop rather than
picking a side — criterion 5 is written to one reading of it and the operator
owns which. If reading an issue's comments through the injected runner turns out
to need a mutating `gh` subcommand, stop: this provider's `advertise` is
read-only by design.
