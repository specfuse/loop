---
feature_id: FEAT-2026-0036
title: Adopt ruff 0.16 and lift the <0.16 pin
slug: adopt-ruff-016
branch: feat/FEAT-2026-0036-adopt-ruff-016
roadmap_goal: Adopt ruff 0.16 — fix the ~300 new import-rule lint errors in the test suite, confirm the suite still passes, then lift the temporary `ruff>=0.6,<0.16` pin so the linter tracks current again.
autonomy_default: review
status: planned                 # active | blocked | deferred | done | abandoned
planned_cost_usd: 10.00
---

# Plan: Adopt ruff 0.16 and lift the <0.16 pin

ruff 0.16.0 tightened its import rules; run against `tests/` it reports ~300
lint errors (unsorted / unconsolidated imports) that predate any one change.
Because CI installed ruff unpinned, 0.16.0's release broke the lint gate on
every PR at once. The emergency fix pinned `ruff>=0.6,<0.16` (`pyproject.toml`).
This feature pays that debt down deliberately: make the tree clean under ruff
0.16, then lift the pin so the linter is current again — the mechanical import
churn separated from the one-line pin flip so review is legible.

This file owns the **shape**: two small implementation units (fix, then unpin)
and a terminal close. Each WU owns its own status; the gate file owns gate
status.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

n/a — no enforcement or measurement designed. This feature adopts an existing
external linter's newer rules and edits import statements to satisfy them; it
introduces no validation rule, severity level, gate, or measurement of its own.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — no check is raised to ERROR and no "zero issues" close predicate is
introduced. The relevant zero-on-correct-input property is ruff's own: after the
import fixes, `ruff check` under 0.16 reports zero on the (now-correct) tree,
which WU-02 verifies before lifting the pin.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0036/T01
        file: WU-01-ruff-016-clean.md
        depends_on: []
      - id: FEAT-2026-0036/T02
        file: WU-02-lift-ruff-pin.md
        depends_on: [FEAT-2026-0036/T01]
      # --- terminal gate: single close WU ---
      - id: FEAT-2026-0036/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0036/T01, FEAT-2026-0036/T02]
```

## Notes

- Single-gate feature (2 substantive WUs ≤ 4): one terminal `close`, no
  `close-intermediate` / `plan-next` — ceremony proportionality
  (`docs/methodology.md §6`).
- Ordering matters: T01 makes the tree clean under 0.16 while the pin still
  installs 0.15.x (a 0.16-clean tree is 0.15-clean too, so CI stays green
  between the WUs — no broken intermediate). T02 then lifts the pin so CI
  actually resolves 0.16 and proves it.
- Dependencies live here, not in WU frontmatter.
