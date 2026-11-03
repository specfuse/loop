---
id: FEAT-LOOP-2026-0249/T05
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 1.50
produces:
  - specfuse/loop/ids.py
  - tests/test_ids_migrate_all.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.31.1
started_at: 2026-11-02T16:13:55.965709+00:00
duration_seconds: 49.392
cost_usd: 0.193922
input_tokens: 14
output_tokens: 2843
---

# T05 — ids migrate follows fragment traces

**Objective.** After `ids migrate`, a fragment's `trace` names the new ID, so `close-k` and the
release still match it.

**Context.** `FEAT-LOOP-2026-0249/T05`; decision 5 in `PLAN.md`. `_rewrite_file` in `ids.py` special-cases
`rel == "CHANGELOG.md"`, rewriting only Unreleased because released sections are append-only.
A fragment is by definition unreleased, so its `trace` is rewritten. Filenames stay as they
are: frontmatter is the source of truth.

**Acceptance criteria.**

1. A test in `tests/test_ids_migrate_all.py` fails on HEAD and passes after: an unkeyed
   `FEAT-` trace in a `changelog.d/` fragment is rewritten by `ids migrate --all --apply`
   without `--include-prose`, its filename is unchanged, and `check` still passes on the result.
2. `python3 -m unittest tests.test_ids_migrate tests.test_ids_migrate_all -b` passes.

**Do not touch.** How `CHANGELOG.md`'s released sections are handled. `changelog_fragments.py`.

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If HEAD already rewrites the trace, the red test cannot go red: keep the
test as coverage, report `Red-test exempt` with that evidence, and change no `ids.py` code.
