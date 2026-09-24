# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Gate 3's `feature_oracle` (FEAT-2026-0113/T07): the backfill mode exists
end to end, for one issue, and the conductor cannot reach it at all.

GATE-03.md's Definition of done is a PAIR, and this module is the command
declared to ask it: a marked, severity-less issue is re-read under
`specfuse-backfill-severity --apply`, its marker amended with `severity=` and
the `severity:<value>` label projected AFTER it; and the same repository under a
conductor run with no flag is left untouched, asserted by argv.

For a while it asked only the second half (#3359). `T10H` removed
`backfill_severity`, the tracer-bullet function the first half drove, and
deleted the test with it -- authorised, and the *behaviour* stayed covered by
`tests/test_severity_backfill_apply.py`. What was lost is that the gate's own
feature-level question had no asserting command: this module passed with two
structural tests while the milestone it declares went unmeasured. Reversing the
write order made the whole run green.

The restored assertion is not a copy of the surviving unit test. That one hands
`apply_severity_backfill` its decisions directly; this one drives `main()`
through argv, so the listing, the classification and the write order are all in
the path being measured -- which is what makes it a *feature* oracle rather than
a second unit test.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from types import SimpleNamespace

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


class TheBackfillAmendsTheMarkerThenProjectsTheLabel(unittest.TestCase):
    """The first half of the Definition of done, driven through `main()`."""

    REPO = "acme-widget/example"
    MARKED_BODY = (
        "<!-- specfuse:triage category=bug confidence=high -->\n\n"
        "Something broke."
    )

    def _run(self):
        from specfuse.agent import severity_backfill

        calls: list = []

        def runner(argv, check: bool = False):
            calls.append(list(argv))
            if argv[:3] == ["gh", "label", "list"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps([
                    {"name": "severity:low", "description": "Low."},
                    {"name": "severity:medium", "description": "Medium."},
                    {"name": "severity:high", "description": "High."},
                    {"name": "severity:critical", "description": "Critical."},
                ]), stderr="")
            if argv[:3] == ["gh", "issue", "list"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps([{
                    "number": 501,
                    "title": "widget renders blank",
                    "body": self.MARKED_BODY,
                    "labels": [],
                }]), stderr="")
            if argv and argv[0] == "claude":
                answer = ("<!-- specfuse:triage category=bug confidence=high "
                          "severity=high -->")
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "result": answer, "total_cost_usd": 0.0, "usage": {},
                }), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        original = severity_backfill._default_runner
        severity_backfill._default_runner = runner
        try:
            rc = severity_backfill.main(["--repo", self.REPO, "--apply"])
        finally:
            severity_backfill._default_runner = original
        return rc, calls

    def test_the_marker_is_amended_and_the_label_projected_after_it(self):
        rc, calls = self._run()
        self.assertEqual(rc, 0)

        edits = [c for c in calls if c[:3] == ["gh", "issue", "edit"]]
        body_calls = [c for c in edits if "--body" in c]
        label_calls = [c for c in edits if "--add-label" in c]

        self.assertEqual(1, len(body_calls), "exactly one marker write")
        self.assertEqual(1, len(label_calls), "exactly one label write")

        amended = body_calls[0][body_calls[0].index("--body") + 1]
        self.assertIn("severity=high", amended)
        self.assertIn("category=bug", amended)
        self.assertIn("confidence=high", amended)

        self.assertEqual(
            "severity:high", label_calls[0][label_calls[0].index("--add-label") + 1])

        self.assertLess(
            calls.index(body_calls[0]), calls.index(label_calls[0]),
            "the marker is the authoritative record and the label a projection "
            "re-derived from it, so a run interrupted between the two leaves "
            "the record written and the projection missing — never the reverse",
        )

    def test_without_apply_the_same_issue_is_not_written_at_all(self):
        # The dry run is what an operator is told to reach for first; a mode
        # that writes without being asked would make that advice dangerous.
        from specfuse.agent import severity_backfill

        calls: list = []
        rc, all_calls = self._run()
        del rc, all_calls

        def runner(argv, check: bool = False):
            calls.append(list(argv))
            if argv[:3] == ["gh", "label", "list"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps([
                    {"name": "severity:high", "description": "High."},
                ]), stderr="")
            if argv[:3] == ["gh", "issue", "list"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps([{
                    "number": 501, "title": "t",
                    "body": self.MARKED_BODY, "labels": [],
                }]), stderr="")
            if argv and argv[0] == "claude":
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "result": "<!-- specfuse:triage category=bug "
                              "confidence=high severity=high -->",
                    "total_cost_usd": 0.0, "usage": {},
                }), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        original = severity_backfill._default_runner
        severity_backfill._default_runner = runner
        try:
            severity_backfill.main(["--repo", self.REPO])
        finally:
            severity_backfill._default_runner = original

        self.assertEqual(
            [], [c for c in calls if c[:3] == ["gh", "issue", "edit"]],
            "no --apply, no write",
        )
