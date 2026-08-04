---
name: accept-hedged-close
description: "Accept a standing hedged verdict (`met_locally` / `partially_met`) on a feature whose close WU is `done`, recording the operator's reason and the carried-forward follow-up list in the feature folder, then re-checking the verdict through the driver's `--recheck-verdict` primitive so the terminal flips fire through their one owner. Refuses on `met` (nothing to accept), `not_met`, or a close WU that is not `done`. Single propose-and-confirm."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Accept hedged close (interactive, propose-and-confirm)

Companion to `/wrap-feature`'s refusal. A `close` WU that legitimately passes
with `verdict: met_locally` (or `partially_met`) leaves every WU `done`, the
terminal gate `awaiting_review`, and PLAN + roadmap `active` — correctly, by
design. For some features that hedge is the ceiling **by construction**: no
gate size, extra WU, or amount of test-writing inside a dispatched session can
close a criterion whose oracle lives outside the repo. `/wrap-feature` then
refuses and says "do not attempt manual reconciliation here." Today an
operator hand-edits `PLAN.md` status, the gate status, and the roadmap row
anyway, and no artifact records why. This skill is the auditable alternative:
it writes the operator's reason and the accepted follow-up list, then hands
the actual flip to the one mechanism allowed to fire it.

Posture mirrors `/unblock-wu`: propose-and-confirm, mandatory one-line
rationale, empty or whitespace-only input refused and re-prompted.

**Run interactively.** The confirmation and rationale prompts are the whole
point; `claude -p` with redirected stdin falls back to a degraded "report
state and stop" mode.

## The constraint that outranks every step below

`[FEAT-2026-0023/G1-CLOSE]`: terminal-state flips have exactly ONE owner
inside the loop package — `fire_terminal_flips` in `specfuse/loop/loop.py`.

**This skill does not edit `PLAN.md`'s `status` field, a `GATE-NN.md`'s
`status` field, or the roadmap row.** Those three surfaces are never opened
for a write by this skill. The only mechanism this skill uses to cause a flip
is the driver's `--recheck-verdict FEATURE_ID` CLI flag
(`recheck_terminal_verdict` in `specfuse/loop/loop.py`), which itself only
ever calls the existing `fire_terminal_flips` — this skill duplicates no flip
logic and reimplements no state transition. A version of this skill that
wrote those three surfaces itself would have rebuilt issue #49 with a
friendlier name and must be rejected at review even if every gate is green.

## When to invoke

When `/wrap-feature` (or `/gate-status`) reports that a feature's terminal
gate is `awaiting_review`, PLAN.md and the roadmap row are still `active`,
and the terminal `close` WU is `status: done` with `verdict: met_locally` or
`verdict: partially_met` — and the operator has decided, having read the
close WU's hedged-verdict follow-up record, that shipping now with the
follow-ups carried forward (not discharged) is the right call.

If the verdict is already `met`: stop. Nothing to accept — the flips should
already have fired, or run `python3 .specfuse/scripts/loop.py --recheck-verdict
FEATURE_ID` directly; this skill has no role.

## Method

### 1. Locate and confirm state

- Resolve the feature (from `--feature FEATURE_ID` or ask which one).
- Read `PLAN.md`'s frontmatter and walk the graph to the terminal gate's
  `close`-type WU; read its frontmatter directly from disk (never an
  in-memory value).
- **Refuse, naming which condition failed, on any of:**
  - the close WU's `status` is not `done` — nothing to accept yet; point at
    `/gate-status`.
  - the close WU's `verdict` is `met` — nothing to accept; point at
    `--recheck-verdict` directly.
  - the close WU's `verdict` is `not_met` — this skill accepts a *hedge*
    carried forward with known follow-ups, not a failed verdict; a `not_met`
    feature needs rework, not acceptance.
  - Each refusal prints the condition it hit and stops. No write happens on
    any refusal path.
- On a `met_locally` or `partially_met` verdict with the close WU `done`,
  continue.

### 2. Lead with the verdict ceiling, then the record

- Locate the close-discipline follow-up record the close WU was required to
  produce (`RETROSPECTIVE.md` or the gate review) — one `### `-titled entry
  per unmet criterion: the criterion verbatim, why it is unverifiable here,
  the exact re-run condition that would upgrade the verdict, and a `kind:`
  per [`close-discipline.md`](../../rules/close-discipline.md) §2. If no
  such record exists, stop and say so — accepting a hedge with no follow-up
  record to carry forward defeats the point of this skill; the close WU
  itself is incomplete.
