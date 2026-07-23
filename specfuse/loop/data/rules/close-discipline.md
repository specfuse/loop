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

## 2. Hedged-verdict follow-up record

On `met_locally`, the close must produce a named record — in the gate review
or `RETROSPECTIVE.md` — with one entry per unmet criterion:

- the criterion, verbatim;
- why it is unverifiable in this environment;
- the exact re-run condition that would upgrade the verdict to `met`.

The driver (>= 0.3.21) already guarantees the surfaces stay un-flipped on a
hedged verdict (gate `awaiting_review`, roadmap `active`, PLAN `active`);
this record is the other half: without it, `met_locally` is a dead end —
no artifact says what would make it `met`, and the honest hedged verdict
degrades into a polite synonym for "unknown".

## 3. Consumer-visible contract changes enumerated, human-acknowledged

The close enumerates every consumer-visible addition, removal, or rename the
feature makes across ALL its producing WUs — API surface, generated models,
published schemas, CLI flags, whatever contract consumers depend on — and
blocks on explicit human acknowledgment of the list. A feature with no such
changes writes exactly: `n/a — no consumer-visible contract change` (do not
fabricate an empty enumeration; the n/a line is the reviewed claim).

A close carrying this obligation is always load-bearing
(`auto_close_disabled: true`).

> **Provenance.** A breaking removal from a generated model survived four
> gates unreviewed because no close surface owned the breaking-change list.
> A silent breaking change is the most expensive false-done, and it is not
> language-specific — any generated or published contract has this surface.

## Split with project-local rules

These are the generic obligations. The concrete grounding — which command is
the oracle, which surface is "the API", project-specific regeneration
hazards — is per-project and belongs in that project's
`.specfuse/rules-local/` (never touched by upgrade), referencing this rule.
