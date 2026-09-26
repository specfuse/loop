#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0116/T01 — the gate's walking skeleton, #3414 verbatim.

Two Maven reports whose tails read `FAIL: Tests run: …` and whose failing
lines name `WrittenSubtreeCensusTest.writtenSubtreesMatchesTheCommittedCensus`
and
`CleanScopeCoverageTest.everyDeclaredCleanScopeCoversItsOwnDirectoriesWithoutTouchingAnEarlierSibling`
respectively used to collapse onto the identical signature `Tests` — the
first word of the run-level summary line, not either failing test's name.
This pins the fix: `parse_gate_failure_signature` derives the signature from
the sorted set of failing test ids the new `extract_failing_tests` extractor
finds, not the first regex match in the report tail.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_MAVEN_REPORT_1 = """\
### tests: FAIL
```
$ ./mvnw -q test
[INFO] Running dev.acme.WrittenSubtreeCensusTest
[ERROR] WrittenSubtreeCensusTest.writtenSubtreesMatchesTheCommittedCensus:42 \
expected: <x> but was: <y>
[INFO] Tests run: 20, Failures: 1, Errors: 0, Skipped: 0
FAIL: Tests run: 20, Failures: 1, Errors: 0, Skipped: 0
```
"""

_MAVEN_REPORT_2 = """\
### tests: FAIL
```
$ ./mvnw -q test
[INFO] Running dev.acme.CleanScopeCoverageTest
[ERROR] CleanScopeCoverageTest.\
everyDeclaredCleanScopeCoversItsOwnDirectoriesWithoutTouchingAnEarlierSibling:77 \
expected: <x> but was: <y>
[INFO] Tests run: 8, Failures: 1, Errors: 0, Skipped: 0
FAIL: Tests run: 8, Failures: 1, Errors: 0, Skipped: 0
```
"""


class TestBug3414TwoMavenReportsNameTheirOwnTest(unittest.TestCase):
    def test_the_two_reports_get_different_signatures(self):
        _, sig1 = loop.parse_gate_failure_signature(_MAVEN_REPORT_1)
        _, sig2 = loop.parse_gate_failure_signature(_MAVEN_REPORT_2)
        self.assertNotEqual(sig1, sig2)

    def test_neither_signature_is_the_bare_run_level_word(self):
        _, sig1 = loop.parse_gate_failure_signature(_MAVEN_REPORT_1)
        _, sig2 = loop.parse_gate_failure_signature(_MAVEN_REPORT_2)
        self.assertNotEqual(sig1, "Tests")
        self.assertNotEqual(sig2, "Tests")

    def test_each_signature_names_its_own_failing_test(self):
        failure_class1, sig1 = loop.parse_gate_failure_signature(_MAVEN_REPORT_1)
        failure_class2, sig2 = loop.parse_gate_failure_signature(_MAVEN_REPORT_2)
        self.assertEqual(failure_class1, "tests")
        self.assertEqual(failure_class2, "tests")
        self.assertIn(
            "WrittenSubtreeCensusTest.writtenSubtreesMatchesTheCommittedCensus",
            sig1,
        )
        self.assertIn(
            "CleanScopeCoverageTest."
            "everyDeclaredCleanScopeCoversItsOwnDirectoriesWithoutTouching"
            "AnEarlierSibling",
            sig2,
        )


class TestExtractFailingTestsPerRunner(unittest.TestCase):
    def test_unittest(self):
        lines = ["FAIL: test_boot (tests.test_x.TestX)"]
        self.assertEqual(
            loop.extract_failing_tests(lines), ["tests.test_x.TestX.test_boot"],
        )

    def test_pytest(self):
        lines = ["FAILED tests/test_foo.py::test_bar - AssertionError"]
        self.assertEqual(
            loop.extract_failing_tests(lines), ["tests/test_foo.py::test_bar"],
        )

    def test_surefire_lowercase_package(self):
        lines = ["[ERROR]   dev.acme.FooTest.testBar:88 expected: <x> but was: <y>"]
        self.assertEqual(
            loop.extract_failing_tests(lines), ["dev.acme.FooTest.testBar"],
        )

    def test_vitest_jest(self):
        lines = ["FAIL src/App.test.tsx", "  ✕ renders correctly"]
        self.assertEqual(
            loop.extract_failing_tests(lines),
            ["renders correctly", "src/App.test.tsx"],
        )

    def test_dotnet(self):
        lines = ["  Failed MyNamespace.MyTests.TestSomething [10 ms]"]
        self.assertEqual(
            loop.extract_failing_tests(lines),
            ["MyNamespace.MyTests.TestSomething"],
        )

    def test_dart(self):
        lines = ["app_test.dart: some test description [E]"]
        self.assertEqual(
            loop.extract_failing_tests(lines),
            ["app_test.dart: some test description"],
        )

    def test_bats(self):
        lines = ["not ok 3 renders the header"]
        self.assertEqual(
            loop.extract_failing_tests(lines), ["renders the header"],
        )

    def test_sorted_and_deduplicated(self):
        lines = [
            "FAILED tests/test_b.py::test_b",
            "FAILED tests/test_a.py::test_a",
            "FAILED tests/test_a.py::test_a",
        ]
        self.assertEqual(
            loop.extract_failing_tests(lines),
            ["tests/test_a.py::test_a", "tests/test_b.py::test_b"],
        )