- **Read every entry's `kind:` field before printing anything.** This
  answers the operator's first question — *why isn't this `met`?* — before
  they have to ask it.
  - **Every entry carries a `kind:` recognized by
    `closing_requirements.FOLLOW_UP_KINDS`.** Compute the ceiling over the
    set of kinds present with `closing_requirements.verdict_ceiling_for_kinds`
    and print the **headline first, before quoting any entry detail**:
    - if every entry is `acceptance-discharged`, `routed-finding`, or
      `inherent`, the ceiling is `verdict_ceiling_for_kinds`'
      `NO_IN_REPO_REWORK` value — print exactly: **"no in-repo rework can
      raise this verdict"**.
    - if **any** entry is `externally-verifiable-later`, the ceiling is
      `verdict_ceiling_for_kinds`' `REWORK_EXISTS` value — print: **"rework
      exists: `<the named re-run condition, quoted verbatim from that
      entry>`"**. The operator now has a real choice between accepting now
      and staying hedged until that condition is met.

    Only `externally-verifiable-later` implies rework exists. The other
    three kinds all collapse to "no in-repo rework can raise this verdict",
    for different reasons: `acceptance-discharged` needs a human signature
    (accepting *is* the discharge), `routed-finding` is owned on another
    surface, and `inherent` is not assertable, ever. This mapping is
    `close-discipline.md` §2's table; this skill reads the computed answer,
    it does not re-derive the rule.
  - **Any entry has no `kind:`, or an unrecognized one** (a record written
    before this contract shipped, or a typo): do **not** compute a ceiling
    and do **not** guess one from the entry's wording — `kind` is written by
    the close WU, which has the context; a reader sees only prose after the
    fact and would be guessing. Report plainly, naming the entry: `"entry
    <N> carries no recognized kind: — ceiling not computed"`, then fall back
    to today's behaviour for that entry: quote it in full and let the
    operator reason about it unaided.
- After the headline (or the unclassified-entry notice), quote every entry
  to the operator in full, as before.
- **For each `routed-finding` entry, prompt for its tracking surface —
  non-blocking.** `routed-finding` is the one kind whose whole meaning is
  *"someone else owns this now"*, and today that someone is named only in
  retrospective prose nobody reopens. Ask, per entry: `"entry <N> is
  routed-finding — where is it tracked? give an existing issue or roadmap
  reference, or say 'create' to run `/roadmap-add` or `gh issue create`, or
  say 'nowhere, deliberately' if it is untracked on purpose"`. Any answer is
  accepted, including "nowhere, deliberately", and it is recorded as given —
  this prompt is not a gate: `/accept-hedged-close` is a single-confirm
  skill, and a mandatory sub-decision here would turn it into a multi-step
  interrogation, the exact friction this feature exists to remove. The other
  three kinds never trigger this prompt: `acceptance-discharged` is
  discharged by the acceptance itself, `inherent` is never actionable by
  anyone, and `externally-verifiable-later` already carries its exact re-run
  condition in the record, which *is* its tracking surface. This skill does
  not create the issue or roadmap row itself — it offers the commands; the
  operator runs them.

### 3. Require the operator's input before any write

Before writing anything, require, in order:

1. **The feature ID** (already resolved in step 1 — confirm it back).
2. **Confirmation the close WU is `done` with a hedged verdict** (already
   checked in step 1 — state it back: `"<wu_id> is done, verdict: <verdict>"`).
3. **A one-line operator reason** for accepting the hedge now rather than
   reworking the feature. The prompt is scaffolded from step 2's computed
   ceiling — naming *what is being accepted*, never suggesting words for the
   reason itself:
   - ceiling `NO_IN_REPO_REWORK`:
     ```
     acceptance reason required — you are accepting that no in-repo rework
     can raise this verdict; type a one-line reason or Ctrl-C to abort
     ```
   - ceiling `REWORK_EXISTS`:
     ```
     acceptance reason required — you are accepting now instead of waiting
     for: <the named re-run condition>; type a one-line reason or Ctrl-C to
     abort
     ```
   - no ceiling computed (an unclassified entry is present): fall back to
     today's wording, unchanged:
     ```
     acceptance reason required — type a one-line reason or Ctrl-C to abort
     ```
   Empty or whitespace-only input is refused and the prompt repeats. This is
   [`operator-escalation.md`](../../rules/operator-escalation.md)'s
   never-author rule made concrete: the skill names what is being accepted,
   the human supplies every word of the reason — the prompt above contains
   no reason text an operator could accept unread, only the name of the
   thing being accepted. A version of this skill that pre-filled a plausible
   reason string would be worse than a blank line, because it invites
   accepting a sentence the operator never thought, and must be rejected at
   review even if every other criterion passes. This mirrors `/unblock-wu`'s
   rationale discipline exactly — the reason is the audit signal, not a
   formality.
