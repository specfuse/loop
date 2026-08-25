---
feature_id: FEAT-2026-0082
title: Wire the async drafting interview end to end
slug: async-drafting-wiring
branch: feat/FEAT-2026-0082-async-drafting-wiring
roadmap_goal: A specfuse-agent run over a queue holding one undrafted planned feature posts a real drafting-needed question issue, and a later run reads the operator's reply from that issue's comments and produces a drafted feature folder — with events.jsonl showing needs_drafting resolving to a completed drafting dispatch rather than an escalation.
autonomy_default: auto
status: planned
planned_cost_usd: 26.00
---

# Plan: Wire the async drafting interview end to end

FEAT-2026-0050 built the async drafting interview — question-set builder, issue
renderer, reply parser, D1 answer gate, headless drafting invocation, provider
dispatch branch — and closed `partially_met` because **none of it is reachable**.
Seven work units, every one green on its first attempt, delivering a feature its
own retrospective describes as *"green in isolation and connected to nothing."*

Two seams were never assigned to any work unit, and neither gate's definition of
done named either one, so every unit could pass while the bottleneck the feature
was funded for stayed exactly where it was:

```
specfuse/agent/drafting_questions.py:264  render_question_issue(correlation_id, questions) -> (body, labels)
  callers in production: none. The issue is rendered by nothing.

specfuse/agent/providers/feature.py:79    answer_gate: Optional[...]
specfuse/agent/providers/feature.py:90    self._answer_gate = answer_gate or self._fallback_answer_gate
specfuse/agent/run.py:640                 FeatureProvider(...) constructed with NO answer_gate
  so _dispatch_drafting (feature.py:223) takes the fallback branch on every real run.
```

The operator accepted 0050's hedge on 2026-08-17 with the reason *"This will have
to be tested with a real feature."* This feature is the work that makes that test
possible, and its measurable claim is 0050's own re-run condition, unchanged.

