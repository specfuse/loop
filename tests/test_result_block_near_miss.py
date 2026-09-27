# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A near-miss RESULT block is still read (#3442).

FEAT-2026-0116/T01, attempt 1, ended with a legitimate block in a bare fence
whose first line was `RESULT`, and named the reason `reason:` rather than
`blocked_reason:`. RESULT_BLOCK_RE found no ```result block, so the attempt was
read as complete and verified against a tree the session had left untouched.
"""
import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_T01_RESULT = """Confirmed: the pinned test asserts the run-level summary. Escalation trigger fires. Stop, no code edits.

```
RESULT
status: blocked
reason: "Acceptance criterion 4 pins tests.test_surefire_run_level_signature.TestSurefireRunLevelSignature.test_signature_is_the_run_level_error_summary, which asserts a run-level summary line is the signature. Escalation trigger matched verbatim."
files_touched: []
tests_run: "python3 -m unittest tests.test_surefire_run_level_signature -v -b"
tests_result: pass (baseline, unmodified, confirms the conflict, not a fix)
```
"""


class NearMissResultIsRead(unittest.TestCase):
    def test_bare_fence_led_by_RESULT_with_reason_alias_reads_as_blocked(self):
        blocked, reason = loop.agent_reported_blocked(_T01_RESULT)
        self.assertTrue(blocked)
        self.assertIn("Acceptance criterion 4 pins", reason)

    def test_reason_alias_inside_a_proper_result_fence(self):
        out = "```result\nstatus: blocked\nreason: the plan contradicts itself\n```\n"
        self.assertEqual(loop.agent_reported_blocked(out), (True, "the plan contradicts itself"))

    def test_blocked_reason_wins_over_reason_when_both_are_present(self):
        out = "```result\nstatus: blocked\nblocked_reason: the real one\nreason: other\n```\n"
        self.assertEqual(loop.agent_reported_blocked(out), (True, "the real one"))

    def test_a_proper_result_fence_takes_precedence_over_a_near_miss(self):
        out = ("```result\nstatus: complete\nsummary: done\n```\n\n"
               "```\nRESULT\nstatus: blocked\nreason: quoted example\n```\n")
        self.assertEqual(loop.parse_result_block(out)["status"], "complete")

    def test_a_plain_code_fence_is_not_a_result(self):
        out = "Here is the diff:\n\n```\nstatus: blocked\nreason: not a result\n```\n"
        self.assertIsNone(loop.parse_result_block(out))


if __name__ == "__main__":
    unittest.main()
