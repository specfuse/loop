# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A RESULT block whose fields use YAML block scalars still parses (#3436).

FEAT-2026-0115/T02 ended two sessions with a legitimate `status: blocked` whose
`blocked_reason` was a `|` block scalar. The strict mini-YAML parser rejects
block scalars by design (operator config must fail loudly), so
`parse_result_block` returned None, `agent_reported_blocked` returned
(False, None), and the driver ran verify() on an attempt that had written
nothing and escalated it as a spin.
"""
import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_T02_RESULT = """Confirmed genuine escalation match. No edits made.

```result
status: blocked
summary: Investigated evaluate_fix_unit_insertion's two required calls; both hit the WU's own named escalation triggers before any code could be written — no edits made.
blocked_reason: |
  Both escalation triggers in the WU body are real, verified by reading the
  called modules, not guessed:

  1. lint_plan_next_draft(feature_dir, just_closed_gate) has no per-unit
     check separable from its review-file check.
  2. evaluate_arm_predicate has no parameter for a projected graph.
```
"""


class BlockScalarResultParses(unittest.TestCase):
    def test_literal_block_scalar_blocked_reason_reads_as_blocked(self):
        blocked, reason = loop.agent_reported_blocked(_T02_RESULT)
        self.assertTrue(blocked)
        self.assertIn("Both escalation triggers in the WU body are real", reason)
        self.assertIn("1. lint_plan_next_draft(feature_dir, just_closed_gate)", reason)
        self.assertIn("\n\n", reason, "the literal scalar keeps its blank line")

    def test_parsed_block_carries_every_top_level_field(self):
        parsed = loop.parse_result_block(_T02_RESULT)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["status"], "blocked")
        self.assertTrue(parsed["summary"].startswith("Investigated evaluate_fix_unit_insertion"))

    def test_folded_block_scalar_joins_lines_with_spaces(self):
        out = "```result\nstatus: blocked\nblocked_reason: >\n  one line\n  continued here\n```\n"
        blocked, reason = loop.agent_reported_blocked(out)
        self.assertTrue(blocked)
        self.assertEqual(reason.strip(), "one line continued here")

    def test_list_field_beside_a_block_scalar_survives(self):
        out = ("```result\nstatus: complete\nsummary: |\n  did the thing\n"
               "files_changed:\n  - src/a.py\n  - tests/test_a.py\n```\n")
        parsed = loop.parse_result_block(out)
        self.assertEqual(parsed["status"], "complete")
        self.assertEqual(parsed["files_changed"], ["src/a.py", "tests/test_a.py"])
        self.assertEqual(parsed["summary"].strip(), "did the thing")

    def test_a_block_without_a_status_still_degrades_to_none(self):
        out = "```result\nsummary: |\n  no status here\n```\n"
        self.assertIsNone(loop.parse_result_block(out))

    def test_a_well_formed_block_parses_exactly_as_before(self):
        out = "```result\nstatus: blocked\nblocked_reason: one line\n```\n"
        self.assertEqual(loop.agent_reported_blocked(out), (True, "one line"))


if __name__ == "__main__":
    unittest.main()
