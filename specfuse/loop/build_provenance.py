# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Which build am I actually running? (#1040)

An installed console script (`specfuse-loop`, `specfuse-lint`, …) resolves
`specfuse.loop` from `site-packages`. In a checkout of the driver's own source
whose tree has moved ahead of the installed wheel, that means the command runs
**a different program than the session believes it is running** -- and reports
confidently.

The failure mode is the worst kind: it does not error, it returns a plausible
number. Three observed occurrences, two at real cost:

* A gate-1 arming probe swept `specfuse-lint --closing` to confirm a new
  requirement added no findings. It resolved to the installed 0.7.1 wheel,
  which contained neither the new rules nor the module implementing them --
  "the sweep would have reported identically had T03 shipped nothing."
* A terminal close produced **14 spurious red results** before the run was
  repeated from the repo root.

Every affected surface had been patched by convention -- work-unit bodies
saying "use the `.specfuse/scripts/` shim, not the installed console script"
-- which is exactly the shape `a-rule-a-human-must-execute-is-not-a-control`
says does not hold: a rule a session must remember, a silent wrong answer when
it forgets, and no signal telling the two apart.

This module is that signal. It warns; it does not refuse. #1040 lists refusal
as a stronger option and recommends warning first, on the grounds that the
warning's own evidence is what tells you whether refusal is needed.

**Silent for downstream projects by construction.** The check fires only when
the directory being operated on contains a `specfuse/loop/` source tree of its
own -- i.e. a checkout of the driver. A project that installed Specfuse has no
such path, so the console script is the correct thing to run there and this
module never says anything.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

#: The shim that always resolves to the working tree, named in the warning as
#: the concrete fix. `.specfuse/scripts/` is vendored per project.
_SHIM_HINT = "python3 -m specfuse.loop.loop   (or .specfuse/scripts/<script>.py)"

#: Relative path identifying a driver source checkout.
_SOURCE_MARKER = Path("specfuse") / "loop" / "loop.py"


def running_package_dir() -> Path:
    """The `specfuse/loop/` directory this process actually imported.

    Derived from this module's own location rather than by importing
    `loop.py`: the check runs at CLI startup, and importing the driver to ask
    where the driver is would be both slow and circular.
    """
    return Path(__file__).resolve().parent


def source_tree_package_dir(start: Optional[Path] = None) -> Optional[Path]:
    """The `specfuse/loop/` of the source checkout *start* sits in, if any.

    Walks upward from *start* (default: the current directory) looking for a
    `specfuse/loop/loop.py`. Returns `None` when there is none -- the normal
    case for a project that installed Specfuse, and the reason this check is
    silent there.
    """
    current = (start if start is not None else Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / _SOURCE_MARKER).is_file():
            return (candidate / "specfuse" / "loop").resolve()
    return None


def out_of_tree_warning(start: Optional[Path] = None) -> Optional[str]:
    """Return the warning text, or `None` when there is nothing to warn about.

    Separated from the printing so the message can be asserted on directly.
    """
    tree = source_tree_package_dir(start)
    if tree is None:
        return None
    running = running_package_dir()
    if running == tree:
        return None
    return (
        f"warning: running specfuse from {running}, but the working tree at "
        f"{tree.parent.parent} carries its own source.\n"
        f"         This command is measuring the INSTALLED build, not your "
        f"checkout — results can be confidently wrong rather than failing.\n"
        f"         Run instead: {_SHIM_HINT}"
    )


def warn_if_out_of_tree(start: Optional[Path] = None, stream=None) -> Optional[str]:
    """Print the warning to stderr when one applies; return what was printed.

    stderr, not stdout: several of these commands have parseable stdout that a
    caller consumes, and a diagnostic must not land in it.
    """
    message = out_of_tree_warning(start)
    if message is not None:
        print(message, file=stream if stream is not None else sys.stderr)
    return message
