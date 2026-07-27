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

## 4. What the driver checks — the exact strings

Sections 1–3 are obligations you reason about. **This section is a format
contract you must match literally.** The driver refuses a closing WU that
produces correct content in the wrong shape, and it refuses it *after* the WU
has run — so a mismatch costs a full re-dispatch, not a re-arm.

That is not hypothetical. Across 158 closing WUs in 9 repositories, **28% of all
closing-WU spend was burned on attempts the driver refused**, and three guards
whose requirements appeared in no authoring surface accounted for **45% of that
waste**. This table exists so that number goes down.

| Guard | Applies to | What it requires, exactly |
|---|---|---|
| `assert_retrospective_exists` | `close`, `close-intermediate` | `RETROSPECTIVE.md` exists in the feature dir and is non-empty |
| `assert_retrospective_gate_section` | `close-intermediate` | A heading matching `^#{1,3} Gate <N>` — i.e. `## Gate 1`, for the gate being closed. Not "Gate one", not a bare bold line |
| `assert_cost_analysis_section_when_met` | `close` with `verdict: met` | A heading matching `^##+ Cost analysis` (case-insensitive) — `## Cost analysis` is the conventional spelling |
| `assert_failure_class_breakdown_when_failures_present` | `close`, `close-intermediate`, when the gate had ≥1 failed attempt | A literal `### Failure-class breakdown` heading — three hashes, not two |
| `assert_learnings_appended_or_noop` | `close`, `close-intermediate` | Either ≥1 added line to `.specfuse/LEARNINGS.md` in this WU's squash, **or** the exact phrase `nothing generalizes` (case-insensitive) somewhere in `RETROSPECTIVE.md` |
| `assert_doc_or_roadmap_diff` | `close`, `close-intermediate` | The squash touches at least one of: `docs/*`, `.specfuse/roadmap.md`, `.specfuse/LEARNINGS.md`, or any `RETROSPECTIVE.md` |
| `assert_verdict_well_formed` | `close` | A `verdict:` **frontmatter** field on the WU file, one of `met`, `met_locally`, `partially_met`, `not_met`. Not in the body |
| `assert_gate_review_exists` | `plan-next` | **`GATE-{N+1}-REVIEW.md`** — named for the gate being *drafted*, not the gate being closed. A gate-1 `plan-next` writes `GATE-02-REVIEW.md` |
| `assert_next_gate_drafted_or_terminal` | `plan-next` | The next gate has ≥1 WU at `status: draft` in `PLAN.md`, or the feature is terminal |
| `assert_declared_deliverables` | any WU with `produces:` | Every path listed in `produces:` appears in the squash diff |
| `assert_autoclose_debt_reconciled` | `close` | On a `close` WU, if `RETROSPECTIVE.md` carries T06's `<!-- specfuse:autoclose-debt gate=N ... -->` marker for a gate earlier than the terminal gate, the terminal close's `## What the loop did NOT verify` section must name that gate literally as `gate N`. Marker-gated (fires on none of this repo's pre-FEAT-2026-0070 closes); short-circuits `(True, "")` when the terminal close WU is itself `auto_close: true` |

**The `GATE-{N+1}` row is the single most expensive guard in the system**
($53.11 of measured waste across 15 refusals) and the one most likely to
surprise: the review artifact is named for the gate it *arms*, because that is
the gate a human reads it to review. See issue #261.

**If a closing WU retries, read this table before assuming the work was hard.**
By measured cost, format mismatches are the more likely explanation.

> **Provenance (issue #265).** Guard requirements are enforced in
> `specfuse/loop/loop.py`'s `assert_*` functions and were, until this section
> existed, discoverable only by reading them or by paying for a refusal.
> `tests/test_closing_guard_contracts.py` binds this table to those functions'
> own source, so a guard that changes its literal fails a test rather than
> silently invalidating this documentation.

## Split with project-local rules

These are the generic obligations. The concrete grounding — which command is
the oracle, which surface is "the API", project-specific regeneration
hazards — is per-project and belongs in that project's
`.specfuse/rules-local/` (never touched by upgrade), referencing this rule.
