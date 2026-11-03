---
id: FEAT-LOOP-2026-0249/T02
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 3.50
produces:
  - specfuse/loop/closing_requirements.py
  - specfuse/loop/lint_closing.py
  - specfuse/loop/loop.py
  - specfuse/loop/arm_eval.py
  - tests/test_changelog_fragments.py
model: sonnet
effort: high
gate_set: code
produces_driver_helper: [_unreleased_has_entry_for, assert_changelog_entry_for_contract_changes]
driver_version: 0.31.1
started_at: 2026-11-02T16:10:21.928001+00:00
duration_seconds: 124.011
cost_usd: 0.681229
input_tokens: 44
output_tokens: 14217
---

# T02 — one reader for all three guards

**Objective.** Turn clause 2 green: a fragment-only entry satisfies every changelog guard, and
a feature with no entry in either form still fails all of them.

**Context.** `FEAT-LOOP-2026-0249/T02`; decision 2 in `PLAN.md`. Add one helper in
`closing_requirements.py` answering "does this feature have an entry, in `CHANGELOG.md`'s
Unreleased or a valid fragment?" and reusing `changelog_has_entry_for`. Replace all three call
sites: `assert_changelog_entry_for_contract_changes` and `_unreleased_has_entry_for` in
`loop.py`, `_check_changelog_entry_for_contract_changes` in `lint_closing.py`.

- Check for an entry first: a fragment-only project with no `CHANGELOG.md` passes. The
  "does not exist" message (#575) remains when neither form exists.
- A malformed fragment does not count as an entry.
- Refusal messages and the `close-k` description name both locations.
- `arm_eval.py:147` says of `changelog.py` "no gate reads it", which is false: `close-k` reads
  its parser. Move it to the judge registry.

**Acceptance criteria.**

1. The oracle's clause-2 class is unskipped, fails on HEAD and passes after, for all three guards.
2. `grep -c "parse_changelog" specfuse/loop/lint_closing.py` is 0: the check goes through the helper.
3. `python3 -m unittest tests.test_terminal_auto_close_changelog tests.test_load_bearing_close_lint tests.test_judge_path_registry -b` passes.

**Do not touch.** `changelog.py`'s functions. Collation (T03), `check` (T04). FEAT-LOOP-2026-0201's
scope: the absent-section behavior of `close-k` stays as it is.

**Verification.** The narrow tier for `implementation`, plus AC3's command.

**Escalation triggers.** If a fourth reader of the Unreleased section turns up, include it and
say so in evidence. If a guard's behavior for a `single` project would change, block.
