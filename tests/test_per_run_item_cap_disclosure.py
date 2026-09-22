# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`max_items_per_day` is enforced per run, and now says so (#3340).

Most of #3340 landed: budgets resolve from the policy when no flag is given,
`max_open_prs` gates bug-lane dispatch, and the run opens with a line naming
each effective cap and its source.

One expectation was left. The policy key is named `max_items_per_day` and is
applied *per run* -- enforcing it across runs within a day needs state that
survives a process, which is a feature, not this fix. `resolve_max_items`
records that honestly in its docstring, but a docstring is not a surface an
operator reads. The issue offered the alternative explicitly: enforce it across
runs, **or** document it as per-run.

So the operator-facing surfaces carry it. A run that prints `max_items=62
(policy)` against a policy whose key says `per_day` invites exactly the wrong
reading -- and the wrong reading is the unsafe one, since a day of runs can
exceed the number the operator believes they set.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from specfuse.loop import agent_policy

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "plugins/specfuse/skills/derive-agent-policy/SKILL.md"


class PerRunItemCapDisclosure(unittest.TestCase):

    def test_the_run_line_says_the_item_cap_is_per_run(self):
        line = agent_policy.describe_budget_sources(
            max_items=(62, "policy"),
            max_tokens=(2800000, "policy"),
            max_minutes=(None, "none"),
        )

        self.assertIn("per run", line)

    def test_a_flag_sourced_item_cap_says_it_too(self):
        # The cap is per-run whoever set it; the policy key's name is what
        # misleads, but a flag run is bounded the same way.
        line = agent_policy.describe_budget_sources(max_items=(5, "flag"))

        self.assertIn("per run", line)

    def test_other_caps_are_not_annotated(self):
        # Only the item cap has a name that promises something wider than it
        # delivers. Annotating the rest would be noise.
        line = agent_policy.describe_budget_sources(
            max_tokens=(2800000, "policy"),
            max_open_prs=(3, "policy"),
        )

        self.assertNotIn("per run", line)

    def test_an_absent_item_cap_is_not_annotated(self):
        line = agent_policy.describe_budget_sources(max_items=(None, "none"))

        self.assertIn("unbounded", line)
        self.assertNotIn("per run", line)

    def test_the_drafting_skill_discloses_the_semantics(self):
        body = SKILL.read_text(encoding="utf-8")

        self.assertIn(
            "per run", body,
            "/derive-agent-policy drafts `max_items_per_day` into an "
            "operator's policy file. It must say that the key is applied per "
            "run, or the operator writes a number believing it bounds a day "
            "(#3340).",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
