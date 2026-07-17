#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0032 gate 2, WU-07 — resolve the bare `claude` CLI on Windows.

`dispatch()` invokes `CLAUDE_CMD` via `subprocess.run(cmd, ..., shell=False)`.
On Windows, `shell=False` calls `CreateProcess`, which does not consult
`PATHEXT` — a bare `claude` argv[0] does not resolve to the `claude.cmd` shim
the Windows install ships, so dispatch would fail with an opaque "file not
found" error before any agent runs.

These tests assert: on win32, `resolve_claude_cmd()` substitutes argv[0] with
`shutil.which("claude")`'s result (PATHEXT-aware) and dispatch's spawned argv[0]
reflects it; when `shutil.which` returns None on win32, dispatch fails loud
naming `claude` and PATH rather than spawning a bare `claude`; and on POSIX,
argv[0] stays the bare `claude` — no resolution occurs.
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
        "---\n\n# Claude-resolution fixture\n\nbody\n"
    )
    ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md", "depends_on": []}
    return loop.load_wu(tmp, ref)


class TestWin32ClaudeResolvedViaWhich(unittest.TestCase):

    def test_win32_claude_resolved_via_which(self):
        fake_proc = mock.Mock()
        fake_proc.stdout = '{"result": "ok"}'

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "win32"), \
                 mock.patch.object(
                     loop.shutil, "which",
                     return_value=r"C:\Users\me\AppData\Roaming\npm\claude.cmd") as which, \
                 mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
                loop.dispatch(wu, None, cost_tracking=True)

            which.assert_called_with("claude")
            call_args, _ = run.call_args
            argv = call_args[0]
            self.assertEqual(argv[0], r"C:\Users\me\AppData\Roaming\npm\claude.cmd")
            self.assertNotEqual(argv[0], "claude")


class TestWin32ClaudeMissingFailsLoud(unittest.TestCase):

    def test_win32_claude_missing_fails_loud(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "win32"), \
                 mock.patch.object(loop.shutil, "which", return_value=None), \
                 mock.patch.object(loop.subprocess, "run") as run:
                with self.assertRaises(SystemExit) as ctx:
                    loop.dispatch(wu, None, cost_tracking=True)

            self.assertIn("claude", str(ctx.exception))
            self.assertIn("PATH", str(ctx.exception))
            run.assert_not_called()


class TestPosixClaudeUnchanged(unittest.TestCase):

    def test_posix_claude_unchanged(self):
        fake_proc = mock.Mock()
        fake_proc.stdout = '{"result": "ok"}'

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            with mock.patch.object(loop.sys, "platform", "linux"), \
                 mock.patch.object(loop.shutil, "which") as which, \
                 mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
                loop.dispatch(wu, None, cost_tracking=True)

            which.assert_not_called()
            call_args, _ = run.call_args
            argv = call_args[0]
            self.assertEqual(argv[0], "claude")


if __name__ == "__main__":
    unittest.main()