class TestFullLogFallback(unittest.TestCase):
    """A report tail that carries only the run-level summary."""

    _SUMMARY_ONLY = """\
### tests: FAIL
```
$ mvn test
[INFO] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0
FAIL: Tests run: 5, Failures: 1, Errors: 0, Skipped: 0
```
"""

    def test_yields_ids_from_the_full_log_when_the_path_exists(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8",
        )
        try:
            tmp.write("[ERROR]   FooTest.testBar:12 expected true\n")
            tmp.close()
            report = (
                self._SUMMARY_ONLY.rstrip()
                + f"\nfull output: {tmp.name}\n```\n"
            )
            failure_class, sig = loop.parse_gate_failure_signature(report)
            self.assertEqual(failure_class, "tests")
            self.assertEqual(sig, "FooTest.testBar")
        finally:
            os.unlink(tmp.name)

    def test_falls_to_the_existing_keyword_fallback_without_a_log_path(self):
        failure_class, sig = loop.parse_gate_failure_signature(self._SUMMARY_ONLY)
        self.assertEqual(failure_class, "tests")
        # The bare run-level word alone is never the signature (#3414); the
        # existing fallback still fires (it just has nothing better to key
        # off, since no failing test id is available anywhere).
        self.assertNotEqual(sig, "Tests")


class TestSignatureFromFailingTests(unittest.TestCase):
    def test_joins_with_comma_space(self):
        self.assertEqual(
            loop.signature_from_failing_tests(["a.Test.one", "b.Test.two"]),
            "a.Test.one, b.Test.two",
        )

    def test_truncates_with_a_stable_hash_suffix(self):
        ids = [f"pkg.ClassName.testMethodNumber{i:03d}" for i in range(10)]
        sig = loop.signature_from_failing_tests(ids)
        self.assertLessEqual(len(sig), 100)
        sig_again = loop.signature_from_failing_tests(list(ids))
        self.assertEqual(sig, sig_again)

    def test_different_long_sets_get_different_truncated_signatures(self):
        ids_a = [f"pkg.ClassName.testMethodNumber{i:03d}" for i in range(10)]
        ids_b = [f"pkg.ClassName.testMethodNumber{i:03d}" for i in range(10, 20)]
        sig_a = loop.signature_from_failing_tests(ids_a)
        sig_b = loop.signature_from_failing_tests(ids_b)
        self.assertGreater(len(", ".join(ids_a)), 100)
        self.assertNotEqual(sig_a, sig_b)


class TestAttemptOutcomeCarriesFailingTests(unittest.TestCase):
    _WU_BODY = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    _USAGE = {
        "duration_seconds": 1.0, "cost_usd": 0.0, "input_tokens": 0,
        "output_tokens": 0, "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }

    def _make_wu(self):
        import tempfile
        from pathlib import Path

        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(tmp.cleanup)
        wu_file = Path(tmp.name) / "WU-T01.md"
        wu_file.write_text("---\nid: FEAT-2026-9999/T01\n---\n\n# Test WU" + self._WU_BODY)
        return loop.WorkUnit(
            wu_id="FEAT-2026-9999/T01", file=wu_file, depends_on=[],
            type="implementation", model="sonnet", effort="medium",
            status="pending", attempts=0, title="Test WU", body=self._WU_BODY,
        )

    def test_defaults_to_empty_list(self):
        event = loop.emit_attempt_outcome(self._make_wu(), 1, "passed", self._USAGE)
        self.assertEqual(event["payload"]["failing_tests"], [])

    def test_carries_the_declared_failing_tests(self):
        event = loop.emit_attempt_outcome(
            self._make_wu(), 1, "failed", self._USAGE,
            failure_class="tests", failure_signature="foo.Bar.baz",
            failing_tests=["foo.Bar.baz"],
        )
        self.assertEqual(event["payload"]["failing_tests"], ["foo.Bar.baz"])


if __name__ == "__main__":
    unittest.main()