**Live evidence that the bottleneck is still real.** Two `drafting-needed`
escalations (#2381, #2383) were filed against this repository and cleared on
2026-08-25 by an operator running `/draft-feature` interactively — precisely the
manual path this feature exists to remove.

## Scope boundary

**IN.** A shared body-supplied issue emitter; the caller that posts the rendered
question issue; the `answer_gate` that reads the reply back and is injected in
`default_providers`; and one real end-to-end round trip proving a queue entry
reaches a drafted folder without an interactive session.

**OUT, deliberately.**

- **Discharging 0050's second carried-forward follow-up.** That one reads: *"one
  real `drafting-needed` question issue posted to the repository, one operator
  reply, and that reply's verbatim text fed to `parse_reply_answers`."* It needs
  a human to type something. **An agent commenting on its own question issue and
  recording that as an operator reply is manufactured evidence** — a worse hollow
  pass than 0050's, because it would read as verified rather than as absent. It
  stays open. See T04's escalation triggers and the close's forbidden claim.
- **Changing the question set itself.** `build_question_set`'s content, the D1
  gate's semantics, and `parse_reply_answers`' grammar are 0050's and ship
  unchanged. This feature connects them; it does not redesign them. If the real
  round trip shows the parser is wrong, that is a finding to record, not a fix to
  make here.
- **Gate-1 review of any folder this drafts.** Stays human. A drafted folder
  still lands `status: planned` and unarmed, exactly as the interactive path
  produces.
- **Widening beyond `needs_drafting`.** The other dispositions
  (`blocked`, `unreadable`) keep escalating as they do today.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rn "render_question_issue" specfuse/
  -> defined at drafting_questions.py:264; NO production caller

grep -rn "answer_gate" specfuse/agent/
  -> feature.py:79 (param), :90 (fallback default), :223 (call site)
  -> run.py default_providers: never passes it

grep -n "_find_existing_issue|_correlation_marker|_extract_issue_number" specfuse/loop/escalation.py
  -> :158, :55, :201  — the idempotent find-then-create seam, shipped

grep -rn "emit_issue_with_body" specfuse/
  -> 0 hits
```

**Verdict: reusing three shipped mechanisms, building one small new one.**

- **The idempotency seam: found `specfuse/loop/escalation.py`, reusing.**
  `emit_escalation`'s docstring states the property: *"Idempotent: searches for
  an open issue carrying the `needs-human` label and this correlation ID's
  marker before creating."* What it cannot do is take a body somebody else
  rendered — it renders its own. T01 adds `emit_issue_with_body` over the same
  private helpers, and `emit_escalation` becomes a caller rather than a rival.
- **The renderer, the parser, and the gate: all shipped by 0050, all unchanged.**
  `render_question_issue`, `parse_reply_answers`, `evaluate_answer_gate`,
  `build_invocation`. This feature supplies callers. Any change to their
  semantics is out of scope per the boundary above.
- **The provider seam is already a parameter.** `FeatureProvider.__init__` takes
  `answer_gate` and defaults it. T03 injects one; it does not restructure the
  provider.

**Cross-feature coordination (approved at draft time).** FEAT-2026-0052/T03 —
merged, unarmed — was drafted to add `emit_tracking_issue` as a sibling in
`escalation.py`. It needs the same "file an issue from a body I already rendered"
shape. That WU has been given a line telling it to **call
`emit_issue_with_body` if it exists** rather than adding a second near-identical
find-then-create path. This feature ships the shared function because it is ahead
of 0052 in the `agent-policy.yml` queue and because it is the feature that needs
it working end to end.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature flips no severity and adds no blocking check. The nearest thing to
one is T02's suppression rule, and the honest form of the §2 question for it is:

> **What does the run do on a queue entry that is already drafted?**

**Nothing new.** `classify_queue_entry` returns `workable`, not
`needs_drafting`, so neither the poster nor the answer gate is reached and the
run advances the feature exactly as it does today. T02 carries a test asserting a
drafted queue entry posts no question issue — the no-op case, which is the one
that would otherwise spam an issue per run per feature.

And the inverse, which is this feature's actual risk:

> **What does the run do when the question issue cannot be posted?**

**It falls back to today's escalation.** The `needs-human` issue still gets
filed, so a feature waiting on a human is never invisible. T02 owns both exits
and tests both.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0082/T01
        file: WU-01-emit-issue-with-body.md
        depends_on: []
      - id: FEAT-2026-0082/T02
        file: WU-02-post-question-issue.md
        depends_on: [FEAT-2026-0082/T01]
      - id: FEAT-2026-0082/T03
        file: WU-03-answer-gate-wiring.md
        depends_on: [FEAT-2026-0082/T02]
      - id: FEAT-2026-0082/T04
        file: WU-04-end-to-end-round-trip.md
        depends_on: [FEAT-2026-0082/T03]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0082/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0082/T01
          - FEAT-2026-0082/T02
          - FEAT-2026-0082/T03
          - FEAT-2026-0082/T04
```

## Notes

- **Single-gate feature** (4 substantive WUs ≤ 4): one terminal `close`, no
  `close-intermediate` and no `plan-next` — ceremony proportionality,
  `docs/methodology.md §6`.
- **The gate's definition of done is the end-to-end outcome, not the four
  units.** This is the correction 0050 earned: its gates' definitions of done
  named units, so seven green units satisfied them while nothing was reachable.
  A gate that can go green with the seams unconnected has learned nothing from
  the feature it repairs. See `GATE-01.md`.
- **The question issue replaces the escalation rather than accompanying it.**
  `render_question_issue` already *"composes over
  `escalation.render_escalation_body`"* (its docstring), so it is an escalation
  body with per-question markers added. Filing both would put two issues asking
  one human the same thing into the `needs-human` inbox, which is how an inbox
  gets ignored. `/answer-escalation` (FEAT-2026-0080, shipped) already works that
  queue.
- **`autonomy_default: auto` is the operator's explicit choice**, made against a
  recommendation of `review`. Recorded so a later reader does not read it as an
  oversight. The specific hazard, stated once: `RETROSPECTIVE.md`'s first line
  for 0050 reads `## Gate 1 — auto-closed (predicate=v1)`, and that is the gate
  whose definition of done named neither seam. The predicate cannot evaluate
  "is any of this reachable." The mitigations applied here are the gate's
  end-to-end definition of done and `auto_close_disabled: true` on the close;
  the per-WU `human_only: true` lever was deliberately **not** applied.
- **Under `auto`, closes stage lessons to `.specfuse/LEARNINGS-pending.md`.**
  `assert_learnings_staged_under_auto` refuses a direct `LEARNINGS.md` write and
  checks after dispatch, so a criterion naming the real file costs a full
  re-attempt.
- **Exactly one WU carries `unsandboxed: true`** — T04, the real `gh` round
  trip. Per `[FEAT-2026-0014/T01/gh-claudeP-broken]` (CORRECTED) that flag is the
  sanctioned lever and the escape stays confined to the unit that needs it.
- **Queue position.** `agent-policy.yml` puts this at the head, ahead of
  FEAT-2026-0081, because both touch `/draft-feature` and this one *"unblocks the
  queue itself."* Landing it first is what keeps 0081's T03 from editing a prose
  surface this feature is still rewiring.
