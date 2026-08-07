#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0056/T05: the per-criterion close artifact must survive a failed
close attempt's untracked-file cleanup.

`untracked_before` is snapshotted once per work unit, before the attempt
loop; `GATE-NN-CRITERIA.md` is created inside the attempt (by
`_precreate_criteria_state_stub`), so on a failing attempt
`_clean_attempt_untracked` sees it as a file that appeared since the
snapshot and unlinks it. `events.jsonl` has an explicit carve-out for the
same shape of problem; this artifact needs one too, keyed on its filename.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


@contextmanager
def _git_repo_no_sign():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        run = lambda *a: subprocess.run(  # noqa: E731
            ["git", "-C", str(root), *a], check=True, capture_output=True,
        )
        run("init", "-q", "-b", "main")
        run("config", "commit.gpgSign", "false")
        run("config", "gc.auto", "0")
        run("config", "user.email", "test@example.com")
        run("config", "user.name", "Test")
        (root / "README.md").write_text("# fixture\n")
        run("add", ".")
        run("commit", "-q", "-m", "init")
        run("rev-parse", "HEAD")
        prev_cwd = os.getcwd()
        try:
            os.chdir(root)
            yield root
        finally:
            os.chdir(prev_cwd)


class TestCriteriaArtifactSurvivesAttemptReset(unittest.TestCase):
    """Drives the real `_clean_attempt_untracked`, not a re-implementation."""

    def test_criteria_artifact_survives_attempt_reset(self):
        with _git_repo_no_sign() as root:
            events_path = root / "events.jsonl"
            # untracked_before snapshotted BEFORE the artifact exists, exactly
            # as run() snapshots it before the attempt loop.
            untracked_before = loop.untracked_paths()

            feature_dir = root / ".specfuse" / "features" / "FEAT-TEST-0001"
            feature_dir.mkdir(parents=True)
            criteria_path = feature_dir / "GATE-02-CRITERIA.md"
            criteria_path.write_text(
                "### T01#1\n\n- **criterion:** does the thing\n- **state:** `unverified`\n"
            )

            # An unrelated file the failing attempt itself left behind.
            leftover = feature_dir / "scratch-notes.txt"
            leftover.write_text("agent leftover\n")

            loop._clean_attempt_untracked(untracked_before, events_path)

            self.assertTrue(
                criteria_path.is_file(),
                "GATE-NN-CRITERIA.md must survive the attempt-reset cleanup",
            )
            self.assertIn("T01#1", criteria_path.read_text())
            self.assertFalse(
                leftover.exists(),
                "an unrelated file created after the snapshot must still be "
                "cleaned — the carve-out must not widen beyond the artifact",
            )

    def test_events_jsonl_carve_out_is_intact(self):
        """T05 criterion 6: the pre-existing `events.jsonl` carve-out still holds.

        T05 widened `_clean_attempt_untracked` to spare a second filename, so the
        carve-out it was widened alongside needs its own assertion — otherwise a
        later edit could drop the `events_path` branch with this module green.

        `events.jsonl` is created AFTER the snapshot on purpose: a file already in
        `untracked_before` is spared for a different reason, and asserting on that
        would pass whether or not the carve-out exists.
        """
        with _git_repo_no_sign() as root:
            events_path = root / "events.jsonl"
            untracked_before = loop.untracked_paths()

            events_path.write_text('{"event_type":"attempt_outcome"}\n')

            leftover = root / "scratch-notes.txt"
            leftover.write_text("agent leftover\n")

            loop._clean_attempt_untracked(untracked_before, events_path)

            self.assertTrue(
                events_path.is_file(),
                "events.jsonl must survive the attempt-reset cleanup — the "
                "carve-out predates T05 and T05 must not have broken it",
            )
            self.assertIn(
                "attempt_outcome", events_path.read_text(),
                "events.jsonl must survive with its contents intact, not be "
                "truncated or recreated empty",
            )
            self.assertFalse(
                leftover.exists(),
                "the events.jsonl carve-out must not spare unrelated files",
            )
