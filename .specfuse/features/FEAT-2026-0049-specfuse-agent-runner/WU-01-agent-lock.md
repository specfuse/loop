---
id: FEAT-2026-0049/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - specfuse/loop/_filelock.py
  - tests/test_agent_lock.py
produces_driver_helper:
  - acquire_agent_lock
---

# T01 — the agent's own lock

**Context.** The runner must guarantee "exactly one agent per repo." The obvious
move — take the lock the driver already uses — is wrong: `loop.run()` acquires
`.specfuse/.loop.lock` itself at `loop.py:6102` on every non-dry-run, so an agent
holding it would break every driver invocation it makes with `BlockingIOError`.
The agent needs a second lock file with the same mechanics.

`specfuse/loop/_filelock.py::acquire_tree_lock` already has those mechanics —
`fcntl.flock` on POSIX, `msvcrt.locking` on Windows, non-blocking, exclusive —
but hardcodes the filename `.loop.lock`. This unit adds a filename parameter and
a thin `acquire_agent_lock` wrapper.

**Do not build stale-lock detection or a PID file.** The roadmap goal asked for
both; `_filelock`'s own docstring is why they are not built here: "the OS
auto-releases on fd/handle close or process death (SIGKILL included), so no
stale-lock cleanup is ever needed," and it states the property "rules out
pidfiles." A stale lock cannot occur, so detecting one is inventing work.

Carry `[FEAT-2026-0004/G1-LESSONS]` forward: the returned file object must be
bound to a named local in the *caller's* frame for the process lifetime. Do NOT
wrap the acquire in `with` (closes the fd on `__exit__`, silently releasing the
lock) and do NOT assign it to `_` (may be collected). No `atexit`, no
`try/finally` — the kernel is the release mechanism.

**Acceptance criteria.**

1. `tests/test_agent_lock.py::TestAgentLock::test_second_acquire_raises` exists
   and **fails on HEAD before this WU runs** — the file does not yet exist, which
   counts as red. Run it scoped:
   `python3 -m unittest tests.test_agent_lock.TestAgentLock.test_second_acquire_raises`.
2. `specfuse/loop/_filelock.py` gains a filename parameter on `acquire_tree_lock`
   defaulting to the current `.loop.lock`, plus `acquire_agent_lock(specfuse_dir)`
   returning the held file object for `.specfuse/.agent.lock`. The existing
   zero-argument-beyond-`specfuse_dir` call at `loop.py:6102` keeps working
   unchanged — verified by running the existing lock tests, not by inspection.
3. The same test passes after this WU's edits.
4. A second `acquire_agent_lock` against the same directory raises
   `BlockingIOError` while the first is held, and succeeds after the first
   holder's file object is closed.
5. The agent lock and the driver lock are independent: holding
   `.specfuse/.agent.lock` does not prevent `acquire_tree_lock` from taking
   `.loop.lock`, asserted directly in a test rather than argued in prose.
6. `.specfuse/.agent.lock` is gitignored, alongside the existing `.loop.lock`
   entry.

**Do not touch.** `specfuse/loop/loop.py` — the call site at 6102 must keep
working through the parameter default, not through an edit. Every other module
under `specfuse/loop/`. Anything under `specfuse/agent/` (T02–T04 own it) or
`specfuse/monitor/`.

**Verification.** The repo's `code` gate set from `.specfuse/verification.yml`:
`python3 -m unittest discover -s tests -v -b`, `ruff check specfuse .specfuse/scripts tests scripts`,
`bandit -r specfuse .specfuse/scripts -ll`, and the coverage gate at its 90 floor.
Plus the symbol-existence check §9 requires:
`python3 -c "from specfuse.loop._filelock import acquire_agent_lock; print(acquire_agent_lock)"`.

**Escalation triggers.** If adding the filename parameter cannot preserve
`loop.py:6102`'s existing call without editing that call site — for example
because the parameter cannot be given a default that reproduces today's
behaviour — stop and name the ordering conflict rather than refactoring the
driver's early-setup sequence. If Windows' `msvcrt.locking` path turns out to
need a different filename-handling shape than the POSIX path, stop and report
both, rather than making the two platforms diverge silently.

**Note on the driver restart.** This WU's squash touches `specfuse/loop/`, which
matches `driver_edit.DRIVER_MODULE_PREFIXES`, so the driver will halt for a
restart afterwards. That is expected and is not a failure of this unit.
