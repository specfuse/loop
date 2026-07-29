---
gate: 2
status: open
# cost_budget_usd: <set at arming — sum of G1-PLAN's drafted units plus one
# re-attempt of the largest. Deliberately unset until then; see GATE-01.md's
# arming-discipline note.>
---

# Gate 2 — Live arming behind the dial

## Definition of done (skeletal — G1-PLAN drafts the work units)

An `auto` feature arms its next gate without a human when the predicate says
`would_arm`; every stop class parks at `awaiting_review` with the reason
labeled in the event. Sketch of the substantive work: the atomic arm
transaction (one bookkeeping commit: draft→pending flips + gate flip +
tag-before-arm revert point), the dial read from `autonomy_default`, the
contract-field lint warns flipping to blocking under `auto`, FEATURE-REVIEW.md
accumulation of per-gate doubt summaries, and LEARNINGS entries staged to a
pending file promoted at PR review.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Populated when G1-PLAN drafts this gate. Known already: the lint
blocking-under-`auto` flip is a severity flip — §4 runtime probe (lint every
feature folder, paste the finding list into `GATE-02-REVIEW.md`) and §2
satisfiability are mandatory before arming. See `GATE-01.md`'s arming notes.

## Reflection notes

<Written by the human at review time.>