4. **Explicit acknowledgment of the standing follow-up list** quoted in step
   2 — the operator must confirm they have read every entry, not just that
   a list exists. A blanket "yes" to an unquoted list does not satisfy this.

Do not proceed to step 4 until all four are satisfied.

### 4. Write the acceptance record

Append to the feature folder (`RETROSPECTIVE.md`, in a new
`## Hedged verdict accepted` section — do not open a new file) an
acceptance record naming:

- the accepted verdict (`met_locally` or `partially_met`, verbatim);
- the operator's reason (verbatim, from step 3.3);
- every outstanding follow-up, carried forward **verbatim** from the
  hedged-follow-up record surfaced in step 2 — do not paraphrase, do not
  drop entries, do not mark any as discharged;
- for each `routed-finding` entry, the tracking-surface answer collected in
  step 2, written immediately next to that entry — never as a loose
  appendix at the end of the record. An untracked routed finding and its
  tracking reference (or "tracked nowhere, deliberately") must be readable
  together, not stitched together by the reader;
- the timestamp (ISO 8601 UTC) the acceptance was recorded.

This record is the only file this skill writes before invoking the driver.
It does **not** discharge or close any follow-up: accepting a hedge means
shipping with known-open items, not pretending they are done. The follow-ups
remain exactly as open as they were; this record only carries them forward
into a reviewable trail instead of losing them to a silent hand-edit.

### 5. Fire the flips through T02's primitive

Once the acceptance record is written, the only remaining step is to make
the close WU's on-disk verdict `met` so the driver's own re-check primitive
recognizes it as flip-eligible — `verdict_permits_terminal_flips` returns
`True` only for `met`. Edit the close WU frontmatter's `verdict:` field from
its hedged value to `met`, and nowhere else in that file. This is a WU-level
frontmatter edit, not a write to `PLAN.md` status, gate status, or the
roadmap row — those three remain untouched by this skill and are flipped
only by what runs next.

Then run:

```
python3 .specfuse/scripts/loop.py --recheck-verdict FEATURE_ID
```

This is `specfuse/loop/loop.py`'s `recheck_terminal_verdict` entry point
(FEAT-2026-0070/T02). It re-reads the close WU's verdict from disk and, since
it is now `met`, calls the existing `fire_terminal_flips` — the single owner
of the gate/roadmap-row/PLAN.md/archive transition — unchanged. This skill
never calls `fire_terminal_flips` itself and never sets `PLAN.md`'s
`status`, a gate's `status`, or the roadmap row directly.

Report the command's output (`reason` and any `Modified:` line) to the
operator.

### 6. RESULT

Per [`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the acceptance record was written, the close WU's
verdict was updated to `met`, and `--recheck-verdict` ran and reported
`fired: true`. `status: blocked` is reserved for a refusal in step 1 (`met`,
`not_met`, or close WU not `done`) or an operator unavailable to supply the
rationale/acknowledgment in step 3.

## What this skill does NOT do

- **Does not write `PLAN.md`'s `status` field.** That flip belongs to
  `fire_terminal_flips`, invoked only via `--recheck-verdict`.
- **Does not write a `GATE-NN.md`'s `status` field.** Same owner, same path.
- **Does not write the roadmap row.** Same owner, same path.
- **Does not discharge or close any follow-up, and does not drop one.** The
  follow-ups are carried forward verbatim; accepting the hedge is not
  resolving it.
- **Does not run on a `met` or `not_met` verdict.** Nothing to accept in
  either case.
- **Does not touch `/wrap-feature`'s non-`done` refusal.** That checkpoint
  stays; this skill is the path that makes the feature `done` first.

## Version

**v0.1** (FEAT-2026-0070/T03). First cut: propose-and-confirm, mandatory
rationale, acceptance record in `RETROSPECTIVE.md`, flip fired exclusively
through `--recheck-verdict`.
