---
id: FEAT-2026-0203/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - specfuse/monitor/durations.py
  - specfuse/monitor/providers/azure_service_bus.py
  - specfuse/loop/lint_monitoring.py
  - tests/test_monitor_durations.py
  - tests/test_lint_monitoring.py
  - docs/concepts/monitoring-schema.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.27.1
started_at: 2026-10-15T02:55:47.841950+00:00
duration_seconds: 126.578
cost_usd: 0.250054
input_tokens: 18
output_tokens: 5869
---

# T02 — one duration grammar; a malformed stall_after is a lint error (#295)

**Objective.** The `<integer><unit>` duration grammar has one home that both the
adapter and the linter import, and `specfuse-monitor-lint` rejects a `stall_after`
the harvester would refuse at runtime.

**Context.** `FEAT-2026-0203/T02`, gate 1; discharges #295, folded into this feature
by operator decision (2026-10-14). Today the grammar lives only in
`parse_stall_after_seconds` (`specfuse/monitor/providers/azure_service_bus.py:149`,
units `s`/`m`/`h`/`d`), so a typo'd threshold passes lint and is refused on the
harvester's first poll. Move it to `specfuse/monitor/durations.py` (`parse_duration_seconds`),
have the adapter call it, and keep `parse_stall_after_seconds` as a thin alias so its
existing callers and tests are untouched. The module must import nothing from the
Azure SDK: `specfuse.loop` already imports from `specfuse.monitor`
(`bug_lane_run.py`, `labels.py`), and the linter must stay SDK-free.

This **flips a severity** (`planning-discipline.md` §2, §4). PLAN.md answers the
satisfiability question: every shipped `stall_after` is `15m`. `GATE-01.md`'s arming
discipline requires the runtime probe before this unit is armed. The flip reverses a
documented and tested position: `test_queue_stalled_threshold_coordinate_is_opaque`
(`tests/test_lint_monitoring.py:738`) and the sentence in
`docs/concepts/monitoring-schema.md` saying the stall threshold is "accepted but
never parsed or bounded here". Both change in this unit, deliberately.

**Acceptance criteria.**

1. `tests/test_lint_monitoring.py::TestQueueStalled::test_malformed_stall_after_is_a_lint_error`
   fails on HEAD and passes after: `stall_after: 15min` and `stall_after: 10 minutes`
   each produce an error naming the component, the target and the expected grammar;
   `15m`, `90s`, `2h` and `1d` produce none. It replaces
   `test_queue_stalled_threshold_coordinate_is_opaque`, with a comment citing #295 and
   FEAT-2026-0203.
2. `tests/test_monitor_durations.py` asserts `parse_duration_seconds` and
   `parse_stall_after_seconds` agree on every accepted and rejected case in the
   adapter's existing tests, and `grep -cE "re\.compile" specfuse/monitor/providers/azure_service_bus.py`
   no longer counts a duration pattern there (one grammar, one home).
3. Migration check: every `stall_after` in `.specfuse/monitoring.yml.example`,
   `specfuse/loop/data/monitoring.yml.example` and the fenced YAML blocks
   `tests/test_monitoring_fenced_blocks.py` collects passes the new rule —
   `python3 -m unittest tests.test_monitoring_example tests.test_monitoring_fenced_blocks -b` exits 0.
4. `docs/concepts/monitoring-schema.md` states the grammar for `stall_after` and no
   longer says the value is never parsed.

**Do not touch.** The `queue-stalled` adapter's runtime behaviour (same accepted set,
same refusal). Other check types' lint rules. T01's and T03's lint additions for
`http-status-regression` — this unit adds no rule for `window_after_deploy`; T03
uses the grammar this unit ships.

**Verification.** The narrow tier for `implementation`, plus
`python3 -m unittest tests.test_queue_stalled_adapter tests.test_lint_monitoring -b`
and `python3 -c "from specfuse.monitor.durations import parse_duration_seconds"`.

**Escalation triggers.** If any shipped monitoring YAML carries a `stall_after` the
grammar rejects, stop before flipping: PLAN.md's satisfiability answer is wrong and
the migration is not a check after all. If importing `specfuse.monitor.durations`
from the linter pulls in an Azure SDK module, stop and escalate.
