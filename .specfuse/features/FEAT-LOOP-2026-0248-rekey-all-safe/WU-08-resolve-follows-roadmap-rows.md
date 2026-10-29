---
id: FEAT-LOOP-2026-0248/T08
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.00
provenance: "T05's third dispatch (blocked after 3077s, events.jsonl human_escalation agent_reported_blocked, 2026-10-29) found: FEAT-2026-0078 is a planned roadmap row with no feature folder and is queued in .specfuse/agent-policy.yml; the rename re-keys the row and writes an alias, but ids.resolve (ids.py:489) follows an alias only when its target has a folder, so it returns the legacy ID and post-rename validation reports `queue: 'FEAT-2026-0078' has no row in roadmap.md`. Operator chose option A: a code unit for resolve, then re-arm T05 through the driver."
produces:
  - specfuse/loop/ids.py
  - tests/test_migrate_all_repo_stays_valid.py
---

# T08 — an alias resolves to a feature that exists only as a roadmap row

**Objective.** After a full rename, an old ID of a planned feature that has a roadmap row
but no folder yet still resolves, so configuration naming it stays valid.

**Context.** `FEAT-LOOP-2026-0248/T08`. This unit **edits** `ids.py` and the oracle module.
`ids.resolve` (`ids.py:489`) returns the ID itself when it has a folder, else its alias
target, but only when the target **has a folder**; otherwise it warns and returns the old
ID. A planned feature has no folder yet, so its alias is never followed.

Change the existence test for both the input and the alias target to "has a folder under
`.specfuse/features/` **or** a row in `.specfuse/roadmap.md` / `.specfuse/roadmap-archive.md`",
reusing the roadmap-row reader `ids.py` already has. An alias whose target has neither
still warns and returns the input unchanged.

**Acceptance criteria.**

1. New oracle test: a fixture repository with a planned, folderless row queued in
   `agent-policy.yml`; after `migrate --all --apply`, the run exits zero and agent-policy
   validation is clean. A paired case whose alias target has neither folder nor row still
   warns. Fails before, passes after.
2. `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_aliases tests.test_agent_policy_queue -b`
   passes.

**Do not touch.** Rewrite rules, prose scoping, validation, rehearsal (T02–T04, T06, T07).
Tests other than the oracle module.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If a caller of `resolve` relies on a folder existing for the
returned ID (for example to open `PLAN.md`), name it and stop rather than changing it.
