---
id: FEAT-LOOP-2026-0246/T06
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.00
provenance: "The judge_editing_terminal halt on this feature's own close (events.jsonl human_escalation on FEAT-LOOP-2026-0246/G1-CLOSE at 12:37:49) told the operator to write judge_edit_acknowledged with 'the paths', but two of its eleven hits were produces_driver_helper declarations. arm_eval.evaluate_terminal_judge_editing covers those only with the literal key DRIVER_HELPER_ACK_KEY ('produces_driver_helper', arm_eval.py:634), which the brief never names, so an operator listing file paths would re-fire the stop. Found by the operator-side gate-status review; the operator asked for it to be fixed in this feature before the close."
produces:
  - specfuse/loop/arm_eval.py
  - specfuse/loop/loop.py
  - tests/test_arm_eval_terminal.py
  - tests/test_terminal_judge_editing_end_to_end.py
produces_driver_helper:
  - stop_for_terminal_judge_edit
model: sonnet
effort: medium
gate_set: code
oracle_env: macos_local
---

# T06 — the halt brief names the exact acknowledgement entries

**Objective.** An operator who copies the acknowledgement the brief shows clears the
stop on the first try, including for `produces_driver_helper` hits.

**Context.** `FEAT-LOOP-2026-0246/T06`. This unit **edits** `arm_eval.py`, `loop.py` and
the two test modules T01–T03 created. `evaluate_terminal_judge_editing` keys each hit
by its path, or by `DRIVER_HELPER_ACK_KEY` for a `produces_driver_helper`
declaration, and is clean only when the acknowledgement's `paths` contain every key.
The brief (`_format_judge_editing_terminal_brief`) says "the paths and your own
reason" and never names that key.

- Add a pure `arm_eval.terminal_judge_edit_ack_keys(feature_dir, gate_number)`:
  the sorted, de-duplicated keys an acknowledgement must list to cover every current
  hit. Share the hit collection with `evaluate_terminal_judge_editing` rather than
  duplicating it.
- `stop_for_terminal_judge_edit` passes those keys through `escalate_unit` to the
  brief, which shows a paste-ready `judge_edit_acknowledged` YAML block: the keys as
  `paths`, and `reason` as a placeholder the operator replaces with their own words.
  The brief never fills in a reason.

**Acceptance criteria.**

1. `tests/test_arm_eval_terminal.py`: the keys for a fixture with a judge-path
   `produces:` and a `produces_driver_helper` declaration are the path plus
   `produces_driver_helper`, de-duplicated across units; an acknowledgement listing
   exactly those keys makes `evaluate_terminal_judge_editing` clean. Both fail before
   the change.
2. `tests/test_terminal_judge_editing_end_to_end.py`: the halt message for a
   driver-helper fixture contains a `judge_edit_acknowledged:` block listing
   `produces_driver_helper` and a reason placeholder. Fails before the change.
3. The `feature_oracle` and `tests.test_lifecycle_integration` still pass.

**Do not touch.** The acknowledgement matching rule itself (what covers what). Docs.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_lifecycle_integration -b`.

**Escalation triggers.** If showing the keys needs a change to how hits are matched,
stop: that is a semantics change, not a brief fix.
