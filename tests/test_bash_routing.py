#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0032 gate 2, WU-05 — route Windows gate commands through Git-Bash.

`verify()` spawns gate commands with `subprocess.Popen(command, shell=True, ...)`.
On Windows, `shell=True` hands the command to `cmd.exe`, which does not
understand the POSIX shell syntax (`&&`, `||`, globs, pipes) that real
`verification.yml` gate commands routinely use.

These tests assert: on win32, `verify()` spawns `[bash, "-c", command]` with
`shell=False`, where `bash` is resolved by `resolve_bash()` (preferring the
Git-for-Windows `bash.exe`); on POSIX, the existing `shell=True` string-spawn
path is unchanged; and when no Git-Bash can be found on Windows, the failure
names "Git for Windows" instead of silently falling back to `cmd.exe`.
"""

from __future__ import annotations

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
        "---\n\n# Bash-routing fixture\n\nbody\n"
    )
    ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md", "depends_on": []}
    return loop.load_wu(tmp, ref)


class TestWin32GateRoutesThroughBash(unittest.TestCase):

    def test_win32_gate_routes_through_bash(self):
        cfg = {"code": [{"name": "unit", "command": "pytest && exit 0"}]}
        fake_proc = mock.Mock()
        fake_proc.pid = 4321
        fake_proc.communicate.return_value = ("ok", None)
        fake_proc.returncode = 0

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "win32"), \
                 mock.patch.object(loop.subprocess, "Popen", return_value=fake_proc) as popen, \
                 mock.patch.object(loop, "resolve_bash", return_value=r"C:\Program Files\Git\bin\bash.exe"):
                ok, msg = loop.verify(wu, tmp, cfg=cfg)

            self.assertTrue(ok)
            call_args, call_kwargs = popen.call_args
            argv = call_args[0]
            self.assertEqual(argv[0].replace("\\", "/").rsplit("/", 1)[-1].lower(), "bash.exe")
            self.assertEqual(argv[1], "-c")
            self.assertEqual(argv[2], "pytest && exit 0")
            self.assertFalse(call_kwargs.get("shell", False))


class TestPosixGateStillUsesShellTrue(unittest.TestCase):

    def test_posix_gate_still_uses_shell_true(self):
        cfg = {"code": [{"name": "unit", "command": "pytest && exit 0"}]}
        fake_proc = mock.Mock()
        fake_proc.pid = 1234
        fake_proc.communicate.return_value = ("ok", None)
        fake_proc.returncode = 0

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "linux"), \
                 mock.patch.object(loop.subprocess, "Popen", return_value=fake_proc) as popen:
                ok, msg = loop.verify(wu, tmp, cfg=cfg)

            self.assertTrue(ok)
            call_args, call_kwargs = popen.call_args
            self.assertEqual(call_args[0], "pytest && exit 0")
            self.assertTrue(call_kwargs.get("shell") is True)
            self.assertTrue(call_kwargs.get("start_new_session") is True)


class TestNoBashFoundFailsLoud(unittest.TestCase):

    def test_no_bash_found_fails_loud(self):
        cfg = {"code": [{"name": "unit", "command": "pytest && exit 0"}]}

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "win32"), \
                 mock.patch.object(loop, "resolve_bash", return_value=None), \
                 mock.patch.object(loop.subprocess, "Popen") as popen:
                ok, msg = loop.verify(wu, tmp, cfg=cfg)

            self.assertFalse(ok)
            self.assertIn("Git for Windows", msg)
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
