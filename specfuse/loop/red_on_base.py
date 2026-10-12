#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Run a bug-lane PR's own new test at the merge base (#3377).

`evaluate_merge_guardrails`' six original checks all measure the **form** of a
PR: it touches a test path, CI is green, the diff is small, no judge path is
touched, the provenance is traceable, the daily cap is not reached. None of
them measures whether the change works -- whether the symptom the issue
reported stopped reproducing.

Audited on one consumer repository over three days: seven lane PRs passed all
six, four were incomplete for the issue they claimed to close, and two of those
merged unattended and closed the issue behind a symptom that still reproduced.

This module produces the one input that asks a different question. A test that
**passes at the merge base** proves nothing about the fix: it is asserting
behaviour that already held, or testing something adjacent to the defect. Two
runs and no model judgement decide it.

Three deliberate constraints:

* **Never touch the live working tree.** The lane is running there. A
  `git checkout` of the base would move the driver's own ground mid-run, so the
  probe creates an isolated `git worktree`, runs there, and removes it.
* **Never guess the command.** The operator declares it. A guessed command that
  silently matched no tests would exit non-zero, read as "red on base", and
  wave every PR through -- strictly worse than the gap it was meant to close.
* **Run it through a shell.** Operator-authored commands use pipes, `||`, `$(...)`
  and inline environment overrides, exactly as the gate commands in
  `verification.yml` do -- `_run_gate_set` runs those with `shell=True` for the
  same stated reason. A first cut of this module used `shlex.split` and no
  shell, which could not express the command of the very repository it was
  built for: every merge would have declined `red_on_base_unverified` while
  looking configured.
* **Fail closed.** Every unknown returns `None`, which the guardrail reads as
  unverified and declines. An unverifiable claim is not a satisfied one.

