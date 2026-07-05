<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: the verification discipline

Every unit of work runs the same four-step cycle: **state intent, act, verify,
report.** This is the surface-neutral core of the discipline. Each execution
surface expresses step 4 (report) in its own shape — the loop's RESULT block, the
orchestrator's `task_completed` event — but the cycle, and the honesty it demands,
are identical everywhere. This rule is core substrate; the surface-specific report
shapes (`result-contract.md` on the loop, `verify-before-report.md` on the
orchestrator) build on it and must not weaken it.

## The four steps

### 1. State intent
Before acting, state in one sentence what you are about to do and why it is the
next right step. If you cannot state it clearly, you are not ready to act; if the
intent disagrees with the unit's acceptance criteria, the unit is not what you
thought it was. Stay factual and present-tense.

### 2. Act
Perform the change within the scope declared in step 1. If the act expands beyond
the intent — "while I was here I also fixed X" — either revise the intent and
stay, or stop and leave X for another unit. Drift between intent and action is the
most common source of ambiguous diffs. The unit's **Do not touch** boundary is
binding.

### 3. Verify
Two generic meanings, both apply unless the unit narrows the scope:

- **Re-read the produced artifact.** After writing a file, read it back; after
  editing a fixture, inspect the result. The Write/Edit tool reports success for
  the action it took, not for the property you wanted. This catches silent
  truncation, encoding surprises, and "I thought I wrote X but wrote Y."
- **Run the declared verification commands.** The unit names the checks that
  decide done. Run them yourself first, in declared order, with full output.
  Generic verifications — "I assume the tests still pass" — are not verifications.
  The commands are the verification.

**Verification is the exit oracle.** The agent's own report is advisory; done is
decided by the checks passing, not by the agent's belief. If a check fails you are
in one of three situations:

1. **Correctable locally.** Fix the cause, re-run the **full** check set from the
   top, then continue. A re-run that fixes the original failure but introduces a
   new one is still a failed cycle.
2. **Spinning threshold reached** (typically three fresh attempts on one unit).
   Signal blocked with precise evidence rather than spending the cycle guessing.
3. **Fundamentally blocked.** A spec ambiguity, generated code that must change, a
   missing dependency — signal blocked immediately, naming the boundary.

### 4. Report
Report only what verification confirmed. An optimistic report is worse than none:
the driver (or merge gate) re-runs the checks, discovers the gap, the attempt is
wasted, and the next session inherits no useful evidence about why. The concrete
report shape is surface-specific — see `result-contract.md` (loop RESULT block) or
`verify-before-report.md` (orchestrator event). Both carry the same obligation:
no claim of completion without the verification evidence behind it.

## Blocked is a respectable outcome

Signalling blocked after one honest attempt is cheaper than three fresh attempts
chasing a completion the checks keep rejecting. When an escalation trigger fires,
or a unit's acceptance criteria appear to require crossing a boundary named in
`never-touch.md` or `security-boundaries.md`, **stop and signal blocked with a
precise reason naming the boundary** — do not work around it. Silence at a
boundary is not permission. How "blocked" is signalled is surface-specific (a
`status: blocked` RESULT on the loop; a `blocked_*` state transition plus
escalation on the orchestrator); the obligation to stop rather than improvise is
core.

## Honesty over optimism

The whole coordination model runs on the report being an honest claim about what
happened. When a session skips verification, the cost is not its own — it is paid
by the next session that inherits a broken assumption, the driver that wastes
attempts, and the human who reviews evidence that turns out to be wrong. State
intent. Act. Verify. Report. Every time.
