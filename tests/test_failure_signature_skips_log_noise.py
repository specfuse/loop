#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#3222: a failure signature must name the failure, not the first log line.

On a Maven/Java gate whose failure carries no surefire marker, the fallback
in `parse_gate_failure_signature` keyed the signature off the first
informative line after the `### <gate>: FAIL` marker — which under any
SLF4J/Logback default is a `[main] INFO …` line that appears in every run.
Two attempts with different real failures then share a "signature", the
spinning detector fires on the wrong thing, and the re-arm reproduction gate
asks the operator to reproduce a log line.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_MAVEN_FAILURE = """\
### tests: FAIL
```
$ mvn -q test
[main] INFO dev.specfuse.generator.validation.ArazzoValidator - Arazzo validation completed. Found 1
[main] INFO dev.specfuse.generator.validation.ArazzoValidator - Arazzo validation completed. Found 0
[INFO] Scanning for projects...
[ERROR] Failed to execute goal dev.specfuse:validator-maven-plugin:1.2:validate (default) on project generator: Arazzo validation found 1 issue
[ERROR] -> [Help 1]
```
"""

_ONLY_LOG_LINES = """\
### tests: FAIL
```
$ mvn -q test
[main] INFO dev.specfuse.generator.validation.ArazzoValidator - Arazzo validation completed. Found 1
[main] DEBUG dev.specfuse.generator.Loader - loaded 3 specs
[INFO] BUILD SUCCESS
```
"""

_PYTHON_TRACEBACK_AFTER_LOGS = """\
### tests: FAIL
```
$ python3 -m unittest discover -s tests
[main] INFO app.boot - starting fixture
Traceback (most recent call last):
  File "tests/test_x.py", line 3, in test_boot
AssertionError: boot did not complete
```
"""


class TestSignatureSkipsLogNoise(unittest.TestCase):
    def test_maven_error_line_wins_over_leading_info_lines(self):
        failure_class, sig = loop.parse_gate_failure_signature(_MAVEN_FAILURE)
        self.assertEqual(failure_class, "tests")
        self.assertTrue(sig.startswith("[ERROR] Failed to execute goal"), sig)

    def test_only_log_lines_yield_the_no_signature_sentinel(self):
        failure_class, sig = loop.parse_gate_failure_signature(_ONLY_LOG_LINES)
        self.assertEqual(failure_class, "tests")
        self.assertEqual(sig, loop.NO_SIGNATURE)
        # The spin detector must not fire on two such attempts.
        self.assertFalse(
            loop.detect_spinning_signature_repeat((failure_class, sig), (failure_class, sig))
        )

    def test_traceback_line_wins_over_leading_info_line(self):
        _, sig = loop.parse_gate_failure_signature(_PYTHON_TRACEBACK_AFTER_LOGS)
        self.assertNotIn("INFO", sig)
        self.assertTrue(sig.startswith("Traceback") or sig.startswith("AssertionError"), sig)

    def test_two_different_maven_failures_get_different_signatures(self):
        other = _MAVEN_FAILURE.replace("Arazzo validation found 1 issue", "compilation failure in Foo.java")
        _, a = loop.parse_gate_failure_signature(_MAVEN_FAILURE)
        _, b = loop.parse_gate_failure_signature(other)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
