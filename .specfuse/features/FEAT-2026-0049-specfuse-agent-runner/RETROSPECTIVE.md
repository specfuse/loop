## Gate 1 — auto-closed (predicate=v1)

On-plan intermediate close; full close-intermediate ceremony
skipped per `evaluate_auto_close`. `plan-next` WU dispatched
to draft gate 2.

- feature_id: FEAT-2026-0049
- predicate_version: v1
- gate_total_cost: $5.95
- gate_budget: $36.00
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

This gate auto-closed on-plan; the full close-intermediate ceremony did
not run, so the per-criterion deferred-verification list was **not**
enumerated. Any acceptance criterion whose verification is deferred
(loop-sandbox limit, cross-repo coordination, real-system access) is
unrecorded here. Gate 2's close MUST reconcile these
before the feature's terminal verdict — auto-close cannot enumerate them.

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03,T04 criteria=27 predicate=v1 -->

- **FEAT-2026-0049/T01** (`WU-01-agent-lock.md`)
  - deferred: `tests/test_agent_lock.py::TestAgentLock::test_second_acquire_raises` exists
  - deferred: `specfuse/loop/_filelock.py` gains a filename parameter on `acquire_tree_lock`
  - deferred: The same test passes after this WU's edits.
  - deferred: A second `acquire_agent_lock` against the same directory raises
  - deferred: The agent lock and the driver lock are independent: holding
  - deferred: `.specfuse/.agent.lock` is gitignored, alongside the existing `.loop.lock`
- **FEAT-2026-0049/T02** (`WU-02-state-snapshot.md`)
  - deferred: `tests/test_agent_state.py::TestSnapshot::test_queue_read_from_policy` exists
  - deferred: `specfuse/agent/state.py` exposes one public function returning an immutable
  - deferred: The same test passes after this WU's edits.
  - deferred: A repository with no `.specfuse/agent-policy.yml` yields a snapshot with an
  - deferred: A `runner` that fails or returns unparseable output yields a snapshot with
  - deferred: The snapshot performs **no writes**: no issue comment, no label, no file. A
- **FEAT-2026-0049/T03** (`WU-03-budget-and-pause.md`)
  - deferred: `tests/test_agent_budget.py::TestRunBudget::test_cap_is_not_checked_mid_item`
  - deferred: `specfuse/agent/budget.py` exposes a `RunBudget` carrying the three caps and a
  - deferred: The same test passes after this WU's edits.
  - deferred: Each of the three caps independently stops the run: three tests, one per cap,
  - deferred: Absent caps mean unbounded: a `RunBudget` with none set never stops the run.
  - deferred: The PAUSE marker stops the loop at the next boundary and the run summary names
  - deferred: Every stop path yields a distinct, machine-readable stop reason. A run that
- **FEAT-2026-0049/T04** (`WU-04-conductor-loop.md`)
  - deferred: `tests/test_agent_run.py::TestDrainEmpty::test_drains_cleanly_with_no_providers`
  - deferred: `specfuse/agent/run.py` exposes the loop entry point and the action-provider
  - deferred: The same test passes after this WU's edits.
  - deferred: `pyproject.toml` gains `specfuse-agent = "specfuse.agent.run:main"` under
  - deferred: A second concurrently-running agent refuses to start, naming the lock holder's
  - deferred: The run summary names: items attempted, items completed, the stop reason from
  - deferred: With one or more test-double providers registered, the loop selects, executes
  - deferred: The loop performs no git mutation of its own. It invokes; it does not commit,
