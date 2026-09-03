# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0042/T06: the live autofix-wiring run.

Exercises `specfuse.monitor.autofix_run.run_autofix` against a real scratch
issue in this repository through real `gh` calls -- the same live-reach
proof `tests/test_diagnosis_roundtrip_live.py` established for T01's
diagnosis contract (`LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]`
attributes the earlier failure to the command sandbox, not to `gh` itself;
unsandboxed, `gh auth status` and `gh issue` calls both exit 0).

This test decides `decline` (dial off) on purpose, not `fire`: firing a real
headless `fix-bug` session is a multi-minute, real-cost, real-PR-producing
action this suite must not repeat on every run. That live fire-to-completion
proof is `FEAT-2026-0042/T06`'s own one-time manual run, recorded in its
RESULT block with raw `gh` and `autofix_run` output quoted. This test's job
is narrower and repeatable: prove `run_autofix` reaches a real issue, reads
its real fingerprint marker and diagnosis comment, and returns a decision
grounded in what it read there -- not a stub.

Skips **explicitly**, by name, when `gh` is missing or unauthenticated (the
expected outcome inside the driver's normal sandboxed gate run) rather than
passing vacuously -- a silent pass here is exactly the failure mode this
work unit exists to remove.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from specfuse.monitor import autofix_invoke
from specfuse.monitor.autofix_run import run_autofix
from specfuse.monitor.diagnosis import Diagnosis, render
from tests._live import live_target

REPO_ROOT = Path(__file__).resolve().parent.parent
#: The scratch repository named by SPECFUSE_LIVE_REPO; set in setUpClass (#3223).
REPO: str | None = None
_MARKER_TITLE_TAG = "[FEAT-2026-0042/T06-live-test]"
_FINGERPRINT = "feat-2026-0042-t06-live-test-fixture"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _gh_ready() -> tuple[bool, str]:
    try:
        result = _run("auth", "status")
    except FileNotFoundError:
        return False, "gh binary not found on PATH"
    if result.returncode != 0:
        first_line = (result.stderr or result.stdout).strip().splitlines()[:1]
        reason = first_line[0] if first_line else "gh auth status failed"
        return False, f"gh unauthenticated: {reason}"
    return True, ""


class TestAutofixLive(unittest.TestCase):
    """Live run: create a scratch finding issue, post a real diagnosis
    comment via `gh`, and call `run_autofix` against it for real. Uses a
    dial-off decision so the run reaches `decide` and returns without
    invoking a headless `fix-bug` session -- the mechanism this test
    verifies is the read-decide path reaching GitHub live, not a fire."""

    scratch_issue_number: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        global REPO
        ready, reason, repo = live_target(gh_ready=_gh_ready)
        if not ready:
            raise unittest.SkipTest(f"autofix live run skipped: {reason}")
        REPO = repo

    def tearDown(self) -> None:
        if self.scratch_issue_number is not None:
            _run(
                "issue", "close", self.scratch_issue_number,
                "--repo", REPO,
                "--comment", "Closing: FEAT-2026-0042/T06 live test complete.",
            )

    def test_run_autofix_declines_a_real_dial_off_finding(self):
        diagnosis = Diagnosis(
            root_cause="scratch finding created by the T06 live test",
            evidence="posted via gh and read back by run_autofix in the same test run",
            candidate_fix="none: this is disposable test content",
            confidence=0.95,
            fix_scope="small",
        )
        body = (
            f"<!-- specfuse:finding fingerprint={_FINGERPRINT} -->\n\n"
            f"{_MARKER_TITLE_TAG} scratch finding created by the T06 live test. "
            "Safe to delete; closed by the same test run."
        )
        create = _run(
            "issue", "create",
            "--repo", REPO,
            "--title", f"{_MARKER_TITLE_TAG} scratch finding (safe to delete)",
            "--body", body,
            "--label", "monitoring-finding",
        )
        self.assertEqual(
            create.returncode, 0,
            f"gh issue create failed: stdout={create.stdout!r} stderr={create.stderr!r}",
        )
        issue_url = create.stdout.strip()
        issue_number = issue_url.rsplit("/", 1)[-1]
        self.assertTrue(issue_number.isdigit(), f"unexpected issue URL: {issue_url!r}")
        self.scratch_issue_number = issue_number

        comment = _run(
            "issue", "comment", issue_number, "--repo", REPO, "--body", render(diagnosis),
        )
        self.assertEqual(
            comment.returncode, 0,
            f"gh issue comment failed: stdout={comment.stdout!r} stderr={comment.stderr!r}",
        )

        def runner(args, check=True):
            return subprocess.run(args, capture_output=True, text=True, check=check, timeout=60)

        result = run_autofix(
            runner=runner,
            invoker=autofix_invoke,
            repo=REPO,
            finding_issue_number=int(issue_number),
            monitoring_config={
                "components": [{"name": "t06-live-test-component", "autofix": "off"}]
            },
            component="t06-live-test-component",
        )

        self.assertEqual(result.decision, "decline")
        self.assertEqual(result.reason, "dial_off")
        self.assertIsNone(result.outcome)

        view = _run("issue", "view", issue_number, "--repo", REPO, "--json", "body")
        self.assertEqual(view.returncode, 0)
        body_after = json.loads(view.stdout)["body"]
        self.assertNotIn(
            "specfuse:autofix-attempt", body_after,
            "a decline must not record an attempt marker",
        )

        close = _run(
            "issue", "close", issue_number, "--repo", REPO,
            "--comment", "Closing: FEAT-2026-0042/T06 live test complete.",
        )
        self.assertEqual(
            close.returncode, 0,
            f"gh issue close failed: stdout={close.stdout!r} stderr={close.stderr!r}",
        )
        self.scratch_issue_number = None  # closed here; tearDown has nothing to do


if __name__ == "__main__":
    unittest.main()
