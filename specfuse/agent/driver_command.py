# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Which build of the driver does the conductor dispatch? (#2186)

`specfuse-agent` dispatched `specfuse run`, which resolves to whatever
`specfuse` is on `PATH`. In a checkout of the driver's own source that is the
*installed* build -- observed 2026-08-14 roughly twenty merged PRs behind the
working tree, with both reporting the same version string, so no comparison
anyone could make said otherwise. FEAT-2026-0080's terminal close failed three
times against it, $40.27 across a 99-minute run, over a bug fixed on `main`
two days earlier; two people-hours then went into re-diagnosing the fixed bug
before the build was suspected.

**Why the check has to live here.** `build_provenance` warns when a command is
running a build that is not the working tree's, and it did not fire once --
because the installed build predated it. A build old enough to be the problem
is, by construction, old enough to lack the check that would report it. The
dispatcher is always at least as new as what it dispatches, so it is the only
place the comparison can be trusted. That is recommendation (1) of #2186.

**Silent for downstream projects by construction**, on the same test
`build_provenance` uses: the in-tree form is chosen only when the working
directory sits inside a tree carrying `specfuse/loop/loop.py` of its own. A
project that installed Specfuse has no such path and keeps getting
`specfuse run`, which is the correct thing to run there.

This removes the skew rather than reporting it. `python -m` puts the working
directory first on `sys.path`, so the dispatched driver resolves the
checkout's source even when the interpreter belongs to a pipx venv -- the same
fix `build_provenance`'s own warning text recommends to a human.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Sequence

from specfuse.loop.build_provenance import source_tree_package_dir

#: What a project that installed Specfuse runs. The umbrella CLI's `run`
#: subcommand, resolved from `PATH`.
INSTALLED_COMMAND = ("specfuse", "run")

#: The driver's module entry point, dispatched through the running
#: interpreter. Takes the same flags as `specfuse run` -- a test asserts
#: `--help` still advertises `--feature`, so a divergence fails here rather
#: than mid-run.
_MODULE_ENTRY = "specfuse.loop" + ".loop"


def resolve_driver_command(
    *, start: Optional[Path] = None, override: Optional[Sequence[str]] = None
) -> list:
    """The argv prefix one `specfuse run` dispatch should use.

    *override* wins outright and is never second-guessed: a caller that names
    a command has a reason, and tests inject stubs through it.
    """
    if override is not None:
        return list(override)
    if source_tree_package_dir(start) is None:
        return list(INSTALLED_COMMAND)
    return [sys.executable, "-m", _MODULE_ENTRY]


def describe_command(command: Sequence[str]) -> str:
    """One line naming which build a dispatch is about to run.

    The conductor's stdout is what the operator watches; the driver's own
    output is teed to `work/driver-<stamp>.log`, which #2186 notes is "where
    nobody is looking during a run". A dispatch that silently changed which
    build it ran would trade one invisible default for another.
    """
    parts = list(command)
    if len(parts) >= 3 and parts[1] == "-m":
        return f"driver: {parts[2]} from the working tree source ({parts[0]})"
    return f"driver: {' '.join(parts)} — the installed build on PATH"
