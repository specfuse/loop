<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: the RESULT block contract

A dispatched work-unit session ends with one fenced `result` block as the last
thing in its output; the driver reads it, and a session emitting none is a
failed attempt. The RESULT is **advisory** — the driver re-runs verification
itself, and that decides done.

## Who reads it — emit it only when something does

This block is a **machine interface**, not a report. Emit it only when a
program is on the other end: a dispatched work-unit session (always), or a
skill invoked **non-interactively** from a calling program parsing the
outcome (`fix-bug` under `autofix_invoke`).

Do **not** emit it on an interactive run — a human typing `/pick-feature` has
no parser, and the block becomes a slab to scroll past, the verbosity
[`human-output.md`](human-output.md) prevents. Report per that rule instead.
Rule of thumb: a person-typed slash command is interactive; a `claude -p`
dispatch is not.

## The cycle: state intent, act, verify, report

[`verification-discipline.md`](verification-discipline.md) is normative on the
cycle; this file is normative on how the loop surface reports step 4.

1. **State intent.** One sentence on what you are about to do and why it is the
   next right step. If it disagrees with the work unit's acceptance criteria,
   the unit is not what you thought it was.
2. **Act.** Stay inside that scope. "While I was here I also fixed X" is drift;
   the work unit's **Do not touch** section is binding.
3. **Verify.** Re-read what you produced — Write/Edit reports the action taken,
   not the property you wanted — and run the unit's own verification commands,
   in declared order, with full output. On the loop that set is the
   **per-attempt (narrow) tier**: the unit type's gates minus any declaring
   `tier: broad`, with `tests` through its `narrow_command` over the unit's
   `produces:` test modules. The full suite, coverage and every `tier: broad`
   gate are the driver's, once per gate — running them in-session buys
   nothing. "I assume the tests still pass" is not verification. A
   behavioural claim needs a run, not a source reading; a rule-or-severity
   claim needs a **negative observation** — the rule seen rejecting a
   purpose-built bad input.
4. **Report.** Report only what verification confirmed.

A failing check leaves you in one of three situations: correctable locally
(fix the cause, re-run the **whole narrow tier** from the top), spinning
(three fresh attempts is the driver's budget — emit `status: blocked` with
evidence rather than guessing), or fundamentally blocked (spec ambiguity,
generated code that must change, a missing dependency — emit `status: blocked`
naming the boundary).

## Format

````markdown
```result
status: complete | blocked        # complete = "I believe acceptance criteria are met"
summary: <one sentence on what changed>
forward_note: <optional — one sentence on what the NEXT unit should know>
files_changed:
  - path/to/file
acceptance_criteria:
  - text: <criterion, copied from the work unit>
    met: true | false
    evidence: <how you know — a test name, a behavior, a line reference>
blocked_reason: <present only when status is blocked>
blocked_next:                      # optional — a drafted fix unit
  kind: fix_unit
  file: <path to the drafted WU>
  id: <the drafted WU's id>
produces_unchanged:                # optional — obligation 1 below
  - path: <a produces: entry, verbatim>
    justification: <the command you ran and its output showing the deliverable already holds>
produces_amended:                 # optional — obligation 1 below
  - path: <a produces: entry, verbatim>
    justification: <why the plan named it but the solution didn't need it>
```
````

`summary` is backward-looking by this contract's own definition — one sentence
on what changed. `forward_note` is the other half: what surprised you, or what
the next unit should know, that `summary` misses. Optional, never required by
any guard — omit it and the driver's `PROGRESS.md` entry is unchanged
(FEAT-2026-0106/T02).

## Rules

1. **No git.** Edit files only. The driver stages, squashes, and commits one
   trailer-carrying commit per unit.
2. **Verify before reporting.** Do not report success you have not checked.
3. **Blocked is a valid, respectable outcome.** A precise `blocked_reason`
   after one honest attempt beats three attempts chasing a `complete`
   verification keeps rejecting.
4. **Stop at a boundary rather than working around it.** Generated
   directories, secrets, and `.git/` internals are off-limits
   ([`never-touch.md`](never-touch.md),
   [`security-boundaries.md`](security-boundaries.md)); weakening a failing
   gate to pass is the same failure class. Silence at a boundary is not
   permission.
5. **No secret-looking values in evidence.** The driver reads and may archive
   this block.
6. **Never mint or rewrite a correlation ID to make it fit.** A well-formed
   ID disagreeing across surfaces is `blocked`, not a rename
   ([`correlation-ids.md`](correlation-ids.md)).
7. **A "pre-existing" failure claim cites the commit it was measured on.**
   Calling a failure pre-existing is a claim about a *different* commit,
   typically the merge-base, that nothing on your own branch establishes.
   Name the command and commit, give the numbers from both sides, and emit
   `status: blocked` rather than asserting an unmeasured baseline: a mass of
   errors sharing one signature (network refused, unresolvable build
   dependencies) reports where the suite ran, not the repository (#2075).
8. **A block may name its own fix.** `blocked_next:` points at a drafted work
   unit — `provenance: agent`, `status: draft`, the five WU sections filled —
   the driver inserts ahead of this one and re-arms it, when the feature runs
   `auto` and the draft passes the arm checks; no `blocked_next` escalates
   unchanged.

## Closing obligations for implementation WUs (FEAT-2026-0049)

1. **Diff against `produces:` first.** Every path in the WU's `produces:` list
   must show a working-tree change, or the RESULT must justify each unchanged
   path under `produces_unchanged:` (deliverable already held) or
   `produces_amended:` (the plan named a path the solution didn't need — drop
   only, never add) — spelled as `produces:` spells it, plus the proving
   command and output. The driver reads that list: a justified entry passes
   and is recorded as `produces_justified`; an unjustified one, or a blank
   justification, is refused (#198, #3268, outcome `produces_not_in_diff`).
   Silence on an unchanged deliverable is not valid.
2. **A plan-level contradiction is `blocked`, not `complete`.** Put the
   finding in `blocked_reason`; never bury it in a gate document and close
   `complete`.
3. **Every `evidence:` cites an executed command** and its observed exit
   code/output. Reading source or citing another WU's RESULT is not
   verification.
4. **Analysis without edits is not a silent attempt.** Say so; end `blocked`
   rather than spend the attempt on prose.

The driver's whole cycle — re-verify, commit, advance the dependency
frontier, dispatch next — runs on this block being an honest claim. State
intent. Act. Verify. Report. Every time.
