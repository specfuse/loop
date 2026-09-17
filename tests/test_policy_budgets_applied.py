#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`agent-policy.yml` budgets must actually cap a run (#3340).

`budgets.max_tokens_per_run` and `budgets.max_items_per_day` are drafted by
`/derive-agent-policy` and validated by `validate_agent_policy`, and nothing
read them: `specfuse agent`'s `RunBudget` was built only from
`--max-tokens/--max-items`, which default to `None`. A plain run was therefore
uncapped while the policy file declared limits — protection that reads as real
and is not.

A policy that declares caps it does not enforce is worse than no policy, so
these assert the resolution directly: what the policy says, what a flag
overrides, and what happens when the value is absent or malformed.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop import agent_policy


def _policy(tmp: Path, body: str) -> Path:
    path = tmp / "agent-policy.yml"
    path.write_text(body, encoding="utf-8")
    return path


# Block mappings only: the loop's miniyaml parser rejects flow mappings.
BUDGETS = """\
version: 1
budgets:
  max_tokens_per_run: 2800000
  max_items_per_day: 62
"""


class PolicyBudgetsResolve(unittest.TestCase):

    def test_declared_budgets_are_read(self):
        with TemporaryDirectory() as t:
            path = _policy(Path(t), BUDGETS)
            self.assertEqual(
                2800000, agent_policy.resolve_max_tokens(None, path))
            self.assertEqual(62, agent_policy.resolve_max_items(None, path))

    def test_a_flag_overrides_the_policy(self):
        with TemporaryDirectory() as t:
            path = _policy(Path(t), BUDGETS)
            self.assertEqual(10, agent_policy.resolve_max_items(10, path))
            self.assertEqual(5, agent_policy.resolve_max_tokens(5, path))

    def test_an_absent_budgets_block_stays_uncapped(self):
        with TemporaryDirectory() as t:
            path = _policy(Path(t), "version: 1\n")
            self.assertIsNone(agent_policy.resolve_max_tokens(None, path))
            self.assertIsNone(agent_policy.resolve_max_items(None, path))

    def test_an_absent_policy_file_stays_uncapped(self):
        with TemporaryDirectory() as t:
            missing = Path(t) / "nope.yml"
            self.assertIsNone(agent_policy.resolve_max_tokens(None, missing))
            self.assertIsNone(agent_policy.resolve_max_items(None, missing))

    def test_a_malformed_value_does_not_cap_at_zero(self):
        # The failure mode `bug_lane_ci_wait_seconds` guards for: a bad value
        # must not become a cap of 0, which would end every run immediately.
        for bad in ("max_tokens_per_run: nonsense\n", "max_tokens_per_run: 0\n",
                    "max_tokens_per_run: -5\n", "max_tokens_per_run: true\n"):
            with self.subTest(bad), TemporaryDirectory() as t:
                path = _policy(
                    Path(t),
                    "version: 1\nbudgets:\n  " + bad)
                self.assertIsNone(agent_policy.resolve_max_tokens(None, path))


class TheRunReportsItsEffectiveCaps(unittest.TestCase):

    def test_the_source_of_each_cap_is_named(self):
        line = agent_policy.describe_budget_sources(
            max_tokens=(2800000, "policy"), max_items=(10, "flag"),
            max_minutes=(None, "none"))
        self.assertIn("2800000", line.replace(",", ""))
        self.assertIn("policy", line)
        self.assertIn("flag", line)
        self.assertIn("none", line)


if __name__ == "__main__":
    unittest.main()
