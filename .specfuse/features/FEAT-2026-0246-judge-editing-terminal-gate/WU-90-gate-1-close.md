---
id: FEAT-2026-0246/G1-CLOSE
type: close
status: pending
attempts: 0
judge_edit_acknowledged:
  paths:
    - produces_driver_helper
    - specfuse/loop/arm_eval.py
    - specfuse/loop/data/schemas/driver-event.schema.json
    - specfuse/loop/lint_plan.py
    - specfuse/loop/loop.py
  reason: "Reviewed the diff; additive stop, no existing guard weakened"
planned_cost_usd: 5.00
model: sonnet
effort: high
gate_set: plannext
auto_close_disabled: true
---

# G1-CLOSE — terminal close

**Context.** The feature's only gate: a terminal gate whose own substantive units
declare a judge-surface path halts before its close at every autonomy level, an
operator acknowledgement clears it for the paths it names, and the docs say so.

**Acceptance criteria.**

1. **The self-halt fired** (PLAN decision 8). `events.jsonl` shows a
   `human_escalation` with reason `judge_editing_terminal` on this unit naming at least
   `specfuse/loop/arm_eval.py` and `specfuse/loop/loop.py`, followed by
   `terminal_judge_editing_acknowledged` carrying the operator's reason, before this
   close was dispatched. If either event is absent, record `not_met` with a follow-up
   naming which.
2. `RETROSPECTIVE.md` records, per Definition-of-done clause in `GATE-01.md`, what was
   proven and by which test, and that no `unittest.skip` survives in
   `tests/test_terminal_judge_editing_end_to_end.py`.
3. A `## Cost analysis` reconciles every unit against `planned_cost_usd` and
   `events.jsonl`, and states what the self-halt cost in operator wait.
4. "What the loop did NOT verify" names, at minimum: a real consumer-repo halt on a
   universal judge path (PLAN post-merge checklist), and the declared-not-actual-paths
   limit — each with where it actually gets checked.
5. `CHANGELOG.md`'s Unreleased section carries the user-visible change, including that
   consumer projects now halt once when a terminal gate edits `.specfuse/verification.yml`,
   `.specfuse/hooks/`, `.specfuse/rules/`, `.github/workflows/` or `pyproject.toml`,
   and how to clear it.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Source files under `specfuse/` other than docs. Other features.

**Verification.** `specfuse lint --closing`, plus the gate set in
`.specfuse/verification.yml`.

**Escalation triggers.** A surviving skip, or a docs copy still recommending `review`
for a terminal-gate judge edit: record `not_met` with a follow-up.
