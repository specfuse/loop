# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for provision_labels: idempotent, best-effort, never-raising label creation.

No test invokes the real gh binary: every test injects a stub runner.
"""

from __future__ import annotations

import json
import unittest

from specfuse.loop.labels import LABEL_REGISTRY, provision_labels


class _Result:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _list_result(names):
    payload = [{"name": n, "color": "ffffff", "description": ""} for n in names]
    return _Result(returncode=0, stdout=json.dumps(payload))


class _StubRunner:
    """Records calls; returns canned results for `gh label list` / `gh label create`."""

    def __init__(self, existing_names=(), create_failures=(), raise_on=None):
        self.existing_names = set(existing_names)
        self.create_failures = set(create_failures)
        self.raise_on = raise_on or {}
        self.calls = []

    def __call__(self, args, cwd=None, check=False):
        self.calls.append(args)
        if args[:3] == ["gh", "label", "list"]:
            if "list" in self.raise_on:
                raise self.raise_on["list"]
            return _list_result(self.existing_names)
        if args[:3] == ["gh", "label", "create"]:
            name = args[3]
            if name in self.create_failures:
                return _Result(returncode=1, stderr=f"failed to create {name}")
            return _Result(returncode=0)
        raise AssertionError(f"unexpected call: {args}")


class TestProvisionLabels(unittest.TestCase):
    def test_missing_gh_binary_returns_report_without_raising(self):
        runner = _StubRunner(raise_on={"list": FileNotFoundError("gh not found")})
        report = provision_labels("/tmp/does-not-matter", runner=runner)
        self.assertTrue(report.skipped)
        self.assertEqual(report.created, [])
        self.assertEqual(report.failed, [])

    def test_no_existing_labels_creates_every_registry_entry(self):
        runner = _StubRunner(existing_names=())
        report = provision_labels("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(len(create_calls), len(LABEL_REGISTRY))

        by_name = {c[3]: c for c in create_calls}
        for spec in LABEL_REGISTRY:
            call = by_name[spec.name]
            self.assertIn(spec.colour, call)
            self.assertIn(spec.description, call)

        self.assertEqual(sorted(report.created), sorted(s.name for s in LABEL_REGISTRY))

    def test_all_labels_already_present_creates_nothing(self):
        runner = _StubRunner(existing_names=[s.name for s in LABEL_REGISTRY])
        report = provision_labels("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(create_calls, [])
        self.assertEqual(sorted(report.already_present), sorted(s.name for s in LABEL_REGISTRY))
        self.assertEqual(report.created, [])

    def test_subset_present_creates_only_missing(self):
        present = [LABEL_REGISTRY[0].name, LABEL_REGISTRY[1].name]
        missing = [s.name for s in LABEL_REGISTRY[2:]]
        runner = _StubRunner(existing_names=present)
        report = provision_labels("/tmp/repo", runner=runner)

        self.assertEqual(sorted(report.created), sorted(missing))
        self.assertEqual(sorted(report.already_present), sorted(present))

    def test_no_call_ever_passes_force_flag(self):
        runner = _StubRunner(existing_names=())
        provision_labels("/tmp/repo", runner=runner)
        for call in runner.calls:
            self.assertNotIn("--force", call)

    def test_label_with_different_colour_or_description_counts_as_present(self):
        # The stub's `gh label list` only ever reports names (real gh output
        # would include the differing colour/description); presence is keyed
        # on name alone, so a differing colour/description never re-triggers
        # create or update.
        runner = _StubRunner(existing_names=[s.name for s in LABEL_REGISTRY])
        provision_labels("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        edit_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "edit"]]
        self.assertEqual(create_calls, [])
        self.assertEqual(edit_calls, [])

    def test_filenotfound_on_list_returns_report_and_does_not_raise(self):
        runner = _StubRunner(raise_on={"list": FileNotFoundError()})
        report = None
        try:
            report = provision_labels("/tmp/repo", runner=runner)
        except Exception as exc:  # noqa: BLE001 - pragma: no cover - failure path
            self.fail(f"provision_labels raised: {exc}")
        self.assertTrue(report.skipped)

    def test_authentication_failure_returns_report_and_does_not_raise(self):
        class _AuthFailRunner(_StubRunner):
            def __call__(self, args, cwd=None, check=False):
                self.calls.append(args)
                if args[:3] == ["gh", "label", "list"]:
                    return _Result(returncode=1, stderr="gh: authentication required")
                raise AssertionError("should not reach create")

        runner = _AuthFailRunner()
        report = provision_labels("/tmp/repo", runner=runner)
        self.assertTrue(report.skipped)
        self.assertEqual(report.created, [])
        self.assertEqual(report.failed, [])

    def test_not_a_git_repo_or_non_github_remote_returns_report_and_does_not_raise(self):
        class _NotGitRunner(_StubRunner):
            def __call__(self, args, cwd=None, check=False):
                self.calls.append(args)
                if args[:3] == ["gh", "label", "list"]:
                    return _Result(returncode=1, stderr="not a git repository")
                raise AssertionError("should not reach create")

        runner = _NotGitRunner()
        report = provision_labels("/tmp/repo", runner=runner)
        self.assertTrue(report.skipped)
        self.assertEqual(report.created, [])
        self.assertEqual(report.failed, [])

    def test_single_create_failure_does_not_abandon_remaining_labels(self):
        failing = LABEL_REGISTRY[0].name
        runner = _StubRunner(existing_names=(), create_failures={failing})
        report = provision_labels("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(len(create_calls), len(LABEL_REGISTRY))

        self.assertIn(failing, report.failed)
        expected_created = sorted(s.name for s in LABEL_REGISTRY if s.name != failing)
        self.assertEqual(sorted(report.created), expected_created)

    def test_list_raising_generic_exception_returns_report_and_does_not_raise(self):
        runner = _StubRunner(raise_on={"list": RuntimeError("network blip")})
        report = provision_labels("/tmp/repo", runner=runner)
        self.assertTrue(report.skipped)
        self.assertIn("network blip", report.reason)

    def test_malformed_list_output_returns_report_and_does_not_raise(self):
        class _BadJsonRunner(_StubRunner):
            def __call__(self, args, cwd=None, check=False):
                self.calls.append(args)
                if args[:3] == ["gh", "label", "list"]:
                    return _Result(returncode=0, stdout="not json")
                raise AssertionError("should not reach create")

        runner = _BadJsonRunner()
        report = provision_labels("/tmp/repo", runner=runner)
        self.assertTrue(report.skipped)

    def test_create_raising_exception_marks_label_failed_and_continues(self):
        class _RaisingCreateRunner(_StubRunner):
            def __call__(self, args, cwd=None, check=False):
                self.calls.append(args)
                if args[:3] == ["gh", "label", "list"]:
                    return _list_result(())
                if args[:3] == ["gh", "label", "create"]:
                    if args[3] == LABEL_REGISTRY[0].name:
                        raise RuntimeError("boom")
                    return _Result(returncode=0)
                raise AssertionError(f"unexpected call: {args}")

        runner = _RaisingCreateRunner()
        report = provision_labels("/tmp/repo", runner=runner)

        create_calls = [c for c in runner.calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(len(create_calls), len(LABEL_REGISTRY))
        self.assertIn(LABEL_REGISTRY[0].name, report.failed)
        self.assertEqual(
            sorted(report.created),
            sorted(s.name for s in LABEL_REGISTRY[1:]),
        )

    def test_provision_labels_importable(self):
        from specfuse.loop.labels import provision_labels as fn

        self.assertTrue(callable(fn))


if __name__ == "__main__":
    unittest.main()
