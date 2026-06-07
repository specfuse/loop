# Gate 4 review — FEAT-2026-0003

Drafted by `FEAT-2026-0003/G3-PLAN` (Opus) under terminal-case branch B.
Read this before deciding whether to arm gate 4 or close the feature
short of the goal.

This file is **advisory**. It owns no state. The graph lives in
`PLAN.md`; gate status lives in `GATE-04.md`. WU status lives in WU
files — and there are no WU files for gate 4 yet (gate 4's own
`plan-next`, when armed, drafts them).

This document is unusual in shape: gate 4 was NOT in the original
skeleton drafted by `draft-feature`. It was appended by `G3-PLAN` as the
escalation path documented in `GATE-03-REVIEW.md` "Terminal-case
handling." The human-decision question below is therefore broader than
the prior gate reviews: arm gate 4, OR close the feature with the
roadmap goal explicitly partial.

---

## The gap, precisely named

`SMOKE-example-feature.md` ran four live mechanisms; three passed,
one failed:

| Mechanism | Status |
|---|---|
| Discovery (`gh_features.py`) | ✓ PASS — 13 candidates, #287 row parsed |
| Adopt scaffold (`adopt_feature.py`) | ✓ PASS — folder + WU-01 + body embed |
| Report back (`GitHubBackend` label transitions) | ✓ PASS — `state:ready → in-progress → done → ready`, no residue |
| **Adopted-folder lint (`lint_plan.py`)** | **✗ FAIL** — 5 sections reported missing on WU-01 |

The lint failure is NOT a missing-sections issue. Issue #287's body
contains all five sections (`Context`, `Acceptance criteria`,
`Do not touch`, `Verification`, `Escalation triggers`) — as Markdown
ATX headings (`## Context`). `lint_plan.py`'s section detector matches
`^(\**)<section>` (bold-preamble or plain) and does NOT recognise
`^#+\s*<section>` (ATX). A well-formed orchestrator issue body
embedded verbatim by `adopt_feature.py` therefore fails the loop's
linter.

This is the **section-heading-format contract gap** between the two
surfaces:

- Orchestrator issue bodies use Markdown ATX headings (`## Context`).
- The loop's WU template + linter use bold-preamble (`**Context.**`).

Until reconciled, an orchestrator-dispatched feature cannot be ground
end-to-end. The roadmap goal's fourth mechanism is blocked.

---

## The human-decision question

**Arm gate 4 (fix the linter, close the goal) OR close the feature
short of the goal?**

### Arm gate 4

Pros:

- The fix is bounded: one regex constant in `lint_plan.py` + tests +
  re-lint of the existing adopted folder. Smaller than any of gates
  1-3.
- The proof stays contiguous: the smoke that surfaced the finding,
  the adopted folder being verified against, and the linter fix all
  live on one branch with one PR sequence.
- The feature-arc retrospective declares the goal "Not met; gate 4
  follows." Closing without the fix contradicts the retrospective's
  own verdict.
- The cross-repo verification rule from
  `[FEAT-2026-0003/G3-LESSONS/multi-gate]` gets its first prospective
  test — gate 4's review document is the first to include a
  "Cross-repo contracts" section before arming.

Cons:

- This feature was originally scoped to three gates. Extending to four
  was the explicit escalation path G2-PLAN reserved in
  `GATE-03-REVIEW.md` Terminal-case handling; the human should be
  comfortable that the escalation criteria fired honestly (the
  retrospective evidence demands it) rather than as scope drift.
- The methodology's "feature ends" contract is corroded if every
  feature extends to N+1 gates on a smoke finding. Gate 4 must be the
  exception, not the new default.

### Close the feature short of the goal

Pros:

- Three of four mechanisms proved live; the read+adopt+report-back
  capability shape is demonstrably correct.
