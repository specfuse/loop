#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Cost tracking — parse_claude_json_output (unit) + run-loop integration.

Tracks two surfaces:
  - parse_claude_json_output is tolerant: any shape drift returns (raw, None)
    so the caller can fall back to text-mode RESULT-block parsing.
  - run() reads `cost_tracking` from verification.yml (default true) and
    threads it through. When true and dispatch returns usage, the driver
    writes cumulative cost_usd/input_tokens/output_tokens to the WU
    frontmatter and per-attempt usage to events.jsonl. When false, neither.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests.test_driver_integration import (
    integration_workspace,
    write_minimal_feature,
    _read_frontmatter,
    _read_events,
)

loop = load_loop()


# --------------------------------------------------------------------------- #
# parse_claude_json_output                                                    #
# --------------------------------------------------------------------------- #


class TestParseClaudeJsonOutput(unittest.TestCase):

    def test_well_formed_envelope(self):
        raw = json.dumps({
            "type": "result",
            "result": "(agent text)\n```result\nstatus: complete\n```\n",
            "total_cost_usd": 0.0123,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 250,
                "cache_read_input_tokens": 500,
            },
        })
        text, usage = loop.parse_claude_json_output(raw)
        self.assertIn("status: complete", text)
        self.assertEqual(usage["cost_usd"], 0.0123)
        self.assertEqual(usage["input_tokens"], 100)
        self.assertEqual(usage["output_tokens"], 250)
        self.assertEqual(usage["cache_read_input_tokens"], 500)

    def test_malformed_json_returns_raw_none(self):
        text, usage = loop.parse_claude_json_output("not json at all")
        self.assertEqual(text, "not json at all")
        self.assertIsNone(usage)

    def test_json_array_returns_raw_none(self):
        # Top-level array, not the expected envelope object.
        text, usage = loop.parse_claude_json_output('["unexpected"]')
        self.assertEqual(text, '["unexpected"]')
        self.assertIsNone(usage)

    def test_missing_usage_block_returns_none_usage(self):
        raw = json.dumps({"type": "result", "result": "(text)"})
        text, usage = loop.parse_claude_json_output(raw)
        self.assertEqual(text, "(text)")
        self.assertIsNone(usage)

    def test_partial_usage_extracts_what_is_present(self):
        raw = json.dumps({
            "type": "result",
            "result": "(text)",
            "total_cost_usd": 0.005,
            # No `usage` block — only the top-level cost.
        })
        text, usage = loop.parse_claude_json_output(raw)
        self.assertEqual(text, "(text)")
        self.assertEqual(usage, {"cost_usd": 0.005})

    def test_non_string_result_falls_back_to_raw(self):
        raw = json.dumps({"type": "result", "result": 42,
                          "total_cost_usd": 0.001})
        text, usage = loop.parse_claude_json_output(raw)
        self.assertEqual(text, raw)
        self.assertEqual(usage, {"cost_usd": 0.001})


# --------------------------------------------------------------------------- #
# Run-loop integration                                                        #
# --------------------------------------------------------------------------- #


def _write_verification_yml(root: Path, cost_tracking: bool) -> None:
    flag = "true" if cost_tracking else "false"
    (root / ".specfuse/verification.yml").write_text(
        f"cost_tracking: {flag}\n"
        "code:\n  - name: noop\n    command: \"true\"\n"
        "doc:\n  - name: noop\n    command: \"true\"\n"
        "plannext:\n  - name: noop\n    command: \"true\"\n"
    )
    subprocess.run(["git", "-C", str(root), "add", ".specfuse/verification.yml"],
                   check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "cost_tracking config"], check=True)


