---
id: FEAT-2026-0013/T01
type: implementation
model: claude-sonnet-4-6
effort: high
status: done
attempts: 2
# Cost preserved from v1 + v2 + v3-attempt-1 + v3-attempt-2 (see PLAN.md
# ## Prior attempts). v3-attempt-2 again wasted: same ssh-agent-unreachable
# block in test_loop_orchestration._minimal_git_repo. Operator now disabled
# commit.gpgsign locally (git config --local commit.gpgsign false) so v3-
# attempt-3 should not hit it.
historical_cost_usd: 5.228352
historical_duration_seconds: 3181.344
historical_input_tokens: 134
historical_output_tokens: 120510
duration_seconds: 1898.807
cost_usd: 2.715082
input_tokens: 84
output_tokens: 47479
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

**v2 → v3 amendment (2026-06-12).** v2 shipped to PR #9 with macOS
local + Linux Docker 50× both PASS=50 OSError=0. CI on PR re-failed
(run `27417616885`) in `tests/test_loop_files_changed_guard.py::
test_agent_creates_new_file_and_declares_it_completes` — same
OSError, DIFFERENT `integration_workspace` definition. Scope-
discovery miss: the repo has FIVE `def integration_workspace()`
copies (test_driver_integration:40, test_backend:36, test_loop_
files_changed_guard:145, test_loop_smoke_runner:135, test_loop_
zero_token_guard:74). v1+v2 only touched the first.

v3 fix: CENTRALIZE. Create one shared helper at
`tests/_workspace.py::integration_workspace()` carrying the
gc.auto=0 + sync barrier + `ignore_cleanup_errors=True` once.
Replace each of the five duplicate definitions with a single
`from tests._workspace import integration_workspace` import. One
source of truth; future race fixes touch one file. Bare
`tempfile.TemporaryDirectory()` call sites outside the five
helpers are OUT of scope for this WU — most are not git-coupled
(lint tests writing yaml fixtures, etc.) and a follow-on feature
can address them if evidence warrants.

**Acceptance criteria.**
1. **New shared helper at `tests/_workspace.py`** exports a
   `@contextmanager` `integration_workspace()` that yields a
   `pathlib.Path`. The body:
   - constructs `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)`
   - inits a git repo (`git init -q -b main`)
   - sets `gc.auto 0` on the temp repo immediately after init
   - sets user.email and user.name for test commits
   - performs a baseline commit so the repo has HEAD
   - in a `finally:` block before `TemporaryDirectory` exits, runs the
     sync barrier: `subprocess.run(["git", "-C", str(root),
     "rev-parse", "HEAD"], check=True, capture_output=True)`
   - every `subprocess.run` carries `check=True` and captures
     completion (no fire-and-forget)
2. **The 5 duplicate definitions are replaced with imports.** Each of
   the following lines `def integration_workspace():` and the
   immediately-following `with tempfile.TemporaryDirectory()` body MUST
   be deleted; the file MUST instead carry
   `from tests._workspace import integration_workspace` near the top:
   - `tests/test_driver_integration.py:40`
   - `tests/test_backend.py:36`
   - `tests/test_loop_files_changed_guard.py:145`
   - `tests/test_loop_smoke_runner.py:135`
   - `tests/test_loop_zero_token_guard.py:74`
3. **Source-presence check.** Before declaring complete, agent runs:
   `.venv/bin/python3 -c "
   import inspect
   from tests._workspace import integration_workspace
   src = inspect.getsource(integration_workspace)
   assert 'ignore_cleanup_errors=True' in src
   assert 'gc.auto' in src or \"'gc.auto', '0'\" in src
   assert 'rev-parse' in src
   for mod_name in ['tests.test_driver_integration', 'tests.test_backend', 'tests.test_loop_files_changed_guard', 'tests.test_loop_smoke_runner', 'tests.test_loop_zero_token_guard']:
       mod = __import__(mod_name, fromlist=['integration_workspace'])
       assert mod.integration_workspace is integration_workspace, mod_name + ' did not import the shared helper'
   print('v3 surfaces present')
   "`
   — must exit `0` AND print `v3 surfaces present`. If not, emit
   `status: blocked`.
4. **Local 50× audit (weak oracle, necessary not sufficient).** The
   full suite runs 50× locally with zero exit-nonzero:
   `pass=0; fail=0; for i in $(seq 1 50); do .venv/bin/python3 -m unittest discover tests -q >/dev/null 2>&1 && pass=$((pass+1)) || fail=$((fail+1)); done; echo "PASS=$pass FAIL=$fail"`
   Expected: `PASS=50 FAIL=0`. Quote in RESULT block.
5. **Coverage stays ≥90%.** `code` gate set in
   `.specfuse/verification.yml` continues to pass.
6. **No API break.** Every existing `with integration_workspace() as
   root:` call site continues to receive a `Path` named `root`. (The
   imports preserve calling semantics; tests don't change behavior.)

**Do not touch.** Exactly 6 files change:
- `tests/_workspace.py` (NEW)
- `tests/test_driver_integration.py` (replace definition with import)
- `tests/test_backend.py` (replace definition with import)
- `tests/test_loop_files_changed_guard.py` (replace definition with import)
- `tests/test_loop_smoke_runner.py` (replace definition with import)
- `tests/test_loop_zero_token_guard.py` (replace definition with import)

No edits to: `.specfuse/`, `scripts/`, `pyproject.toml`, other test
files, `loop.py`, `verification.yml`, secrets, `.git/`. See
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
