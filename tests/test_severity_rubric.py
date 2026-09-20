# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for read_severity_rubric: the repository's own severity labels win;
specfuse's DEFAULT_SEVERITY_RUBRIC only fills an empty namespace (#3352).

No test invokes the real gh binary: every test injects a stub runner.
"""

from __future__ import annotations

import json
import unittest

from specfuse.loop.agent_policy import SEVERITY_VALUES
from specfuse.loop.labels import (
    DEFAULT_SEVERITY_RUBRIC,
    read_severity_rubric,
)


class _Result:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _list_result(entries):
    payload = [
        {"name": name, "color": "ffffff", "description": description}
        for name, description in entries
    ]
    return _Result(returncode=0, stdout=json.dumps(payload))


class _StubRunner:
    """Records calls; returns canned results for `gh label list` / `gh label create`."""

    def __init__(self, entries=(), create_failures=(), raise_on=None):
        self.entries = list(entries)
        self.create_failures = set(create_failures)
        self.raise_on = raise_on or {}
        self.calls = []

    def __call__(self, args, cwd=None, check=False):
        self.calls.append(args)
        if args[:3] == ["gh", "label", "list"]:
            if "list" in self.raise_on:
                raise self.raise_on["list"]
            return _list_result(self.entries)
        if args[:3] == ["gh", "label", "create"]:
            name = args[3]
            if name in self.create_failures:
                return _Result(returncode=1, stderr=f"failed to create {name}")
            return _Result(returncode=0)
        raise AssertionError(f"unexpected call: {args}")


class SeverityRubric(unittest.TestCase):
    def test_rubric_reads_label_descriptions(self):
        runner = _StubRunner(
            entries=[
                ("severity:low", "Trivial, no user impact"),
                ("severity:high", "Blocks a core workflow"),
            ]
        )

        rubric = read_severity_rubric("/tmp/repo", runner=runner)

        self.assertEqual(
            rubric,
            {"low": "Trivial, no user impact", "high": "Blocks a core workflow"},
        )
        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(create_calls, [])

    def test_no_severity_labels_defined_returns_the_shipped_default(self):
        runner = _StubRunner(entries=[("gate-review", "unrelated")])

        rubric = read_severity_rubric("/tmp/repo", runner=runner)

        self.assertEqual(rubric, DEFAULT_SEVERITY_RUBRIC)
        self.assertEqual(set(rubric), set(SEVERITY_VALUES))

    def test_no_severity_labels_defined_provisions_the_four_defaults(self):
        runner = _StubRunner(entries=())

        read_severity_rubric("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        created_names = {c[3] for c in create_calls}
        self.assertEqual(created_names, {f"severity:{v}" for v in SEVERITY_VALUES})
        for call in create_calls:
            self.assertIn("--force", call)

    def test_repository_defining_its_own_scheme_gets_zero_create_calls(self):
        # `severity:major` alone is not in SEVERITY_VALUES, but its presence
        # still declares the repository's own namespace -- specfuse must not
        # provision anything alongside it. That is this test's actual subject
        # and it is unchanged.
        runner = _StubRunner(entries=[("severity:major", "Company-specific major")])

        rubric = read_severity_rubric("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(create_calls, [])

        # CHANGED BY #3355: the rubric was `{}` here, because `major` was
        # unreadable. The shipped alias table now resolves it to `high` using
        # the REPOSITORY'S OWN description -- no label is created and nothing
        # specfuse authored is introduced, so the non-interference contract
        # this test guards is intact.
        self.assertEqual(rubric, {"high": "Company-specific major"})

    def test_repository_scheme_never_gets_specfuse_authored_descriptions(self):
        # Renamed and re-asserted for #3355. `severity:major` now contributes a
        # `high` entry via the shipped alias table, so the rubric is larger than
        # it was -- but every DESCRIPTION in it is still the repository's own.
        # That is what "never gets specfuse-authored values" was protecting: the
        # keys are specfuse's published vocabulary by construction, since the
        # classifier answers in it; the prose must never be.
        runner = _StubRunner(
            entries=[
                ("severity:major", "Company-specific major"),
                ("severity:low", "Barely worth mentioning"),
            ]
        )

        rubric = read_severity_rubric("/tmp/repo", runner=runner)

        self.assertEqual(
            rubric,
            {"high": "Company-specific major", "low": "Barely worth mentioning"},
        )
        for value, description in rubric.items():
            with self.subTest(value=value):
                self.assertNotEqual(
                    description, DEFAULT_SEVERITY_RUBRIC[value],
                    "a repository that described this value must not have had "
                    "specfuse's wording substituted for its own",
                )

    def test_empty_description_gets_shipped_definition_for_that_value_only(self):
        runner = _StubRunner(
            entries=[
                ("severity:low", ""),
                ("severity:high", "Company definition of high"),
            ]
        )

        rubric = read_severity_rubric("/tmp/repo", runner=runner)

        self.assertEqual(rubric["low"], DEFAULT_SEVERITY_RUBRIC["low"])
        self.assertEqual(rubric["high"], "Company definition of high")

    def test_failed_label_creation_is_not_raised_and_rubric_stays_usable(self):
        runner = _StubRunner(entries=(), create_failures={"severity:critical"})

        rubric = read_severity_rubric("/tmp/repo", runner=runner)

        self.assertEqual(rubric, DEFAULT_SEVERITY_RUBRIC)

    def test_missing_gh_binary_returns_empty_dict(self):
        runner = _StubRunner(raise_on={"list": FileNotFoundError("gh not found")})

        self.assertEqual(read_severity_rubric("/tmp/repo", runner=runner), {})

    def test_nonzero_list_exit_returns_empty_dict(self):
        class _FailRunner(_StubRunner):
            def __call__(self, args, cwd=None, check=False):
                self.calls.append(args)
                if args[:3] == ["gh", "label", "list"]:
                    return _Result(returncode=1, stderr="gh: authentication required")
                raise AssertionError("should not reach create")

        runner = _FailRunner()

        self.assertEqual(read_severity_rubric("/tmp/repo", runner=runner), {})

    def test_unparseable_list_output_returns_empty_dict(self):
        class _BadJsonRunner(_StubRunner):
            def __call__(self, args, cwd=None, check=False):
                self.calls.append(args)
                if args[:3] == ["gh", "label", "list"]:
                    return _Result(returncode=0, stdout="not json")
                raise AssertionError("should not reach create")

        runner = _BadJsonRunner()

        self.assertEqual(read_severity_rubric("/tmp/repo", runner=runner), {})


if __name__ == "__main__":
    unittest.main()
