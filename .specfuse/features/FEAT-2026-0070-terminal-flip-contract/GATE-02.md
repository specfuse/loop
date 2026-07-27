---
gate: 2
status: open
cost_budget_usd: 16.0
---

# Gate 2 — an auto-closed gate's skipped ceremony is a visible debt, not a silent saving

## Definition of done

- An auto-closed gate leaves a concrete deferred-verification worklist in
  `RETROSPECTIVE.md` — each of its WUs' acceptance criteria enumerated, marked as
  not-walked — so the terminal close inherits a list rather than an absence (#241).
- A terminal close that ignores an auto-closed predecessor's debt is **visible**, not
  silent.
- The enumeration costs no agent dispatch. Auto-close exists to avoid a session; a fix
  that reintroduces one has traded the defect for the thing the predicate was built to
  prevent.

**Substantive work units are drafted by gate 1's `plan-next`**, not authored here. The
`G2-CLOSE` entry in `PLAN.md`'s graph is scaffolded so the linter reads this gate as
non-empty and gate 1 as non-terminal.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate is expected to introduce a **post-pass invariant** — a new blocking condition.
`GATE-01.md`'s arming discipline names the probe that must run before it is armed: apply
it locally, run the full oracle, paste the failure list into `GATE-02-REVIEW.md`, and
confirm the count on a correct tree is zero (§2). An invariant that fires on features
which closed correctly is unsatisfiable by construction and must be redesigned rather
than armed.

`cost_budget_usd: 16.0` — the sketch prices gate 2 at ~$11.50; the ceiling carries that
plus roughly one re-attempt of its largest WU, per `planning-discipline.md` §5's
corollary. It is not a prediction of spend.

## Reflection notes

<Written by the human at review time.>
