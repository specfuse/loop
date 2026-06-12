---
id: FEAT-2026-0013/T01
type: implementation
model: claude-sonnet-4-6
effort: high
status: done
attempts: 1
# Cost preserved from v1 (2026-06-12, shipped methodologically but CI race
# recurred on Linux → re-armed; see PLAN.md ## Prior attempts).
historical_cost_usd: 0.326895
historical_duration_seconds: 362.795
historical_input_tokens: 13
historical_output_tokens: 3707
duration_seconds: 266.463
cost_usd: 0.205443
input_tokens: 12
output_tokens: 2535
---

# Audit and fix fd/handle leaks in integration_workspace

**Objective.** Identify every git subprocess handle, file descriptor,
and lock fd that may not be released before
`tempfile.TemporaryDirectory()` exits in `integration_workspace`, and
add explicit close / sync / completion-wait at exit points so
Python 3.12's `shutil.rmtree` no longer races against in-flight handles
on `.git/objects`.

**Context.** This is `FEAT-2026-0013/T01`. The race fires intermittently
on Python 3.12 CI runners with `OSError: [Errno 39] Directory not
empty: '/tmp/.../.git/objects'`. Three confirmed occurrences:

1. 2026-06-10 push, `test_no_files_changed_in_result_block_runs_squash_as_today`
   — root cause was an unclosed `.specfuse/.loop.lock` fd; partial fix in
   commit `7abc809` (try/finally close in `loop.py::run()`).
2. 2026-06-11 PR #7 first run, `test_cumulative_duration_written_to_frontmatter`
   — same OSError, prior fix doesn't touch this test. Subsequent
   re-run of same commit passed — confirms timing-dependence.
3. 2026-06-11 push CI (run `27391633691`) on this session's
   FEAT-2026-0014 branch: `test_agent_creates_new_file_and_declares_it_completes`
   ERROR on TemporaryDirectory cleanup. Reproduced live this session.

Suspect surfaces (each WU author MUST audit):

- `tests/test_driver_integration.py::integration_workspace` body —
  every `subprocess.run(["git", ...])` is a potential leak point if
  git spawns background subtasks (gc, fsck, index lock writes).
- Tests calling `with integration_workspace() as root:` that themselves
  invoke `loop.py` as a subprocess — those subprocesses may open
  `.specfuse/.loop.lock` or `.git/index.lock` and hold them past the
  `with` block's exit.
- Git's `gc.autoDetach` (default true since git 2.0) means `git
  commit` / `git gc --auto` background-detaches a gc subprocess that
  outlives the parent and may still be writing to `.git/objects` when
  `TemporaryDirectory.cleanup()` fires.

Reference the binding rules under `.specfuse/rules/`. Edit files
only; the driver owns all git.

**v1 → v2 amendment (2026-06-12).** v1 (gc.auto=0 + git rev-parse
sync barrier) passed 50× on macOS local but the SAME race fired on
Linux CI runner (run `27412918877`). Oracle was wrong-environment.
v2 keeps v1's root-cause attack AND adds belt-and-suspenders
`ignore_cleanup_errors=True` to suppress the symptom if the
root-cause fix still misses a Linux-only surface. v2's oracle is
CI itself — local audit alone is insufficient evidence.

**Acceptance criteria.**
1. Every `subprocess.run` call inside `integration_workspace()`
   (`tests/test_driver_integration.py`) declares `check=True` and
   captures completion. No fire-and-forget subprocess invocations.
2. `integration_workspace()` disables git background gc for the
   fixture's temp repo by passing `-c gc.auto=0` to every `git`
   invocation inside the context manager body (or equivalent
   project-wide via `git -C <root> config gc.auto 0` after `git
   init`). Rationale: gc.autoDetach is git's #1 documented source
   of post-parent-exit fs writes; eliminating it removes the most
   likely leak shape from the suspect list.
3. Before `TemporaryDirectory`'s context exits — i.e. inside
   `integration_workspace`'s body, after the `yield root` line, in
   a `finally:` block — run a synchronization barrier:
   `subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
   check=True, capture_output=True)`. This is a cheap git command
   that forces the index lock to flush and any pending writers to
   release before teardown.
4. **NEW v2.** `integration_workspace()` constructs its
   `tempfile.TemporaryDirectory` with `ignore_cleanup_errors=True`
   (Python 3.10+). Rationale: Linux-CI race recurrence in
   FEAT-2026-0013 v1 proved AC2-3 alone insufficient. This is
   harm-reduction — root-cause attack stays primary; suppression
   is the safety net for Linux-only surfaces not addressed by
   gc + sync barrier.
5. The 50× audit runs locally with zero failures:
   `for i in $(seq 1 50); do .venv/bin/python3 -m unittest
   tests.test_driver_integration -q 2>&1 | tail -1; done | sort -u`
   prints only `OK` lines. Quote the resulting summary verbatim
   in the RESULT block. (Local-only oracle; insufficient on its
   own — see AC6.)
6. **NEW v2: CI-environment oracle.** A sanity-check that the v2
   spec actually addresses Linux-CI: the agent does NOT run CI
   itself (CI runs at push time, post-squash). Instead the agent
   verifies the produced code path by running:
   `.venv/bin/python3 -c "import tempfile; import inspect; src = inspect.getsource(__import__('tests.test_driver_integration', fromlist=['integration_workspace']).integration_workspace); assert 'ignore_cleanup_errors=True' in src, 'belt-and-suspenders missing'; assert 'gc.auto' in src, 'gc.auto=0 not set'; print('v2 surfaces present')"`
   — must exit `0` AND print `v2 surfaces present`. If not, emit
   `status: blocked`. The CI run on the post-squash push is the
   FINAL oracle; that result is the operator's call at /wrap-feature
   step 7, NOT this WU's responsibility.
7. `integration_workspace` is still a `@contextmanager` (per
   `from contextlib import contextmanager` import) and still yields
   a `pathlib.Path`. No API break. Any test that uses
   `with integration_workspace() as root:` continues to receive a
   `Path` named `root`.
8. **Existence check** before declaring complete:
   `.venv/bin/python3 -c "import inspect; from tests.test_driver_integration import integration_workspace; assert callable(integration_workspace)"`
   must exit `0`. If not, emit `status: blocked`.

**Do not touch.** Exactly 1 file changes:
`tests/test_driver_integration.py`. No edits to: `.specfuse/`,
`scripts/`, `pyproject.toml`, other test files, `loop.py`,
`verification.yml`, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) must continue to pass — coverage
floor stays ≥90%. Plus AC4's 50× loop, which is the load-bearing
oracle for this WU.

**Escalation triggers.**
1. **50× loop fires even one failure.** If AC4's loop shows a single
   `FAILED` or `ERROR` line after your edits, emit `status: blocked`
   with the failing test name + full traceback. Do NOT paper over
   with retry logic.
2. **Root cause not in `integration_workspace`.** If audit reveals
   the leak is in code outside `integration_workspace` (e.g. a
   subprocess invoked by a test, a global git config, a CI-runner-
   only behavior not reproducible locally), emit `status: blocked`
   with a one-paragraph diagnosis. Do NOT widen scope without
   re-planning.
3. **API break.** If your fix changes the `integration_workspace`
   signature (no longer a context manager, no longer yielding `Path`,
   etc.), emit `status: blocked`. The fix must be a behind-the-scenes
   leak fix, not an API redesign.
4. **Completeness.** If `tests/test_driver_integration.py` does not
   show the `gc.auto=0` config AND the post-yield sync barrier after
   your edits, emit `status: blocked` — do not claim complete.
