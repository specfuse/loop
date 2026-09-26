---
id: FEAT-2026-0117/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
produces_driver_helper:
  - resolve_carry_forward_narrow_greens
  - reset_stale_criteria_entries
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/criteria_state.py
  - tests/test_reclose_carries_narrow_greens_e2e.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T18:36:08.413087+00:00
duration_seconds: 975.457
cost_usd: 5.13032
input_tokens: 240
output_tokens: 73783
---

# A re-armed close keeps the narrow greens the first close proved

**Objective.** Stop the re-arm skeleton step from wiping `narrow`/`pass` entries
in `GATE-NN-CRITERIA.md`, so the second close's worklist carries them forward
as `close-discipline.md` §5 already says it may.

**Context.** FEAT-2026-0117/T01, this gate's **walking skeleton**: it turns
`GATE-01.md`'s `feature_oracle` green; T02–T04 refine it. The reset lives in
`_precreate_criteria_state_stub` in `specfuse/loop/loop.py` (the #3279 block
that clears `oracle`, `kind`, `state`, `proved_at_sha` and `attempt` on entries
whose `attempt` exceeds the current one). Lift it into
`reset_stale_criteria_entries(entries, current_attempt, carry_narrow)`, in
`specfuse/loop/criteria_state.py` beside the parser: with `carry_narrow` true,
an entry with `kind: narrow` and `state: pass` keeps every field and gains
`carried_from_attempt: <n>`; everything else resets as today. `carry_narrow`
comes from `resolve_carry_forward_narrow_greens(cfg)` reading `verification.yml`
`defaults.carry_forward_narrow_greens` (default `True`). `build_reverification_worklist`
already partitions such entries as carried; make it accept the
`carried_from_attempt` field and leave the tree check to T02. Red test first:
the gate's oracle, shaped like `tests/test_rearm_clears_stale_criteria_state.py`'s
harness with two `loop.run()` passes.

**Acceptance criteria.**

1. `tests/test_reclose_carries_narrow_greens_e2e.py` fails on HEAD before this
   unit's edits (the module is absent); after,
   `python3 -m unittest tests.test_reclose_carries_narrow_greens_e2e -v -b`
   exits 0.
2. That module asserts, over two `loop.run()` passes with a re-arm between
   them: the second close dispatch's prompt lists the two narrow entries under
   the "Carried forward" heading and the broad entry under "Re-verify"; on
   disk the narrow entries read `state: pass` with their first-close
   `proved_at_sha` and `carried_from_attempt: 1`; the broad entry reads
   `unverified`.
3. A second case sets `defaults: carry_forward_narrow_greens: false` and
   asserts all three entries read `unverified` on the second dispatch (today's
   behaviour, unchanged).
4. `python3 -m unittest tests.test_criteria_state tests.test_criteria_worklist tests.test_loop_criteria_skeleton tests.test_loop_criteria_survival tests.test_lint_closing_criteria -v -b`
   exits 0 with no edit to those modules; `tests/test_rearm_clears_stale_criteria_state.py`
   may be edited only to split its fixture into a `broad` entry (still reset)
   and a `narrow` entry (now carried) — state the split in the RESULT summary.

**Do not touch.** The `proved_at_sha`-versus-diff check (T02); `judge.py` and
the close's Measurements (T03); `.specfuse/rules/` and `docs/` (T04);
`lint_closing.py`; `.specfuse/verification.yml`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if `lint_closing`'s
close-l rejects a carried narrow entry (say which check); or if the re-arm path
rewrites `GATE-NN-CRITERIA.md` somewhere other than the skeleton step (name it).
