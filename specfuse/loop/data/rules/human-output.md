<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: writing for the human reading the output

Binding on **everything a human reads** — skill output, status reports, pick
lists, confirmations, the summary at the end of a run. When work *stops and needs
a decision*, [`operator-escalation.md`](operator-escalation.md) governs the shape;
this rule still governs the language and the length.

The reader is using the tool, not maintaining it. They did not read the work unit,
the event log, or this repository's source.

## 1. Answer first

Open with the finding, the state, or the decision — not the derivation that
produced it. What you looked at, which files you read, and how you reached the
conclusion are evidence. Evidence goes after the answer, or behind a request for
it. A report that reconstructs your reasoning before stating its result makes the
reader do your summarising.

## 2. Short by default, complete on request

Aim for what fits on a screen. Say the thing once — a point made in the summary
does not need restating in the detail below it.

When you have more that a reader might want, do not pre-emptively include it. End
with one line naming what you are holding back and how to get it:

```
More on request: the per-attempt failure history, the cost breakdown.
```

Name the specific things, not a generic offer. "Let me know if you want more
detail" tells the reader nothing about what exists. If there is genuinely nothing
held back, omit the line rather than writing a hollow one.

Detail the reader must act on is not "more" — it belongs in the answer.

## 3. Domain words, not schema keys

Field names from `PLAN.md` frontmatter, `events.jsonl`, and work-unit status
enums are storage, not vocabulary. Say what they mean:

| Internal | Write instead |
|---|---|
| `blocked_human` | stopped — needs you |
| `awaiting_review` | waiting for your review |
| `not_met` | goal not met |
| `FOLLOW-UPS.md` | what it could not finish, one tracked issue each |
| `type: human` unit | a step waiting on a person |
| `failure_class`, `failure_signature` | why it failed, and the error it failed on |
| `attempt_outcome` | what happened on each try |
| `re_arm_count` | times this was retried after a stop |
| `correlation_id` | which work unit this belongs to |
| `produces:` | the files this was supposed to deliver |
| `hollow pass` | reported success without changing anything |

Keep the words the methodology is *made of* — feature, gate, work unit, arm,
close, roadmap. Those are the domain; explain them once where a first-time reader
meets them, then use them plainly. `.specfuse/docs/glossary.md` defines them for
a reader who wants one, so point there rather than re-explaining inline. When a raw field genuinely is the most precise
thing to show — a verbatim error, an exact status being written — show it and gloss
it once: `awaiting_review` (waiting for your review).

## 4. Every command must be runnable as printed

Naming the next command or skill is expected — it is how the reader makes
progress. It just has to work when pasted:

- `specfuse run`, `specfuse lint <feature-dir>` — the installed suite command.
  Never `python3 .specfuse/scripts/*.py`; that directory does not exist in a
  scaffolded project.
- `python3 -m specfuse.loop.<module>` for helpers with no subcommand.
- `/arm-gate`, `/gate-status` — skills, named as the user invokes them.

One command, not a chain. If checking first is optional, say so in a clause rather
than printing three commands to run in order.

## 5. Say what happened, including when it went badly

A refusal, a partial result, or a step you skipped is information the reader
needs. State it plainly and move on — no apology, no re-explaining the mistake.
Never report a step as done that was not run.
