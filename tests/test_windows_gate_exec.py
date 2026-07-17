#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0032 gate 2, WU-08 — real-Windows oracle for gate execution.

Skipped everywhere except win32. On a real Windows runner (windows-latest,
Git for Windows preinstalled) this drives the driver's actual `verify()` code
path — no mocked `subprocess.Popen`, no mocked `sys.platform` — against a
fixture gate command that (a) uses a POSIX shell feature (`&&`) `cmd.exe`
cannot execute, proving T05's Git-Bash routing, and (b) begins with a
`python3` token, proving T06's interpreter normalization. A green PASS here
is the oracle that T05+T06 actually work end-to-end on native Windows, not
just in Linux-sandboxed mocked unit tests.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _write_wu(tmp: Path) -> object:
    path = tmp / "WU-T01.md"
    path.write_text(
        "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "---\n\n# Windows gate-exec fixture\n\nbody\n"
    )
    ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md", "depends_on": []}
    return loop.load_wu(tmp, ref)


@unittest.skipUnless(
    sys.platform == "win32",
    "real-Windows oracle: exercises Git-Bash routing + python3 normalization "
    "on an actual win32 host; not meaningful (or runnable) elsewhere.",
)
class TestWindowsGateExecutesThroughGitBash(unittest.TestCase):
    def test_posix_and_python3_gate_command_passes(self):
        cfg = {
            "code": [
                {
                    "name": "posix-and-python3",
                    "command": (
                        'python3 -c "import specfuse.loop.loop" '
                        "&& echo GATE_OK"
                    ),
                }
            ]
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = _write_wu(tmp)
            ok, msg = loop.verify(wu, tmp, cfg=cfg)

        self.assertTrue(ok, msg)
        self.assertIn("GATE_OK", msg)


if __name__ == "__main__":
    unittest.main()
