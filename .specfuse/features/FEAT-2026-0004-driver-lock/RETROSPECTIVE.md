---
feature: FEAT-2026-0004
gate: 1
unit: FEAT-2026-0004/T01
authored: 2026-06-07
---

# Gate 1 retrospective — Single-driver working-tree lock

## Summary

Gate 1 contained one implementation unit (T01) plus four closing units
(G1-RETRO through G1-PLAN). This document covers T01 only; the closing
units are post-implementation bookkeeping and are not analyzed here.

---

## T01: Prevent two loop drivers running concurrently in one working tree

### Attempt count

**1** (task_started 04:03:48 UTC → task_completed 04:08:51 UTC, ~5 min).
No retry was needed. All six acceptance criteria were met in a single session.

### Cost

$0.89 USD. 6,045 prompt tokens (own), 1,208,968 cache reads, 67,136 cache
creation, 17,452 output tokens.

### What worked

**1. Lock acquire-site ordering was unambiguous in practice.**
`run()` has a clear early phase: read args, load feature frontmatter (read-only
file I/O), then branch into dry-run vs. real. The first git-mutating calls are
`require_git_ready()` and `ensure_feature_branch()`, both guarded by
`if not dry_run:`. Placing the lock acquire at the top of that guard block —
before either call — satisfied AC1 exactly. No large refactor of `run()`'s early
ordering was needed; the function's structure was already compatible.

**2. The extracted `acquire_tree_lock()` helper was the right abstraction.**
Isolating the flock logic into a named helper (AC6 required it) meant the tests
need no subprocess dispatch and the acquire site in `run()` reads as a single
intent. The helper raises `BlockingIOError` directly, so the caller in `run()`
can catch and print the message in one place.

**3. `_lock_fd` lifetime handled correctly.**
Python local variables are kept alive for the function's execution frame. `_lock_fd`
assigned inside `run()` and never closed means the kernel auto-releases the flock
when `run()` returns (or the process exits, including SIGKILL). The solution
required no `atexit` hook, no try/finally, and no context manager — which is
exactly right for a "held for process lifetime" pattern.

**4. `init.sh` idempotency via `grep -qxF`.**
Using the `-x` (full-line) and `-F` (literal string) flags ensures the check
matches only the exact line `.specfuse/.loop.lock` and not a prefix or
superstring. Re-running `init.sh` in either INIT or UPGRADE mode against a repo
that already has the line leaves `.gitignore` untouched. The dry-run branch
reports clearly what would happen without writing.

**5. Tests proved both kernel-level cases.**
`test_second_acquire_raises_while_first_held` and
`test_second_acquire_succeeds_after_first_released` cover the two contract
properties (exclusion and release-on-close) without spawning processes.

**6. `--dry-run` exclusion handled cleanly and documented at the acquire site.**
The one-line comment at the acquire site (`# dry-run performs no mutation;
inspecting while a real run is active must stay allowed`) satisfies AC3's
documentation requirement and explains the exemption to future readers.

### What failed

Nothing failed. There was no second attempt, no blocked RESULT, and no
escalation trigger fired.

### Ambiguities and missing rules/templates

The unit went cleanly, but these points were underspecified and could have
caused failures on a less-informed attempt:

**1. Acquire site vs. pre-lock read operations in `run()`.**
The WU spec said "before any git-mutating call (`require_git_ready` /
`ensure_feature_branch`)." This is precise enough, but the spec does not describe
`run()`'s full early call graph. Between the top of `run()` and `require_git_ready()`
there are several non-mutating operations: argument parsing, feature-frontmatter
loading, `SPECFUSE_DIR` resolution. The spec did not need to enumerate them, but a
template for "lock before first mutation" could save analysis time by stating
explicitly: "non-mutating reads before the lock are permitted; the invariant is
that no `subprocess.run(git ...)` call precedes the acquire." No binding rule
covers this.

**2. Python fd-lifetime semantics for POSIX locks.**
No existing template, rule, or skill file describes the pattern of "assign an fd
to a local variable in a long-running function to keep the POSIX lock alive."
The WU spec was explicit ("caller keeps it alive for the process lifetime"), but
this could trip an agent that defaults to context managers or assigns to `_`
(which triggers GC). Worth adding to a lessons or template document.

