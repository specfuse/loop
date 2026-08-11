---
id: FEAT-2026-0049/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.50
produces:
  - specfuse/agent/run.py
  - tests/test_agent_run.py
---

# T04 — the conductor loop and the `specfuse-agent` entry point

**Context.** This unit assembles T01's lock, T02's snapshot, and T03's budget
into the loop the feature exists for — select, execute, reconcile, repeat — and
exposes it as `specfuse-agent run`.

**It registers no action providers.** That is deliberate and is gate 1's whole
shape: the loop's stopping properties are what is most expensive to get wrong and
cheapest to prove before any provider can spend money on the other side of them.
This unit defines the *protocol* a provider satisfies — how one advertises
available work, how one executes an item, how one reports an outcome — and runs
the loop against an empty registry, which must drain cleanly and immediately.
Gate 2 supplies the four real providers.

Resist implementing "just one small provider to prove it works." A test double
implementing the protocol proves it works; a real provider imports a whole action
class into a gate that has not planned for it.

Selection order comes from policy, not from judgment: `rules.bugs.preempt` means
bugs outrank features, and the `queue:` order settles features among themselves.
Where policy does not decide, the loop must escalate rather than guess — that is
the "priority is policy, not intelligence" principle the whole agent design rests
on.

**Acceptance criteria.**

1. `tests/test_agent_run.py::TestDrainEmpty::test_drains_cleanly_with_no_providers`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_run.TestDrainEmpty.test_drains_cleanly_with_no_providers`.
2. `specfuse/agent/run.py` exposes the loop entry point and the action-provider
   protocol. The loop acquires the agent lock via T01, builds one snapshot via
   T02, and consults T03's budget before every item.
3. The same test passes after this WU's edits.
4. `pyproject.toml` gains `specfuse-agent = "specfuse.agent.run:main"` under
   `[project.scripts]`, alongside the four existing entry points.
5. A second concurrently-running agent refuses to start, naming the lock holder's
   path — not a traceback. Asserted by acquiring the lock in the test and then
   invoking `main`.
6. The run summary names: items attempted, items completed, the stop reason from
   T03's closed set, and **actual elapsed time** rather than the cap.
7. With one or more test-double providers registered, the loop selects, executes
   and reconciles in policy order, and a provider raising an exception parks that
   item with an escalation instead of ending the run. The double lives in the
   test file; no production provider ships in this gate.
8. The loop performs no git mutation of its own. It invokes; it does not commit,
   branch, or merge. A test asserts the injected runner received no such command.

**Do not touch.** `specfuse/loop/` entirely — in particular do **not** import
`loop.run` and call it; the driver is a subprocess in this design (PLAN.md D1,
and the live hazards #757 and #1040), and gate 3 is where that invocation
actually lands. `specfuse/monitor/`. T01's `_filelock.py`, T02's `state.py`, and
T03's `budget.py` — consume them, do not edit them. If one is wrong, escalate
rather than patch.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol and entry-point checks:
`python3 -c "from specfuse.agent.run import main; print(main)"` and, after an
editable install, `specfuse-agent --help` exits 0.

**Escalation triggers.** If the provider protocol cannot be defined without
knowing a concrete provider's shape — that is, if designing it in the abstract
produces something gate 2 would clearly have to redesign — stop and say so with
the specific unknown named. That is a real risk of building the protocol before
its first consumer, and reporting it is more useful than guessing a shape that
gets thrown away. If wiring the console script requires changing packaging
metadata beyond adding the one `[project.scripts]` line, name the change and stop.
