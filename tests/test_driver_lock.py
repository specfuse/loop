#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the working-tree exclusive lock in the loop driver.

Covers acquire_tree_lock() directly — no claude -p dispatch needed:
  (a) second acquire raises BlockingIOError while the first fd is open;
  (b) second acquire succeeds once the first fd is closed (process-exit sim).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


class TestAcquireTreeLock(unittest.TestCase):

    def test_second_acquire_raises_while_first_held(self):
        """Lock is exclusive: second flock raises BlockingIOError."""
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            fd1 = loop.acquire_tree_lock(specfuse_dir)
            try:
                with self.assertRaises(BlockingIOError):
                    loop.acquire_tree_lock(specfuse_dir)
            finally:
                fd1.close()

    def test_second_acquire_succeeds_after_first_released(self):
        """Lock is released on fd close (simulates process exit)."""
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            fd1 = loop.acquire_tree_lock(specfuse_dir)
            fd1.close()
            fd2 = loop.acquire_tree_lock(specfuse_dir)
            fd2.close()


if __name__ == "__main__":
    unittest.main()
