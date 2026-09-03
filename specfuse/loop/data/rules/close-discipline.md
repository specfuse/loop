<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: close discipline

Three obligations for `close` and `close-intermediate` WUs, binding at close
time. Sibling of [`planning-discipline.md`](planning-discipline.md) (plan/arm
time) and of the per-WU closing obligations in
[`result-contract.md`](result-contract.md). Provenance: FEAT-2026-0049
(the specfuse-generator dogfood), where three gates auto-closed at
`attempts: 0` and the one close forced to run caught two false-`done` WUs and
an unsatisfiable predicate — 48% of the feature's spend landed after the
terminal gate had already "auto-closed". A close that only writes prose
verifies nothing.

A close whose acceptance criteria include ANY obligation below is
**load-bearing**: the plan author sets `auto_close_disabled: true` in that
WU's frontmatter so the auto-close predicate cannot optimize it away (#189).

## 1. Oracles re-run fresh

The close re-runs every oracle the feature's acceptance criteria name — the
full test command(s), plus any compile/execution gates — fresh, in this
session, exit codes read directly. Never inherit a producing WU's
self-report: `done` is a claim, the re-run is the verification. When the
feature's criteria assert on generated artifacts, regenerate into a clean
output directory before asserting — stale output satisfies any assertion.

> **Provenance.** A WU reported `done` while its source was untouched and its
> oracle never ran; the driver-side produces-vs-diff guard now refuses that
> pass (specfuse-loop >= 0.3.21), but only the close's own fresh re-run
> catches the composite: all WUs individually green while the feature-level
> oracle fails.

## 2. The verdict is binary; unfinished work is tracked, not hedged

The verdict a close records is `met` or `not_met` — there is no partial
credit. On `not_met` the close writes `FOLLOW-UPS.md` in the feature folder,
one `### `-headed entry per failed criterion carrying the criterion verbatim,
the evidence (the command run and its exit code or output line), and the
re-run condition that would satisfy it; after the close passes, the driver
files one tracked `specfuse:follow-up` issue per entry and writes the issue
number back. A criterion that needs a person to reply, sign, click, or run
something interactively is a `type: human` work unit placed *before* the
close — the driver halts on it, the operator marks it `done` with
`evidence:`, and the close quotes that evidence — and a criterion that can
only be observed in production is a `## Post-merge checklist` line in
`PLAN.md`, filed as one `specfuse:post-merge` issue at close, never an
acceptance criterion.

`close-m` is the guard: a `not_met` close whose `FOLLOW-UPS.md` is absent or
carries no `### ` entry is refused as `closing_deliverable_missing`, pre-squash
and by `specfuse lint --closing`. `gh` being absent or failing leaves the file
itself as the record; the driver never deletes or rewrites it.

> **Provenance (FEAT-2026-0085).** Across 273 features in 12 repositories, 48%
> of verdict-bearing closes ended on one of the two soft-success verdicts this
> feature retired, and 59 of those were later flipped to `met` by an
> acceptance skill with nothing re-run. Of 101 hedged features, 42 hedged
> because a criterion asked the loop to observe production, 16 because a human
> had to sign or act, and 9 because auto-closed gates had seeded every
> criterion into the retrospective as debt the terminal close could not
> reconcile — the three cases the three channels above now carry honestly.
> Only about 13 carried information a hedge is for, and no surveyed external
> loop uses partial credit. The retired values stay *readable* on disk;
> `docs/methodology.md` § Migrating a hedged close says what to do with a
> standing hedged close.

## 3. Consumer-visible contract changes enumerated, human-acknowledged

The close enumerates every consumer-visible addition, removal, or rename the
feature makes across ALL its producing WUs — API surface, generated models,
published schemas, CLI flags, whatever contract consumers depend on — and
blocks on explicit human acknowledgment of the list. A feature with no such
changes writes exactly: `n/a — no consumer-visible contract change` (do not
fabricate an empty enumeration; the n/a line is the reviewed claim).

A close carrying this obligation is always load-bearing
(`auto_close_disabled: true`).

