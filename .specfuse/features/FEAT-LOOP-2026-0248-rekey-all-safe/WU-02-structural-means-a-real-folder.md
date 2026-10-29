---
id: FEAT-LOOP-2026-0248/T02
type: implementation
status: done
attempts: 2
oracle_env: macos_local
planned_cost_usd: 2.50
produces:
  - specfuse/loop/ids.py
  - tests/test_ids_migrate_all.py
  - tests/test_migrate_all_repo_stays_valid.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T15:13:15.820935+00:00
duration_seconds: 73.164
cost_usd: 0.335791
input_tokens: 22
output_tokens: 4891
---

# T02 — structural means a folder that exists

**Objective.** The rename never rewrites a path that only a test fixture uses, and always
rewrites an exact existing folder name wherever it appears.

**Context.** `FEAT-LOOP-2026-0248/T02`. This unit **edits** `ids.py` and two test modules.
Today `_rewrite_line` treats a match as structural when the text before it ends with
`features/` (`ids.py` ~line 361), whatever follows. In the rehearsal that re-keyed
`tests/test_deliverable_presence_gate.py`'s expected `.specfuse/features/FEAT-2026-0028-green-path`
(a fixture; the real folder is `FEAT-2026-0028-umbrella-cli-wiring`) while the fixture
code that creates the folder kept the old ID.

Change the rule: in any file, an occurrence of `<old ID>-<slug>` (with or without a
leading `features/`) is structural **only** when `.specfuse/features/<old ID>-<slug>`
exists in the repository being renamed. Such an occurrence is rewritten without
`--include-prose`; this is what carries `lint_plan.DONE_FEATURE_GATE_EXCLUSIONS`' keys
(`"FEAT-2026-0001-health-endpoint"`) along with the folder. Any other `features/<ID>-…` is
prose. The roadmap, `PLAN.md`/WU frontmatter, `events.jsonl` and folder-move rules are
unchanged.

Un-skip the oracle's clause-3 class.

**Acceptance criteria.**

1. The clause-3 class: in a fixture repository with a real folder `FEAT-2026-0005-real`,
   a test file's `features/FEAT-2026-0005-fixture` is left alone, a code dict key
   `"FEAT-2026-0005-real"` is rewritten, and both behave the same with and without a
   leading `features/`. Fails before, passes after.
2. `tests/test_ids_migrate_all.py` passes, with any case whose expectation encoded the old
   rule updated and the reason stated in the test.

**Do not touch.** Prose scoping (T03), the post-apply check (T01), `next_id`, the grammar.

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If an exact folder name appears inside a code span or fenced block
in markdown, treat it like any other structural occurrence unless that breaks a T05 of
FEAT-2026-0247 test; then stop and name the case.
