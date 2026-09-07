---
id: FEAT-2026-0102/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 8.00
oracle_env: macos_local
produces_driver_helper: order_gate_set
produces:
  - specfuse/loop/loop.py
  - tests/test_loop_gate_needs.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.15.0
started_at: 2026-09-07T18:48:28.968837+00:00
duration_seconds: 1058.307
cost_usd: 1.053505
input_tokens: 86
output_tokens: 13531
---

# Order the gate set by `needs:` and skip a gate whose dependency failed

**Objective.** Teach `_run_gate_set` that a gate may declare `needs: [<gate>]`:
run the set in dependency order, and report a gate whose dependency failed as
`SKIP` without running it and without counting it as a pass.

**Context.** FEAT-2026-0102/T01; read `PLAN.md`, including its
existing-mechanism search. `_run_gate_set` (`loop.py:4025`) currently iterates
the set unconditionally. `_miniyaml` already parses `needs: [tests]` into
`{'needs': ['tests']}` and `load_verification` (`loop.py:3874`) passes the key
through, so no parser work is needed. Both callers must get the behaviour:
`verify()` (`loop.py:4127`) and `probe_baseline()` (`loop.py:4175`). Resolve
order in a helper both call — validation cannot live in `verify()` alone or the
baseline probe silently keeps the old semantics.

**This lands inert.** No `verification.yml` declares `needs:` yet, so after
this unit every gate still runs exactly as it does today. That is deliberate:
T03 flips this repo's gate set only after the mechanism is tested, so sibling
units keep the oracle they were dispatched under ([FEAT-2026-0019/G1]).

**Two details that are easy to get wrong.**

1. A skipped gate must carry `ok=False`, never `True`. A skip that reads as
   green is the hollow-pass shape issue #134 forced `detect_degraded_oracle` to
   fail loudly for; do not reintroduce it through the skip path.
2. The skip's report line must **not** match `^### ([\w-]+): FAIL`
   (`loop.py:1256`), so `parse_gate_failure_signature` still attributes the
   attempt to the dependency that actually failed rather than to its dependent.
   Write `### <name>: SKIP — dependency '<dep>' failed`.

**Acceptance criteria.**

- `tests/test_loop_gate_needs.py::test_dependent_skipped_when_dependency_fails` fails on HEAD and passes after: with `coverage` declaring `needs: [tests]` and `tests` exiting non-zero, `coverage`'s command never runs, its result carries `ok=False`, and its report contains `SKIP`.
- `::test_skip_report_does_not_capture_failure_attribution`: on that same run, `parse_gate_failure_signature` over the joined report returns `failure_class == "tests"`.
- `::test_declared_order_is_topological`: a set declaring `coverage` (needs `tests`) before `tests` runs `tests` first, and two gates with no edges keep their declared relative order.
- `::test_unknown_needs_target_is_configuration_error` and `::test_needs_cycle_is_configuration_error`: each returns the CONFIGURATION ERROR shape used for unknown `extra_gates` (`loop.py:4159`), naming the offending gate, from **both** `verify()` and `probe_baseline()`.
- `::test_absent_needs_is_inert`: a gate set with no `needs:` key runs every gate in declared order, unchanged from HEAD.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** `specfuse/loop/gate_commands.py` (T02);
`.specfuse/verification.yml` and `plugins/specfuse/skills/verification/SKILL.md`
(T03) — declaring `needs:` anywhere in this unit would change the oracle your
own siblings run under. `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`.

**Escalation triggers.** Emit `status: blocked` if ordering the set breaks an
existing test that asserts gate execution order or report concatenation — name
the test rather than rewriting its expectation. Also block if the skip verdict
cannot be expressed without changing `_run_gate_set`'s return contract
(`{"name", "ok", "report"}`), which `probe_baseline` and `verify` both destructure.
</content>
