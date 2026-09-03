<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: operator escalation framing

Binding whenever work **stops and needs a human decision** — a `blocked` work
unit, a gate at `awaiting_review`, a hedged verdict, a scope question, a refusal,
or any skill that asks before writing.

The audience is someone **deciding**, not someone executing. They may not have
been following. Lead with the shape of the problem; put the evidence after.

Language and length are governed by [`human-output.md`](human-output.md); this
rule governs what an escalation must *contain*.

## How much to write

The six parts below are the required **content**, not a required length. Deliver
them as a decision brief a reader can act on without scrolling:

- **Always in full:** what this is about (2), what decision is needed (3), the
  options named with their one-line trade-off (5), and the recommendation (6).
- **One line each, expanded on request:** the state so far (1) and why it did not
  close automatically (4). One sentence each is usually enough to make the
  decision; the cost table, the guard name, and the attempt history are evidence.
- **Held back until asked:** per-work-unit narration, event excerpts, full cost
  reconciliation, artifact paths beyond the one or two worth opening.

Close with a single line naming what you are holding, so the reader knows the
depth exists and can ask for exactly the part they want:

```
More on request: the attempt history, the full cost breakdown, the retrospective.
```

Compressing is not the same as omitting. Every part still has to be *answered* —
a decision brief that drops the trade-offs or the recommendation has not become
concise, it has become useless. When a part genuinely has nothing to report, say
so in that line rather than dropping it silently.

## The six parts, in this order

1. **What has been done so far.** The state, not the narrative. What landed, what
   passed, what it cost.
2. **What this issue is about.** The underlying problem in plain English —
   understandable to someone who has not read the work unit, the issue, or the
   code.
3. **What decision is needed, and why.** The specific thing only a human can
   settle, and what turns on it.
4. **Why it did not, or could not, close automatically.** Name the mechanism that
   withheld it. *"The safety catch fired as designed"* and *"something broke"* are
   different answers and must not read the same.
5. **Options, each with pros and cons.** Include the reject / do-nothing option.
   Prose, not a bare table — a table flattens away the trade-offs that make the
   choice legible.
6. **A recommendation**, with the one reason it wins *here*.

## The feature briefing — required when the halt is at feature scope

The six parts frame a **decision**. When the halt is at feature or gate scope —
a hedged terminal verdict, a feature that stopped partway and needs a human —
the decision is not the whole question. The operator also needs to know whether
the work *achieved what it was funded to achieve*, and that is a separate
question from whether the tasks passed.

Lead with this briefing. The six parts follow inside part 6. Points 1–5 are a
paragraph at most each — the operator is reading to judge whether the spend
bought what it was meant to buy, and that judgement rarely needs more. The same
"more on request" line closes the briefing.

1. **Why we picked this.** The business problem, in the terms that justified the
   spend — the cost, the risk, the recurring pain. Take it from the roadmap
   row's own framing; do not invent a rationale that sounds better.
2. **What we set out to accomplish — and whether that claim still stands.** If
   the goal or the expected benefit changed during the work, say so plainly and
   say what it is now. A business case that quietly shrank is the single most
   important thing an operator can be told, and the easiest to omit.
3. **What was delivered**, in outcome terms. What can be done now that could not
   before.
4. **Where it fell short, and why.** Including — stated as a headline, not
   buried — whether the feature has actually been *shown* to deliver its benefit.
   Separate "not proven" from "disproven"; they are different, and conflating
   them either oversells or buries real work.
5. **What it cost**, against what was planned.
6. **What the operator must do to bring it to completion**, in order, with the
   decision framed per the six parts above.
7. **What to be aware of going forward.** Expectations to reset, limits that
   outlive this feature, anything a reader would otherwise assume wrongly.

### The rule this briefing exists to enforce

**"Every work unit passed" is not "the feature worked."** Answer the second
question explicitly, and answer it first. A feature can land every task green,
every gate clean, and under budget, while the outcome it was funded for remains
unmeasured — that is a normal result, not a shameful one, and reporting it as
success is the failure this section prevents.

### What to leave out

- **Per-work-unit narration.** Which unit passed on which attempt is machinery.
  It belongs below the briefing or in an answer to a follow-up question, never
  in the briefing itself.
- **Guard names, correlation IDs, verdict literals, file paths** as the *carrier*
  of meaning. Say what happened; name the artifact afterwards for anyone who
  wants to look.
- **Anything not traceable to an artifact.** Every claim comes from the roadmap
  row, the retrospective, the follow-up record, or the cost reconciliation.
  Business rationale is never reconstructed from the diff.

## What "plain English" means

- **No unexplained jargon on first use.** Write "the list of criteria nobody
  actually verified", then name it. `not_met`, `closing_deliverable_missing`,
  and `assert_gate_review_exists` mean nothing to someone deciding whether to
  ship.
- **Name what a thing *does*, not what it is called.** "The command that refuses
  unfinished features" beats "`/wrap-feature`'s hard rule."
- **Evidence goes after the framing, never instead of it.** Correlation IDs, cost
  tables, and guard names are all still required — below the six parts.

## Three failures this rule exists to prevent

- **Options without a recommendation.** Surfacing choices and stopping pushes the
  analysis back onto the person who asked. Always make the call; they can override.
- **A refusal reported as a malfunction.** A withheld terminal flip on a hedged
  verdict is the contract working. Reporting it in the same tone as a crash makes
  a correct system look broken and invites someone to "fix" the safety catch.
- **Writing the human's own justification for them.** Where a field records *why a
  human accepted something* — `/accept-hedged-close`'s reason line, `/unblock-wu`'s
  rationale, a contract-change acknowledgment — that text must come from the human.
  An agent that drafts it has removed the signature it was collecting. Ask; do not
  supply.

> **Provenance — the feature briefing.** Requested by the operator on
> 2026-08-06 at FEAT-2026-0056's hedged close. The escalation satisfied the six
> parts and was still the wrong answer: it reported which work units passed, what
> each cost, and which guard withheld the flips, when the question was *"why did
> we build this, did it work, and what do I do now?"* The operator's own words —
> *"I don't care about the machinery and how each WU succeeded or not."* That
> feature also demonstrated the rule above: eleven work units green, both gates
> under budget, and the benefit it was funded for still unmeasured, because the
> saving only appears on a repeat close and only a first close had run.
>
> **Provenance.** Requested by the operator on 2026-07-27 at FEAT-2026-0070's
> hedged close. Escalations to that point led with correlation IDs, guard names,
> and cost deltas — accurate, and unreadable to anyone deciding rather than
> executing. The same close also demonstrated the third failure: the feature had
> shipped `/accept-hedged-close`, whose whole purpose is to capture an operator's
> reason, and the agent's first instinct was to draft that reason itself.

## Relationship to the other rules

[`result-contract.md`](result-contract.md) governs the **machine-readable** RESULT
block a dispatched unit emits — `status: blocked` and its `blocked_reason`. This
rule governs the **human-readable prose** that accompanies any halt, wherever it
surfaces: a skill's output, a gate review, a close's escalation section. A unit
that emits a correct RESULT block and an unreadable explanation has satisfied one
and failed the other.
