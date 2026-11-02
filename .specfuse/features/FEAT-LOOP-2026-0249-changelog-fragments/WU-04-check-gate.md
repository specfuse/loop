---
id: FEAT-LOOP-2026-0249/T04
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 1.50
produces:
  - specfuse/loop/changelog_fragments.py
  - .specfuse/verification.yml
  - tests/test_changelog_fragments.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.31.1
started_at: 2026-11-02T16:13:22.446147+00:00
duration_seconds: 33.062
cost_usd: 0.182498
input_tokens: 10
output_tokens: 2848
---

# T04 — PR-time fragment check

**Objective.** Turn clause 4 green: a malformed fragment fails at PR time, not at release.

**Context.** `FEAT-LOOP-2026-0249/T04`; decision 7 in `PLAN.md`. Add a `check` subcommand using the same
validation as `collate`, and a `changelog-fragments` gate in `.specfuse/verification.yml`
running `python3 -m specfuse.loop.changelog_fragments check`. `scripts/smoke-test.sh` and CI
derive their gates from that file, so no other wiring is needed.

**Acceptance criteria.**

1. The oracle's clause-4 class is unskipped, fails on HEAD and passes after: wrong class, bad
   trace, missing frontmatter and multi-line body each exit non-zero naming the file; an absent
   directory and valid fragments exit zero.
2. `python3 -m specfuse.loop.changelog_fragments check` exits zero on this repository.

**Do not touch.** Other gates in `verification.yml`. `collate`'s behavior (T03).

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If a test pins the gate list and fails on the new gate, update that
list and say so in evidence; do not drop the gate.
