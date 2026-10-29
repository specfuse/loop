---
id: FEAT-LOOP-2026-0248/T06
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 1.50
provenance: "Operator-session rehearsal on 2026-10-29 (after T05 blocked): `ids migrate --all --include-prose '.specfuse/**' 'specfuse/**' 'docs/**' 'plugins/**' --rehearse` reported 'migration failed (exit 1)' with lint_plan ERRORs for FEAT-LOOP-2026-0001-health-endpoint and FEAT-LOOP-2026-0036-adopt-ruff-016 although specfuse/** was rewritten in the worktree. ids._validate_tree (ids.py:511) imports agent_policy, lint_plan and lint_roadmap into the running process, so a rehearsal validates the renamed copy with the real checkout's pre-rename DONE_FEATURE_GATE_EXCLUSIONS."
produces:
  - specfuse/loop/ids.py
  - tests/test_migrate_all_repo_stays_valid.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T17:04:12.901570+00:00
duration_seconds: 95.252
cost_usd: 0.293477
input_tokens: 20
output_tokens: 6793
---

# T06 — post-apply validation runs the renamed tree's own code

**Objective.** The check that ends `--apply` and `--rehearse` judges the renamed tree with
the renamed tree's linters, never with modules already loaded from somewhere else.

**Context.** `FEAT-LOOP-2026-0248/T06`. This unit **edits** `ids.py` (T01's
`_validate_tree`) and the oracle module. Today `_validate_tree` imports `agent_policy`,
`lint_plan` and `lint_roadmap` in-process. In `--rehearse` the process runs the real
checkout's code, so the renamed copy is validated against the real checkout's
`lint_plan.DONE_FEATURE_GATE_EXCLUSIONS` (old folder names) and fails falsely. A real
`--apply` has the same exposure whenever one of those modules was imported before the
rewrite.

Run the validation in a fresh `sys.executable` subprocess with `cwd` set to the target
tree and `PYTHONPATH` set to that tree, invoking a small entry point
(`python3 -m specfuse.loop.ids validate`) that prints the same ERROR lines and exits
non-zero on any. `--apply` and `--rehearse` call it the same way. Keep the output format
T01 established.

**Acceptance criteria.**

1. A new oracle test in `tests/test_migrate_all_repo_stays_valid.py`: in a fixture
   repository whose own copy of a code table keys a feature by its old folder name, a
   rehearsal (and an `--apply`) that renames both reports validation clean, where the
   in-process version reported the stale entry. Fails before, passes after.
2. `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all tests.test_caller_check_ratchet -b`
   passes (the new `validate` entry point has its CLI caller).

**Do not touch.** Rewrite rules and prose scoping (T02, T03), the rehearsal's worktree
handling (T04) beyond calling the new entry point.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If `agent_policy` validation cannot run without the real
checkout's environment (for example a path it resolves from `__file__`), stop and name it.
