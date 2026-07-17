#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests that the driver's working-tree lock is portable off POSIX fcntl.

Covers: (a) `specfuse.loop.loop` imports even with `fcntl` unavailable;
(b) the POSIX branch calls `fcntl.flock` with LOCK_EX | LOCK_NB; (c) the
Windows branch calls `msvcrt.locking` and never touches `fcntl`.
"""

from __future__ import annotations

import builtins
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class TestLoopImportsWithFcntlAbsent(unittest.TestCase):

    def test_loop_imports_with_fcntl_absent(self):
        real_import = builtins.__import__

        def blocking_import(name, *args, **kwargs):
            if name == "fcntl":
                raise ImportError("no module named fcntl (simulated)")
            return real_import(name, *args, **kwargs)

        saved_modules = {
            name: mod
            for name, mod in sys.modules.items()
            if name == "fcntl" or name.startswith("specfuse.loop")
        }
        for name in list(saved_modules):
            del sys.modules[name]

        try:
            with mock.patch("sys.platform", "linux"), \
                 mock.patch.object(builtins, "__import__", blocking_import):
                import specfuse.loop.loop  # noqa: F401
        finally:
            for name in list(sys.modules):
                if name == "fcntl" or name.startswith("specfuse.loop"):
                    del sys.modules[name]
            sys.modules.update(saved_modules)


class TestPosixUsesFcntlFlock(unittest.TestCase):

    def test_posix_uses_fcntl_flock(self):
        import specfuse.loop._filelock as filelock

        mock_fcntl = mock.MagicMock()
        mock_fcntl.LOCK_EX = 2
        mock_fcntl.LOCK_NB = 4

        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            with mock.patch.object(filelock, "sys") as mock_sys, \
                 mock.patch.dict(sys.modules, {"fcntl": mock_fcntl}):
                mock_sys.platform = "linux"
                fd = filelock.acquire_tree_lock(specfuse_dir)
                fd.close()
                mock_fcntl.flock.assert_called_once()
                args = mock_fcntl.flock.call_args[0]
                self.assertEqual(args[1], 2 | 4)


class TestWin32BranchUsesMsvcrtLocking(unittest.TestCase):

    def test_win32_branch_uses_msvcrt_locking(self):
        import specfuse.loop._filelock as filelock

        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            mock_msvcrt = mock.MagicMock()
            mock_msvcrt.LK_NBLCK = 1
            with mock.patch.object(filelock, "sys") as mock_sys, \
                 mock.patch.dict(sys.modules, {"msvcrt": mock_msvcrt}):
                mock_sys.platform = "win32"
                fd = filelock.acquire_tree_lock(specfuse_dir)
                fd.close()
                mock_msvcrt.locking.assert_called_once()
                self.assertNotIn("fcntl", str(mock_msvcrt.mock_calls))


if __name__ == "__main__":
    unittest.main()
