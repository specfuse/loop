---
gate: 1
status: open
---

# Gate 1 — Post-pass invariant guard + helper-declaration field

## Definition of done

- `POST_PASS_INVARIANTS_BY_TYPE` dict registered in `loop.py` keyed
  by WU type. Initial entry: `close` → `[assert_terminal_flips_fired]`.
- `assert_terminal_flips_fired(wu, feature_dir, repo_root, head_before)`
  helper that re-reads WU frontmatter, returns `(True, "")` on hedged
  verdict (`met_locally` / `partially_met`), and on `verdict: met`
  asserts ALL of: terminal gate `passed`, roadmap row `done`,
  archive anchor present.
- `verify_post_pass_invariants` runner wired into the passed path
  AFTER squash + verdict-flip but BEFORE bookkeeping flush. On
  failure: `reset_preserving_events`, append
  `attempt_outcome: post_pass_invariant_failed`, count as failed
  attempt for spinning detection.
- `produces_driver_helper` optional WU frontmatter field; lint
  warns on `implementation` WUs whose body mentions driver wiring
  without declaring the symbol(s).
- Regression test reproducing FEAT-2026-0015/T06 G2-CLOSE bug pattern;
  asserts new guard would have caught it.
- G1-CLOSE exercises `assert_terminal_flips_fired` against itself
  (recursive dogfood). If T01's wiring is broken, G1-CLOSE blocks.
- `RETROSPECTIVE.md` exists, durable lessons (if any) in
  `.specfuse/LEARNINGS.md`, `PLAN.md` and roadmap row reflect `done`,
  archive section populated.

Single-gate terminal: 1-WU combined `close` ceremony (NEW contract,
not legacy 4-WU). No `plan-next` — no successor gate.

## Reflection notes

<Written by the human at review time.>
