---
id: FEAT-2026-0101/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces_driver_helper: read_gate_feature_oracle
produces:
  - specfuse/loop/loop.py
  - tests/test_feature_oracle_e2e.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.16.0
started_at: 2026-09-07T22:23:35.460061+00:00
duration_seconds: 1463.591
cost_usd: 3.637576
input_tokens: 252
output_tokens: 38843
---

# Tracer bullet — declare a gate's `feature_oracle`, read it, run it in `verify()`

**Objective.** Make `feature_oracle` in `GATE-NN.md` frontmatter real: read it,
run it through the existing gate runner, and include its verdict in the
verification of every unit in that gate.

**Context.** FEAT-2026-0101/T01; read `PLAN.md`, especially its
existing-mechanism search. **This is the tracer bullet** — the unit that makes
`GATE-01.md`'s own `feature_oracle` runnable and green, and the only unit in
this gate permitted to leave stubs behind it. `_run_gate_set(gate_set,
feature_dir)` takes an **arbitrary list of `{name, command}` dicts**, not a
`verification.yml` set name, so synthesize a one-element list and hand it to
that runner. Do not build a second execution path: the timeout, process-group
kill, Windows bash routing, degraded-oracle detection and `failure_class`
attribution all live there already and took four bug fixes to get right.

**Where it plugs in.** `verify(wu, feature_dir, cfg)` resolves the WU's gate
set and calls `_run_gate_set`. The oracle is appended to that list for units
whose gate declares one, so one call still runs everything and the existing
`ok_all` / report concatenation is unchanged. Read the key with a helper —
`read_gate_feature_oracle(gate_file)` — beside `read_gate_baseline`, which is
the established shape for reading a gate's frontmatter.

**Two failure modes that must not be silent.** A gate declaring
`feature_oracle:` with an empty or whitespace-only value, and a declaration the
runner cannot execute at all, are both CONFIGURATION ERRORs in the same shape as
an unknown `extra_gates` name — refused before any unit dispatches. A gate
declaring no key at all is not an error here; T03 owns that judgement.

**Acceptance criteria.**

- `tests/test_feature_oracle_e2e.py::test_declared_oracle_runs_during_unit_verification` fails on HEAD and passes after: a temp feature whose `GATE-01.md` declares an oracle has that command actually executed when a unit in that gate is verified, proven by a side effect the command itself produces (a file it writes), not by asserting on a mock.
- `::test_failing_oracle_fails_the_unit`: a red oracle makes `verify()` return False for a unit whose other gates are all green, and the report names the oracle.
- `::test_gate_without_oracle_is_unchanged`: a gate declaring no `feature_oracle` verifies byte-identically to HEAD's behaviour — absent-key behaviour is inert.
- `::test_empty_oracle_is_configuration_error`: an empty declaration returns the CONFIGURATION ERROR shape, naming the gate file, from `verify()`.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** The close path and `## Measurements` (T02); `lint_plan.py`
(T03); templates, skills and `methodology.md` (T04); `probe_baseline` — the
oracle is deliberately **not** part of the baseline probe, because it is
required to be red at gate entry and a probe that halts on it would make every
feature unstartable; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's own `feature_oracle` once it is green.

**Escalation triggers.** Emit `status: blocked` if appending the oracle to
`verify()`'s gate list cannot be done without changing `_run_gate_set`'s return
contract (`{"name", "ok", "report"}`), which `probe_baseline` and `verify` both
destructure. Also block if the end-to-end test cannot observe the oracle
actually running without mocking the runner — a test that asserts on a mock
would not prove the wiring, which is this unit's whole point.
</content>
