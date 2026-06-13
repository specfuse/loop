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


if __name__ == "__main__":
    unittest.main()
