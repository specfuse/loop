---
name: answer-escalation
description: "Read one parked needs-human GitHub issue, explain in plain English what stopped the agent, and record the operator's disposition — hand off, answer, close, or skip. Leaves guidance the next agent run reads and unparks the issue. Trigger phrases: /answer-escalation, answer this escalation, work the needs-human queue, disposition issue NN, unpark issue NN."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Answer an escalation (interactive, human-invoked only)

This skill reads one parked `needs-human` GitHub issue, explains what stopped
the agent in plain English, and records the operator's disposition so the next
agent run reads real guidance instead of finding the issue still parked.
`AnsweredEscalationProvider` (`specfuse/agent/providers/answers.py`) already
posts an acknowledgment comment when an operator replies with a number, but its
own docstring says it "does not carry out the chosen option" and leaves
`NEEDS_HUMAN_LABEL` in place. `BugsProvider.advertise` skips any issue carrying
`needs-human` or `blocked-wu`. Net effect without this skill: an answered
escalation stays parked forever.

**Human-invoked only — never run headless.** The disposition choice is the
entire point of this skill: which of four options an escalation gets is a
judgment call, not something inferable from the issue text. A headless
invocation with stdin redirected has no channel to supply that choice, so
there is nothing to fall back to — unlike a skill with a sensible default,
skipping the question here means guessing the operator's decision for them.
Run this interactively.

## What this skill does not do

- **Triggers no fix and no retry.** It never invokes `/fix-bug`, never opens a
  PR, and never merges anything. Every disposition below either hands the
  operator to another skill to run themselves, or records prose.
- **Does not carry out the option on the operator's behalf.** Handing off to
  `/arm-gate` or `/draft-feature` means naming the command for the human to
  run — this skill does not run it for them. The distinction is the invoker,
  not the callee.

## Method

### 1. Pick the issue

Read the operator's target issue number, or list open `needs-human`-labelled
issues (`gh issue list --label needs-human --state open`) and let them pick
one.

**Graceful `gh` degradation.** Probe `gh auth status` first. If `gh` is
unavailable or unauthenticated, report that plainly and stop — do not attempt
to half-apply a disposition (e.g. drafting guidance with no way to write it
back). There is no degraded mode for this skill; every disposition below ends
in a `gh` write.

### 2. Read and explain the escalation

Read the issue's title, body, labels, and comments (`gh issue view <number>
--json title,body,labels,comments`). The body follows
`.specfuse/rules/operator-escalation.md`'s six-part shape (what's been done,
what this is about, what decision is needed, why it didn't close
automatically, options with pros and cons, a recommendation) — present that
framing back to the operator per `.specfuse/rules/human-output.md`, not the
raw issue text. Read any existing comments too: a prior reply may already
carry a numbered answer that `AnsweredEscalationProvider` acknowledged but
never acted on.

### 3. Route by category

Read the issue's category label — one of `escalation.CATEGORY_LABELS`. Each
category has one owning skill; this skill's job is to route the operator to
it, not to reimplement it:

| Category | Owning skill |
|---|---|
| `gate-review` | `/arm-gate` |
| `drafting-needed` | `/draft-feature` |
| `blocked-wu` | `/unblock-wu` (work-unit level) or `/roadmap-add` (promote to a feature) |
| `triage-question` | `/triage-issues` |
| `merge-approval` | merged by hand — point the operator at the PR, do not merge it |

Present the routing as part of the explanation from step 2 — "this is a
`<category>` escalation, which `<owning skill>` owns" — before asking for a
disposition.

### 4. Ask for a disposition

Offer exactly four dispositions, each documented as its own step below. Ask
in plain text, prose options with pros and cons per
`.specfuse/rules/human-output.md` — never a table, never an AskUserQuestion
picker.

#### Disposition: hand off

The operator wants to run the owning skill from step 3 themselves. Name the
exact command (e.g. `/arm-gate`, `/unblock-wu`) and stop — this skill does not
invoke it. Once the operator has run it and the underlying state has changed
(gate armed, WU unblocked, issue promoted), proceed to step 5 to release the
label; the guidance comment can note that the owning skill was run directly.

#### Disposition: answer

The operator supplies free-text guidance for the next agent run — a numbered
option from the issue, or prose that doesn't fit one. Write that guidance
verbatim; do not draft it on the operator's behalf
(`.specfuse/rules/operator-escalation.md`'s "writing the human's own
justification for them" failure). Proceed to step 5.

#### Disposition: close

The escalation is resolved and needs no further agent action — e.g. the
operator fixed it out of band. Record why in the guidance comment, then
proceed to step 5 and also close the issue (`gh issue close <number>`).

#### Disposition: skip

The operator defers the decision to a later session. **Writes nothing at
all** — no guidance comment, no label edit, no issue state change. An
operator who defers must leave no trace a later reader could mistake for a
decision made now. Do not proceed to step 5.

### 5. Write order: guidance comment first, label release second

For every disposition except `skip`:

1. Post the guidance as a comment carrying the marker
   `<!-- specfuse:operator-guidance id=<correlation_id> -->` (the same
   `<!-- specfuse:... -->` idiom `escalation.py`'s own correlation and
   acknowledgment markers use), so a later reader — human or agent — can
   locate the operator's guidance mechanically:
   `gh issue comment <number> --repo <repo> --body "<guidance>\n<!-- specfuse:operator-guidance id=<correlation_id> -->"`
2. Only after that comment succeeds, remove `NEEDS_HUMAN_LABEL` (and, for
   `blocked-wu`, `blocked-wu` too) from the issue:
   `gh issue edit <number> --repo <repo> --remove-label needs-human --remove-label blocked-wu`

   **Both labels, not just `needs-human`.** `BugsProvider._HUMAN_OWNED_LABELS`
   is `{needs-human, blocked-wu}` and skips an issue carrying *either*, so
   releasing only the first leaves the issue answered and still parked — the
   exact failure this skill exists to remove. Omit `--remove-label blocked-wu`
   only when the issue does not carry it (`gh issue edit` errors on removing a
   label that is absent).

This order is deliberate (PLAN.md D3): the comment is the authoritative
record, the label is a projection of it. A failed label release leaves an
issue correctly answered and merely still-parked — recoverable and visible.
Releasing the label before the comment lands risks the reverse: an unparked
issue with no guidance, which is the state that produced this skill.

## Example (placeholder values)

```
$ gh issue view 42 --repo example-org/example-repo --json title,body,labels,comments
...
Category: blocked-wu — owning skill: /unblock-wu
Operator disposition: answer
Guidance: "Credentials rotated; re-run should succeed now."

$ gh issue comment 42 --repo example-org/example-repo --body \
  "Credentials rotated; re-run should succeed now.
<!-- specfuse:operator-guidance id=FEAT-2026-0080/T01 -->"

$ gh issue edit 42 --repo example-org/example-repo --remove-label needs-human --remove-label blocked-wu
```

## What this skill is not

Not an executor: it never runs `/fix-bug`, never opens a PR, never merges.
Not a second source of truth: the issue and its comments remain
authoritative; this skill only reads and appends to them. Not headless-safe:
every run needs the interactive channel to collect the operator's
disposition.
