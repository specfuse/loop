#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Detect whether a set of changed paths edits the driver's own importable
surface (FEAT-2026-0075/T01).

Python caches modules in `sys.modules` at first import, so a work unit that
edits the driver changes nothing for anything the same process dispatches
afterwards. Detection keys on a commit's actual diff, never on a work unit's
`produces:` or `produces_driver_helper` declarations — those are
author-supplied and the lint on the latter is WARN-only, so a unit can edit
`loop.py` while declaring nothing.

Only `changed_paths_for_commit` shells out to git; `diff_edits_driver` and
`driver_paths_in` are pure. This module must not import
`specfuse.loop.loop` — `loop.py` imports this module, and the reverse edge
would be a cycle.
"""

from __future__ import annotations

import subprocess

DRIVER_MODULE_PREFIXES = ("specfuse/loop/",)


def diff_edits_driver(paths):
    """Return True if any path in `paths` falls under a driver module prefix."""
    for path in paths:
        if path.startswith(DRIVER_MODULE_PREFIXES):
            return True
    return False


def driver_paths_in(paths):
    """Return only the paths in `paths` that fall under a driver module prefix,
    in input order."""
    return [path for path in paths if path.startswith(DRIVER_MODULE_PREFIXES)]


def changed_paths_for_commit(sha, repo_root):
    """Return the list of paths a commit touched, relative to `repo_root`."""
    result = subprocess.run(
        ["git", "show", "--no-commit-id", "--name-only", "--pretty=format:", sha],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]
