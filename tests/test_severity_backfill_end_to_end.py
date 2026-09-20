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
import sys
import unittest

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class SeverityBackfill(unittest.TestCase):
    def test_the_conductor_cannot_reach_the_backfill(self):
        """The Q1 decision as a durable invariant, not a branch-scoped diff.

        This asserted `git diff main -- specfuse/agent/run.py` was empty —
        FEAT-2026-0113/T07's criterion 2, "this gate does not edit the
        conductor". That was true of **that gate** and is not an invariant of
        the repository: #3343 legitimately edits `run.py` to add the run-level
        failure breaker, and the assertion failed on work that has nothing to
        do with the backfill.

        A test comparing HEAD against `main` asserts a property of the branch,
        not of the code: it passes for the branch's whole life and then fails
        forever after merge, or — as here — fails the first time anyone
        touches the file for an unrelated reason.

        What survives is the claim worth keeping: the conductor holds no
        reference to the backfill, so no flag, branch or import in it can
        reach that mode. True on any branch, before or after any merge.
        """
        run_py = REPO_ROOT / "specfuse" / "agent" / "run.py"
        text = run_py.read_text(encoding="utf-8")
        self.assertEqual(
            text.count("severity_backfill"), 0,
            "specfuse-backfill-severity is a separate console script "
            "(GATE-03.md, arm-checkpoint Q1): a bulk issue-mutating mode must "
            "not be reachable from the binary an unattended run uses",
        )

    def test_pyproject_registers_the_backfill_console_script(self):
        """The Q1 arm-checkpoint decision, as a merge-independent invariant.

        This replaces a test that compared `[project.scripts]` against `main`
        and asserted the entry was *added*. That claim is only true while the
        feature is unmerged: once it lands on `main` the difference is empty
        and the test is permanently red. It was written for the arm checkpoint,
        where the question was "does this PR add exactly one script and smuggle
        no dependency with it" — a question with no meaning after the merge,
        because there is no baseline left to diff.

        What survives the merge is the decision itself: the backfill is its own
        console script pointing at its own module, and `specfuse-agent` is not
        it. The no-dependency-change half is not reconstructable here and was
        checked where it mattered, in review of the PR that introduced it.
        """
        pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r"\[project\.scripts\]\n(.*?)\n\n", pyproject_text, re.DOTALL)
        self.assertIsNotNone(match, "pyproject.toml declares no [project.scripts] block")
        scripts = dict(
            (line.split("=", 1)[0].strip(), line.split("=", 1)[1].strip().strip('"'))
            for line in match.group(1).splitlines()
            if "=" in line and not line.strip().startswith("#")
        )
        self.assertEqual(
            scripts.get("specfuse-backfill-severity"),
            "specfuse.agent.severity_backfill:main",
        )
        self.assertNotEqual(
            scripts.get("specfuse-agent"),
            "specfuse.agent.severity_backfill:main",
            "the conductor must not point at the backfill (GATE-03.md, Q1)",
        )
