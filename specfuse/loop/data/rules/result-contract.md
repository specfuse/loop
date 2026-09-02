<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: the RESULT block contract

A dispatched work-unit session ends with a single fenced `result` block as the
very last thing in its output. The driver reads it; a dispatched session that
emits none is treated as a failed attempt. The RESULT is **advisory** — the
driver re-runs verification itself, and that is what decides done.

## Who reads it — emit it only when something does

This block is a **machine interface**, not a report. Emit it when a program is
on the other end: a work-unit session the driver dispatched (always), or a skill
invoked **non-interactively** from a calling program that parses the outcome
(`fix-bug` under `autofix_invoke` is the live example).

Do **not** emit it on an interactive run. A human who typed `/pick-feature` has
no parser; the block lands as a slab to scroll past, which is the verbosity
[`human-output.md`](human-output.md) exists to prevent — report to them per that
rule instead. When in doubt, look at who invoked you: a slash command typed by a
person is interactive; a `claude -p` dispatch is not.

## The cycle: state intent, act, verify, report

[`verification-discipline.md`](verification-discipline.md) is normative on the
cycle; this file is normative on how the loop surface reports step 4.

1. **State intent.** One sentence on what you are about to do and why it is the
   next right step. If it disagrees with the work unit's acceptance criteria,
   the unit is not what you thought it was.
2. **Act.** Stay inside that scope. "While I was here I also fixed X" is drift;
   the work unit's **Do not touch** section is binding.
3. **Verify.** Re-read what you produced — the Write/Edit tool reports the
   action it took, not the property you wanted — and run the work unit's own
   verification commands, in declared order, with full output. "I assume the
   tests still pass" is not a verification. A behavioural claim needs a run, not
   a reading of the source; a rule-or-severity claim needs a **negative
   observation**, the rule seen rejecting a purpose-built bad input.
4. **Report.** Report only what verification confirmed.

A failing check leaves you in one of three situations: correctable locally (fix
the cause, re-run the **full** gate set from the top), spinning (three fresh
attempts is the driver's budget — emit `status: blocked` with the evidence
rather than guessing), or fundamentally blocked (a spec ambiguity, generated
code that must change, a missing dependency — emit `status: blocked` naming the
boundary).

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
   trailer-carrying commit per work unit.
2. **Verify before you report.** Do not report success you have not checked.
3. **Blocked is a valid, respectable outcome.** A precise `blocked_reason` after
   one honest attempt is cheaper than three attempts chasing a `complete` that
   verification keeps rejecting.
4. **Stop at a boundary rather than working around it.** Generated directories,
   secrets, and `.git/` internals are off-limits
   ([`never-touch.md`](never-touch.md),
   [`security-boundaries.md`](security-boundaries.md)); weakening a failing gate
   to make a unit pass is the same class of failure. Silence at a boundary is
   not permission.
5. **No secret-looking values in evidence.** The block is read by the driver and
   may be archived.
6. **Never mint or rewrite a correlation ID to make something fit.** A
   well-formed ID that disagrees across surfaces is `blocked`, not a rename
   ([`correlation-ids.md`](correlation-ids.md)).
7. **A "pre-existing" failure claim cites the commit it was measured on.**
   Calling a failure pre-existing is a claim about a *different* commit —
   typically the merge-base — and nothing observed on your own branch
   establishes it. Name the command and the commit, give the numbers from both
   sides, and emit `status: blocked` rather than asserting a baseline you could
   not measure: a mass of errors sharing one signature (network refused,
   unresolvable build dependencies) is a report about where the suite ran, not
   about the repository (#2075).

## Closing obligations for implementation WUs (FEAT-2026-0049)

1. **Diff against `produces:` first.** Every path in the WU's `produces:` list
   must show a working-tree change, or the RESULT must justify each unchanged
   path with the command and output showing the deliverable already holds.
   Silence on an unchanged deliverable is not a valid close (#198, outcome
   `produces_not_in_diff`).
2. **A plan-level contradiction is `blocked`, not `complete`.** If the plan
   cannot be delivered as written, put the finding in `blocked_reason`; never
   write it into a gate document and close `complete`.
3. **Every `evidence:` cites an executed command** and its observed exit
   code/output. Reading source, grepping for a string, or citing another WU's
   RESULT is not verification.
4. **Analysis without edits is not a silent attempt.** Say so explicitly and end
   `blocked` rather than spending the attempt on prose.

The driver's whole cycle — re-verify, commit, advance the dependency frontier,
dispatch the next unit — runs on this block being an honest claim about what
happened. State intent. Act. Verify. Report. Every time.
