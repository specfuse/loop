#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""GitHubBackend: Backend subclass that emits state:* label transitions on lifecycle events."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

# Add scripts dir to path so `import loop` resolves from the same install.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import loop as _loop  # noqa: E402


def _default_runner(args: list) -> None:
    """Shell out to gh with the given argument list. Not called in tests."""
    subprocess.run(args, check=True, capture_output=True, text=True)


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
        self._runner([
            "gh", "issue", "edit", str(self.issue_number),
            "--repo", self.repo,
            "--add-label", "state:in-progress",
            "--remove-label", "state:ready",
        ])

    def on_gate_passed(self, feature_id: str, gate_number: int) -> None:
        """No-op v0.1 stub: gate-level observability lives in the per-feature event log."""

    def on_feature_complete(self, feature_id: str) -> None:
        self._runner([
            "gh", "issue", "edit", str(self.issue_number),
            "--repo", self.repo,
            "--add-label", "state:done",
            "--remove-label", "state:in-progress",
        ])
