#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0032 gate 2, WU-06 — normalize `python3` to the Windows interpreter.

Windows Python ships `python` / the `py` launcher, never `python3`. Target
repos hardcode `python3` in `verification.yml`, and the driver's own
smoke-import runner (`run_smoke_imports`) matches `python3 -c "from X import
Y"` lines. Both must be rewritten to a real Windows interpreter token before
spawn — on POSIX both stay untouched.

These tests assert: `normalize_interpreter()` rewrites a leading `python3`
token on win32 (leaving `python3` inside a quoted argument alone), is applied
at both the `verify()` gate-command site and the `run_smoke_imports` site, and
is a no-op on POSIX at both sites.
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
        "---\nid: FEAT-2026-9998/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "---\n\n# Interpreter-normalization fixture\n\nbody\n"
    )
    ref = {"id": "FEAT-2026-9998/T01", "file": "WU-T01.md", "depends_on": []}
    return loop.load_wu(tmp, ref)


class TestWin32GateCommandPython3Normalized(unittest.TestCase):

    def test_win32_gate_command_python3_normalized(self):
        cfg = {"code": [{"name": "unit", "command": 'python3 -m unittest discover'}]}
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
            call_args, _ = popen.call_args
            argv = call_args[0]
            spawned_command = argv[2]
            self.assertNotIn("python3", spawned_command)
            self.assertTrue(spawned_command.startswith("python "),
                            f"expected resolved interpreter, got: {spawned_command!r}")


class TestWin32SmokeImportPython3Normalized(unittest.TestCase):

    def test_win32_smoke_import_python3_normalized(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            with mock.patch.object(loop.sys, "platform", "win32"), \
                 mock.patch.object(loop.subprocess, "run") as run:
                run.return_value = mock.Mock(returncode=0, stderr="")
                ok, summary = loop.run_smoke_imports(
                    ['python3 -c "from sys import version"'], cwd,
                )

            self.assertTrue(ok)
            spawned_command = run.call_args[0][0]
            self.assertNotIn("python3", spawned_command)
            self.assertTrue(spawned_command.startswith("python "),
                            f"expected resolved interpreter, got: {spawned_command!r}")


class TestPosixPython3Unchanged(unittest.TestCase):

    def test_posix_python3_unchanged(self):
        cfg = {"code": [{"name": "unit", "command": 'python3 -m unittest discover'}]}
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
            call_args, _ = popen.call_args
            self.assertEqual(call_args[0], "python3 -m unittest discover")

        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            with mock.patch.object(loop.sys, "platform", "linux"), \
                 mock.patch.object(loop.subprocess, "run") as run:
                run.return_value = mock.Mock(returncode=0, stderr="")
                ok, summary = loop.run_smoke_imports(
                    ['python3 -c "from sys import version"'], cwd,
                )

            self.assertTrue(ok)
            spawned_command = run.call_args[0][0]
            self.assertEqual(spawned_command, 'python3 -c "from sys import version"')


if __name__ == "__main__":
    unittest.main()
