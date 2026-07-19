#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unit tests for `reset_preserving_events` — FEAT-2026-0015 bug fix.

Bug context: `git reset --hard head_before` between WUs rolled events.jsonl
back to its last-committed state, silently dropping the prior WU's lifecycle
events that had been flushed-but-not-yet-committed. Surfaced
FEAT-2026-0015/T02: ran clean, events flushed post-squash, then T03 blocked
→ bare hard-reset wiped T02's events.

Fix: helper captures events.jsonl content, performs hard-reset, restores
content. Subsequent flush_events appends; subsequent commit_bookkeeping
captures the full history.
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
    """Minimal git repo with signing disabled (operator config-independent)."""
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
        # Sync barrier
        run("rev-parse", "HEAD")
        # cwd swap so loop's git() helper (which runs without -C) operates
        # on this tree
        prev_cwd = os.getcwd()
        try:
            os.chdir(root)
            yield root
        finally:
            os.chdir(prev_cwd)


class TestResetPreservingEventsHelper(unittest.TestCase):
    """Direct unit-level tests on reset_preserving_events()."""

    def test_preserves_flushed_but_uncommitted_events_content(self):
        """events.jsonl modifications since head_before survive the reset."""
        with _git_repo_no_sign() as root:
            # Setup: commit a baseline events.jsonl + README
            events_path = root / "events.jsonl"
            events_path.write_text("# committed baseline\n")
            subprocess.run(
                ["git", "-C", str(root), "add", "events.jsonl"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "baseline"],
                check=True, capture_output=True,
            )
            head_before = loop.git("rev-parse", "HEAD")

            # Simulate prior-WU events flushed post-squash, not yet committed:
            # events.jsonl on disk has new content vs head_before's commit.
            events_path.write_text(
                "# committed baseline\n"
                '{"correlation_id":"FEAT-PRIOR/T01","event_type":"task_completed"}\n'
            )
            # Simulate an agent's tracked-file edit that reset SHOULD wipe.
            readme = root / "README.md"
            readme.write_text("# AGENT-VANDALIZED\n")

            loop.reset_preserving_events(head_before, events_path)

            # Reset reverted the agent's tracked-file edit
            self.assertEqual(readme.read_text(), "# fixture\n")
            # But events.jsonl content survived (NOT rolled back to baseline)
            self.assertIn("FEAT-PRIOR/T01", events_path.read_text())

    def test_missing_events_file_does_not_crash(self):
        """If events.jsonl doesn't exist, helper still resets cleanly."""
        with _git_repo_no_sign() as root:
            head_before = loop.git("rev-parse", "HEAD")
            readme = root / "README.md"
            readme.write_text("# agent garbage\n")
            events_path = root / "events.jsonl"
            self.assertFalse(events_path.is_file())

            loop.reset_preserving_events(head_before, events_path)

            self.assertEqual(readme.read_text(), "# fixture\n")
            # events.jsonl still absent — nothing to preserve
            self.assertFalse(events_path.is_file())

    def test_preserves_multi_line_events_content(self):
        """Multi-line events.jsonl content fully preserved."""
        with _git_repo_no_sign() as root:
            events_path = root / "events.jsonl"
            events_path.write_text("# baseline\n")
            subprocess.run(
                ["git", "-C", str(root), "add", "events.jsonl"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "baseline"],
                check=True, capture_output=True,
            )
            head_before = loop.git("rev-parse", "HEAD")

            events_content = (
                "# baseline\n"
                '{"correlation_id":"X/T01","event_type":"task_started"}\n'
                '{"correlation_id":"X/T01","event_type":"task_completed"}\n'
                '{"correlation_id":"X/T02","event_type":"task_started"}\n'
            )
            events_path.write_text(events_content)
            (root / "README.md").write_text("# vandalized\n")

            loop.reset_preserving_events(head_before, events_path)

            self.assertEqual((root / "README.md").read_text(), "# fixture\n")
            self.assertEqual(events_path.read_text(), events_content)