**Also append it to `CHANGELOG.md`'s `Unreleased` section (FEAT-2026-0064).**
When this section is a real enumeration — not the `n/a` line — the close
appends each item to `Unreleased`, classified `added` / `changed` / `fixed` /
`breaking` and carrying the feature's `FEAT-YYYY-NNNN` ID, via
`specfuse/loop/changelog.py`'s schema. **This is the same material the
paragraph above already requires you to write, put where a consumer will
read it — not a second write.** An author who treats the changelog append as
new work will write the enumeration twice, badly; write it once, in both
places, from the same understanding. `closing_requirements.py`'s `close-k`
requirement (enforced by `assert_changelog_entry_for_contract_changes` in
`loop.py`, and pre-squash by `specfuse lint --closing`) fires when this
section names a real change and `Unreleased` gained no entry tracing to this
feature's FEAT-ID.

**An `n/a` close appends nothing to `Unreleased`, and that is correct.** A
changelog padded with "no user-facing change" entries is noise that trains
readers to skip it — the `close-k` check does not fire on an `n/a` section.

> **Provenance.** A breaking removal from a generated model survived four
> gates unreviewed because no close surface owned the breaking-change list.
> A silent breaking change is the most expensive false-done, and it is not
> language-specific — any generated or published contract has this surface.

## 4. What the driver checks — check it before you report, not after you fail

Sections 1–3 are obligations you reason about. The driver additionally
refuses a closing WU that produces correct content in the wrong shape, and it
refuses it *after* the WU has run — so a mismatch used to cost a full
re-dispatch, not a re-arm.

That used to mean memorizing a table of literal guard strings. It no longer
does. Two mechanical surfaces replace the table:

- **The skeleton is pre-created at dispatch.** Every `close` /
  `close-intermediate` / `plan-next` WU starts its session with the
  guard-required files and headings already scaffolded in place
  (`RETROSPECTIVE.md`, the `## Gate <N>` / `## Cost analysis` /
  `### Failure-class breakdown` sections, the `GATE-{N+1}-REVIEW.md`
  filename) — see `precreate_dispatch_skeleton` in `specfuse/loop/loop.py`.
  You fill the skeleton in; you do not need to remember its shape from
  scratch.
- **`specfuse lint --closing` is the mandatory pre-report check.** Run it
  before emitting your `RESULT` block. It reads the same registry the driver
  itself checks and reports pass/fail per requirement in-session, so a format
  mismatch is caught while you can still fix it, not after the driver refuses.

The registry of record — every guard, what it requires, which WU types it
applies to — lives in `specfuse/loop/closing_requirements.py`. That module
and `specfuse/loop/lint_closing.py` (the `--closing` implementation) are the
one place these requirements are enumerated; this rule does not duplicate
them.

**Migration posture.** Already-drafted features need no conversion — the
skeleton applies at dispatch time for any WU dispatched from here forward,
regardless of when its body was authored. Older WU bodies that restate guard
strings inline (pre-dating this section) are inert, not wrong: the driver
never read that prose, only the actual artifacts. Removing such prose from an
old WU body is optional cleanup, not required migration work.

> **Provenance (issue #265, FEAT-2026-0054).** Guard requirements are
> enforced in `specfuse/loop/loop.py`'s `assert_*` functions. They were
> briefly literal-string-documented in this rule (28% of closing-WU spend
> going to driver-refused attempts, three undocumented guards accounting for
> 45% of that waste) — but a second copy of the requirements drifts, so
> FEAT-2026-0054 replaced the copy with the two mechanical surfaces above and
> made `closing_requirements.py` the single registry both the driver and the
> lint read.

## 5. Per-criterion state and the narrow/broad oracle contract

A gate may carry a `GATE-NN-CRITERIA.md` artifact recording, per acceptance
criterion, which oracle proved it, that oracle's exit code, and the tree state it
ran against. Each entry also carries a `kind` (`narrow` or `broad`) and a `state`
(the pass/fail result the oracle produced).

A `narrow` oracle has a knowable scope — a scoped test nodeid, a symbol-existence
import, a structural assert, a grep with a countable output — so its green may be
carried forward across close attempts. A `broad` oracle — the full test suite, a
full regeneration, a scenario matrix — has no knowable scope, so a carried-forward
green would be an unsound coverage claim; it re-runs on every close attempt.

`kind` and `state` are written by the close that ran the oracle and are never
inferred by a reader, the same posture §2 already takes on the hedged-record
`kind:`. `specfuse lint --closing` is the check.

## Split with project-local rules

These are the generic obligations. The concrete grounding — which command is
the oracle, which surface is "the API", project-specific regeneration
hazards — is per-project and belongs in that project's
`.specfuse/rules-local/` (never touched by upgrade), referencing this rule.
