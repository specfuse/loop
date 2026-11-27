#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The build-pin record is committed on the feature branch (#3628).

A pinned driver records `driver_build_pinned` and commits it at once. That
commit was made before the run entered the feature branch, so a run started
on `main` (with `--prepare`, `--prepare-only`, or a plain run) left a driver
commit on `main`. After the feature merged, local `main` could no longer
fast-forward to `origin/main`.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace
from tests.test_run_progress import FEATURE_ID, SLUG, _passing_session, _scaffold

loop = load_loop()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def _pinned_events(ref: str) -> list:
    rel = f".specfuse/features/{FEATURE_ID}-{SLUG}/events.jsonl"
    shown = subprocess.run(["git", "show", f"{ref}:{rel}"],
                           capture_output=True, text=True, check=False)
    return [json.loads(line) for line in shown.stdout.splitlines()
            if '"driver_build_pinned"' in line]


class BuildPinStaysOffTheStartingBranch(unittest.TestCase):

    def _run(self, **kwargs):
        with integration_workspace() as root, \
                tempfile.TemporaryDirectory() as snapshots:
            cwd = os.getcwd()
            os.chdir(root)
            try:
                _scaffold(root, Path(snapshots))
                main_before = _git("rev-parse", "main")
                out = io.StringIO()
                with mock.patch.dict(os.environ,
                                     {loop.PINNED_BUILD_ENV_VAR: "abc123"}), \
                        mock.patch.object(loop, "dispatch", _passing_session), \
                        contextlib.redirect_stdout(out), \
                        contextlib.redirect_stderr(out):
                    loop.run(None, dry_run=False, **kwargs)
                return (main_before, _git("rev-parse", "main"),
                        _pinned_events("main"),
                        _pinned_events(f"feat/{SLUG}"), out.getvalue())
            finally:
                os.chdir(cwd)

    def test_prepare_only_leaves_main_alone(self):
        before, after, on_main, _, out = self._run(prepare_only=True)
        self.assertEqual(after, before, out)
        self.assertEqual(on_main, [])

    def test_a_run_started_on_main_records_the_pin_on_the_feature_branch(self):
        before, after, on_main, on_feature, out = self._run()
        self.assertEqual(after, before, out)
        self.assertEqual(on_main, [])
        self.assertEqual(len(on_feature), 1, out)
        self.assertEqual(on_feature[0]["payload"]["tree"], "abc123")


if __name__ == "__main__":
    unittest.main()
