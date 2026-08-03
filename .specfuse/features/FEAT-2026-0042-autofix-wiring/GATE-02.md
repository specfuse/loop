---
gate: 2
status: open
cost_budget_usd: 0.00
---

# Gate 2 — the dial goes live, verified end to end

## Definition of done

<Drafted by `FEAT-2026-0042/G1-PLAN` at gate 1's close. Substantive work units are
inserted into `PLAN.md`'s graph BEFORE the pre-declared `G2-CLOSE`.>

The intended shape, recorded at draft time so `G1-PLAN` has a starting point rather
than a blank page — it may revise this after reading gate 1's retrospective:

- the firing wiring: a diagnosed finding that T01's predicate approves actually
  invokes T03's headless `fix-bug` mode, records the attempt through T02's state, and
  labels the outcome;
- a live end-to-end run against a **scratch issue in this repository carrying a
  planted trivial bug** — real branch, real pull request, verified, then cleaned up.
  Not a real finding, so the PR is disposable by construction. Follow
  `FEAT-2026-0041/T04`'s posture: `unsandboxed: true` with its rationale, raw command
  output dumped between markers rather than classified, and cleanup as an explicit
  acceptance criterion.

## The safety floor — carried forward, not re-decidable here

Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048) and is
**impossible in this feature**. No work unit in this gate may merge a pull request,
enable auto-merge, or push to a protected branch. The ceiling is an unwanted PR on a
branch. A drafted WU that widens this is an escalation to the operator, not a
judgement call for `G1-PLAN`.

## Arming discipline — `G1-PLAN` must re-answer, not inherit

Gate 1's answers do not carry into this gate. Both of the checks below are re-answered
at drafting time, not inherited.

The §4 runtime probe is required for this gate. Gate 1's "not applicable" answer does
not carry: gate 2 introduces firing behaviour behind a dial that is currently inert,
which is precisely the case `planning-discipline.md` §4 exists for. Answer it in
`GATE-02-REVIEW.md` before arming.

**§2 satisfiability must be re-answered too.** Gate 1 was satisfiable by construction
because nothing fired. Gate 2 fires, so its criteria meet a real repository — and fix
*correctness* remains unassertable.

## Cost budget

`cost_budget_usd` is `0.00` as a placeholder. `G1-PLAN` sets it to the sum of the
work units it drafts plus one re-attempt of the largest, per the GATE template.

## Reflection notes

<Written by the human at review time.>