class TestCostTrackingIntegration(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_enabled_writes_cost_to_wu_frontmatter_and_events(self):
        """T01 PASSES with a usage dict returned from dispatch → WU
        frontmatter carries cost_usd / input_tokens / output_tokens, and
        events.jsonl's task_completed carries an attempts_usage list."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=True)
            write_minimal_feature(root, "FEAT-2026-9201", "cost-enabled",
                                  "feat/cost-on", [
                                      ("FEAT-2026-9201/T01", "implementation", "pending"),
                                  ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                return ("(stub)\n",
                        {"cost_usd": 0.0034,
                         "input_tokens": 1500, "output_tokens": 800})

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9201-cost-enabled"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done")
            # Cost values written to frontmatter — read as strings by the
            # bare-line helper; coerce to float/int for comparison.
            self.assertAlmostEqual(float(t01_fm["cost_usd"]), 0.0034, places=6)
            self.assertEqual(int(t01_fm["input_tokens"]), 1500)
            self.assertEqual(int(t01_fm["output_tokens"]), 800)

            # events.jsonl carries attempts_usage on the task_completed event.
            events = _read_events(fdir / "events.jsonl")
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == "FEAT-2026-9201/T01"]
            self.assertEqual(len(completed), 1)
            au = completed[0]["payload"]["attempts_usage"]
            self.assertEqual(len(au), 1)
            self.assertEqual(au[0]["attempt"], 1)
            self.assertAlmostEqual(au[0]["cost_usd"], 0.0034, places=6)

    def test_disabled_writes_no_cost_fields(self):
        """cost_tracking: false → WU frontmatter has no cost_usd, and
        events.jsonl's task_completed has no attempts_usage entries."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=False)
            write_minimal_feature(root, "FEAT-2026-9202", "cost-disabled",
                                  "feat/cost-off", [
                                      ("FEAT-2026-9202/T01", "implementation", "pending"),
                                  ])

            # Even if dispatch were to return a usage dict, cost_tracking
            # being False means run() should pass cost_tracking=False to
            # dispatch (the stub honors it by returning None).
            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # Real dispatch returns (text, None) when cost_tracking is False;
                # we mirror that contract here.
                if not cost_tracking:
                    return "(stub)\n", None
                return ("(stub)\n",
                        {"cost_usd": 0.01, "input_tokens": 100,
                         "output_tokens": 100})

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9202-cost-disabled"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done")
            self.assertNotIn("cost_usd", t01_fm)
            self.assertNotIn("input_tokens", t01_fm)
            self.assertNotIn("output_tokens", t01_fm)

            events = _read_events(fdir / "events.jsonl")
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == "FEAT-2026-9202/T01"]
            self.assertEqual(len(completed), 1)
            au = completed[0]["payload"]["attempts_usage"]
            # duration_seconds is always recorded (independent of cost_tracking);
            # cost/token fields are absent when cost_tracking is False.
            self.assertEqual(len(au), 1)
            self.assertIn("duration_seconds", au[0])
            self.assertNotIn("cost_usd", au[0])
            self.assertNotIn("input_tokens", au[0])

    def test_default_is_enabled_when_key_absent(self):
        """No cost_tracking key in verification.yml → defaults to enabled."""
        with integration_workspace() as root:
            os.chdir(root)
            # integration_workspace already wrote verification.yml WITHOUT
            # the cost_tracking key, so the default applies.
            write_minimal_feature(root, "FEAT-2026-9203", "cost-default",
                                  "feat/cost-default", [
                                      ("FEAT-2026-9203/T01", "implementation", "pending"),
                                  ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # Assert the default propagated as True.
                self.assertTrue(cost_tracking,
                                "default cost_tracking should be True")
                return ("(stub)\n",
                        {"cost_usd": 0.001, "input_tokens": 10,
                         "output_tokens": 5})

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            loop.run(None, dry_run=False)

            fdir = root / ".specfuse/features/FEAT-2026-9203-cost-default"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertIn("cost_usd", t01_fm)

    def test_cumulative_sum_across_failed_attempts(self):
        """Three failed attempts then a spinning escalation — cumulative
        cost on WU frontmatter is the SUM across all three attempts; events
        carry the per-attempt breakdown."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root, cost_tracking=True)
            write_minimal_feature(root, "FEAT-2026-9204", "cost-cum",
                                  "feat/cost-cum", [
                                      ("FEAT-2026-9204/T01", "implementation", "pending"),
                                  ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                return ("(stub)\n",
                        {"cost_usd": 0.01,
                         "input_tokens": 100, "output_tokens": 50})

            # verify always fails → 3 attempts → spinning.
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "(fail)"))
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)  # blocked from spinning

            fdir = root / ".specfuse/features/FEAT-2026-9204-cost-cum"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "blocked_human")
            self.assertAlmostEqual(float(t01_fm["cost_usd"]), 0.03, places=6)
            self.assertEqual(int(t01_fm["input_tokens"]), 300)
            self.assertEqual(int(t01_fm["output_tokens"]), 150)

            events = _read_events(fdir / "events.jsonl")
            esc = [e for e in events
                   if e["event_type"] == "human_escalation"][0]
            self.assertEqual(len(esc["payload"]["attempts_usage"]), 3)


if __name__ == "__main__":
    unittest.main()
