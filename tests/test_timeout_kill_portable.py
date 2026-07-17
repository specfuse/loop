#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0032 gate 1, WU-02 — gate-timeout kill must be cross-platform.

`verify()`'s subprocess.TimeoutExpired handler unconditionally called
`os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` — POSIX-only. On Windows
(`os.killpg`/`os.getpgid`/`signal.SIGKILL` absent) a timed-out gate raised
`AttributeError` instead of terminating the child process tree.

These tests assert the branch split: win32 spawns with
`CREATE_NEW_PROCESS_GROUP` and kills via `taskkill /T /F`; POSIX is unchanged
(`start_new_session=True`, `os.killpg(..., SIGKILL)`).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop

loop = load_loop()


def _write_wu(tmp: Path) -> object:
    path = tmp / "WU-T01.md"
    path.write_text(
        "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "---\n\n# Timeout-kill fixture\n\nbody\n"
    )
    ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md", "depends_on": []}
    return loop.load_wu(tmp, ref)


class TestWin32TimeoutKill(unittest.TestCase):

    def test_win32_timeout_uses_process_group_not_killpg(self):
        cfg = {"code": [{"name": "hang", "command": "sleep 999"}]}
        fake_proc = mock.Mock()
        fake_proc.pid = 4321
        fake_proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="sleep 999", timeout=900),
            ("", None),
        ]

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "win32"), \
                 mock.patch.object(loop.subprocess, "Popen", return_value=fake_proc) as popen, \
                 mock.patch.object(loop.os, "killpg", create=True) as killpg, \
                 mock.patch.object(loop.subprocess, "run") as run_mock:
                ok, msg = loop.verify(wu, tmp, cfg=cfg)

            killpg.assert_not_called()
            self.assertFalse(ok)
            self.assertIn("GATE TIMEOUT", msg)

            _, spawn_kwargs = popen.call_args
            self.assertNotIn("start_new_session", spawn_kwargs)
            self.assertIn("creationflags", spawn_kwargs)
            self.assertTrue(
                spawn_kwargs["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP
                if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
                else True
            )

            self.assertTrue(run_mock.called, "timeout kill must invoke taskkill /T /F")
            taskkill_call = run_mock.call_args
            taskkill_cmd = taskkill_call.args[0] if taskkill_call.args else taskkill_call.kwargs.get("args")
            self.assertIn("taskkill", taskkill_cmd)
            self.assertIn("/T", taskkill_cmd)
            self.assertIn("/F", taskkill_cmd)
            self.assertIn(str(fake_proc.pid), taskkill_cmd)


class TestPosixTimeoutKillUnchanged(unittest.TestCase):

    def test_posix_timeout_still_uses_killpg(self):
        cfg = {"code": [{"name": "hang", "command": "sleep 999"}]}
        fake_proc = mock.Mock()
        fake_proc.pid = 1234
        fake_proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="sleep 999", timeout=900),
            ("", None),
        ]

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "linux"), \
                 mock.patch.object(loop.subprocess, "Popen", return_value=fake_proc) as popen, \
                 mock.patch.object(loop.os, "killpg") as killpg, \
                 mock.patch.object(loop.os, "getpgid", return_value=9999) as getpgid:
                ok, msg = loop.verify(wu, tmp, cfg=cfg)

            self.assertFalse(ok)
            killpg.assert_called_once_with(9999, loop.signal.SIGKILL)
            getpgid.assert_called_once_with(fake_proc.pid)

            _, spawn_kwargs = popen.call_args
            self.assertTrue(spawn_kwargs.get("start_new_session") is True)
            self.assertNotIn("creationflags", spawn_kwargs)


if __name__ == "__main__":
    unittest.main()
