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
from pathlib import Path
from typing import Any, Callable, Optional


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


def test_was_red_on_base(
    runner: Callable,
    *,
    base_sha: str,
    test_files: Any,
    command_template: str,
    worktree_root: Any,
) -> Optional[bool]:
    """`True` if *test_files* fail at *base_sha*, `False` if they pass, else `None`.

    `command_template` is the operator's own command with a `{tests}`
    placeholder -- `pytest {tests}`, `mvn -q test -Dtest={tests}`, whatever the
    repository actually uses. Absent, this returns `None` and the merge
    declines: see the module docstring on why guessing is worse than the gap.

    `None` means "could not establish", never "fine". A worktree that will not
    create, a runner that raises, no declared command and no test file in the
    diff all land there.
    """
    if not command_template or not str(command_template).strip():
        return None
    files = [str(p) for p in (test_files or [])]
    if not files:
        return None
    root = Path(str(worktree_root)) / f"red-on-base-{uuid.uuid4().hex[:12]}"

    try:
        created = runner(
            ["git", "worktree", "add", "--detach", str(root), str(base_sha)],
            check=False,
        )
    except Exception:  # noqa: BLE001 - a probe never takes the run down with it
        return None
    if getattr(created, "returncode", 1) != 0:
        return None

    try:
        rendered = command_template.replace("{tests}", " ".join(files))
        try:
            result = runner(shlex.split(rendered), cwd=str(root), check=False)
        except Exception:  # noqa: BLE001 - same reason as above
            return None
        code = getattr(result, "returncode", None)
        if not isinstance(code, int):
            return None
        # Non-zero at the base is the proof we want: the test the PR adds does
        # not hold on the tree the fix was written against.
        return code != 0
    finally:
        # Cleanup failure must not mask the verdict the probe just produced,
        # and a leaked worktree is a tidiness problem rather than a correctness
        # one. `suppress` rather than `except: pass` so the intent is explicit
        # and ruff's S110 stays meaningful where it fires for real.
        with contextlib.suppress(Exception):
            runner(["git", "worktree", "remove", "--force", str(root)], check=False)
