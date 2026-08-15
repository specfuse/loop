---
id: FEAT-2026-0049/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces:
  - specfuse/agent/budget.py
  - tests/test_agent_budget.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.11.0
started_at: 2026-08-11T00:52:14.481601+00:00
duration_seconds: 719.973
cost_usd: 1.277438
input_tokens: 58
output_tokens: 12814
---

# T03 — caps and the kill switch

**Context.** The operator's control over what an unattended agent costs is
entirely this unit. Three caps bound a run — `--max-minutes`, `--max-tokens`,
`--max-items` — and a PAUSE marker stops it between iterations.

**The decisive semantic, settled at draft time (PLAN.md D3): a cap is checked
only at item boundaries, and a running item is never interrupted.** A cap can
therefore overshoot, and that is accepted. The alternative — killing a driver
subprocess mid-work-unit — manufactures partially-flipped state on disk (WU
frontmatter and `events.jsonl` written, no commit), whose cheapest known recovery
is discarding the work wholesale. Do not add a mid-item abort path, a timeout
that kills a subprocess, or a signal handler that interrupts one. If the
implementation seems to need one, that is an escalation, not a design choice.

Because overshoot is real, it must be *stated* rather than hidden: `--max-minutes`
is documented in its own flag help as "do not start new work after N minutes,"
and the run summary reports actual elapsed time, not the cap.

The PAUSE marker is a file whose presence stops the loop. Check it each
iteration, before selecting the next item. Do not check it mid-item either — same
reasoning.

**Acceptance criteria.**

1. `tests/test_agent_budget.py::TestRunBudget::test_cap_is_not_checked_mid_item`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_budget.TestRunBudget.test_cap_is_not_checked_mid_item`.
2. `specfuse/agent/budget.py` exposes a `RunBudget` carrying the three caps and a
   single predicate answering "may another item start?", plus a PAUSE-marker
   check. Time is injected (a clock callable), never read from `time` directly,
   so the tests are deterministic.
3. The same test passes after this WU's edits.
4. Each of the three caps independently stops the run: three tests, one per cap,
   each asserting the *next* item does not start and the item in flight was not
   disturbed.
5. Absent caps mean unbounded: a `RunBudget` with none set never stops the run.
   `--max-items 0` is distinguishable from "unset" and stops immediately — a test
   asserts the two are not conflated.
6. The PAUSE marker stops the loop at the next boundary and the run summary names
   the marker as the stop reason, distinguishing it from a drained queue and from
   a cap.
7. Every stop path yields a distinct, machine-readable stop reason. A run that
   ends must always say which of drained / cap / pause / error ended it.

**Do not touch.** `specfuse/loop/` entirely. `specfuse/monitor/`.
`specfuse/agent/state.py` (T02's). `specfuse/agent/run.py` and `pyproject.toml`
(T04's) — this unit ships the budget object and its tests, and T04 wires it.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus the
§9 symbol check:
`python3 -c "from specfuse.agent.budget import RunBudget; print(RunBudget)"`.

**Escalation triggers.** If honouring a cap appears to require interrupting an
item in flight — for example because token spend is only observable after a
subprocess exits, making `--max-tokens` unenforceable at boundaries alone — stop
and report the specific cap and the specific observability gap. Do **not** resolve
it by adding a mid-item abort; that is the decision D3 already took, and
reversing it is the operator's call, not the session's. If the PAUSE marker's
location is not already established by an existing convention in this repo, name
the two or three candidate paths and stop rather than choosing one silently.
