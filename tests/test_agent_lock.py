#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the agent's own lock (.specfuse/.agent.lock).

Covers: second acquire raises while held, release-then-reacquire succeeds,
and independence from the driver's `.loop.lock`.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop._filelock import acquire_agent_lock, acquire_tree_lock


class TestAgentLock(unittest.TestCase):

    def test_second_acquire_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()

            fd1 = acquire_agent_lock(specfuse_dir)
            try:
                with self.assertRaises(BlockingIOError):
                    acquire_agent_lock(specfuse_dir)
            finally:
                fd1.close()

            fd2 = acquire_agent_lock(specfuse_dir)
            fd2.close()

    def test_independent_of_driver_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()

            agent_fd = acquire_agent_lock(specfuse_dir)
            try:
                driver_fd = acquire_tree_lock(specfuse_dir)
                driver_fd.close()
            finally:
                agent_fd.close()


if __name__ == "__main__":
    unittest.main()
