# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0041/T04: the live `gh` round-trip.

`LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]` blamed `gh` itself and
banned it from every acceptance criterion; PLAN.md's investigation for this
feature shows the real cause is the command *sandbox* — unsandboxed, `gh
auth status` and `gh issue view` both exit 0 against the real API. This test
is the in-loop proof: it renders a `Diagnosis` through T01, posts it as a
real comment on a scratch issue this test creates, reads the comment back
through `gh`, parses it, and asserts equality — then closes the scratch
issue in the same run.

It skips **explicitly**, by name, when `gh` is missing or unauthenticated
(the expected outcome inside the driver's normal sandboxed gate run) rather
than passing vacuously — a silent pass here is exactly the failure mode
this work unit exists to remove. Run unsandboxed (as this feature's WU-04
attempt was), it reaches GitHub for real.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from specfuse.monitor.diagnosis import Diagnosis, parse, render
from tests._live import live_target

REPO_ROOT = Path(__file__).resolve().parent.parent
#: The scratch repository named by SPECFUSE_LIVE_REPO; set in setUpClass (#3223).
REPO: str | None = None
_MARKER_TITLE_TAG = "[FEAT-2026-0041/T04]"


def _run(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
    argv = ["gh", *args]
    if args and args[0] == "issue":
        # Never the current checkout: every issue call names the scratch
        # repository the operator opted into (#3223).
        assert REPO, "live test ran without SPECFUSE_LIVE_REPO"
        argv += ["--repo", REPO]
    return subprocess.run(
        argv,
        cwd=REPO_ROOT,
        input=input_text,
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


class TestDiagnosisRoundtripLive(unittest.TestCase):
    """Live round-trip: create a scratch issue, post a rendered `Diagnosis`
    as a real comment, read it back through `gh`, parse it, and assert it
    equals the one rendered — then close the scratch issue."""

    scratch_issue_number: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        global REPO
        ready, reason, repo = live_target(gh_ready=_gh_ready)
        if not ready:
            raise unittest.SkipTest(f"gh live round-trip skipped: {reason}")
        REPO = repo

    def tearDown(self) -> None:
        if self.scratch_issue_number is not None:
            _run(
                "issue",
                "close",
                self.scratch_issue_number,
                "--comment",
                "Closing: FEAT-2026-0041/T04 live round-trip test complete.",
            )

    def test_diagnosis_round_trips_through_a_real_gh_comment(self):
        diagnosis = Diagnosis(
            root_cause="scratch issue created by the T04 live round-trip test",
            evidence="posted, read back, and parsed via gh in the same test run",
            candidate_fix="none: this is disposable test content",
            confidence=0.33,
            fix_scope="small",
        )
        rendered = render(diagnosis)

        create = _run(
            "issue",
            "create",
            "--title",
            f"{_MARKER_TITLE_TAG} scratch issue — live round-trip test (safe to delete)",
            "--body",
            "Scratch issue created by the FEAT-2026-0041/T04 automated test. "
            "Created, commented on, and closed by the same test run. If this "
            "issue is open, it is residue from a killed attempt.",
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
            "issue", "comment", issue_number, "--body", rendered,
        )
        self.assertEqual(
            comment.returncode, 0,
            f"gh issue comment failed: stdout={comment.stdout!r} stderr={comment.stderr!r}",
        )

        view = _run(
            "issue", "view", issue_number, "--json", "comments",
        )
        self.assertEqual(
            view.returncode, 0,
            f"gh issue view failed: stdout={view.stdout!r} stderr={view.stderr!r}",
        )
        comments = json.loads(view.stdout)["comments"]
        self.assertTrue(comments, "no comments read back from the scratch issue")
        read_back_body = comments[-1]["body"]

        # Criterion 5: the marker survives GitHub's own body handling.
        parsed = parse(read_back_body)
        self.assertIsNotNone(parsed, "marker did not survive the gh round-trip")
        self.assertEqual(parsed, diagnosis)

        close = _run(
            "issue",
            "close",
            issue_number,
            "--comment",
            "Closing: FEAT-2026-0041/T04 live round-trip test complete.",
        )
        self.assertEqual(
            close.returncode, 0,
            f"gh issue close failed: stdout={close.stdout!r} stderr={close.stderr!r}",
        )
        self.scratch_issue_number = None  # closed here; tearDown has nothing to do


if __name__ == "__main__":
    unittest.main()