- The linter fix is genuinely a self-contained unit of work that could
  live in a separate `FEAT-2026-0004` (titled e.g. *"lint_plan.py
  accepts ATX section headings"*) — the loop's gate-1 module belongs
  morally to all features, not just this one.
- A separate feature gets its own roadmap row and PR narrative —
  cleaner for future readers tracing the linter's history.

Cons:

- Re-discovers the same finding from scratch — a new feature run
  re-establishes the smoke evidence the loop already has on hand.
- Leaves this feature shipping a capability that demos in three steps
  and stalls on the fourth, against its stated `roadmap_goal`.

**G3-PLAN's recommendation: arm gate 4.** The fix is small, the
evidence is fresh, and the proof stays contiguous. But the call is
the human's — branch B of G3-PLAN is the escalation path, not a
default, and the human is the one who decides whether to take it.

---

## Cross-repo contracts (for gate 4's plan-next to verify before arming)

Per `[FEAT-2026-0003/G3-LESSONS/multi-gate]`, every plan-next gate
review must list the values the plan invented alongside the
authoritative source the human must read before arming. Gate 4 is
small, but the rule applies prospectively even at this small scope.

| Value gate 4 will invent | Authoritative source | Status |
|---|---|---|
| Section-heading format the orchestrator's issue-body template emits | `example-org/orchestrator/` issue-body template / docs / a recent orchestrator-authored `specfuse:feature` issue | UNCHECKED — gate-4 plan-next must verify |
| Whether ATX is the ONLY heading style the orchestrator uses, or one of several | Same source above | UNCHECKED — affects whether the union-pattern framing is correct vs an ATX-only pattern |
| Whether `lint_plan.py`'s section list itself (the five section names) matches the orchestrator's template field names | Orchestrator template + this repo's `lint_plan.py` `REQUIRED_SECTIONS` | LIKELY OK — same names are used in #287's body — but cheap to re-confirm |
| Whether the `state:*` label namespace settled at gate 3 needs any gate-4 follow-up | Already verified at gate 3 (the `state:*` scheme is canonical in `example-org/orchestrator/docs/naming-convention.md §5.1`) | OK — no action required |

The first two entries are load-bearing for the linter regex shape.
Gate 4's plan-next must check them and update this table with verified
values before locking gate 4's substantive WU ACs.

---

## Open questions (for gate 4's plan-next)

### Q1. Does the gate-4 fix belong in `lint_plan.py` or in `adopt_feature.py`?

Three options were enumerated in `SMOKE-example-feature.md`:

1. Broaden `lint_plan.py` section detection — smallest, loop-side;
   makes adopted folders lint clean. **Recommended.**
2. Normalise headings in `adopt_feature.py` when embedding the body
   (`## X` → `**X.**`) — keeps the linter strict but couples adopt to
   a format.
3. Fix the orchestrator issue-body template to emit bold sections —
   pushes the change to the other surface (cross-repo coordination).

G3-PLAN's recommendation is option 1. The argument: ATX is the more
standard Markdown; the loop should accept what real issue bodies use.
Option 2 inverts the dependency (adopt becomes lint-aware); option 3
forces a cross-repo PR for a loop-side limitation.

Gate 4's plan-next picks. Defaulting to option 1 is fine if the
plan-next agrees with the reasoning above; if it diverges, it must
say why in its review document.

### Q2. Is a re-smoke against #287 required for gate-4 closure?

G3-PLAN's recommendation: **NO**. The gate-3 smoke already proved the
report-back mechanism end-to-end against the real GitHub API; the
gate-4 fix is offline (linter regex + tests) and offline-verifiable
against the already-adopted folder. A re-smoke adds a second
production-issue mutation cycle (`state:*` transitions on #287
again) for marginal evidence.

If gate 4's plan-next disagrees and includes a re-smoke WU, the
GATE-04-REVIEW (drafted by gate-4 plan-next, not this document) must
state why the offline re-lint is insufficient.

### Q3. Should gate 4 also widen `lint_plan.py`'s section list to handle case-insensitive matching?

The current section names are exact-case (`Context`, not `context`).
A user-authored issue body that uses `## context` (lowercase) would
still fail even after the ATX widening. Out of scope for this gate
unless evidence demands otherwise — but gate 4's plan-next should
note it as a potential gap.

---

## Summary

Gate 4 fixes a single bounded gap: `lint_plan.py`'s section detector
must accept ATX headings so an adopted orchestrator-issue-body lints
clean. The fix is roughly one regex widening + tests + a re-lint of
the existing `example-feature-…` folder. Smaller than any prior
gate in this feature.

**The decision is binary.** Arm gate 4 (G3-PLAN's recommendation) OR
close the feature short of the goal and open `FEAT-2026-0004` for the
linter fix. Either is defensible; G3-PLAN names "arm gate 4" because
the proof stays contiguous and the cross-repo verification rule from
LEARNINGS gets its first prospective test.

If armed, gate 4's plan-next drafts T08, T09, and the closing-sequence
WUs (with the closing-WU numbering convention from
`[FEAT-2026-0003/G1-LESSONS]` — file numbering 102-105 continues the
gate-1/2/3 sequence). The "Cross-repo contracts" table above must be
verified and updated before gate-4's substantive WUs are locked.
</content>
