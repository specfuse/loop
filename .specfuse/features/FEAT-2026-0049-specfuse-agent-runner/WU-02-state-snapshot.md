---
id: FEAT-2026-0049/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 5.00
produces:
  - specfuse/agent/__init__.py
  - specfuse/agent/state.py
  - tests/test_agent_state.py
---

# T02 — the repo-state snapshot, and the first reader of `queue:`

**Context.** The agent has no database, by design: every fact it acts on is
either derivable from GitHub, the roadmap, the policy file, and feature folders,
or is safely losable. This unit builds the one function that gathers those facts
into a single snapshot, so the selector reads a value rather than issuing calls
mid-decision.

The notable piece: **this is the first code anywhere that reads `queue:`.**
`agent_policy.py:225` validates the list against the roadmap and stops there;
`/groom-backlog` writes it and nothing has ever consumed it. Verify that claim
before building — `grep -rn 'get("queue")\|\["queue"\]' --include="*.py" specfuse/`
— and if a reader has landed since this was drafted, extend it rather than adding
a second one.

Everything else composes existing readers. Do not reimplement policy parsing
(`agent_policy.load_policy`), issue listing (the `runner` pattern in
`specfuse/loop/triage.py` and `specfuse/monitor/issues.py`), or feature-folder
walking (`lint_plan` and `arm_sweep` both already do it — read them and reuse
whichever fits, per §10's helper-duplication pre-flight).

Follow the injection seam every comparable module already uses: a `runner(argv,
check=...)` callable parameter, never a direct `subprocess` call. That is what
makes this testable without a network and what `bug_lane_run`, `issues`, and
`autofix_state` all do.

**Acceptance criteria.**

1. `tests/test_agent_state.py::TestSnapshot::test_queue_read_from_policy` exists
   and **fails on HEAD before this WU runs** (the file does not yet exist). Run
   scoped: `python3 -m unittest tests.test_agent_state.TestSnapshot.test_queue_read_from_policy`.
2. `specfuse/agent/state.py` exposes one public function returning an immutable
   snapshot carrying, at minimum: the ordered `queue:` list, the resolved policy
   dials the selector needs, open issues with their labels and triage markers,
   open PRs, and the feature folders with their PLAN status and current gate
   status. Every GitHub read goes through an injected `runner`.
3. The same test passes after this WU's edits.
4. A repository with no `.specfuse/agent-policy.yml` yields a snapshot with an
   empty queue and default dials — not an exception. The agent must be able to
   report "nothing to do" in a repo that never configured a policy.
5. A `runner` that fails or returns unparseable output yields a snapshot with
   that section empty and a recorded reason, never a partial object that reads as
   authoritative. Asserted with a failing-runner test.
6. The snapshot performs **no writes**: no issue comment, no label, no file. A
   test asserts the injected runner received no mutating `gh` subcommand.

**Do not touch.** `specfuse/loop/` entirely — including `agent_policy.py`, which
is consumed as-is; if it lacks a reader this unit needs, add the reader in
`specfuse/agent/state.py`, not there. `specfuse/monitor/`. `pyproject.toml`
(T04 owns the entry point). The `.specfuse/agent-policy.yml` file itself.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus the
§9 symbol check:
`python3 -c "import specfuse.agent.state as s; print(s)"`.

**Escalation triggers.** If a `queue:` reader already exists somewhere the
pre-flight grep finds, stop and name it rather than adding a second — a duplicate
reader is exactly the §10 failure this check exists to prevent. If gathering the
feature-folder half requires importing from `specfuse/loop/`, report which symbol
and why before doing it: an import is acceptable, but it creates a coupling the
plan should know about, and a *copy* is not acceptable.
