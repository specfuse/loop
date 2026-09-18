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

import json
import re
import subprocess
import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.severity_backfill import backfill_severity

_MARKED_BODY = "<!-- specfuse:triage category=bug confidence=high -->"


def _make_runner(*, issue_number: int, body: str):
    calls: list = []

    def runner(argv, check: bool = False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "list"]:
            payload = [
                {
                    "number": issue_number,
                    "body": body,
                    "labels": [{"name": "triage:bug"}],
                }
            ]
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
        if argv[:3] == ["gh", "issue", "edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner, calls


def _body_edit_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--body" in c]


def _label_add_calls(calls: list) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--add-label" in c]


class SeverityBackfill(unittest.TestCase):
    def test_marked_issue_without_severity_is_amended_then_labelled(self):
        runner, calls = _make_runner(issue_number=501, body=_MARKED_BODY)

        report = backfill_severity(runner, "o/r", 501, apply=True)

        self.assertTrue(report["amended"])

        body_calls = _body_edit_calls(calls)
        label_calls = _label_add_calls(calls)
        self.assertEqual(len(body_calls), 1)
        self.assertEqual(len(label_calls), 1)

        body_arg = body_calls[0][body_calls[0].index("--body") + 1]
        self.assertIn("severity=", body_arg)
        label_arg = label_calls[0][label_calls[0].index("--add-label") + 1]
        self.assertIn("severity:", label_arg)

        for call in (body_calls[0], label_calls[0]):
            self.assertIn(str(501), call)
            self.assertIn("o/r", call)

        body_index = calls.index(body_calls[0])
        label_index = calls.index(label_calls[0])
        self.assertLess(body_index, label_index)

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
        self.assertEqual(diff.stdout, "")

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

    def test_import_exposes_backfill_severity_and_the_named_stub(self):
        result = subprocess.run(
            [
                sys.executable, "-c",
                "from specfuse.agent.severity_backfill import backfill_severity",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        import specfuse.agent.severity_backfill as mod

        self.assertFalse(hasattr(mod, "_amend_marker"))


if __name__ == "__main__":
    unittest.main()
