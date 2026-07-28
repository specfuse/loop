---
gate: 1
status: passed
cost_budget_usd: 19.00
baseline:
  sha: 85c36e8803932c7e358780b8524cff22eaf62846
  probed_at: 2026-07-28T15:09:14.018692+00:00
  failing: []
---

# Gate 1 — every declared structural invariant has a check behind it

## Definition of done

- Every directory under `.specfuse/skills/` is asserted to have a `.claude/skills/`
  link resolving to it, with the reverse direction filtered to links pointing
  inside `.specfuse/skills/` so operator tooling does not trip it.
- `scripts/sync-scaffold.sh` creates a missing forward link instead of documenting
  a contract it does not enforce.
- `lint_plan` refuses a `done` feature whose gates are not all `passed`, with the
  two legitimate exclusions carried by ID and reason.
- The state already on disk is reconciled, so both checks report zero on a correct
  tree.
- `RETROSPECTIVE.md` exists; lessons are promoted to `.specfuse/LEARNINGS.md`; the
  roadmap reflects what was built.

Terminal gate, so the closing sequence is the single `close` work unit.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** **Required for T03.** It
  introduces a new blocking `lint_plan` error, which is a severity flip in the
  sense §4 means: a tree that lints clean today can lint dirty after it. Before
  arming, apply T03's check locally and run the exact command its tests gate will
  run — `python3 .specfuse/scripts/lint_plan.py` across every feature directory —
  and paste the resulting finding list into the gate review. That list is the
  enumerated surface T03 must reconcile. Expected at draft time: three findings
  (FEAT-2026-0007, FEAT-2026-0008, FEAT-2026-0036). If the probe returns a
  different set, the WU's scope is wrong and must be re-drafted before dispatch.
- **Flag-scope table (§3).** Not applicable — no work unit introduces or gates on
  a behavior flag. The exclusions in T01 and T03 are data, not flags.
- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`, and it is
  the load-bearing answer for this gate: both checks report zero **only after**
  T03's reconciliation lands, which is why the check and the reconciliation are
  the same work unit rather than two.

## Arming probe result (§4, run at draft time)

The enumerated surface T03 must reconcile, from a sweep of every feature directory
for a `done` PLAN with a non-`passed` gate:

```
FEAT-2026-0001-health-endpoint          GATE-01.md = open             → exclude (bundled fixture)
FEAT-2026-0001-health-endpoint          GATE-02.md = open             → exclude (bundled fixture)
FEAT-2026-0007-dispatch-cost-controls   GATE-02.md = awaiting_review  → flip to passed
FEAT-2026-0008-driver-completeness-guard GATE-01.md = awaiting_review → flip to passed
FEAT-2026-0036-adopt-ruff-016           GATE-01.md = open             → exclude (close never ran)
```

Five findings across four features, matching T03's drafted scope exactly. If a
re-probe at arming time returns a different set, T03 is mis-scoped and must be
re-drafted before dispatch rather than absorbing the difference silently.

## Reflection notes

<Written by the human at review time.>
