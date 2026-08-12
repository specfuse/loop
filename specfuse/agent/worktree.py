# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Give the operator back the branch they started on (#2055).

A `specfuse-agent` run dispatches `/fix-bug` sessions, and those create and
check out branches. When the run ends, the working tree is left on whatever
branch the last dispatched session made. Observed 2026-08-12: a run that
began on `main` ended on `fix/issue-1859-learnings-curate-vendored-promote`,
with nothing in the summary saying so. An operator who reads
`items completed: 0` and starts working is now committing onto an abandoned
feature branch without noticing.

**This lives outside `run_agent` on purpose.** The conductor's invariant --
"there is no code path here that can commit, branch, or merge", enforced by
`tests/test_agent_run.py`, which asserts the loop's runner issues only `gh`
and never a mutating verb -- is a real safety property and worth keeping. The
mutation is not the loop's; it belongs to the dispatched sessions. What the
loop's *caller* owns is the process boundary: `specfuse-agent` is one command
to the operator, and a command that moves your branch and does not move it
back is the surprise. So `main()` brackets the run, and the conductor stays
pure.

Restoring is deliberately conservative. A dirty tree is never forced past --
a checkout there could discard a dispatched session's uncommitted work, which
is strictly worse than the branch being wrong. Both the restore and the
refusal are reported, so a run that could not put things back says so rather
than leaving the operator to discover it.
"""

from __future__ import annotations

import subprocess
from typing import Callable, Optional


def _default_runner(argv: list, check: bool = False):
    return subprocess.run(argv, check=check, capture_output=True, text=True)


def current_branch(runner: Callable = _default_runner) -> Optional[str]:
    """The checked-out branch, or `None` if that cannot be determined.

    `None` covers a detached HEAD and a non-repository alike: in both, there
    is no branch name to put back, and guessing one would be worse than
    leaving the tree alone.
    """
    try:
        result = runner(["git", "branch", "--show-current"], check=False)
    except Exception:  # noqa: BLE001 - never break a run over bookkeeping
        return None
    if getattr(result, "returncode", 1) != 0:
        return None
    name = (getattr(result, "stdout", "") or "").strip()
    return name or None


def is_dirty(runner: Callable = _default_runner) -> Optional[bool]:
    """Whether the tree has uncommitted changes. `None` when unreadable."""
    try:
        result = runner(["git", "status", "--porcelain"], check=False)
    except Exception:  # noqa: BLE001
        return None
    if getattr(result, "returncode", 1) != 0:
        return None
    return bool((getattr(result, "stdout", "") or "").strip())


def restore_branch(
    original: Optional[str],
    *,
    runner: Callable = _default_runner,
    report: Optional[Callable[[str], None]] = None,
) -> bool:
    """Check *original* back out if the run moved off it. Returns success.

    A silent no-op only when the tree never moved, or when *original* is
    `None` because there was no branch to record at the start. Every other
    non-restore -- unreadable branch, dirty tree, failed checkout -- reports
    and returns False, because a restore that did not happen and says nothing
    is the failure mode this whole module exists to remove.
    """
    def _say(message: str) -> None:
        if report is not None:
            report(message)

    if not original:
        return True

    now = current_branch(runner)
    if now == original:
        return True
    if now is None:
        # Unreadable, not "fine". Returning success here would be a silent
        # path: git is broken or the tree is detached, we restored nothing,
        # and the operator hears nothing about either.
        _say(
            f"could not read the current branch, so '{original}' was not "
            f"restored — check where the tree is before continuing"
        )
        return False

    dirty = is_dirty(runner)
    if dirty is None:
        _say(
            f"working tree left on '{now}' (started on '{original}') — could "
            f"not read its status, so it was left alone"
        )
        return False
    if dirty:
        # Refusing loudly beats forcing: a checkout over uncommitted changes
        # can discard a dispatched session's work, and losing work is worse
        # than being on the wrong branch.
        _say(
            f"working tree left on '{now}' (started on '{original}') — NOT "
            f"restored: it has uncommitted changes. Inspect them before "
            f"switching back."
        )
        return False

    try:
        result = runner(["git", "checkout", original], check=False)
    except Exception as exc:  # noqa: BLE001
        _say(f"could not restore branch '{original}' — {type(exc).__name__}: {exc}")
        return False
    if getattr(result, "returncode", 1) != 0:
        stderr = (getattr(result, "stderr", "") or "").strip()
        _say(f"could not restore branch '{original}' — {stderr or 'checkout failed'}")
        return False

    _say(f"working tree restored to '{original}' (the run left it on '{now}')")
    return True