class TestResetClearsAttemptUntracked(unittest.TestCase):
    """Issue #162: the reset must clear the failed attempt's untracked output.

    `git reset --hard` rolls back tracked content but leaves untracked files
    on disk. Because `untracked_before` is snapshotted once per WU (loop.py
    :3709) and the attempt loop runs beneath it (:3769), attempt 1's new
    files survive into attempt 2 and are indistinguishable from attempt 2's
    own work — `verify_files_changed` passes them and `squash_commit` commits
    them, so an attempt can pass on its predecessor's leftovers.

    The snapshot is the exclusion set: untracked paths present at dispatch
    are the operator's and must survive; anything else appeared during the
    attempt and must go.
    """

    def _snapshot(self):
        return loop.untracked_paths()

    def test_untracked_file_created_during_attempt_is_removed(self):
        with _git_repo_no_sign() as root:
            head_before = loop.git("rev-parse", "HEAD")
            before = self._snapshot()

            # The attempt creates a new deliverable, then fails.
            (root / "new.sh").write_text("#!/bin/sh\necho hi\n")

            loop.reset_preserving_events(
                head_before, root / "events.jsonl", untracked_before=before,
            )

            self.assertFalse(
                (root / "new.sh").exists(),
                "attempt's untracked output must not survive into the next "
                "attempt — it is what lets a later attempt hollow-pass",
            )

    def test_operator_untracked_file_survives(self):
        with _git_repo_no_sign() as root:
            # Operator WIP predates dispatch (#150's concern).
            (root / "scratch.md").write_text("my notes\n")
            head_before = loop.git("rev-parse", "HEAD")
            before = self._snapshot()
            self.assertIn("scratch.md", before)

            (root / "new.sh").write_text("#!/bin/sh\n")

            loop.reset_preserving_events(
                head_before, root / "events.jsonl", untracked_before=before,
            )

            self.assertTrue((root / "scratch.md").exists())
            self.assertEqual((root / "scratch.md").read_text(), "my notes\n")
            self.assertFalse((root / "new.sh").exists())

    def test_untracked_file_in_subdir_is_removed(self):
        with _git_repo_no_sign() as root:
            head_before = loop.git("rev-parse", "HEAD")
            before = self._snapshot()

            (root / "scripts").mkdir()
            (root / "scripts" / "check.sh").write_text("#!/bin/sh\n")

            loop.reset_preserving_events(
                head_before, root / "events.jsonl", untracked_before=before,
            )

            self.assertFalse((root / "scripts" / "check.sh").exists())

    def test_events_file_survives_even_when_untracked(self):
        """events.jsonl is driver-managed; the cleanup must never eat it.

        It can be untracked (first run on a fresh branch) and is by
        definition not in the pre-dispatch snapshot when the driver just
        created it — exactly the shape the cleanup deletes.
        """
        with _git_repo_no_sign() as root:
            head_before = loop.git("rev-parse", "HEAD")
            before = self._snapshot()

            events_path = root / "events.jsonl"
            events_path.write_text(
                '{"correlation_id":"X/T01","event_type":"task_started"}\n'
            )

            loop.reset_preserving_events(
                head_before, events_path, untracked_before=before,
            )

            self.assertTrue(events_path.is_file())
            self.assertIn("X/T01", events_path.read_text())

    def test_gitignored_file_survives(self):
        """Gitignored paths (e.g. the feature's `work/` dir) are out of scope.

        `untracked_paths` honors .gitignore, so ignored files never enter the
        delete set. Asserted explicitly because deleting them would destroy
        agent scratch space mid-run.
        """
        with _git_repo_no_sign() as root:
            (root / ".gitignore").write_text("work/\n")
            subprocess.run(
                ["git", "-C", str(root), "add", ".gitignore"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "ignore"],
                check=True, capture_output=True,
            )
            head_before = loop.git("rev-parse", "HEAD")
            before = self._snapshot()

            (root / "work").mkdir()
            (root / "work" / "scratch.txt").write_text("agent scratch\n")

            loop.reset_preserving_events(
                head_before, root / "events.jsonl", untracked_before=before,
            )

            self.assertTrue((root / "work" / "scratch.txt").exists())

    def test_omitting_snapshot_preserves_untracked(self):
        """Back-compat: no snapshot means no cleanup.

        An empty set is NOT the right default — it reads as "the operator had
        nothing untracked", which would make every existing call site delete
        the whole untracked working tree. Absence must stay inert.
        """
        with _git_repo_no_sign() as root:
            head_before = loop.git("rev-parse", "HEAD")
            (root / "new.sh").write_text("#!/bin/sh\n")

            loop.reset_preserving_events(head_before, root / "events.jsonl")

            self.assertTrue((root / "new.sh").exists())

    def test_tracked_rollback_still_happens_with_cleanup(self):
        """The cleanup must not displace the reset's original job."""
        with _git_repo_no_sign() as root:
            head_before = loop.git("rev-parse", "HEAD")
            before = self._snapshot()

            (root / "README.md").write_text("# AGENT-VANDALIZED\n")
            (root / "new.sh").write_text("#!/bin/sh\n")

            loop.reset_preserving_events(
                head_before, root / "events.jsonl", untracked_before=before,
            )

            self.assertEqual((root / "README.md").read_text(), "# fixture\n")
            self.assertFalse((root / "new.sh").exists())


if __name__ == "__main__":
    unittest.main()
