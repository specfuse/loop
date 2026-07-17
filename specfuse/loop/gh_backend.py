#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""GitHubBackend: Backend subclass that emits state:* label transitions on lifecycle events."""

from __future__ import annotations

import subprocess
from typing import Callable, Optional

from . import loop as _loop


def _default_runner(args: list, check: bool = True):
    """Shell out to gh with the given argument list. Not called in tests.

    Returns the completed process so probing callers (e.g. the `gh pr view`
    idempotency check) can inspect `.returncode` without raising; side-effecting
    callers pass no `check` override and get the prior raise-on-failure behavior.
    """
    return subprocess.run(args, check=check, capture_output=True, text=True)


class GitHubBackend(_loop.Backend):
    """Backend that transitions state:* labels on a GitHub issue per lifecycle event.

    Lifecycle mapping:
      on_feature_start    -> add state:in-progress, remove state:ready
      on_gate_passed      -> no-op v0.1 (gate observability lives in event log)
      on_feature_complete -> add state:done, remove state:in-progress
    """

    def __init__(
        self,
        repo: str,
        issue_number: int,
        runner: Optional[Callable] = None,
    ) -> None:
        self.repo = repo
        self.issue_number = issue_number
        self._runner = runner if runner is not None else _default_runner

    def on_feature_start(self, feature_id: str, feat_fm: dict) -> None:
        self._feat_fm = feat_fm   # stored for on_feature_complete
        self._runner([
            "gh", "issue", "edit", str(self.issue_number),
            "--repo", self.repo,
            "--add-label", "state:in-progress",
            "--remove-label", "state:ready",
        ])

    def on_gate_passed(self, feature_id: str, gate_number: int) -> None:
        """No-op v0.1 stub: gate-level observability lives in the per-feature event log."""

    def on_feature_complete(self, feature_id: str) -> None:
        feat_fm = getattr(self, "_feat_fm", {})
        branch = feat_fm.get("branch", "")
        title = feat_fm.get("title", feature_id)

        # Idempotent: skip PR creation if one already exists for this branch.
        check = self._runner(
            ["gh", "pr", "view", branch, "--repo", self.repo, "--json", "number"],
            check=False,
        )
        if check.returncode != 0:
            body = (
                f"Closes #{self.issue_number}\n\n"
                f"Correlation: `{feature_id}`\n\n"
                f"Part of initiative `{feat_fm.get('initiative', '')}`. "
                f"All loop gates passed; see feature event log for details."
            )
            self._runner([
                "gh", "pr", "create",
                "--title", f"[{feature_id}] {title}",
                "--body", body,
                "--base", _loop.resolve_base(feat_fm),
                "--head", branch,
            ])

        self._runner([
            "gh", "issue", "edit", str(self.issue_number),
            "--repo", self.repo,
            "--add-label", "state:done",
            "--remove-label", "state:in-progress",
        ])
