---
name: diagnose-issue
description: "Read a harvester finding issue and the component source it implicates, produce a root-cause diagnosis (root cause, evidence trail, candidate fix, confidence, fix_scope), and post it as one comment via specfuse.monitor.diagnosis. Does not decide whether to fix anything — FEAT-2026-0042 gates on the fields this skill emits. Triggers — \"/diagnose-issue NN\", \"diagnose issue NN\", \"root-cause finding NN\"."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Diagnose a harvester finding (interactive)

This skill answers "why did this fire?" for one `monitoring-finding`-labelled
GitHub issue. It reads the finding, reads the component source the finding
implicates, and produces a structured diagnosis — root cause, evidence trail,
candidate fix, `confidence`, `fix_scope` — posted as a single comment on the
issue.

It does **not** decide whether to fix anything. That is a separate concern,
owned by a downstream consumer that gates on `confidence` and `fix_scope`.
This skill's whole job stops at producing and posting an honest diagnosis.

## Hard rules

- **One diagnosis comment per invocation.** Exactly one `gh issue comment` call,
  once, per run. Never post twice, never post a "revised" follow-up comment in
  the same invocation.
- **Never closes or edits the finding issue.** No `gh issue close`, no
  `gh issue edit`, no label change. The issue's lifecycle belongs to the
  harvester (`specfuse/monitor/issues.py`); this skill only comments.
- **Never invents a root cause the evidence does not support.** An honest
  `confidence: low` (or a low float) with the evidence gap named in prose beats
  a confident-sounding guess. Guessing a cause because the finding is old, or
  because a plausible one exists, is the failure mode this rule exists to
  prevent.
- **Renders through `specfuse/monitor/diagnosis.py`, never hand-written.** This
  skill builds a `Diagnosis` and calls `render(diagnosis)` for the comment
  body. It does not compose the marker, the section headers, or the field
  layout itself — that contract lives in `diagnosis.py` and nowhere else.
- **Redaction is not this skill's job.** `render()` already redacts prose
  fields at the boundary. Do not pre-redact, and do not bypass `render()` to
  post raw text.
- **One issue per invocation.** If the user names more than one issue number,
  ask which to diagnose first.

## When to invoke

- User runs `/diagnose-issue <issue-number>` directly.
- User asks to "diagnose", "root-cause", or "explain why" a specific
  monitoring-finding issue by number.
- User pastes a link to a `monitoring-finding`-labelled issue and asks what
  caused it.

Do NOT invoke for: an issue that is not `monitoring-finding`-labelled (this
skill's evidence-reading method assumes a harvester finding's shape — a
fingerprint, a component, an observed failure signature); a request to also
fix the underlying bug (that is `/fix-bug`'s or the autofix consumer's job,
not this skill's); or a request to diagnose "whatever's failing right now"
with no issue number given (ask which issue first).

## Method

### 1. Fetch the finding

- `gh issue view <issue-number> --json number,title,body,labels`.
- Confirm the `monitoring-finding` label is present. If it is not, stop and
  tell the user this does not look like a harvester finding — ask them to
  confirm the issue number or invoke `/fix-bug` instead if it is a plain bug
  report.
- Parse the finding's embedded marker and body per `specfuse/monitor/issues.py`
  (fingerprint, component, check type, occurrence count, observed failure
  text). The marker in the body is the sole authority for these fields; do not
  trust the issue title's paraphrase over it.

### 2. Read the implicated component source

- Use the finding's `component` field to locate the source that produced the
  failure. Read the actual current code — the finding's `observed_text` is a
  snapshot from whenever the failure fired, and the source may have moved on
  since.
- Trace the failure signature back to the specific function, branch, or
  configuration that plausibly produced it. This is the step that makes the
  diagnosis worth more than the finding alone: joining a failure artifact with
  the code that produced it.
- If the component cannot be located, or the code at that location does not
  plausibly explain the observed failure, that is evidence of a gap — carry it
  into step 3 as a named gap, not a reason to guess.

### 3. Produce the diagnosis

Build a `specfuse.monitor.diagnosis.Diagnosis`:

- `root_cause` — the specific mechanism, named plainly, tied to what step 2
  found. If the evidence does not clearly support one mechanism over another,
  say so here rather than picking one.
- `evidence` — the trail: what in the finding and what in the source led to
  the root-cause claim. Concrete: file, function, the specific line of
  reasoning. Not "the logs suggest a timeout" — which log line, which code
  path.
- `candidate_fix` — the shape of a plausible fix, not a diff. If no evidence
  supports a specific fix, say what additional evidence would be needed
  instead of proposing one anyway.
- `confidence` — a float in `[0.0, 1.0]` reflecting how well the evidence trail
  actually supports the root-cause claim, not how confident the prose sounds.
  Weak or partial evidence gets a low number; do not round up because a guess
  feels plausible.
- `fix_scope` — one of `small` / `large` / `external`, per
  `specfuse/monitor/diagnosis.py`'s `FIX_SCOPES`: `small` for a contained
  code change, `large` for a change spanning multiple components or requiring
  design work, `external` for a fix outside this repo's control (a
  third-party outage, an upstream dependency bug).

