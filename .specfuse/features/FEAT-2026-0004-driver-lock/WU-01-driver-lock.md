---
id: FEAT-2026-0004/T01
type: implementation
model: claude-sonnet-4-6
status: done
attempts: 1
cost_usd: 0.894365
input_tokens: 6045
output_tokens: 17452
---

# Prevent two loop drivers running concurrently in one working tree

**Objective.** Make `loop.py` acquire an exclusive, auto-released advisory lock
on the working tree before it mutates any git state, so a second driver launched
against the same checkout exits immediately with a clear message instead of
racing the first. Ensure the lock file is never committed — in this repo and in
every repo `init.sh` sets up.

**Context.** This is `FEAT-2026-0004/T01`. The driver's per-WU
`git reset --hard` / soft-reset and `git checkout -B <branch>` are **tree-global**
operations: two drivers sharing one working tree clobber each other regardless of
whether they target the same feature. The unit to protect is the **working
tree**, not the feature. Observed failure (FEAT-2026-0003 build): a second driver,
launched because a sandboxed `ps` falsely reported the first as dead, interleaved
its resets with the first's and produced commits mixing multiple WUs' work plus
contradictory WU statuses. True parallelism across features uses separate
`git worktrees` (each its own tree → its own lock), never two drivers in one tree.
Full design: [`docs/wu-draft-loop-concurrency-lock.md`](../../../docs/wu-draft-loop-concurrency-lock.md).
Reference the binding rules under `.specfuse/rules/`; honor `result-contract.md`,
`never-touch.md`. The driver owns all git — edit files only.

**Acceptance criteria.**
1. `loop.py`'s `run()` acquires a **non-blocking exclusive** advisory lock via
   `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on a lock file at `.specfuse/.loop.lock`,
   **before** the first git-mutating call (`require_git_ready` /
   `ensure_feature_branch`). The fd is held open for the driver's lifetime so the
   kernel **auto-releases on process exit, including SIGKILL** (no stale-lock
   cleanup path). The lock is working-tree scoped — one lock file per checkout,
   independent of `--feature`.
2. On contention (`flock` raises `BlockingIOError`), the driver prints a single
   clear line to stderr — e.g. `another loop driver is already running in this
   working tree (.specfuse/.loop.lock held)` — and exits non-zero **without
   touching git or any WU/GATE file**.
3. `--dry-run` does **not** acquire the lock (it performs no mutation; inspecting
   a tree while a real run is active must stay allowed). State this in a one-line
   comment at the acquire site.
4. `init.sh` ensures the **destination** repo ignores the lock file: it adds the
   exact line `.specfuse/.loop.lock` to the target repo's `.gitignore` (creating
   the file if absent), **idempotently** (no duplicate line on re-run / upgrade
   mode), and **without** ignoring the rest of `.specfuse/` (preserve the
   existing gitignore-guard warning). A targeted ignore of just the lock file.
5. This repo's own root `.gitignore` gains the line `.specfuse/.loop.lock`.
6. Tests in `tests/` cover, via a small extracted helper (e.g.
   `acquire_tree_lock(specfuse_dir)`) so no real `claude -p` dispatch is needed:
   (a) a second acquire raises/exits while the lock is held by an open fd; and
   (b) a second acquire succeeds once the first fd is closed (simulating process
   exit).

**Do not touch.** The `Backend` seam / `make_backend`, the verification gate
semantics, `lint_plan.py`, `gh_features.py`, `adopt_feature.py`, `gh_backend.py`,
any binding rule under `.specfuse/rules/`, any skill, generated dirs, secrets,
`.git/`. The driver owns git — edit files only. Files this WU changes:
`.specfuse/scripts/loop.py`, `init.sh`, this repo's root `.gitignore`, and one
new/extended test file under `tests/`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests,
ruff, bandit, coverage ≥ floor). Run them in order. `fcntl`/`flock` is stdlib —
no new dependency.

**Escalation triggers.** `fcntl.flock` is POSIX-only — if Windows support is a
hard requirement, stop and emit `status: blocked`: a portable fallback (pidfile +
liveness check) reintroduces the stale-lock handling this design deliberately
avoids and is a separate WU. If `run()` cannot acquire the lock before a git
mutation without a larger refactor of its early-setup ordering, block and name
the ordering conflict rather than relocating git mutations silently.
</content>
