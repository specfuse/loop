---
id: FEAT-LOOP-2026-0248/T01
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/agent_policy.py
  - specfuse/loop/ids.py
  - tests/test_migrate_all_repo_stays_valid.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T15:12:17.907356+00:00
duration_seconds: 57.562
cost_usd: 0.397029
input_tokens: 24
output_tokens: 6897
---

# T01 — walking skeleton: policy resolves old IDs, and `--apply` validates what it wrote

**Objective.** Make the gate's `feature_oracle` runnable and turn clauses 1 and 2 green:
after a full rename the operator's configuration still validates, and `--apply` itself says
whether the tree it left is valid. Tracer bullet: stubs are allowed here only.

**Context.** `FEAT-LOOP-2026-0248/T01`. This unit **edits** `agent_policy.py` and `ids.py`
(FEAT-LOOP-2026-0247 created `ids.py`).

- `agent_policy`'s queue-against-roadmap check (the "has no row in roadmap.md" error and
  the done-feature WARN) resolves each queue entry with `ids.resolve` before looking up
  the roadmap row; a queue entry that resolves through an alias is not an error.
- `ids migrate --all --apply` (and `--planned-only --apply`) ends by running, in-process,
  `lint_plan` over every `.specfuse/features/*/`, `lint_roadmap`, and agent-policy
  validation when `.specfuse/agent-policy.yml` exists. Print each ERROR; exit non-zero if
  any, with one line saying the tree is under git and `git checkout -- . && git clean -fd
  .specfuse/features` undoes the rename. Exit zero when all pass.

Create `tests/test_migrate_all_repo_stays_valid.py`, one class per Definition-of-done
clause 1–5 in `GATE-01.md`; implement 1 and 2, skip 3–5 naming T02–T04.

**Acceptance criteria.**

1. The oracle's clause-1 and clause-2 classes fail on HEAD and pass after. Clause 2 has a
   positive control: a fixture whose rename produces a `lint_plan` error exits non-zero,
   and a clean fixture exits zero.
2. `python3 -m unittest tests.test_agent_policy_queue tests.test_agent_policy_schema tests.test_ids_migrate tests.test_ids_migrate_all -b`
   passes.

**Do not touch.** Rewrite classification (T02), prose scoping (T03), rehearsal (T04).
`lint_plan.py`, `lint_roadmap.py` (called, not changed).

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If `lint_plan` cannot be called in-process over a folder without
its CLI's `sys.exit`, call its function-level entry point; if there is none, stop and name
what is missing rather than shelling out.
