#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#2883 (part 2): surefire output pins the run-level verdict, not a per-class pass.

A gate-entry probe once reported `NO VERDICT FOUND` on output that ended in
`[ERROR] Tests run: 3514, Failures: 2, Errors: 0, Skipped: 1` /
`[INFO] BUILD FAILURE`, and recorded a passing per-class line
(`[INFO] Tests run: 5, Failures: 0 …`) as the failure signature. Two fixes
since then cover it: #1413 taught `select_gate_report_lines` the surefire
summary and per-test markers, and #3222 keeps logger chatter out of the
signature fallback. This test pins both against the exact shape from the
report so neither regresses silently.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_SUREFIRE_RUN = """\
### tests: FAIL
```
$ ./mvnw -q test
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.003 s -- in dev.specfuse.generator.AlphaTest
[INFO] Tests run: 7, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.011 s -- in dev.specfuse.generator.GammaTest
[ERROR] Tests run: 3514, Failures: 2, Errors: 0, Skipped: 1
[INFO] BUILD FAILURE
```
"""


class TestSurefireRunLevelSignature(unittest.TestCase):
    def test_signature_is_the_run_level_error_summary(self):
        failure_class, sig = loop.parse_gate_failure_signature(_SUREFIRE_RUN)
        self.assertEqual(failure_class, "tests")
        self.assertTrue(sig.startswith("[ERROR] Tests run: 3514, Failures: 2"), sig)

    def test_a_passing_per_class_line_is_never_the_signature(self):
        _, sig = loop.parse_gate_failure_signature(_SUREFIRE_RUN)
        self.assertNotIn("Failures: 0", sig)

    def test_report_lines_carry_a_verdict_not_the_no_verdict_note(self):
        lines = loop.select_gate_report_lines(_SUREFIRE_RUN)
        joined = "\n".join(lines)
        self.assertNotIn("NO VERDICT FOUND", joined)
        self.assertIn("Tests run: 3514, Failures: 2", joined)


if __name__ == "__main__":
    unittest.main()