**3. `init.sh` block placement relative to existing dry-run and upgrade guards.**
`init.sh`'s existing pattern is `if [[ $DRY_RUN -eq 0 ]]; then ... fi` guards
around each write section. The lock-file block breaks from that pattern: it wraps
its own internal dry-run fork so it can produce output in both modes. This is
correct but inconsistent with adjacent blocks. The spec said "both modes" without
calling out the structural inconsistency. A future agent editing `init.sh` could
normalize it the wrong way.

**4. `init.sh` placement applies to UPGRADE as well as INIT.**
The spec said "idempotent" and "re-run / upgrade mode" but did not explicitly say
where in the script the block should sit relative to the UPGRADE/INIT fork. The
agent correctly placed it after both mode-specific blocks (so it runs regardless
of mode). No rule codified this.

**5. No escalation trigger fired — but the ordering conflict was real.**
The WU spec listed an escalation trigger: "If `run()` cannot acquire the lock
before a git mutation without a larger refactor of its early-setup ordering, block
and name the ordering conflict." In practice the ordering was clean. But this
trigger reflects a genuine risk that materialized in the spec design phase: if
`require_git_ready()` had been called before the dry-run branch, the lock would
have needed to move earlier and the `dry_run` exemption would have been harder to
express. The current `run()` structure avoids that trap; a future refactor of
`run()`'s early phase should be aware of it.

### Generalizable observations

- The fd-lifetime pattern for POSIX advisory locks in Python is not covered by
  any rule or template and should be. (→ G1-LESSONS candidate)
- `grep -qxF` for idempotent single-line gitignore entries is worth codifying as
  the canonical `init.sh` idiom. (→ G1-LESSONS candidate)
- The WU spec's explicit escalation trigger ("if ordering requires a larger
  refactor, block") was load-bearing: it named the risk precisely enough that the
  agent could confirm it did not fire rather than quietly working around it.

---

## Feature-arc retrospective — FEAT-2026-0004

**Roadmap goal.** *"A second loop driver launched against the same working tree
exits cleanly instead of racing the first and corrupting state."*

**Verdict: met.** The feature is ready for closure.

### Evidence

1. **Lock enforced at the right site.** `loop.py`'s `run()` calls
   `acquire_tree_lock()` before `require_git_ready()` and
   `ensure_feature_branch()` — the first two git-mutating calls. A non-blocking
   `fcntl.flock(LOCK_EX | LOCK_NB)` on `.specfuse/.loop.lock` raises
   `BlockingIOError` on contention; the driver prints the contention message to
   stderr and exits non-zero without touching git or any WU/GATE file. The fd is
   held in a `run()`-local variable so the kernel auto-releases on process exit,
   including SIGKILL — no stale-lock cleanup path required.

2. **Contention test passes.** `tests/test_driver_lock.py` covers both contract
   properties without subprocess dispatch:
   `test_second_acquire_raises_while_first_held` (exclusion) and
   `test_second_acquire_succeeds_after_first_released` (release on fd close,
   simulating process exit).

3. **Lock file gitignored — both surfaces.** This repo's root `.gitignore` line
   29 contains `.specfuse/.loop.lock`. `init.sh` (lines 391+) idempotently
   appends the same line to every target repo's `.gitignore` via `grep -qxF
   "$line" "$file" || echo "$line" >> "$file"` — runs in both INIT and UPGRADE
   modes, no duplicates on re-run, no over-ignoring of the rest of `.specfuse/`.

4. **`--dry-run` exemption documented.** A one-line comment at the acquire site
   states that dry-run performs no mutation and inspecting a tree while a real
   run is active must stay allowed.

### Why no gate 2

Branch B was considered and rejected. The flock approach proved sufficient: the
two-test contract pass, the WU completed in a single attempt, and no escalation
trigger fired. The one bounded follow-up that could justify a gate 2 — a portable
fallback for non-POSIX hosts (Windows) — is out of scope for this feature: the
WU spec named that as a hard `status: blocked` trigger, not a same-feature
extension, and the loop's host requirements remain POSIX-only. If Windows
support is later required, it should be a fresh feature (pidfile + liveness
check has its own design trade-offs and reintroduces the stale-lock handling
this design deliberately avoids — categorically a new unit, not a gate
appendix).

### Closure

PLAN.md's `gates:` graph is unchanged. No `GATE-02.md` or `GATE-02-REVIEW.md`
was written. The feature is ready for closure on the merits of T01 alone — the
smallest viable form for a single-fix feature.
