"""Issue #3293 part 2 — a failed Maven `tests` gate must reach the retry, and
`events.jsonl`, with the failing test's name, and the gate's full output must
survive somewhere an operator can read it.

Observed on the generator (FEAT-2026-0167/T01, T02): each attempt failed on
one real surefire failure, and the whole record was a 500-byte excerpt whose
head was the echoed `$ ./mvnw ...` command line (it contains `FAIL`, so it
passed the keyword filter) and whose tail was the driver's own NO VERDICT
note. On a real 105 MB log, `_VERDICT_RE` matched 2,285 application log
lines (`Found 0 errors, 0 warnings`, the ruff pattern) and the pinned block
carried no test. A Maven build-level failure (`[ERROR] Failed to execute
goal ...`) matched nothing at all. And the gate's stdout was dropped after
15 lines, so the only way to learn the test name was to read
`target/surefire-reports` by hand.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_APP_LOG = ("[INFO] 12:00:01 INFO dev.acme.generator.Project - Arazzo validation "
            "completed. Found 0 errors, 0 warnings\n")

_SUREFIRE_FAILURE = (
    "[INFO] -------------------------------------------------------\n"
    "[INFO]  T E S T S\n"
    "[INFO] -------------------------------------------------------\n"
    "[INFO] Running dev.acme.DateSampleRegressionTest\n"
    "[ERROR] ANonDateFakerSampleIsLeftAlone(dev.acme.DateSampleRegressionTest)  "
    "Time elapsed: 0.031 s  <<< FAILURE!\n"
    "org.opentest4j.AssertionFailedError: expected: <x> but was: <y>\n"
    "[INFO] Tests run: 12, Failures: 1, Errors: 0, Skipped: 0\n"
    "[ERROR] Failures: \n"
    "[ERROR]   DateSampleRegressionTest.ANonDateFakerSampleIsLeftAlone:88 "
    "expected: <x> but was: <y>\n"
    "[INFO] \n"
    "[ERROR] Tests run: 12, Failures: 1, Errors: 0, Skipped: 0\n"
    "[INFO] BUILD FAILURE\n"
    "[ERROR] Failed to execute goal org.apache.maven.plugins:"
    "maven-surefire-plugin:3.2.5:test (default-test) on project generator: "
    "There are test failures.\n"
    "[ERROR] \n"
    "[ERROR] To see the full stack trace of the errors, re-run Maven with "
    "the -e switch.\n"
    "[ERROR] Re-run Maven using the -X switch to enable full debug logging.\n"
    "[ERROR] \n"
    "[ERROR] For more information about the errors and possible solutions, "
    "please read the following articles:\n"
    "[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/"
    "MojoFailureException\n"
)

_MAVEN_LOG = _APP_LOG * 300 + _SUREFIRE_FAILURE + _APP_LOG * 40

_CLEAN_PLUGIN_FAILURE = (
    "[INFO] Scanning for projects...\n"
    "[INFO] --- clean:3.2.0:clean (default-clean) @ generator ---\n"
    "[INFO] Deleting /work/generator/target\n"
    "[INFO] BUILD FAILURE\n"
    "[ERROR] Failed to execute goal org.apache.maven.plugins:"
    "maven-clean-plugin:3.2.0:clean (default-clean) on project generator: "
    "Failed to clean project: Failed to delete /work/generator/target/classes\n"
    "[ERROR] -> [Help 1]\n"
) + "[ERROR] [Help 1] http://cwiki.apache.org/x\n" * 20


class TestEchoedCommandIsNotTheExcerpt(unittest.TestCase):

    def test_the_command_line_is_excluded_from_candidates(self):
        report = (
            "### tests: FAIL\n"
            "$ ./mvnw clean test || { grep -rhE '<<< (FAILURE|ERROR)' "
            "target/surefire-reports/*.txt | sed 's/^/FAIL: /'; }\n"
            "[ERROR]   DateSampleRegressionTest.ANonDateFakerSampleIsLeftAlone:88 "
            "expected: <x> but was: <y>\n"
        )
        excerpt = loop.extract_failure_excerpt(report, max_chars=500)
        self.assertNotIn("./mvnw", excerpt,
                         "a command that mentions FAIL in its own text is not "
                         "the excerpt")
        self.assertIn("ANonDateFakerSampleIsLeftAlone", excerpt)


class TestSurefirePinningIsExclusive(unittest.TestCase):

    def test_application_log_lines_do_not_crowd_out_the_failing_test(self):
        lines = loop.select_gate_report_lines(_MAVEN_LOG, window=15)
        joined = "\n".join(lines)
        self.assertIn("DateSampleRegressionTest.ANonDateFakerSampleIsLeftAlone:88",
                      joined, "the actionable [ERROR]   Class.method line is pinned")
        self.assertIn("Tests run: 12, Failures: 1", joined)
        marker = next(i for i, ln in enumerate(lines) if "elided" in ln)
        pinned = "\n".join(lines[:marker])
        self.assertNotIn("Found 0 errors", pinned,
                         "once surefire markers are seen, the ruff-shaped "
                         "application log lines are not verdicts (the "
                         "positional tail after the marker is kept as ever)")
        self.assertNotIn(loop._NO_VERDICT_NOTE, lines)

    def test_the_signature_names_the_test(self):
        report = "### tests: FAIL\n```\n$ ./mvnw test\n" + "\n".join(
            loop.select_gate_report_lines(_MAVEN_LOG, window=15)) + "\n```"
        cls, sig = loop.parse_gate_failure_signature(report)
        self.assertEqual(cls, "tests")
        self.assertEqual(sig, "DateSampleRegressionTest.ANonDateFakerSampleIsLeftAlone")


class TestMavenBuildLevelFailureIsAVerdict(unittest.TestCase):

    def test_failed_to_execute_goal_is_pinned_not_no_verdict(self):
        lines = loop.select_gate_report_lines(_CLEAN_PLUGIN_FAILURE, window=5)
        joined = "\n".join(lines)
        self.assertNotIn(loop._NO_VERDICT_NOTE, lines)
        self.assertIn("Failed to execute goal", joined)
        self.assertIn("BUILD FAILURE", joined)


class TestGateOutputIsPersisted(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_full_stdout_lands_under_work_and_the_report_names_it(self):
        feature_dir = Path("feat")
        feature_dir.mkdir()
        # 200 lines: far more than the 15-line report window keeps.
        cmd = "for i in $(seq 1 200); do echo \"line $i\"; done; echo FAILED; exit 1"
        results = loop._run_gate_set([{"name": "tests", "command": cmd}], feature_dir)
        self.assertFalse(results[0]["ok"])
        logs = sorted((feature_dir / "work" / "gate-logs").glob("tests-*.log"))
        self.assertEqual(len(logs), 1, "one log per gate run")
        text = logs[0].read_text()
        self.assertIn("line 1\n", text)
        self.assertIn("line 200\n", text)
        self.assertIn("full output: " + str(logs[0]), results[0]["report"])

    def test_old_logs_are_pruned_per_gate(self):
        feature_dir = Path("feat")
        log_dir = feature_dir / "work" / "gate-logs"
        log_dir.mkdir(parents=True)
        for i in range(loop.GATE_LOG_KEEP + 5):
            (log_dir / f"tests-20260101T0000{i:02d}Z.log").write_text("old\n")
        loop._run_gate_set([{"name": "tests", "command": "true"}], feature_dir)
        logs = sorted(log_dir.glob("tests-*.log"))
        self.assertEqual(len(logs), loop.GATE_LOG_KEEP)
        self.assertNotIn("tests-20260101T000000Z.log", [p.name for p in logs],
                         "the oldest go first")


if __name__ == "__main__":
    unittest.main()
