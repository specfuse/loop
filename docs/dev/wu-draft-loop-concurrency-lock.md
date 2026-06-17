# WU draft — single-driver working-tree lock

**Status: draft spec, not yet wired into a feature graph.** See "Container" at
the bottom. Written after the FEAT-2026-0003 dogfood, where two concurrent
`loop.py` drivers in one working tree corrupted gate-1 state (competing
`git reset --hard` cycles squashed mixed work into mislabeled commits). The
fix prevents a second driver from running in the same working tree at all.

---

```
type: implementation
model: claude-sonnet-4-6
```

# Prevent two loop drivers running concurrently in one working tree

**Objective.** Make `loop.py` acquire an exclusive, auto-released advisory lock
on the working tree before it mutates any git state, so a second driver
launched against the same checkout exits immediately with a clear message
instead of racing the first. Ensure the lock file is never committed — in this
repo and in every repo `init.sh` sets up.

**Context.** The driver's per-WU `git reset --hard` / soft-reset and
`git checkout -B <branch>` are **tree-global** operations: two drivers sharing
one working tree clobber each other regardless of whether they target the same
feature. The unit to protect is therefore the **working tree**, not the
feature. Observed failure (FEAT-2026-0003 build): a second driver, launched
because a sandboxed `ps` falsely reported the first as dead, interleaved its
resets with the first's and produced commits mixing multiple WUs' work plus
contradictory WU statuses. True parallelism across features is achieved with
separate `git worktrees` (each its own tree → its own lock), not two drivers in
one tree. Reference the binding rules under `.specfuse/rules/`; honor
`result-contract.md`, `never-touch.md`.

**Acceptance criteria.**
1. `loop.py`'s `run()` acquires a **non-blocking exclusive** advisory lock via
   `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on a lock file at `.specfuse/.loop.lock`,
   **before** the first git-mutating call (`require_git_ready` /
   `ensure_feature_branch`). The fd is held open for the driver's lifetime so the
   kernel **auto-releases on process exit, including SIGKILL** (no stale-lock
   cleanup path). The lock is repo/working-tree scoped — one lock file per
   checkout, independent of `--feature`.
2. On contention (`flock` raises `BlockingIOError`), the driver prints a single
   clear line to stderr — e.g. `another loop driver is already running in this
   working tree (.specfuse/.loop.lock held)` — and exits non-zero **without
   touching git or any WU/GATE file**.
3. `--dry-run` does **not** acquire the lock (it performs no mutation; inspecting
   a tree while a real run is active must stay allowed). Document this choice in
   a one-line comment.
4. `init.sh` ensures the **destination** repo ignores the lock file: it adds the
   exact line `.specfuse/.loop.lock` to the target repo's `.gitignore`
   (creating the file if absent), **idempotently** (no duplicate line on
   re-run / upgrade mode), and **without** ignoring the rest of `.specfuse/`
   (which the loop needs tracked — preserve the existing gitignore-guard
   warning). A targeted ignore of just the lock file, not `.specfuse/`.
5. This repo's own root `.gitignore` gains the line `.specfuse/.loop.lock` (the
   loop runs on itself; the lock must not be committed here either).
6. Tests in `tests/` cover: (a) `run()` (or a small extracted
   `acquire_tree_lock()` helper) raises/exits when the lock is already held by
   another fd, and (b) the lock is released — a second acquire succeeds — once
   the first fd is closed (simulating process exit). No real `claude -p`
   dispatch; test the lock helper directly with a stub feature dir.

**Do not touch.** The `Backend` seam, `make_backend`, the verification gate
semantics, `lint_plan.py`, `gh_features.py`, `adopt_feature.py`, `gh_backend.py`,
binding rules, secrets, `.git/`. The driver owns git — edit files only. Files
this WU changes: `.specfuse/scripts/loop.py`, `init.sh`, this repo's root
`.gitignore`, and one new/extended test file.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
ruff, bandit, coverage ≥ floor). Run them in order. Manually confirm: start one
`loop.py` run, launch a second against the same tree, observe the second exits
non-zero with the contention message and leaves no git/WU changes.

**Escalation triggers.** `fcntl.flock` is POSIX-only — if Windows support is a
hard requirement, stop and emit `status: blocked`: a portable fallback
(pidfile + liveness check) reintroduces the stale-lock handling this design
deliberately avoids and is a different WU. If `run()` cannot acquire the lock
before a git mutation without a larger refactor of its early setup ordering,
block and name the ordering conflict rather than moving git mutations around
silently.

---

## Container (placement recommendation)

Strictly, this is **not a hygiene WU** in the methodology sense — a hygiene WU
(`T<NN>H`) is a narrow precursor to a *blocked* substantive WU on a pre-existing
bug in a forbidden path, with an `events.jsonl` escalation it quotes. This has
no blocked target; it is a new improvement.

The methodology-honest home is a small new feature — **`FEAT-2026-0004`
("single-driver working-tree lock")**, single gate, this as `T01` — so it runs
through the gate cycle (verify-as-oracle + squashed commit + closing sequence)
like any other change. Alternatively fold it into the planned `FEAT-2026-0002`
(driver run-loop test coverage / driver hardening) as an added gate.

If you want it run through the loop, say so and I'll scaffold `FEAT-2026-0004`
around this WU (PLAN + GATE-01 + this as `WU-01` + the closing sequence).
</content>
