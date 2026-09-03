#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Opt-in gate for the live GitHub round-trip tests (#3223).

Two test modules create real issues through `gh`. They used to run whenever
`gh auth status` succeeded — which on CI it always does — and opened about
200 scratch issues in this repository in two days, polluting `/attention`,
the triage queue, and the next-id scan.

The rule now: a live test runs only when the operator has said so and has
named where scratch objects may be created.

  SPECFUSE_LIVE_TESTS=1          opt in (anything else, or unset, skips)
  SPECFUSE_LIVE_REPO=owner/name  the scratch repository the tests may write to

An authenticated `gh` is necessary but never sufficient.
"""

from __future__ import annotations

import os
import subprocess
from typing import Callable, Mapping, Optional

OPT_IN_VAR = "SPECFUSE_LIVE_TESTS"
REPO_VAR = "SPECFUSE_LIVE_REPO"


def default_gh_ready() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, timeout=30, check=False,
        )
    except FileNotFoundError:
        return False, "gh binary not found on PATH"
    if result.returncode != 0:
        first_line = (result.stderr or result.stdout).strip().splitlines()[:1]
        reason = first_line[0] if first_line else "gh auth status failed"
        return False, f"gh unauthenticated: {reason}"
    return True, ""


def live_target(
    env: Optional[Mapping[str, str]] = None,
    gh_ready: Callable[[], tuple[bool, str]] = default_gh_ready,
) -> tuple[bool, str, Optional[str]]:
    """Return `(ready, reason, repo)` for a live test.

    `ready` is True only when the opt-in variable is exactly `1`, the repo
    variable names a non-empty `owner/name`, and `gh_ready()` reports an
    authenticated CLI. `reason` names the first missing piece so a skip
    message tells the operator what to set.
    """
    e = os.environ if env is None else env
    if e.get(OPT_IN_VAR, "") != "1":
        return False, f"{OPT_IN_VAR} is not set to 1 — live tests are opt-in", None
    repo = (e.get(REPO_VAR) or "").strip()
    if not repo or "/" not in repo:
        return False, f"{REPO_VAR} must name the scratch repository as owner/name", None
    ok, why = gh_ready()
    if not ok:
        return False, why, None
    return True, "", repo
