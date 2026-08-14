# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Work out which GitHub repo a `specfuse-agent` run is about (#2271).

`--repo` defaulted to `None` and nothing filled it in, so the ordinary
invocation -- `specfuse agent`, from inside the checkout you mean -- carried
no repo at all. Nothing said so. `default_providers` returns `()` on a `None`
repo, so the run had nothing selectable and reported `stop reason: drained`,
which reads as "no work left" rather than "no work was ever offered", and
exited 0. Observed 2026-08-14 on two unrelated projects.

Detection is deliberately narrow. `gh repo view` is asked first because it
already knows the answer the rest of the agent's calls will be made against
-- it resolves the same default remote `gh issue list` would use, so a
disagreement between them is impossible. The git remote is the fallback for
when `gh` is absent or unauthenticated, and only for GitHub hosts: a
`gitlab.com` remote yields `None`, because the value is about to be handed to
`gh` and a plausible-looking `OWNER/NAME` from the wrong forge would fail
further downstream with a worse message.

Every failure here is `None`, never an exception. The caller
(`specfuse.agent.run.main`) owns what an undetectable repo means, and it
means a plain error naming `--repo` -- not a traceback, and not a run.
"""

from __future__ import annotations

import re
import subprocess
from typing import Callable, Optional

#: `OWNER/NAME`, and nothing that merely contains one. A detected value is
#: about to become a `gh --repo` argument, so a stray path segment or a URL
#: fragment surviving the parse would be spent on a call that fails later.
_SLUG = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")

#: `git@github.com:owner/name.git`, `https://github.com/owner/name`, and the
#: `ssh://`/`git://` spellings of either. Enterprise hosts are not matched --
#: see the module docstring on why a wrong-forge guess is worse than `None`.
_REMOTE = re.compile(
    r"^(?:(?:https?|ssh|git)://)?(?:[^@/]+@)?github\.com[:/]"
    r"(?P<slug>[A-Za-z0-9._-]+/[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)


def _default_runner(argv: list, check: bool = False):
    return subprocess.run(argv, check=check, capture_output=True, text=True)


def _stdout(runner: Callable, argv: list) -> Optional[str]:
    """The command's trimmed stdout, or `None` if it did not succeed."""
    try:
        result = runner(argv, check=False)
    except Exception:  # noqa: BLE001 - a missing `gh` or `git` is a fallback,
        return None    # not a crash; the caller has another source to try.
    if getattr(result, "returncode", 1) != 0:
        return None
    return (getattr(result, "stdout", "") or "").strip() or None


def detect_repo(*, runner: Callable = _default_runner) -> Optional[str]:
    """The `OWNER/NAME` of the checkout, or `None` when it cannot be read.

    Asks `gh repo view` first and the `origin` remote second; see the module
    docstring for why that order and why non-GitHub remotes are declined.
    """
    slug = _stdout(
        runner, ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
    )
    if slug and _SLUG.match(slug):
        return slug

    remote = _stdout(runner, ["git", "remote", "get-url", "origin"])
    if not remote:
        return None
    match = _REMOTE.match(remote)
    return match.group("slug") if match else None


def resolve_repo(
    explicit: Optional[str], *, runner: Callable = _default_runner
) -> Optional[str]:
    """*explicit* if the operator passed one, else whatever `detect_repo`
    finds. An explicit value probes nothing -- it is already the answer, and
    a detection run behind it could only produce a value that is ignored."""
    if explicit:
        return explicit
    return detect_repo(runner=runner)