Construct the dataclass directly — its `__post_init__` validates `fix_scope`
and the `confidence` bound, so an illegal value raises before render is ever
attempted.

### 4. Render and post

- Call `specfuse.monitor.diagnosis.render(diagnosis)` to get the comment body.
  Do not add anything to it, do not restate the marker or section headers by
  hand.
- Post it: `gh issue comment <issue-number> --body <rendered-body>`. This is
  the one comment this invocation posts.
- Report the comment URL (or the `gh` command, if `gh` could not be probed —
  see below) back to the user, along with the `confidence` and `fix_scope`
  values so they can see the machine-readable summary without opening GitHub.

### 5. RESULT

Per [`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means: the finding was fetched and confirmed as a
harvester finding, the implicated source was read, a `Diagnosis` was built
and rendered through `diagnosis.py`, and one comment was posted.
`status: blocked` is reserved for: the issue is not a `monitoring-finding`,
the implicated component cannot be located at all, or `gh` is unreachable in
this environment.

## What this skill does NOT do

- **Does not decide whether to fix anything.** No autofix routing, no branch,
  no PR. The `confidence`/`fix_scope` fields exist for a downstream consumer
  to gate on; this skill does not gate on them itself.
- **Does not close or edit the finding issue.** Comment-only.
- **Does not compose the comment format itself.** `diagnosis.py` owns render
  and parse; this skill calls it.
- **Does not run automatically.** No auto-trigger on new fingerprints, no
  per-component dial. Interactive/headless invocation only, always naming one
  issue.
- **Does not modify `specfuse/monitor/diagnosis.py` or
  `specfuse/monitor/issues.py`.** If a diagnosis genuinely needs a field the
  `Diagnosis` model does not expose, that is an escalation to the model's
  owner, not a quiet edit made from inside this skill's flow.

## Escalation framing (binding — `.specfuse/rules/operator-escalation.md`)

Whenever this skill halts for a human decision — the issue isn't a finding,
the implicated component can't be located, `gh` is unreachable, or the
evidence is too thin to name any root cause at all — present it in the six
parts that rule requires, in plain English, **before** any correlation ID,
fingerprint, or field name: what has been done so far; what the finding is
about; what decision is needed and why; why it did not resolve automatically;
the options with their pros and cons; and a recommendation.

Never author the operator's own justification. Where a field records *why a
human decided something*, that text comes from them.

## Version

**v0.1.** First cut: fetch, read source, diagnose, render through
`diagnosis.py`, post one comment. `FEAT-2026-0041/T02`, the entry point half of
the diagnosis contract T01 shipped. Expected to grow once
`FEAT-2026-0042`'s autofix consumer surfaces which `fix_scope`/`confidence`
combinations its gating logic actually needs distinguished.
