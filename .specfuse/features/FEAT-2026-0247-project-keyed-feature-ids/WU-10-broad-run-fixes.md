---
id: FEAT-2026-0247/T10
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 1.00
provenance: "Gate 1's broad run at 2026-10-29T14:04:39 (events.jsonl human_escalation reason broad_run_gate_failure; gate log tests-20261029T140401776445Z.log) failed 4 tests, all deterministic consequences of this feature, none environmental: test_layout_no_layout_goldens' two GOLDEN_TEMPLATE_SHA256 checks (T06 intentionally changed .specfuse/roadmap.template.md's Notes), test_judge_path_registry.test_no_module_is_unclassified ('ids.py' in neither JUDGE_MODULES nor NON_JUDGE_MODULES), and test_caller_check_ratchet ('anchor' and 'sort_key' in specfuse/loop/ids.py have no caller outside tests/). Diagnosed in the operator's session; added under the operator's standing instruction to bring the feature to completion."
produces:
  - specfuse/loop/arm_eval.py
  - specfuse/loop/ids.py
  - tests/test_layout_no_layout_goldens.py
  - tests/test_ids.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T14:05:49.104566+00:00
duration_seconds: 35.717
cost_usd: 0.133118
input_tokens: 8
output_tokens: 1951
---

# T10 — fix the three registry and golden checks the broad run caught

**Objective.** Gate 1's broad run is green: the feature's new module is classified, has
no test-only public symbols, and the no-layout golden reflects the template T06
deliberately changed.

**Context.** `FEAT-2026-0247/T10`. This unit **edits** files earlier units created or
changed. Each per-attempt narrow tier passed; these are suite-wide registries that only
the broad run exercises.

- **Classify `ids.py` as a judge module.** It supplies `lint_plan`'s
  `CORRELATION_ID_RE`, and `lint_plan.py` is in `arm_eval.JUDGE_MODULES`; an edit to
  `ids.py` changes what the close's lint accepts. Add it to `JUDGE_MODULES` with the
  same reasoning style as its neighbours.
- **`ids.anchor` gets its real callers.** `ids.py`'s own rewrite paths lower-case IDs
  inline (`old.lower()`, `new.lower()` around lines 192-210 and 379); call `anchor()`
  there instead. **Remove `ids.sort_key`** and its test: nothing calls it (PLAN Known
  limits explains why lexical order is sufficient), and the ratchet's baseline is not
  the place for an unused helper.
- **Re-record the no-layout golden.** Update `GOLDEN_TEMPLATE_SHA256` in
  `tests/test_layout_no_layout_goldens.py` to the sha256 of the current
  `.specfuse/roadmap.template.md` (before the layout region markers, exactly as the
  existing constant is computed), with a comment citing FEAT-2026-0247/T06 as the
  intentional change. Do not loosen the test.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_judge_path_registry tests.test_caller_check_ratchet tests.test_layout_no_layout_goldens -b`
   fails on the current tree (4 failures) and passes after.
2. `python3 -m unittest tests.test_ids tests.test_ids_migrate tests.test_ids_migrate_all tests.test_keyed_feature_ids_end_to_end -b`
   still passes.

**Do not touch.** `.specfuse/roadmap.template.md` (T06's text stands). Any other entry
of `JUDGE_MODULES`, `NON_JUDGE_MODULES` or the caller-check `BASELINE`.

**Verification.** The narrow tier for `implementation`, plus both commands above.

**Escalation triggers.** If the golden's recorded value differs from the current
template for any reason other than T06's Notes change, stop and name the difference.
