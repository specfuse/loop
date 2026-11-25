---
id: FEAT-LOOP-2026-0251/T02
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.50
produces:
  - specfuse/loop/loop.py
  - .specfuse/verification.yml.example
  - specfuse/loop/data/verification.yml.example
  - tests/test_fail_fast_deliverables.py
produces_driver_helper:
  - execute_unit_attempt
model: sonnet
effort: medium
---

# T02 — presence refusals early, and the `fail_fast_deliverables` opt-out

**Objective.** Turn Definition-of-done clauses 2 and 3 green.

**Context.** `FEAT-LOOP-2026-0251/T02`; decisions 4 and 6 in `PLAN.md`.

- Route `deliverable_missing` and `no_deliverable_files` through the same pre-`verify_fn` step
  T01 added, each through one helper shared with its late call site.
- Add `resolve_fail_fast_deliverables(verification_cfg)` beside
  `resolve_retain_on_guard_refusal`, reading `defaults.fail_fast_deliverables`, default `True`.
  `False` skips the early step, so all three refusals run after `verify_fn` exactly as before
  this feature.
- Document the key in `.specfuse/verification.yml.example` next to `retain_on_guard_refusal`,
  then run `scripts/sync-scaffold.sh` so the packaged copy matches.

**Acceptance criteria.**

1. `tests.test_fail_fast_deliverables.TestPresenceEarly` fails on HEAD and passes after: an
   absent or empty declared path ends `deliverable_missing`, and a diff naming only the unit
   file and events ends `no_deliverable_files`, each with `verify_fn` called 0 times.
2. `TestOptOut` fails on HEAD and passes after: with `fail_fast_deliverables: false`, each of
   the three cases calls `verify_fn` once before refusing, with the same outcome and failure
   class as the default path.
3. `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example` is
   empty.

**Do not touch.** Retry-note path lists (T03). `lint_plan.py` and docs (T04).

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If `no_deliverable_files` depends on state only the squash commit
creates, block with the evidence.
