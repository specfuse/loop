#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`gh pr checks` is asked for fields that exist — issue #1826.

`pr_ci_conclusion` requested `--json conclusion`. That field does not exist:
`gh` exits 1 with `Unknown JSON field: "conclusion"`, so the function returned
`unknown` on every pull request and `evaluate_merge_guardrails` declined every
time. `rules.bugs.automerge` had never been able to fire.

The real shape, captured from `gh pr checks --json name,state,bucket`:

    [{"bucket":"pass","name":"smoke-test","state":"SUCCESS"}, ...]

`bucket` is gh's own normalisation — `pass` / `fail` / `pending` / `skipping` /
`cancel` — and is what this module reads.

**Why these tests are shaped this way.** #1786's tests injected a stub returning
`[{"conclusion": "SUCCESS"}]`, a shape assumed rather than observed; the stub
agreed with the code and both disagreed with `gh`, so a green run of the suite
proved nothing. `TestArgvUsesOnlyRealGhFields` below pins the requested field
names against `gh pr checks --help`'s own list, which is the one assertion that
would have caught the original defect.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from types import SimpleNamespace

from specfuse.loop.bug_lane_run import pr_ci_conclusion

#: Verbatim from `gh pr checks --json` with no value, gh version 2.x.
_GH_CHECK_FIELDS = frozenset({
    "bucket", "completedAt", "description", "event",
    "link", "name", "startedAt", "state", "workflow",
})


def _rows(*buckets):
    return SimpleNamespace(
        returncode=0,
        stdout=json.dumps([
            {"bucket": b, "name": f"check-{i}", "state": b.upper()}
            for i, b in enumerate(buckets)
        ]),
        stderr="",
    )


class _Runner:
    def __init__(self, results):
        self._results = list(results)
        self.calls: list[list] = []

    def __call__(self, args, check=False):
        self.calls.append(list(args))
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _sleeper(clock):
    def _sleep(seconds):
        clock.now += seconds
    return _sleep


def _conclude(runner, **kw):
    clock = _Clock()
    kw.setdefault("deadline_seconds", 60)
    return pr_ci_conclusion(
        runner, "acme/widget", 1, sleep=_sleeper(clock), clock=clock, **kw,
    )


class TestArgvUsesOnlyRealGhFields(unittest.TestCase):
    """The assertion that would have caught the original defect."""

    def test_requested_json_fields_all_exist(self):
        runner = _Runner([_rows("pass")])
        _conclude(runner)
        argv = runner.calls[0]
        self.assertIn("--json", argv)
        requested = argv[argv.index("--json") + 1].split(",")
        unknown = [f for f in requested if f not in _GH_CHECK_FIELDS]
        self.assertEqual(
            unknown, [], f"requests field(s) gh pr checks does not have: {unknown}",
        )

    def test_conclusion_is_never_requested(self):
        runner = _Runner([_rows("pass")])
        _conclude(runner)
        self.assertNotIn("conclusion", " ".join(runner.calls[0]))


class TestBucketMapping(unittest.TestCase):

    def test_all_pass_is_success(self):
        self.assertEqual(_conclude(_Runner([_rows("pass", "pass")])), "success")

    def test_a_failing_bucket_is_not_success(self):
        self.assertNotEqual(_conclude(_Runner([_rows("pass", "fail")])), "success")

    def test_skipping_alongside_pass_is_success(self):
        """A skipped check is not a failure — a required check that did not
        need to run must not block a merge forever."""
        self.assertEqual(_conclude(_Runner([_rows("pass", "skipping")])), "success")

    def test_cancelled_is_not_success(self):
        self.assertNotEqual(_conclude(_Runner([_rows("pass", "cancel")])), "success")

    def test_pending_then_pass_waits_and_reads_success(self):
        runner = _Runner([_rows("pending", "pass"), _rows("pass", "pass")])
        self.assertEqual(_conclude(runner), "success")
        self.assertGreater(len(runner.calls), 1, "did not wait on a pending bucket")


class TestReadabilityEdgesFromRealGhBehaviour(unittest.TestCase):
    """`gh pr checks` exits non-zero when checks FAIL, not only when the
    invocation is bad — so exit code alone cannot mean 'unreadable'."""

    def test_non_zero_exit_with_parseable_failing_rows_is_not_success(self):
        result = SimpleNamespace(
            returncode=1,
            stdout=json.dumps([{"bucket": "fail", "name": "x", "state": "FAILURE"}]),
            stderr="",
        )
        self.assertNotEqual(_conclude(_Runner([result])), "success")

    def test_non_zero_exit_with_parseable_passing_rows_is_success(self):
        """gh exits 8 when some checks are skipped; the rows still parse and
        still say pass. Treating exit code as authoritative loses that."""
        result = SimpleNamespace(
            returncode=8,
            stdout=json.dumps([{"bucket": "pass", "name": "x", "state": "SUCCESS"}]),
            stderr="",
        )
        self.assertEqual(_conclude(_Runner([result])), "success")

    def test_unparseable_output_is_unknown(self):
        result = SimpleNamespace(returncode=1, stdout='Unknown JSON field: "x"', stderr="")
        self.assertEqual(_conclude(_Runner([result])), "unknown")

    def test_no_checks_registered_yet_waits_then_gives_up(self):
        """An empty row list on a fresh PR is pending, not unreadable — but it
        must still be bounded. Reports the public `"pending"` at the deadline
        (#3177/FEAT-2026-0108/T04), not `"unknown"`."""
        empty = SimpleNamespace(returncode=0, stdout="[]", stderr="")
        self.assertEqual(_conclude(_Runner([empty]), deadline_seconds=30), "pending")

    def test_raising_runner_is_unknown(self):
        class _Boom:
            def __call__(self, args, check=False):
                raise OSError("gh exploded")

        self.assertEqual(_conclude(_Boom()), "unknown")


class TestAgainstRealGh(unittest.TestCase):
    """Compares the field list this module requests against the live `gh`
    binary. Skipped where gh is absent; this is the only test here that can
    notice gh changing its schema."""

    def test_requested_fields_are_accepted_by_the_installed_gh(self):
        try:
            probe = subprocess.run(
                ["gh", "pr", "checks", "--json"],
                capture_output=True, text=True, timeout=20, check=False,
            )
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            self.skipTest(f"gh unavailable: {exc}")

        advertised = probe.stdout + probe.stderr
        if "bucket" not in advertised:
            self.skipTest("gh did not advertise its --json fields as expected")

        runner = _Runner([_rows("pass")])
        _conclude(runner)
        argv = runner.calls[0]
        for field in argv[argv.index("--json") + 1].split(","):
            self.assertIn(
                field, advertised,
                f"`gh pr checks` does not advertise a {field!r} field",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
