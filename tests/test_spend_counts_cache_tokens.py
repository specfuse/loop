# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3522: `usage_spend` must count cache tokens, or `max_tokens_per_run` never binds.

With prompt caching, nearly all of a headless session's input arrives as
`cache_read_input_tokens` / `cache_creation_input_tokens`. Counting only
`input_tokens + output_tokens` reported 16,147 tokens for a run that included
a 13-minute, 9-file `/fix-bug` session, so a 2,835,000 cap could not fire.
"""

from __future__ import annotations

import sys
import unittest

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.budget import RunBudget
from specfuse.agent.invoke import usage_spend


class TestUsageSpendCountsCacheTokens(unittest.TestCase):
    def test_all_four_usage_fields_are_counted(self):
        usage = {
            "input_tokens": 900,
            "output_tokens": 300,
            "cache_read_input_tokens": 5000,
            "cache_creation_input_tokens": 200,
        }
        self.assertEqual(usage_spend(usage), 6400)

    def test_cache_only_session_is_not_free(self):
        usage = {
            "input_tokens": 3,
            "output_tokens": 0,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 0,
        }
        self.assertEqual(usage_spend(usage), 1_000_003)

    def test_missing_cache_fields_count_as_zero(self):
        self.assertEqual(usage_spend({"input_tokens": 10, "output_tokens": 5}), 15)


class TestCacheHeavySessionTripsTheCap(unittest.TestCase):
    def test_cap_binds_on_cache_traffic(self):
        budget = RunBudget(clock=lambda: 0.0, max_tokens=2_835_000)
        self.assertTrue(budget.may_start_next_item())
        budget.record_tokens(usage_spend({
            "input_tokens": 40,
            "output_tokens": 16_000,
            "cache_read_input_tokens": 3_000_000,
            "cache_creation_input_tokens": 120_000,
        }))
        self.assertFalse(budget.may_start_next_item())


if __name__ == "__main__":
    unittest.main()
