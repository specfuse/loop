---
id: FEAT-LOOP-2026-0249/T01
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/changelog_fragments.py
  - specfuse/loop/layout.py
  - specfuse/loop/arm_eval.py
  - tests/test_changelog_fragments.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.31.1
started_at: 2026-11-02T16:09:17.197647+00:00
duration_seconds: 64.389
cost_usd: 0.444282
input_tokens: 18
output_tokens: 7189
---

# T01 — walking skeleton: the writer, the setting and the oracle

**Objective.** Make the gate's `feature_oracle` runnable and turn clause 1 and clause 5's
writer half green. This is the tracer bullet: stubs are allowed here only.

**Context.** `FEAT-LOOP-2026-0249/T01`; decisions 1, 3, 4 and 5 in `PLAN.md`. This unit **creates**
`changelog_fragments.py` and **edits** `layout.py` and `arm_eval.py`.

- `layout.py`: add `changelog.mode` to `KEYS` and `changelog` to `KNOWN_TOP_LEVEL`. Absent
  means `single`. `validate` reports an error on any other value.
- `python3 -m specfuse.loop.changelog_fragments add --class C --trace T --summary S [--repo DIR]`:
  in `fragments` mode writes `changelog.d/<normalized-trace>-<slug>.md`; in `single` mode
  calls `append_entry` on `CHANGELOG.md`. It refuses a bad class, a trace `parse_changelog`
  would reject, a multi-line summary, and an existing target file. Normalizing: `#3563`
  becomes `3563`, `/` becomes `-`.
- Register the module in `arm_eval.py` as a judge module (T02 makes `close-k` read it).

Create `tests/test_changelog_fragments.py`, one class per Definition-of-done clause in
`GATE-01.md`; implement 1 and the writer half of 5, skip the rest naming T02–T04.

**Acceptance criteria.**

1. The oracle's clause-1 class fails on HEAD and passes after, including its `single`-mode
   conflict control.
2. Clause 5's writer test passes: with no `changelog.mode` key, `add` leaves no `changelog.d/`
   and the new entry parses under `Unreleased`.
3. `python3 -m unittest tests.test_judge_path_registry tests.test_changelog_release_wiring -b` passes.

**Do not touch.** The driver and the closing guards (T02).
`scripts/bump_version.py` (T03). `.specfuse/layout.yml` (T07).

**Verification.** The narrow tier for `implementation`, plus AC3's command, plus
`python3 -c "from specfuse.loop.changelog_fragments import main"`.

**Escalation triggers.** If `layout.validate` cannot take a nested key without changing
`ids.key` behavior, block with the evidence.