The limit, stated rather than implied: this catches "the test proves nothing",
not "the test proves the wrong thing". A test red on base for a reason
unrelated to the reported symptom still passes here. Closing that needs the
issue to carry a machine-readable reproduction, which is a separate ask.
"""

from __future__ import annotations

import contextlib
import shlex
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


#: POSIX reserves these for the shell's own failure to run the command: 126 is
#: "found but not executable", 127 is "not found". Neither says anything about
#: the test, so neither may be read as a verdict on it (#3403).
_COULD_NOT_EXECUTE = frozenset({126, 127})

#: How much of git's stderr a reason carries -- enough to name the failure,
#: short enough to sit on one line of an escalation.
_STDERR_CHARS = 200


@dataclass(frozen=True)
class RedOnBaseProbe:
    """The probe's verdict, and why it could not reach one (#3416).

    `reason` is empty whenever `verdict` is a bool. When `verdict` is `None`
    it names the step that gave up -- `no_command`, `no_test_files`,
    `base_sha_lookup_failed`, `head_sha_lookup_failed`, `fetch_failed: <stderr>`,
    `worktree_add_failed: <stderr>`, `overlay_failed: <stderr>`, `runner_raised: <exc>` or
    `could_not_execute: exit <n>` -- so an `unverified` decline can be acted
    on without re-deriving the probe by hand.
    """

    verdict: Optional[bool]
    reason: str = ""


def _stderr_of(result: Any) -> str:
    text = (getattr(result, "stderr", "") or "").strip().replace("\n", " ")
    return text[:_STDERR_CHARS]


def _unverified(reason: str) -> RedOnBaseProbe:
    return RedOnBaseProbe(verdict=None, reason=reason)


def _ensure_commit(runner: Callable, sha: str) -> str:
    """Make *sha* present locally; return `""`, or a `fetch_failed` reason.

    The base and head SHAs come from GitHub, and either can be a commit the
    local clone has never seen -- the base after a merge during the run
    (#3416), the head when the PR was pushed from elsewhere.
    """
    present = runner(["git", "cat-file", "-e", f"{sha}^{{commit}}"], check=False)
    if getattr(present, "returncode", 1) == 0:
        return ""
    fetched = runner(["git", "fetch", "origin", str(sha)], check=False)
    if getattr(fetched, "returncode", 1) != 0:
        return f"fetch_failed: {_stderr_of(fetched)}"
    return ""


def select_test_files(changed_files: Any, test_paths: Any) -> list:
    """The changed files that live under a declared test root.

    Returns `[]` for anything unreadable rather than falling back to "all
    changed files": a wrong selection here runs production sources as if they
    were tests, and an empty selection declines, which is the safe direction.
    """
    if changed_files is None or isinstance(changed_files, (str, bytes)):
        return []
    if test_paths is None or isinstance(test_paths, (str, bytes)):
        return []
    try:
        roots = tuple(str(p) for p in test_paths)
        candidates = [str(p) for p in changed_files]
    except TypeError:
        return []
    if not roots:
        return []
    return [path for path in candidates if path.startswith(roots)]


def probe_red_on_base(
    runner: Callable,
    *,
    base_sha: str,
    test_files: Any,
    command_template: str,
    worktree_root: Any,
    head_sha: Optional[str] = None,
) -> RedOnBaseProbe:
    """`True` if *test_files* fail at *base_sha*, `False` if they pass, else `None`
    -- with the reason, when `None` (#3416).

    `command_template` is the operator's own command with a `{tests}`
    placeholder, run through `sh -c` so pipes, `||` and `$(...)` all work --
    a Maven repository needs `$(...)` just to turn the changed file paths into
    the class names `-Dtest=` accepts. Absent, this returns `None` and the
    merge declines: see the module docstring on why guessing is worse than the
    gap.

    `sh -c` rather than `subprocess(shell=True)` so the command still arrives
    through the injected runner as an argv, which is what makes this testable
    without executing anything. It also means the template is POSIX shell; a
    Windows runner would need its own spelling, and none is invented here.

    *head_sha* is the PR's head (#3417). Its version of each test path is
    overlaid onto the base worktree before the command runs, so the probe
    runs the PR's tests against the base's production code. Without it, the
    base's own copy of a modified test file ran: a test added to an existing
    class, or an updated golden, passed there and could never read red. A
    blank *head_sha* -- the caller could not look it up -- is unverified;
    `None` skips the overlay.

    `None` means "could not establish", never "fine". A worktree that will not
    create, a runner that raises, no declared command and no test file in the
    diff all land there.
    """
    if not command_template or not str(command_template).strip():
        return _unverified("no_command")
    files = [str(p) for p in (test_files or [])]
    if not files:
        return _unverified("no_test_files")
    if not base_sha or not str(base_sha).strip():
        return _unverified("base_sha_lookup_failed")
    if head_sha is not None and not str(head_sha).strip():
        return _unverified("head_sha_lookup_failed")
    root = Path(str(worktree_root)) / f"red-on-base-{uuid.uuid4().hex[:12]}"

    try:
        # #3416: `base_sha` is the base branch's tip on GitHub *now*. A PR
        # merged there during the run moves it past the local `origin/main`,
        # and `worktree add` of a commit the clone has never seen fails. Fetch
        # it by SHA when it is absent -- and the head too, for the overlay.
        for sha in (base_sha, head_sha):
            if sha is None:
                continue
            missing = _ensure_commit(runner, str(sha))
            if missing:
                return _unverified(missing)
        created = runner(
            ["git", "worktree", "add", "--detach", str(root), str(base_sha)],
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - a probe never takes the run down with it
        return _unverified(f"runner_raised: {exc}")
    if getattr(created, "returncode", 1) != 0:
        return _unverified(f"worktree_add_failed: {_stderr_of(created)}")

    try:
        if head_sha is not None:
            try:
                overlaid = runner(
                    ["git", "-C", str(root), "checkout", str(head_sha), "--", *files],
                    check=False,
                )
            except Exception as exc:  # noqa: BLE001 - same reason as above
                return _unverified(f"runner_raised: {exc}")
            if getattr(overlaid, "returncode", 1) != 0:
                return _unverified(f"overlay_failed: {_stderr_of(overlaid)}")
        rendered = command_template.replace(
            "{tests}", " ".join(shlex.quote(p) for p in files))
        try:
            result = runner(["sh", "-c", rendered], cwd=str(root), check=False)
        except Exception as exc:  # noqa: BLE001 - same reason as above
            return _unverified(f"runner_raised: {exc}")
        code = getattr(result, "returncode", None)
        if not isinstance(code, int):
            return _unverified("could_not_execute: no exit code")
        if code in _COULD_NOT_EXECUTE:
            # The shell could not run the command at all. That is "the check
            # never ran", not "the test failed" -- and the difference is the
            # whole point of keeping those two declining reasons apart.
            #
            # Measured: an operator whose command is a committed script hits
            # this on every PR whose merge base predates that script. The
            # worktree is the BASE tree, so the script is simply absent there,
            # `sh` exits 127, and reading that as red would let the merge
            # through on the strength of a command that never ran. Fail-open,
            # in the one guardrail whose entire job is to be harder to satisfy
            # than the others.
            return _unverified(f"could_not_execute: exit {code}")
        # Non-zero at the base is the proof we want: the test the PR adds does
        # not hold on the tree the fix was written against.
        return RedOnBaseProbe(verdict=code != 0)
    finally:
        # Cleanup failure must not mask the verdict the probe just produced,
        # and a leaked worktree is a tidiness problem rather than a correctness
        # one. `suppress` rather than `except: pass` so the intent is explicit
        # and ruff's S110 stays meaningful where it fires for real.
        with contextlib.suppress(Exception):
            runner(["git", "worktree", "remove", "--force", str(root)], check=False)

