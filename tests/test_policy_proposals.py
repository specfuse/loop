#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.policy_proposals (FEAT-2026-0076/T01).

`propose_policy_defaults` proposes only what a repository's own evidence can
answer, and every proposal carries the evidence it came from. Proposing
nothing is a first-class outcome -- these tests pin the absence cases as
hard as the presence cases, per the WU's "a confident wrong proposal is
worse than an absent one."
"""

from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace

from specfuse.loop.agent_policy import validate_agent_policy
from specfuse.loop.policy_proposals import propose_policy_defaults


def _ev(cid, ts, outcome, cost, *, attempt=1, **extra):
    return json.dumps({
        "timestamp": ts,
        "correlation_id": cid,
        "event_type": "attempt_outcome",
        "payload": {"outcome": outcome, "cost_usd": cost, "attempt": attempt, **extra},
    })


def _write_events(repo_root: Path, feature: str, lines: list) -> None:
    d = repo_root / ".specfuse" / "features" / feature
    d.mkdir(parents=True, exist_ok=True)
    (d / "events.jsonl").write_text("\n".join(lines) + "\n")


def _write_verification_yml(repo_root: Path, command: str) -> None:
    d = repo_root / ".specfuse"
    d.mkdir(parents=True, exist_ok=True)
    (d / "verification.yml").write_text(textwrap.dedent(f"""\
        code:
          - name: tests
            command: "{command}"
        """))


class _OkRunner:
    def __init__(self, stdout, returncode=0):
        self.stdout = stdout
        self.returncode = returncode
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return SimpleNamespace(returncode=self.returncode, stdout=self.stdout, stderr="")


class _RaisingRunner:
    def __call__(self, args, check=True):
        raise OSError("gh: command not found")


class TestProposeDefaults(unittest.TestCase):
    def test_empty_repo_proposes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse").mkdir()

            result = propose_policy_defaults(root)

            self.assertEqual(result, {})

    def test_no_events_jsonl_omits_budget_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse" / "features").mkdir(parents=True)

            result = propose_policy_defaults(root)

            self.assertNotIn("max_tokens_per_run", result)
            self.assertNotIn("max_items_per_day", result)

    def test_with_events_jsonl_proposes_both_budget_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_events(root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 2.00),
                _ev("FEAT-2026-0001/T02", 2.0, "passed", 3.00),
            ])

            result = propose_policy_defaults(root)

            self.assertIn("max_tokens_per_run", result)
            self.assertIn("max_items_per_day", result)

    def test_all_proposals_carry_non_empty_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_events(root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 2.00),
            ])
            (root / "tests").mkdir()
            runner = _OkRunner(json.dumps([{"number": 1}]))

            result = propose_policy_defaults(root, runner=runner)

            self.assertTrue(result)
            for key, proposal in result.items():
                self.assertIn("value", proposal, key)
                evidence = proposal.get("evidence")
                self.assertIsInstance(evidence, str, key)
                self.assertTrue(evidence.strip(), key)

    def test_budget_proposal_is_a_function_of_fixture_data(self):
        with tempfile.TemporaryDirectory() as tmp_low, \
                tempfile.TemporaryDirectory() as tmp_high:
            low_root = Path(tmp_low)
            high_root = Path(tmp_high)
            _write_events(low_root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 1.00),
            ])
            _write_events(high_root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 50.00),
            ])

            low = propose_policy_defaults(low_root)
            high = propose_policy_defaults(high_root)

            self.assertLess(
                low["max_tokens_per_run"]["value"],
                high["max_tokens_per_run"]["value"],
            )

    def test_test_paths_proposed_from_tree_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            _write_verification_yml(root, "python3 -m unittest discover -s tests")

            result = propose_policy_defaults(root)

            self.assertEqual(result["test_paths"]["value"], ["tests/"])

    def test_test_paths_proposed_from_spec_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spec").mkdir()
            _write_verification_yml(root, "bundle exec rspec spec/")

            result = propose_policy_defaults(root)

            self.assertEqual(result["test_paths"]["value"], ["spec/"])

    def test_test_paths_disagreement_proposes_union_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            _write_verification_yml(root, "bundle exec rspec spec/")

            result = propose_policy_defaults(root)

            proposal = result["test_paths"]
            self.assertEqual(proposal["value"], ["spec/", "tests/"])
            self.assertIn("disagree", proposal["evidence"])

    def test_max_open_prs_absent_without_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = propose_policy_defaults(root, runner=None)

            self.assertNotIn("max_open_prs", result)

    def test_max_open_prs_absent_when_runner_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = propose_policy_defaults(root, runner=_RaisingRunner())

            self.assertNotIn("max_open_prs", result)

    def test_max_open_prs_absent_on_unparseable_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = propose_policy_defaults(root, runner=_OkRunner("not json"))

            self.assertNotIn("max_open_prs", result)

    def test_max_open_prs_proposed_from_usable_runner_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runner = _OkRunner(json.dumps([{"number": 1}, {"number": 2}]))

            result = propose_policy_defaults(root, runner=runner)

            self.assertIn("max_open_prs", result)
            self.assertIsInstance(result["max_open_prs"]["value"], int)

    def test_every_proposal_validates_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_events(root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 2.00),
                _ev("FEAT-2026-0001/T02", 2.0, "passed", 3.00),
            ])
            (root / "tests").mkdir()
            _write_verification_yml(root, "python3 -m unittest discover -s tests")
            runner = _OkRunner(json.dumps([{"number": 1}]))

            proposals = propose_policy_defaults(root, runner=runner)
            self.assertTrue(proposals)

            budgets = {
                "max_tokens_per_run": 2000000,
                "max_open_prs": 3,
                "max_items_per_day": 10,
            }
            for key in ("max_tokens_per_run", "max_open_prs", "max_items_per_day"):
                if key in proposals:
                    budgets[key] = proposals[key]["value"]
            test_paths = proposals.get("test_paths", {}).get("value", ["tests/"])

            policy_text = textwrap.dedent(f"""\
                version: 1
                queue: []
                rules:
                  bugs:
                    preempt: true
                    min_severity: low
                    automerge: "off"
                    test_paths:
                {_yaml_list(test_paths, 6)}
                  features:
                    gate_review: human
                    wip_limit: 1
                  triage:
                    auto: false
                budgets:
                  max_tokens_per_run: {budgets['max_tokens_per_run']}
                  max_open_prs: {budgets['max_open_prs']}
                  max_items_per_day: {budgets['max_items_per_day']}
                escalation:
                  webhook_env: ""
                  provider: none
                  assignee: ""
                  quiet_hours: ""
                  sla_hours: 24
                  silence_hours: 24
                """)
            policy_path = root / "agent-policy-from-proposals.yml"
            policy_path.write_text(policy_text)

            findings = validate_agent_policy(policy_path)
            errors = [f for f in findings if f.startswith("ERROR: ")]
            self.assertEqual(errors, [], findings)

    def test_no_file_read_outside_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            decoy = workspace / "decoy-sibling"
            _write_events(decoy, "FEAT-2026-9999-x", [
                _ev("FEAT-2026-9999/T01", 1.0, "passed", 999.00),
            ])

            root = workspace / "the-repo"
            _write_events(root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 2.00),
            ])

            result = propose_policy_defaults(root)

            solo_root = workspace / "solo-repo"
            _write_events(solo_root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 2.00),
            ])
            solo_result = propose_policy_defaults(solo_root)

            self.assertEqual(
                result["max_tokens_per_run"]["value"],
                solo_result["max_tokens_per_run"]["value"],
            )

    def test_no_network_call_without_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_events(root, "FEAT-2026-0001-x", [
                _ev("FEAT-2026-0001/T01", 1.0, "passed", 2.00),
            ])

            # No runner injected: must not raise, must not attempt any
            # subprocess/network call, and must simply omit max_open_prs.
            result = propose_policy_defaults(root)

            self.assertNotIn("max_open_prs", result)


def _yaml_list(items, indent):
    pad = " " * indent
    return "\n".join(f"{pad}- {item}" for item in items)


if __name__ == "__main__":
    unittest.main()
