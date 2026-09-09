#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every spawn that runs project code strips the pin marker (FEAT-2026-0109).

The pin marker (`SPECFUSE_LOOP_PINNED_TREE`) is set by `_reexec_pinned` and is
meaningful to exactly one process: the driver. It is passed by environment, so
any child inherits it — and pin-conditional branches then behave as though the
child were the pinned driver.

**This has now been the same bug three times**, each time at a spawn site
nobody had thought about yet:

1. the gate runner — a pinned driver's gate subprocess saw the marker and
   `test_driver_edit_halts_before_next_dispatch` took the pinned branch;
2. agent dispatch — an agent runs the narrow tier in-session and hits the
   same branches;
3. the judge — `run_judge_session` spawned without `env=`, so a judge
   dispatched from a pinned driver observed three pin-conditional tests
   failing and **lowered a correct `met` to `not_met`** on evidence that was
   an artifact of its own environment.

Patching known sites one at a time is what produced three occurrences. This
test enumerates the spawn sites in `loop.py` and fails on any that runs project
code without an explicit `env=`, so the *next* one is caught by construction
rather than by a judge, a broad run, or a person noticing.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

LOOP_PY = Path(__file__).resolve().parent.parent / "specfuse" / "loop" / "loop.py"

#: Spawn sites that run git plumbing only. Git does not read the pin marker and
#: never executes project code, so these need no strip. Identified by the argv
#: literal starting with "git" on the spawn line or the line after it.
_GIT_ARGV = re.compile(r'\[\s*"git"|\["git",|\[\s*"git"\s*,')

#: Spawns that manage processes rather than running project code. `taskkill`
#: is the Windows half of the gate runner's timeout kill; it takes a PID and
#: executes nothing of the project's.
_PROCESS_MGMT_ARGV = re.compile(r'"taskkill"')


def _is_code_line(line: str) -> bool:
    """True when the spawn appears as code, not in a comment or docstring.

    `loop.py` discusses `subprocess.run(...)` in several docstrings — the
    shell=True rationale, the Windows CreateProcess note, the hang defences.
    Those are prose about spawning, not spawns.
    """
    stripped = line.strip()
    if stripped.startswith("#"):
        return False
    # Prose references the call in backticks or mid-sentence; real calls are
    # either a bare call or the right-hand side of an assignment.
    if "`" in line:
        return False
    return bool(re.search(r"(^\s*|=\s*|\(\s*)subprocess\.(run|Popen)\($", line.rstrip())
                or re.search(r"(^\s*|=\s*)subprocess\.(run|Popen)\(", line))


def _spawn_sites(source: str) -> list[tuple[int, str]]:
    """(line number, call text) for each real subprocess.run/Popen call."""
    lines = source.splitlines()
    sites = []
    for i, line in enumerate(lines):
        if "subprocess.run(" not in line and "subprocess.Popen(" not in line:
            continue
        if not _is_code_line(line):
            continue
        # Take the call and a small window after it: the argv and kwargs are
        # usually on the following lines.
        window = "\n".join(lines[i:i + 8])
        sites.append((i + 1, window))
    return sites


class TestEverySpawnStripsThePinMarker(unittest.TestCase):

    def test_non_git_spawns_pass_an_explicit_env(self):
        source = LOOP_PY.read_text()
        offenders = []
        for lineno, window in _spawn_sites(source):
            if _GIT_ARGV.search(window):
                continue                      # git plumbing: no project code
            if _PROCESS_MGMT_ARGV.search(window):
                continue                      # PID management, not project code
            if "env=" in window:
                continue                      # explicit env — strip is visible
            first = window.splitlines()[0].strip()
            offenders.append(f"loop.py:{lineno}: {first}")

        self.assertEqual(
            [], offenders,
            "these spawns run without an explicit `env=`, so they inherit the "
            "driver's pin marker and any pin-conditional branch they touch "
            "will behave as though they were the pinned driver. Pass "
            "`env=child_env_without_pin_marker()` (or an explicit env that "
            "drops it). Sites:\n  " + "\n  ".join(offenders))

    def test_the_three_known_sites_are_covered(self):
        """Belt and braces: the three sites this bug actually occurred at.

        The enumeration above is the general guard; this names the specific
        regressions so a future refactor that moves them cannot quietly drop
        the strip and still satisfy a heuristic.
        """
        source = LOOP_PY.read_text()
        for marker in (
            "popen_argv, stdin=subprocess.DEVNULL",      # the gate runner
            "cmd, input=prompt",                          # agent dispatch
            "build_judge_cmd(), input=prompt",            # the judge
        ):
            idx = source.find(marker)
            self.assertNotEqual(idx, -1, f"spawn site moved: {marker!r}")
            window = source[idx:idx + 400]
            self.assertIn(
                "child_env_without_pin_marker()", window,
                f"the spawn at {marker!r} no longer strips the pin marker")


if __name__ == "__main__":
    unittest.main()
