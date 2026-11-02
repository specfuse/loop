---
id: FEAT-LOOP-2026-0249/T06
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 2.00
produces:
  - plugins/specfuse/skills/fix-bug/SKILL.md
  - .specfuse/skills/fix-bug/SKILL.md
  - .specfuse/rules/close-discipline.md
  - specfuse/loop/data/rules/close-discipline.md
  - docs/lifecycles.md
  - specfuse/loop/data/docs/lifecycles.md
model: sonnet
effort: medium
gate_set: code
---

# T06 — skills, rules and docs call the writer

**Objective.** `/fix-bug` and close-discipline §3 tell agents to run `add`, so neither branches
on the mode or hand-edits. An adopter can find out how to opt in.

**Context.** `FEAT-LOOP-2026-0249/T06`; decision 4 in `PLAN.md`. Sync runs in **two opposite directions**:
edit the skill in `plugins/specfuse/skills/` and sync to `.specfuse/skills/`; edit the rule in
`.specfuse/rules/` and sync to `specfuse/loop/data/rules/`. Docs sync to `specfuse/loop/data/docs/`.

- `fix-bug` Step "Before opening the PR": run `add` with `--trace '#<issue-number>'`, and include
  what it wrote in the fix commit.
- `close-discipline.md` §3: one `add` per enumerated item, with the feature's ID as trace; the
  `close-k` sentence says an entry lives in `CHANGELOG.md` or a fragment.
- `docs/lifecycles.md`: bug flow's changelog step; how to opt in with `changelog.mode`; the
  `check` gate an adopter should add; collating before stamping in a custom release script.

Red-test exempt: prose only; `tests.test_plugin_prose_cross_refs` and the sync bats suites are
the oracle.

**Acceptance criteria.**

1. `grep -c "changelog_fragments add" plugins/specfuse/skills/fix-bug/SKILL.md` is at least 1.
2. `grep -c "changelog_fragments add" .specfuse/rules/close-discipline.md` is at least 1.
3. `diff .specfuse/rules/close-discipline.md specfuse/loop/data/rules/close-discipline.md` is empty.
4. `python3 -m unittest tests.test_plugin_prose_cross_refs -b` passes.

**Do not touch.** Other sections of either file. `flows.html` beyond any one-line caption the
sync requires. Python under `specfuse/`.

**Verification.** The narrow tier for `implementation`, plus AC4's command.

**Escalation triggers.** If a sync check fails on a file this unit did not edit, block with the
evidence; that drift predates this unit.
