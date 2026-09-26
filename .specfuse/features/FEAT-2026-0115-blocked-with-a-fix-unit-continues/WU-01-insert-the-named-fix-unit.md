---
id: FEAT-2026-0115/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 7.00
produces_driver_helper:
  - parse_blocked_next
  - insert_fix_unit
  - resolve_fix_unit_insertion
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_fix_unit_insertion_e2e.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T16:07:55.668902+00:00
duration_seconds: 704.898
cost_usd: 3.486723
input_tokens: 168
output_tokens: 62635
---

# A blocked RESULT that names a drafted fix unit is inserted and the gate continues

**Objective.** When a session reports `status: blocked` with a valid
`blocked_next:` fix unit, insert the draft ahead of the blocked unit, re-arm the
blocked unit behind it, and keep dispatching — no escalation.

**Context.** FEAT-2026-0115/T01, this gate's **walking skeleton**: the thinnest
end-to-end path that turns `GATE-01.md`'s `feature_oracle` green; T02–T04 refine
it. The handler is the `agent_reported_blocked` branch of `run()`'s attempt loop
in `specfuse/loop/loop.py` (it resets the tree, sets `blocked_human`, calls
`escalate_unit`, and breaks). Add `parse_blocked_next(result_block)` reading
`result_block["blocked_next"]` = `{kind: fix_unit, file, id}`; anything else
returns None and the branch behaves as today. `insert_fix_unit(feature_dir,
plan_path, gate, blocked_wu, draft)`: the draft file must exist in the feature
dir with matching `id:`, `status: draft` and `provenance:`; append it to the
gate's graph entry in `PLAN.md` with `depends_on: []`, add its id to the blocked
unit's `depends_on`, flip the draft to `pending`, set the blocked unit back to
`pending` with `re_arm_count` incremented so `detect_rearm_dispatch` records
`re_arm_dispatched` with reason `fix_unit_inserted`, emit
`build_event("fix_unit_inserted", blocked_id, {fix_unit_id, file, gate,
insertion_count})`, register the type in
`specfuse/loop/data/schemas/driver-event.schema.json` ($comment and enum, as
`replan` was), write a PROGRESS line, commit the bookkeeping, refresh the
in-memory `units` the way `reload_unit_after_replan` does, and `continue` the
gate. Keep the blocked attempt's `attempt_outcome` (`agent_status: blocked`)
and the tree reset as they are. `resolve_fix_unit_insertion(cfg)` reads
`verification.yml` `defaults.fix_unit_insertion` (default `True`). Only when
`PLAN.md` `autonomy_default` is `auto`; otherwise fall through to today's
escalation (T03 words the brief). Red test first: the gate's oracle, shaped
like `tests/test_replan_end_to_end.py`'s harness.

**Acceptance criteria.**

1. `tests/test_fix_unit_insertion_e2e.py` fails on HEAD before this unit's
   edits (the module is absent); after,
   `python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b` exits 0.
2. That module asserts, end to end through `loop.run()`: the dispatch order is
   T01 (blocked with `blocked_next`), T05, T01; both end `done`; `events.jsonl`
   carries one `fix_unit_inserted` and one `re_arm_dispatched` for T01 and no
   `human_escalation`; `PLAN.md` lists T05 in gate 1 and T01's `depends_on`
   names it.
3. Two more cases: a blocked RESULT without `blocked_next:` ends
   `blocked_human` with `human_escalation` reason `agent_reported_blocked`
   (today, unchanged); with `autonomy_default: review` the same RESULT as case
   2 escalates and the draft stays `draft`.
4. `python3 .specfuse/scripts/event_type_gate.py` exits 0, and
   `python3 -m unittest tests.test_spinout_brief_end_to_end tests.test_replan_end_to_end tests.test_attempt_outcome_contract -v -b`
   exits 0 with no edit to those modules.

**Do not touch.** `run_replan_turn` and `should_replan_instead_of_retry`;
`arm_eval.py` and `arm_txn.py` (T02 calls them, does not edit them);
`gate_eval.py` (T03); `.specfuse/rules/` and `docs/` (T04);
`.specfuse/verification.yml`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if the gate-start check
that exits 2 on any `draft` unit fires against the inserted draft before the
flip lands (name the check); or if `PLAN.md`'s graph cannot be edited without a
YAML round-trip that reorders or reformats other entries — say which helper
you tried.
