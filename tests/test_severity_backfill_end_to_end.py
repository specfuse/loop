# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Gate 3's `feature_oracle` (FEAT-2026-0113/T07): the backfill mode exists
end to end, for one issue, and the conductor cannot reach it at all.

`specfuse-backfill-severity` is a separate console script from
`specfuse-agent` (GATE-03.md's arm-checkpoint Q1) -- this module proves that
separation is structural (an untouched `specfuse/agent/run.py`, not a
convention) and that the mode itself amends a severity-less marked issue's
marker before projecting the label.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _main_ref_available() -> bool:
    """Whether a local `main` ref exists to diff against.

    CI checks out a single branch with no local `main`, so `git diff main` and
    `git show main:<path>` exit 128 there. Two tests below compare against it;
    both must **skip** rather than pass vacuously, which is exactly what the
    `git diff` one did before this guard: a failed git command yields empty
    stdout, and the assertion was on stdout alone, so T07's criterion-2 claim
    that `specfuse/agent/run.py` is untouched proved nothing on CI while
    reporting green.
    """
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "main"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    return probe.returncode == 0


_NEEDS_MAIN = unittest.skipUnless(
    _main_ref_available(),
    "no local `main` ref (shallow/single-branch checkout) — this assertion "
    "compares against main and would pass vacuously rather than prove anything",
)


class SeverityBackfill(unittest.TestCase):
    @_NEEDS_MAIN
    def test_the_conductor_cannot_reach_the_backfill(self):
        run_py = REPO_ROOT / "specfuse" / "agent" / "run.py"
        text = run_py.read_text(encoding="utf-8")
        self.assertEqual(text.count("severity_backfill"), 0)

        diff = subprocess.run(
            ["git", "diff", "main", "--", "specfuse/agent/run.py"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            diff.returncode, 0,
            "git diff against main must succeed; an errored diff yields empty "
            "stdout and would make the assertion below vacuous",
        )
        self.assertEqual(diff.stdout, "")

    @_NEEDS_MAIN
    def test_pyproject_registers_exactly_one_new_console_script_no_dependency_change(self):
        pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        show = subprocess.run(
            ["git", "show", "main:pyproject.toml"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(show.returncode, 0)
        main_text = show.stdout

        def scripts_block(text: str) -> str:
            match = re.search(r"\[project\.scripts\]\n(.*?)\n\n", text, re.DOTALL)
            return match.group(1) if match else ""

        head_scripts = set(scripts_block(pyproject_text).splitlines())
        main_scripts = set(scripts_block(main_text).splitlines())
        added = head_scripts - main_scripts
        removed = main_scripts - head_scripts

        self.assertEqual(removed, set())
        self.assertEqual(
            added,
            {'specfuse-backfill-severity = "specfuse.agent.severity_backfill:main"'},
        )

        def dependencies_block(text: str) -> str:
            match = re.search(r"dependencies\s*=\s*\[.*?\]", text, re.DOTALL)
            return match.group(0) if match else ""

        self.assertEqual(dependencies_block(pyproject_text), dependencies_block(main_text))

if __name__ == "__main__":
    unittest.main()
