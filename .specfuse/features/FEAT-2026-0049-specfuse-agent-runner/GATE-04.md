---
gate: 4
status: open
---

# Gate 4 — the agent advances features

## Definition of done

The agent reads the `queue:` top, advances that feature by invoking `specfuse
run` as a subprocess, classifies the driver's halt, escalates on
`awaiting_review` and switches to the next workable item, and parks blocked items
with an escalation. A drafting-needed queue top escalates rather than drafting —
async drafting is FEAT-2026-0050, explicitly out of scope here.

This is the terminal gate: its closing sequence is a single `close` work unit.

## Status

Substantive work units are drafted by gate 3's `plan-next` (`G3-PLAN`). The
terminal `close` WU is scaffolded now as a `draft` placeholder so the linter
reads the earlier gates as non-terminal; `G3-PLAN` inserts gate 4's substantive
units above it and sets its real `depends_on`.

**Renumbered from gate 3 by `G2-PLAN` (2026-08-11).** The findings gate was
inserted ahead of this one — the sizing decision recorded in `GATE-02-REVIEW.md`
§ "The sizing decision" — which moved this gate and its terminal close from 3 to
4. Nothing else about this gate changed.

## The constraint that must survive to here

The driver is invoked as a **subprocess**, never imported and called in-process.
Two live defects make in-process invocation wrong: #757 (a work unit that edits
the driver cannot take effect for anything the same process dispatches
afterwards) and #1040 (console scripts resolving `specfuse.loop` from
site-packages rather than the working tree). A gate-4 work unit that imports
`loop.run` has broken the feature's central design decision.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** Halt classification reads
  the driver's exit codes and halt reasons. If any drafted WU changes what a halt
  *means* rather than only reading it, that is a severity change and needs the
  local runtime probe before arming.
- **Subprocess invariant.** Confirm no drafted WU imports `loop.run`. This is the
  one constraint that must survive from draft time to here; check it at arming,
  when the WUs actually exist, rather than trusting the prose above. Note it now
  survives an extra gate: it was drafted when this was gate 3.
- **Scope check.** A drafting-needed queue top escalates. A drafted WU that
  attempts to draft a feature has taken on FEAT-2026-0050's scope and must not be
  armed.
