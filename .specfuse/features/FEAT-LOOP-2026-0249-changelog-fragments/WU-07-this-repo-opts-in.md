---
id: FEAT-LOOP-2026-0249/T07
type: implementation
status: done
attempts: 2
oracle_env: macos_local
planned_cost_usd: 1.00
produces:
  - .specfuse/layout.yml
  - tests/test_changelog_fragments.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.31.1
started_at: 2026-11-02T16:58:17.249178+00:00
duration_seconds: 61.872
cost_usd: 0.224013
input_tokens: 18
output_tokens: 2386
---

# T07 — this repository opts in

**Objective.** This repository writes fragments from here on, so G1-CLOSE passes on a
fragment-only entry and the feature proves itself on its own close.

**Context.** `FEAT-LOOP-2026-0249/T07`; decision 9 in `PLAN.md`. Set `changelog.mode: fragments` in
`.specfuse/layout.yml`, leaving `ids.key` alone.

**Acceptance criteria.**

1. A test fails on HEAD and passes after: on this repository `python3 -m specfuse.loop.layout get
   changelog.mode` prints `fragments` and `get ids.key` still prints `LOOP`.
2. `python3 -m unittest tests.test_changelog_schema tests.test_terminal_auto_close_changelog tests.test_changelog_fragments -b` passes.

**Do not touch.** `CHANGELOG.md`: its existing `Unreleased` entries stay there.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If a test fixture inherits this repository's setting and changes
behavior, fix the fixture to set its own mode and name it in evidence.
