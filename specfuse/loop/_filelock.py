#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Cross-platform advisory lock for the driver's single-instance working-tree lock.

The kernel must auto-release the lock on process exit, including SIGKILL, with
no cleanup step — this is why POSIX `fcntl.flock` and Windows `msvcrt.locking`
are used here instead of any userspace primitive. Pidfiles are ruled out: the
pid-holder can die without a chance to remove its file, leaving a stale lock
that stalls or is silently skipped by the next launch.
"""

from __future__ import annotations

import sys
from pathlib import Path


def acquire_tree_lock(specfuse_dir: Path):
    """Open .specfuse/.loop.lock and acquire a non-blocking exclusive lock.

    Returns the open file object; caller keeps it alive for the process
    lifetime — the OS auto-releases on fd/handle close or process death
    (SIGKILL included), so no stale-lock cleanup is ever needed.
    Raises BlockingIOError if another process already holds the lock.
    """
    lock_path = specfuse_dir / ".loop.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = lock_path.open("w")
    try:
        if sys.platform == "win32":
            import msvcrt
            try:
                msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise BlockingIOError from exc
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.close()
        raise
    return fd
