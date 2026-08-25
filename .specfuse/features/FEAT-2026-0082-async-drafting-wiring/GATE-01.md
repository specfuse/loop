---
gate: 1
status: open
cost_budget_usd: 32.00
---

# Gate 1 — the seams closed, proven end to end

**Definition of done — stated as an outcome, not as four units.** A
`specfuse-agent` run over a `queue:` holding one undrafted `planned` feature
posts a real `drafting-needed` question issue; a later run reads a reply from
that issue's comments and produces a drafted feature folder; and that run's
`events.jsonl` shows `needs_drafting` resolving to a **completed drafting
dispatch rather than an escalation**.

This wording is verbatim FEAT-2026-0050's re-run condition for its first
carried-forward follow-up, and it is deliberately not a list of work units.

**Why the wording matters more than usual here.** 0050's gates defined done in
terms of its units. Seven units passed on their first attempt, both gates closed,
and the feature delivered something its own retrospective calls *"green in
isolation and connected to nothing."* A gate that can go green with the two seams
still unconnected would repeat that exactly. If T01–T04 all pass and the outcome
above is not demonstrated, **this gate is not done** — that is a block, not a
rounding error.

## Arming discipline

- **`autonomy_default: auto` is the operator's explicit decision**, made against
  a recommendation of `review`. It stands. Read the hazard once and move on:
  `RETROSPECTIVE.md`'s first line for 0050 is `## Gate 1 — auto-closed
  (predicate=v1)`, and that is the gate whose definition of done named neither
  seam. `evaluate_auto_close` measures attempts and costs; it has no way to ask
  whether the work is reachable. Two mitigations are applied — this gate's
  outcome-shaped definition of done, and `auto_close_disabled: true` on the
  close. The per-WU lever, if it is ever revisited, is one line:
  `human_only: true` on `WU-04-end-to-end-round-trip.md`.
- **Exactly one WU carries `unsandboxed: true`** — T04. A second WU wanting the
  flag is an escalation, not a copy-paste.
- **T04 will leave real artifacts on this repository** — at minimum one question
  issue and one comment. Expect them, and expect the close to name them so
  somebody can clean them up.
- **The chain is strictly serial.** T01 ships the emitter T02 calls; T02 posts
  the issue T03 reads; T03 injects the gate T04 exercises end to end. A unit
  whose predecessor is not `done` cannot meaningfully run.

## What this gate must not claim

FEAT-2026-0050 carried **two** follow-ups. This gate discharges the first and
**must not claim the second**.

Follow-up 2 is: *"one real `drafting-needed` question issue posted to the
repository, one operator reply, and that reply's verbatim text fed to
`parse_reply_answers` with the resulting bindings recorded."* It requires a human
to type something.

An agent that comments on its own question issue and records that as an operator
reply has manufactured its own evidence — and because it would read as verified
rather than as absent, it is a worse outcome than 0050's honest "none, ever."
The round trip T04 runs is a **scripted** reply proving the machinery; it is not
an operator, and the close says so in those words.
