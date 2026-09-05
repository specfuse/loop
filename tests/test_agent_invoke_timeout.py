# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for `run_claude`'s wall-clock timeout (FEAT-2026-0108/T03).

Covers: a runner raising `subprocess.TimeoutExpired` is reported as
`InvokeResult(timed_out=True, ...)` rather than propagated, and
`resolve_item_timeout_seconds` resolves `budgets.item_timeout_minutes` from
`.specfuse/agent-policy.yml` (default 45 minutes) into the seconds
`run_claude` forwards to its runner as `timeout`.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.invoke import (
    DEFAULT_ITEM_TIMEOUT_MINUTES,
    resolve_item_timeout_seconds,
    run_claude,
)


class TestRunnerTimeoutIsReportedNotRaised(unittest.TestCase):
    def test_runner_timeout_is_reported_not_raised(self):
        def timing_out_runner(argv, **kwargs):
            self.assertEqual(kwargs.get("timeout"), 5)
            raise subprocess.TimeoutExpired(
                cmd=argv,
                timeout=kwargs.get("timeout"),
                output="partial output captured before the deadline",
            )

        result = run_claude(
            ["claude", "-p"], "do the thing", runner=timing_out_runner, timeout_seconds=5
        )

        self.assertTrue(result.timed_out)
        self.assertEqual(result.text, "partial output captured before the deadline")
        self.assertIsNone(result.usage)

    def test_runner_completing_normally_is_not_timed_out(self):
        def runner(argv, **kwargs):
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")

        result = run_claude(["claude", "-p"], "prompt", runner=runner, timeout_seconds=5)

        self.assertFalse(result.timed_out)


class TestItemTimeoutComesFromPolicy(unittest.TestCase):
    def test_item_timeout_comes_from_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "agent-policy.yml"
            policy_path.write_text("budgets:\n  item_timeout_minutes: 7\n")

            timeout_seconds = resolve_item_timeout_seconds(policy_path)
            self.assertEqual(timeout_seconds, 420)

            captured = {}

            def runner(argv, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(returncode=0, stdout="{}", stderr="")

            run_claude(
                ["claude", "-p"], "prompt", runner=runner, timeout_seconds=timeout_seconds
            )

            self.assertEqual(captured.get("timeout"), 420)

    def test_absent_key_gives_the_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "agent-policy.yml"
            policy_path.write_text("budgets:\n  max_tokens_per_run: 100000\n")

            self.assertEqual(
                resolve_item_timeout_seconds(policy_path),
                DEFAULT_ITEM_TIMEOUT_MINUTES * 60,
            )

    def test_missing_policy_file_gives_the_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist.yml"

            self.assertEqual(
                resolve_item_timeout_seconds(missing),
                DEFAULT_ITEM_TIMEOUT_MINUTES * 60,
            )


if __name__ == "__main__":
    unittest.main()
