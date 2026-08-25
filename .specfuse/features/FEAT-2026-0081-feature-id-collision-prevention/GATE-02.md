---
gate: 2
status: open
---

# Gate 2 — Cheap recovery: renumbering as a command

Definition of done: renumbering a feature is one command whose result is
verifiable, instead of a hand sweep across a dozen files where getting it wrong
is silent.

**This gate is deliberately undrafted.** Its substantive work units are written
by gate 1's `plan-next` (`FEAT-2026-0081/G1-PLAN`), against what gate 1 actually
shipped rather than against a guess made before it ran. The terminal `close` work
unit below is pre-declared so the linter reads gate 1 as non-terminal; `plan-next`
inserts the substantive units above it and sets its real `depends_on`.

## What `plan-next` must carry into this gate

**The ID-bearing surface list T02 enumerates.** Gate 1's collision check has to
know every place a feature ID is claimed in order to compare them. That
enumeration is this gate's work list. Re-deriving it by inspection is precisely
how the original manual renumbering missed files.

**The keep-the-old-ID rule, verbatim from PLAN.md's scope boundary.**
`events.jsonl` and `PLAN.baseline.json` keep the **old** correlation ID under any
renumbering: the run really did execute under it, and rewriting a log to match a
later rename falsifies history to tidy a name. The renumbered feature's
retrospective carries a note so a future reader correlating events knows what to
expect. This rule is stated in the PLAN because it is the one most likely to be
reasoned away at drafting time by someone optimising for internal consistency —
do not let a gate-2 work unit "fix" it.

**The CLI boundary.** `specfuse-renumber` ships as a flat console script in this
repo's `[project.scripts]`, working standalone. `specfuse renumber` requires a
one-line `DELEGATED_COMMANDS` entry in the umbrella repo, which this repo cannot
land — it is a cross-repo follow-up, not a work unit here.

## Arming discipline

A renumbering command is a bulk mutator over a feature folder, the roadmap, and
the archive. Whatever shape `plan-next` gives it, the gate should not arm without
a dry-run mode and a criterion that exercises it, because the failure this
feature exists to make cheap is a silent partial rewrite — and a tool that
produces one is worse than the hand sweep it replaces.
