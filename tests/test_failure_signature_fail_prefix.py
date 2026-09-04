#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#2885: a `FAIL: <anything>` line names the failure, not only `FAIL: test_*`.

A project whose `tests` gate post-processes surefire output into
`FAIL: <class>.<method> <<< FAILURE!` lines missed the `tests` pattern,
which was anchored on `FAIL: test_`; the signature then fell to the first
informative line — a passing `[INFO] Tests run: 5, Failures: 0 …` per-class
summary — so the halt named a green test class and both the `tests` and
`coverage` gates shared one signature.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_POST_PROCESSED_SUREFIRE = """\
### tests: FAIL
```
$ ./mvnw clean test
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.003 s -- in dev.specfuse.generator.AlphaTest
[INFO] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.010 s -- in dev.specfuse.generator.BetaTest
--- failing tests (surefire) ---
FAIL: dev.specfuse.generator.BetaTest.rendersDescription -- Time elapsed: 0.004 s <<< FAILURE!
```
"""


class TestFailPrefixSignature(unittest.TestCase):
    def test_fail_prefixed_class_method_is_the_signature(self):
        failure_class, sig = loop.parse_gate_failure_signature(_POST_PROCESSED_SUREFIRE)
        self.assertEqual(failure_class, "tests")
        self.assertEqual(sig, "dev.specfuse.generator.BetaTest.rendersDescription")

    def test_passing_per_class_summary_is_never_the_signature(self):
        _, sig = loop.parse_gate_failure_signature(_POST_PROCESSED_SUREFIRE)
        self.assertNotIn("Failures: 0", sig)

    def test_unittest_shape_still_matches(self):
        out = "### tests: FAIL\n```\n$ python3 -m unittest\nFAIL: test_boot (tests.test_x.TestX.test_boot)\n```\n"
        _, sig = loop.parse_gate_failure_signature(out)
        self.assertEqual(sig, "test_boot")


if __name__ == "__main__":
    unittest.main()
