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

**A third state (FEAT-2026-0109/T08).** An out-of-tree build used to be
uniformly "confidently wrong" -- an arbitrary installed wheel, indistinguishable
from a driver that forgot to rebuild. It no longer is: `main()` now
materializes its own pin of `specfuse/` outside the working tree, keyed on
`HEAD^{tree}`, and re-enters execution from it (`loop.py`'s `_reexec_pinned`).
That pin's provenance is recorded (`_PIN_MARKER_NAME`), so `out_of_tree_warning`
can tell the two apart: a *recorded* pin reports both tree hashes and says
which one it executed; an *unidentified* out-of-tree build keeps the alarming
text verbatim, because it is still exactly as dangerous as the wheel that
motivated this module.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
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


#: Repo root, relative to which the pin cache lives -- overridable so tests
#: (and an operator with no writable platform cache) can redirect it without
#: env-var-shaped magic sprinkled through the pinning logic itself.
_PIN_CACHE_ENV_VAR = "SPECFUSE_PIN_CACHE_DIR"

#: Marker file written into a materialized pin, naming the tree hash it was
#: built from. Its presence (and matching content) is what lets
#: `out_of_tree_warning` tell a recorded pin apart from an arbitrary
#: out-of-tree build -- anything under the pin cache root WITHOUT this marker
#: (or whose content disagrees with its own directory name) is treated as
#: unidentified, never trusted silently.
_PIN_MARKER_NAME = ".specfuse-pin-tree"

#: The launcher `main()` re-execs through once a pin is materialized. Its own
#: directory becomes `sys.path[0]` for a script invocation (probed fact #2 in
#: FEAT-2026-0109/T08's work-unit body), so it lives beside the pinned
#: `specfuse/` copy rather than importing it via `-m` or `-c`, both of which
#: the probe showed the working tree's copy shadows.
PIN_LAUNCHER_NAME = "_run_pinned.py"

_PIN_LAUNCHER_SOURCE = '''\
"""Generated by specfuse.loop.build_provenance.materialize_pin — do not edit.

Re-enters `specfuse.loop.loop:main` from this pin. This file's own directory
is `sys.path[0]` for a script invocation, ahead of the cwd, so the `specfuse`
package importable next to it resolves before the working tree's copy does.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from specfuse.loop.loop import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
'''


def repo_root_for(start: Optional[Path] = None) -> Optional[Path]:
    """The repo root of the source checkout *start* sits in, if any."""
    tree = source_tree_package_dir(start)
    return None if tree is None else tree.parent.parent


def head_tree_hash(repo_root: Path) -> Optional[str]:
    """`git rev-parse HEAD^{tree}` for *repo_root*, or None if unavailable.

    None (rather than raising) covers every reason a tree hash might not be
    resolvable -- no git binary, not a git repo, no commits yet -- and each
    one means the same thing to a caller: pinning cannot proceed, run
    unpinned. `never-touch.md`'s "stop at a boundary" posture, not a bug to
    chase down.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    tree_hash = result.stdout.strip()
    return tree_hash or None


def pin_cache_root() -> Path:
    """Where materialized pins live -- always outside any working tree.

    A platform cache directory keyed by tree hash, per the work unit's
    flag-scope table: putting it inside the tree it names would make its own
    key (`HEAD^{tree}`) move every time the pin is written. `$TMPDIR` (or its
    override) rather than a dotfile under the repo for the same reason.
    """
    override = os.environ.get(_PIN_CACHE_ENV_VAR)
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "specfuse-pins"


def pin_dir_for(tree_hash: str) -> Path:
    return pin_cache_root() / tree_hash


def materialize_pin(repo_root: Path, tree_hash: str) -> Path:
    """Copy *repo_root*'s `specfuse/` package to a pin keyed on *tree_hash*.

    Idempotent: a pin already materialized for this tree hash (the marker
    file matches) is reused as-is, so a second process pinning the same
    commit does not re-copy. Builds into a sibling temp directory first and
    installs it with a single `os.replace` so a reader never observes a
    half-copied pin.
    """
    pin_dir = pin_dir_for(tree_hash)
    marker = pin_dir / _PIN_MARKER_NAME
    if marker.is_file() and marker.read_text(encoding="utf-8").strip() == tree_hash:
        return pin_dir

    cache_root = pin_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{tree_hash}-", dir=str(cache_root)))
    try:
        shutil.copytree(
            repo_root / "specfuse", staging / "specfuse",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        (staging / PIN_LAUNCHER_NAME).write_text(_PIN_LAUNCHER_SOURCE, encoding="utf-8")
        (staging / _PIN_MARKER_NAME).write_text(tree_hash, encoding="utf-8")
        if pin_dir.exists():
            # Another process won the race and finished first; its copy is
            # equally valid (same tree hash), so keep it and discard ours.
            shutil.rmtree(staging, ignore_errors=True)
        else:
            os.replace(staging, pin_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return pin_dir


def pinned_build_info(running: Path) -> "Optional[tuple[str, Path]]":
    """If *running* is a recorded pin, return `(tree_hash, pin_root)`; else None.

    Trusts only a marker directly under a pin whose directory name equals the
    marker's own content -- an out-of-tree build that merely happens to sit
    under the cache root without a matching marker is still unidentified, not
    a free pass.
    """
    pin_root = running.parent.parent  # running == pin_root/specfuse/loop
    marker = pin_root / _PIN_MARKER_NAME
    if not marker.is_file():
        return None
    try:
        recorded = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not recorded or pin_root.name != recorded:
        return None
    return recorded, pin_root


def out_of_tree_warning(start: Optional[Path] = None) -> Optional[str]:
    """Return the warning text, or `None` when there is nothing to warn about.

    Separated from the printing so the message can be asserted on directly.

    Three states (FEAT-2026-0109/T08): in-tree (`None`), a **recorded pin**
    (reports both tree hashes, no alarming language -- this driver
    materialized it, from a named commit, this run), and an **unidentified**
    out-of-tree build (the original, unchanged "confidently wrong" text --
    still exactly as dangerous as the stale wheel that motivated this module).
    """
    tree = source_tree_package_dir(start)
    if tree is None:
        return None
    running = running_package_dir()
    if running == tree:
        return None
    pin_info = pinned_build_info(running)
    if pin_info is not None:
        pinned_hash, pin_root = pin_info
        working_root = tree.parent.parent
        working_hash = head_tree_hash(working_root)
        return (
            f"running a recorded pin of specfuse from {pin_root} "
            f"(tree {pinned_hash}); the working tree at {working_root} is "
            f"now at tree {working_hash or 'unknown'}."
        )
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
