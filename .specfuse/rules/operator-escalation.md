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

## What "plain English" means

- **No unexplained jargon on first use.** Write "the list of criteria nobody
  actually verified", then name it. `met_locally`, `closing_deliverable_missing`,
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
