---
id: FEAT-2026-0032/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 0.75
oracle_env: linux_docker
produces: tests/test_redaction_windows_home.py
produces_driver_helper: _HOME_PATH_RE
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Redact the Windows home-path shape (C:\Users\<name>\)

**Objective.** Extend the home-path redaction so it matches the Windows home
shape, closing a leak where `C:\Users\name\...` reaches `events.jsonl` and PR
bodies unredacted on a Windows run.

**Context.** Part of FEAT-2026-0032 (native Windows execution), gate 1. The
driver redacts home paths out of agent-authored text before staging via
`_HOME_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s]+/")` (`loop.py:~476-477`).
That pattern only matches POSIX layouts (`/Users/<name>/`, `/home/<name>/`); a
Windows home path `C:\Users\<name>\` does not match, so on a Windows run the
redaction silently does nothing and the username leaks into the events log and
any PR body the driver composes. This is a security fix, not cosmetic — it must
ship with the rest of gate 1, not after.

This surface is fully verifiable in the Linux loop sandbox: it is pure regex
behavior over input strings; no Windows environment is required to prove it.

Bind by reference: `.specfuse/rules/security-boundaries.md`,
`.specfuse/rules/result-contract.md`, `.specfuse/rules/never-touch.md`,
`.specfuse/skills/verification/SKILL.md`.

**Acceptance criteria.**
1. `tests/test_redaction_windows_home.py::test_windows_userprofile_path_redacted`
   exists and **fails on HEAD before this WU runs** — it passes a string
   containing `C:\Users\alice\secret.txt` through the same redaction path the
   driver uses and asserts the username segment is redacted. On HEAD the
   POSIX-only regex leaves it intact, so the test is red (or the test file does
   not yet exist — also red).
2. The redaction matches the Windows home shape `C:\Users\<name>\` — including a
   mixed separator (`C:\Users\<name>/...`) and a case-insensitive drive letter —
   and redacts the `<name>` segment, in addition to the existing POSIX shapes.
3. `tests/test_redaction_windows_home.py::test_windows_userprofile_path_redacted`
   **passes after this WU's edits**.
4. `tests/test_redaction_windows_home.py::test_posix_home_redaction_unchanged`
   asserts `/Users/<name>/` and `/home/<name>/` still redact exactly as before —
   and passes. Any existing redaction tests (e.g. in
   `tests/test_leak_findings_redaction.py`) pass unmodified.
5. The `leak-scan` gate stays clean on the changed files.

**Do not touch.** Other gate-1 WU surfaces: the lock (T01), the timeout kill
path (T02), `.github/workflows/ci.yml` (T04). Secrets, `.git/`. The driver owns
all git — edit files only.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (`tests`,
`lint`, `security`, `coverage --fail-under=90`, `leak-scan`), plus the scoped
red/green proof `python3 -m unittest tests.test_redaction_windows_home`.

**Escalation triggers.**
- If more than one redaction site or regex governs home-path redaction (enumerate
  with `grep -rn "Users|home\|_HOME_PATH_RE\|expanduser" specfuse/loop/`), every
  site that stages agent text is in scope; block if any is left POSIX-only rather
  than silently fixing one (§10 helper-duplication).
- If widening the pattern would over-redact legitimate non-home text (a false
  positive on `C:\Users\` used as a literal example in docs the driver stages),
  surface the trade-off and block for a human call rather than guessing.
