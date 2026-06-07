---
id: FEAT-2026-0008/T03
type: implementation
model: claude-opus-4-7
effort: high
status: pending
attempts: 0
---

# WU-Verification smoke-import runner

**Objective.** When a WU body's `Verification` section contains one or
more `python3 -c "from X import Y"` smoke-import commands, the driver
**executes** them after a successful squash and **before** advancing the
dependency frontier. A non-zero exit fails the WU (status NOT flipped
to `done`; soft-reset; re-dispatch as a failed attempt).

**Context.** This is `FEAT-2026-0008/T03`. FEAT-2026-0007/G1-LESSONS
promoted the rule that WUs naming new symbols should include explicit
existence checks in their Verification section. The rule was authored as
prose; this WU turns the prose into driver-enforced behavior.

The WU body is loaded by `load_wu` at `loop.py:211`-ish; the body string
is held in `WorkUnit.body`. The `verify()` function at `loop.py:537`
runs the gate-set commands from `.specfuse/verification.yml`. This WU
adds a NEW step that runs **between** the existing verify and the
status-flip-to-done, scoped to WU-declared smoke commands.

The exact match pattern is conservative: the line must match the regex
`^\s*python3?\s+-c\s+"from\s+\S+\s+import\s+\S+"\s*$` (or its
single-quote equivalent). Free-form Python via `-c` is NOT executed —
only the import-form, because (a) it has a falsifiable success criterion
(import succeeds or raises), (b) it is safe to run after a squash on a
known-clean tree, (c) it cannot mutate the working tree.

Reference the binding rules under `.specfuse/rules/`. The driver owns
git; edit files only.

**Acceptance criteria.**
1. New helper `extract_smoke_imports(wu_body: str) -> list[str]` returns
   the list of lines in the WU body matching the conservative pattern
   above. Each returned element is the **full command string** ready to
   pass to `subprocess.run(shell=True, ...)`. Order preserved.
2. New helper `run_smoke_imports(commands: list[str], cwd: Path) ->
   tuple[bool, str]` runs each command in sequence in `cwd`. Returns
   `(True, "")` if all exit 0; returns `(False, summary)` on the first
   non-zero exit with `summary` containing the command and stderr.
3. The attempt loop, after `verify()` returns success AND after
   `squash_commit` returns a commit hash AND before
   `set_wu(wu, "status", DONE)`, calls
   `extract_smoke_imports(wu.body)` then `run_smoke_imports(...)`. When
   the latter returns `(False, summary)`:
   (a) the squash commit is rolled back via
       `git reset --hard <head_before>` — the verify-passing-but-smoke-
       failing tree must NOT remain in history,
   (b) an event `attempt_outcome` with `outcome: "smoke_import_failed"`
       and payload `summary` is appended,
   (c) the attempt counts as a verification failure (continue to next
       attempt or spinning escalation).
4. When `extract_smoke_imports(wu.body)` returns an empty list, the new
   step is a no-op — no behavior change for WUs that do not declare
   smoke checks. This preserves existing-WU compatibility.
5. The smoke commands run with the **active venv** the driver was
   launched with — same PATH inheritance as `verify()`'s shell commands
   per `[loop-driver-operation]` memory rule.
6. New unit tests in `tests/test_loop_smoke_runner.py`:
   (a) `extract_smoke_imports` finds two import-form lines in a body
       with mixed content; ignores non-matching `python3 -c` lines and
       non-Python content.
   (b) `run_smoke_imports` returns `(True, "")` on `["python3 -c \"from
       sys import version\""]`.
   (c) `run_smoke_imports` returns `(False, ...)` on `["python3 -c
       \"from nonexistent_module_xyz import nothing\""]`.
   (d) Integration via a stubbed dispatch + a temp git repo: a WU whose
       body's Verification section names a smoke check that FAILS causes
       a squash rollback, a `smoke_import_failed` event, and a retry — no
       `done` status flip; no `task_completed` event.
   (e) Integration: a WU whose body declares no smoke check runs end-to-
       end as today (no new event types, no rollback, status flips to
       `done`).
7. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
   `python3 -c "from loop import extract_smoke_imports, run_smoke_imports"`
   must succeed before declaring complete.

**Do not touch.** Exactly 2 files change: `.specfuse/scripts/loop.py`
and one new test file `tests/test_loop_smoke_runner.py`. No edits to:
`.specfuse/verification.yml` (the smoke check is a WU-declared
additional check, not a gate-set redesign), `WU.template.md` (existing
WUs already document smoke imports; this WU only enforces them),
`.specfuse/rules/`, existing WU files, secrets, `.git/`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`,
plus the existence smoke check in AC 7.

**Escalation triggers.**
1. **Completeness.** If `extract_smoke_imports` or `run_smoke_imports`
   is absent from `loop.py` after your edits, emit `status: blocked` —
   do not claim complete.
2. **Pattern over-match.** If your regex catches free-form `python3 -c`
   lines (anything beyond the import form), stop and narrow it. Running
   arbitrary agent-authored Python in the driver process is a security
   regression; only the strict import form is in scope.
3. **Rollback order.** The rollback to `head_before` MUST run before the
   event is logged AND before the next attempt iterates, otherwise the
   next attempt starts from a tree containing the failed code. If the
   event-log path or the attempt-counter increment forces a different
   order, stop and emit `status: blocked` naming the conflict.
4. **Venv inheritance.** If the smoke commands cannot find the active
   venv's `python3` (PATH not inherited correctly), the smoke check will
   false-negative on every run. Verify via integration test in the
   stubbed-dispatch fixture; if the inheritance is fragile, document
   what is required (e.g. driver must be invoked from within an active
   venv per `[loop-driver-operation]`).
