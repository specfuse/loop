# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the shared headless-`claude` invoker (FEAT-2026-0108/T01).

Covers: `run_claude` parsing the CLI's `--output-format=json` envelope into
text plus a usage block, falling back to raw text with `usage=None` when the
CLI's output is not the envelope shape, and a provider that reports real
`spend` from that usage feeding `RunBudget`'s `max_tokens` cap through
`run_agent` end to end.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent import run as run_module
from specfuse.agent.invoke import run_claude, usage_spend
from specfuse.agent.run import ActionItem, ActionOutcome, STATUS_COMPLETED, run_agent
from specfuse.agent.budget import STOP_CAP


def _json_runner(envelope: dict, calls: list = None):
    def runner(argv, check: bool = False):
        if calls is not None:
            calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout=json.dumps(envelope), stderr="")

    return runner


class TestRunClaudeParsesUsageEnvelope(unittest.TestCase):
    def test_run_claude_parses_usage_envelope(self):
        envelope = {
            "result": "session text back",
            "total_cost_usd": 0.0421,
            "usage": {
                "input_tokens": 900,
                "output_tokens": 300,
                "cache_read_input_tokens": 50,
                "cache_creation_input_tokens": 10,
            },
        }
        calls = []
        runner = _json_runner(envelope, calls)

        result = run_claude(["claude", "-p", "--model", "sonnet"], "do the thing", runner=runner)

        self.assertEqual(result.text, "session text back")
        self.assertEqual(result.usage["input_tokens"], 900)
        self.assertEqual(result.usage["output_tokens"], 300)
        self.assertEqual(result.usage["cost_usd"], 0.0421)
        self.assertEqual(result.returncode, 0)

        # `run_claude` appends `--output-format json` and the prompt itself --
        # no invoke site builds either of those inline any more.
        self.assertIn("--output-format", calls[0])
        self.assertIn("json", calls[0])
        self.assertEqual(calls[0][-1], "do the thing")

    def test_usage_spend_excludes_cache_reads(self):
        usage = {
            "input_tokens": 900,
            "output_tokens": 300,
            "cache_read_input_tokens": 5000,
            "cache_creation_input_tokens": 200,
        }
        self.assertEqual(usage_spend(usage), 1200)


class TestNonJsonOutputYieldsNoUsage(unittest.TestCase):
    def test_non_json_output_yields_no_usage_and_text_intact(self):
        def runner(argv, check: bool = False):
            return SimpleNamespace(returncode=0, stdout="<!-- specfuse:triage category=bug -->", stderr="")

        result = run_claude(["claude", "-p"], "classify this", runner=runner)

        self.assertIsNone(result.usage)
        self.assertEqual(result.text, "<!-- specfuse:triage category=bug -->")
        self.assertEqual(usage_spend(result.usage), 0)


class _SpendingProvider:
    """A test double that reports a fixed `spend` per item, modelling a
    provider whose `run_claude` usage came back non-trivial."""

    def __init__(self, item_ids, spend: int):
        self._items = {
            item_id: ActionItem(item_id=item_id, kind="triage", queue_key=None)
            for item_id in item_ids
        }
        self._spend = spend
        self.executed = []

    def advertise(self, snapshot):
        return tuple(self._items.values())

    def execute(self, item):
        self.executed.append(item.item_id)
        del self._items[item.item_id]
        return ActionOutcome(status=STATUS_COMPLETED, detail="ok", spend=self._spend)

    def reconcile(self, item, outcome):
        return None


def _empty_json_runner(calls):
    def runner(argv, check=False):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    return runner


class TestBudgetTokenCapFiresAfterOneItem(unittest.TestCase):
    def test_budget_token_cap_fires_after_one_item(self):
        provider = _SpendingProvider(["triage-1", "triage-2"], spend=1200)
        lines: list = []

        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            summary = run_agent(
                specfuse_dir=specfuse_dir,
                repo="o/r",
                runner=_empty_json_runner([]),
                providers=(provider,),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=features_root,
                max_tokens=1000,
                reporter=lines.append,
            )

        self.assertEqual(summary.items_attempted, 1)
        self.assertEqual(summary.stop_reason, STOP_CAP)
        self.assertEqual(summary.tokens_spent, 1200)
        self.assertEqual(provider.executed, ["triage-1"])

        rendered = run_module._format_summary(summary)
        self.assertIn("tokens spent:     1200", rendered)


if __name__ == "__main__":
    unittest.main()
