---
gate: 2
status: passed
cost_budget_usd: 16.0
baseline:
  sha: 9fb81ddcfaf8c501ecdd3a79082531bb6fa42f81
  probed_at: 2026-07-27T04:03:53.026581+00:00
  failing: []
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

**Confirmed as still right at gate-1 `plan-next` (2026-07-27), not revised.** The drafted
WUs total exactly **$11.50** (T05 $1.00, T06 $2.00, T07 $2.25, T08 $1.25, `G2-CLOSE`
$5.00). §5's corollary — sum plus one re-attempt of the largest WU — gives
$11.50 + $5.00 = **$13.75**, so `16.0` holds with $2.25 of slack. Gate 1's actual argues
for keeping the slack rather than trimming to $13.75: its substantive half came in 53.5%
under plan, but its `close-intermediate` came in **41.6% over** ($6.37 against $4.50), and
the largest WU here is the $5.00 `close`. The reasoning is recorded in
`GATE-02-REVIEW.md` § *Cost reconciliation*.

Note the interaction the budget has with `evaluate_auto_close`: `cost_budget_usd` is
check 6's ceiling, so a generous budget makes the predicate *more* willing to auto-close.
That is harmless here — `G2-CLOSE` carries `auto_close_disabled: true` (its AC4, AC5, and
AC7 are load-bearing), so the feature that makes auto-close debt visible cannot auto-close
its own terminal gate.

## Reflection notes

<Written by the human at review time.>
