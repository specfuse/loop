---
id: FEAT-2026-0085/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 8.00
model: opus
effort: high
oracle_env: macos_local
produces_driver_helper: VERDICT_VALUES, LEGACY_VERDICT_VALUES
produces:
  - specfuse/loop/closing_requirements.py
  - specfuse/loop/loop.py
  - tests/test_binary_verdict.py
duration_seconds: 1206.201
cost_usd: 6.521841
input_tokens: 146
output_tokens: 44935
re_arm_count: 1
re_arm_history:
  - timestamp: 2026-09-02T20:17:32+00:00
    prior_status: blocked_human
    prior_attempts: 0
    prior_cost_usd: 6.521841
    prior_duration_seconds: 1206.201
    reason: "AC3 rescoped to Python files, mirror is T05's"
---

# The verdict is met or not_met; delete the hedge machinery

**Objective.** Narrow `VERDICT_VALUES` to `{met, not_met}` and remove
everything that existed only to scaffold `met_locally` and `partially_met`:
the hedged follow-up `kind:` taxonomy, the verdict ceiling, requirement
`close-j`, and their guards, lint checks, and tests.

**Context.** FEAT-2026-0085/T01; read `PLAN.md` § Existing-mechanism search for
the deletion set. Legacy values stay readable: add `LEGACY_VERDICT_VALUES =
{met_locally, partially_met}` so `load_wu` and `recheck_terminal_verdict` parse
old closes without crashing, while `assert_verdict_well_formed` rejects them on
a close dispatched now with a message naming the two legal values and the
migration note (T05 writes it; reference `docs/methodology.md` § Migrating a
hedged close). `revert_terminal_surfaces` stays and now serves `not_met` only.
`terminal_gate_message` gets a `not_met` branch pointing at `FOLLOW-UPS.md`
(T03 creates that artifact; name it now). `lint_plan.py:248` drops the
`met_locally|partially_met` load-bearing signal and `:1581-1611` names the two
values. Delete `tests/test_hedged_kind_contract.py`; update the other test
files the search names rather than deleting assertions wholesale. Red test
first.

**Acceptance criteria.**

- `tests/test_binary_verdict.py::test_met_locally_is_rejected_at_outcome` fails on HEAD and passes after: a fixture close WU whose frontmatter says `verdict: met_locally` makes `assert_verdict_well_formed` return `(False, reason)` with `met` and `not_met` in the reason.
- `python3 -c "from specfuse.loop.closing_requirements import VERDICT_VALUES, LEGACY_VERDICT_VALUES; assert VERDICT_VALUES == frozenset({'met','not_met'}) and LEGACY_VERDICT_VALUES == frozenset({'met_locally','partially_met'})"` exits 0.
- `grep -rn --include="*.py" "HEDGED_VERDICT_VALUES\|FOLLOW_UP_KIND\|verdict_ceiling_for_kinds\|assert_hedged_followup_kinds_classified\|close-j" specfuse/ tests/ | wc -l` reports 0. Python only: the one prose mention, in `close-discipline.md` and its byte-identical mirror under `specfuse/loop/data/rules/`, is T05's to remove (attempt 1 blocked on exactly that mirror; see `events.jsonl`).
- `tests/test_binary_verdict.py::test_recheck_refuses_legacy_verdict_with_migration_pointer`: `recheck_terminal_verdict` on a fixture whose done close says `met_locally` returns `fired: False` and a reason containing `legacy`.
- `python3 -m unittest discover -s tests -q` reports `OK`, run outside any sandbox.

**Do not touch.** The auto-close stubs and debt marker (T02); `escalation.py`
(T03); `DISPATCHABLE` and type sets (T04); `.specfuse/rules/`, `docs/`,
`plugins/` (T05); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus the
commands above.

**Escalation triggers.** Emit `status: blocked` if a test outside the deletion
set asserts hedged behaviour that cannot be rewritten without changing an
unrelated guard; name the test. Emit `status: blocked` if `VERDICT_VALUES` is
absent from the files you edited.
