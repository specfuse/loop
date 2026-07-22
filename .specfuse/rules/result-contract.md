<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: the RESULT block contract

Every work-unit session ends with a single fenced `result` block as the very last
thing in its output. The driver reads it; a session that does not emit one is treated
as a failed attempt. This is the agent-to-driver interface, and it is the single-repo
shape of the orchestrator's `task_completed` event — keep them aligned so the fold-in
is a rename, not a redesign.

The agent's RESULT is **advisory**. The driver runs verification itself (see
[`../skills/verification/SKILL.md`](../skills/verification/SKILL.md)) and that is
what decides done. Report honestly: claiming `complete` on work that fails the gates
wastes an attempt and teaches the next session nothing.

## The four-step discipline

This contract is the loop-surface expression of the neutral
[`verification-discipline.md`](verification-discipline.md) rule (vendored from the
Specfuse methodology core): it extends that rule's **state intent → act → verify →
report** cycle with the loop's concrete RESULT-block shape and status vocabulary.
The neutral rule is normative on *what* the discipline requires; this file is
normative on *how* the loop surface reports it.

Every session operates on the same cycle: **state intent, act, verify, report.** The
RESULT block is step 4, but it is only trustworthy when steps 1–3 ran first.

### 1. State intent

Before acting, state in one sentence what you are about to do and why it is the next
right step. If you cannot state the intent clearly, you are not ready to act; if the
stated intent disagrees with the work unit's acceptance criteria, the unit is not
what you thought it was. Stay factual and present-tense ("I will add a `GET /health`
route to the existing router," not "this unit requires various modifications").

### 2. Act

Perform the change. Stay within the scope declared in step 1. If the act expands
beyond the intent — "while I was here I also fixed X" — either revise the intent and
stay, or stop and leave X for another work unit. Drift between intent and action is
the most common source of ambiguous diffs and is fixable only by discipline. The
work unit's **Do not touch** section is binding.

### 3. Verify

Two generic meanings, both apply unless the unit narrows the scope:

- **Re-read the produced artifact.** After writing a file, read it back. After
  editing a fixture, inspect the result. The Write/Edit tool reports success for the
  action it took, not for the property you wanted. This catches silent truncation,
  encoding surprises, and "I thought I wrote X but wrote Y."
- **Run the declared verification commands.** Every WU's `Verification` section
  names the gate set in `.specfuse/verification.yml` that the driver will re-run.
  Run them yourself first, in declared order, with full output. Generic
  verifications — "I assume the tests still pass" — are not verifications. The
  commands are the verification.

If a check fails, you are in one of three situations:

1. **Correctable locally.** Fix the cause, re-run the **full** gate set from the
   top, then continue. A re-run that fixes the original failure but introduces a
   new one counts as a failed cycle.
2. **Spinning threshold reached** (the driver allows three fresh attempts per WU).
   Emit `status: blocked` with the precise evidence rather than spending the cycle
   on guesswork.
3. **Fundamentally blocked.** A spec ambiguity, generated code that needs to
   change, a missing dependency — emit `status: blocked` immediately with a
   `blocked_reason` naming the boundary.

### 4. Report

Report only what verification confirmed. Step 4 is the RESULT block. An optimistic
RESULT is worse than no RESULT: the driver re-runs the gates and discovers the lie,
the attempt is wasted, and the next fresh session inherits no useful evidence about
why the previous one was wrong.

## Format

````markdown
```result
status: complete | blocked        # complete = "I believe acceptance criteria are met"
summary: <one sentence on what changed>
files_changed:
  - path/to/file
acceptance_criteria:
  - text: <criterion, copied from the work unit>
    met: true | false
    evidence: <how you know — a test name, a behavior, a line reference>
blocked_reason: <present only when status is blocked>
```
````

## Rules

1. **No git.** You edit files only. The driver stages, squashes, and commits one
   trailer-carrying commit per work unit. Do not run `git` at all.
2. **Verify before you report.** Re-read what you produced and run the work unit's
   own verification before writing `status: complete`. Do not report success you
   have not checked.
3. **Blocked is a valid, respectable outcome.** If an escalation trigger fires, emit
   `status: blocked` with a precise `blocked_reason` and stop.
4. **Honesty over optimism.** A truthful `blocked` after one attempt is cheaper than
   three fresh attempts chasing a `complete` that verification keeps rejecting.
5. **No secret-looking values in evidence.** The RESULT block is read by the driver
   and may be archived. See [`security-boundaries.md`](security-boundaries.md).

## Closing obligations for implementation WUs (FEAT-2026-0049)

Four binding obligations before `status: complete`. Each guards a way a prior WU
closed on nothing:

1. **Diff against `produces:` first.** Every path in the WU's `produces:` list must
   show a working-tree change, or the RESULT must justify each unchanged path
   explicitly: "no change needed because X; here is the evidence the deliverable
   already holds: `<command + output>`." Silence on an unchanged deliverable is not
   a valid close. (The driver will enforce this mechanically — loop #189 fix 3 — the
   obligation binds now.)
2. **A plan-level contradiction is `blocked`, not `complete`.** If mid-WU you find
   the plan cannot be delivered as written (a decision contradicts another, a
   deliverable cannot exist), emit `status: blocked` with the finding in
   `blocked_reason`. Never write the finding into a gate document and close
   `complete`. `complete` means the deliverables exist; `blocked` means they cannot
   or should not.
3. **Every `evidence:` cites an executed command** — its observed exit code/output.
   Reading source, grepping for a string, or citing another WU's RESULT is not
   verification. For a validation-rule or severity claim the evidence must include a
   negative observation (the rule seen rejecting a purpose-built bad input); see
   [`verification-discipline.md`](verification-discipline.md) §3.
4. **Analysis without edits is not a silent attempt.** If an attempt produces
   analysis but no file edits, say so explicitly and end `blocked` (or with a
   concrete next-edit plan). Do not exhaust the attempt on prose.

## Why this matters

The driver's trust model is that the RESULT block is an honest claim about what
happened. The cycle that follows — re-verify, commit, advance the dependency
frontier, dispatch the next unit — runs on that signal. When a session skips
verification, the cost is not its own: it is paid by the next fresh session that
inherits a broken assumption, by the driver that wastes attempts on a unit that was
never close to done, and by the human who reviews a gate believing the evidence in
front of them.

State intent. Act. Verify. Report. Every time.
