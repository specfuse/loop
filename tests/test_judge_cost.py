#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The judge's spend is the close's spend (FEAT-2026-0100/T03).

Reuses `JudgeClosePathCase` from `tests/test_judge_close_path.py`: same
fixture (one feature, one terminal gate, one close WU), same
dispatch/verify/run_judge_session patch points, same setUp/tearDown restore.
"""

from __future__ import annotations

import os

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace
from tests.test_judge_close_path import (
    JudgeClosePathCase, _events, _judge_output, _read_frontmatter,
)

loop = load_loop()


class TestJudgeCostFolding(JudgeClosePathCase):

    def _judge_usage_runner(self, output: str, usage: dict | None):
        def runner(prompt, *, timeout=None):
            self.judge_prompts.append(prompt)
            return output, usage
        return runner

    def _restore_patches(self) -> None:
        for name, original in self._patches:
            setattr(loop, name, original)
        self._patches = []
        self.judge_prompts = []

    def test_close_cost_includes_judge_usage(self):
        """A judge with its own cost envelope raises the close's cost by exactly that."""
        # Run 1: judge disabled — the close's cost is dispatch's own only.
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9901"
            fdir = self._write_feature(
                root, feature_id, close_verdict="met",
                plan_extra="judge_disabled: true\n",
            )

            def never_called(prompt, *, timeout=None):
                raise AssertionError("judge must not dispatch when disabled")

            self._install_stubs(fdir, "met", never_called)
            self._run()

            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            cost_without_judge = float(wu_fm.get("cost_usd"))

        self._restore_patches()

        # Run 2: judge enabled, agrees, and carries its own $0.42 envelope.
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9902"
            fdir = self._write_feature(root, feature_id, close_verdict="met")
            self._install_stubs(
                fdir, "met",
                self._judge_usage_runner(
                    _judge_output("met"),
                    {"cost_usd": 0.42, "input_tokens": 100, "output_tokens": 50},
                ),
            )
            self._run()

            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            cost_with_judge = float(wu_fm.get("cost_usd"))

            outcomes = _events(fdir, "attempt_outcome")
            passed = [e for e in outcomes if e["payload"].get("outcome") == "passed"]
            self.assertEqual(len(passed), 1)
            passed_cost = float(passed[0]["payload"]["cost_usd"])

        self.assertAlmostEqual(cost_with_judge - cost_without_judge, 0.42, places=6,
                               msg="the close WU's cost_usd must be larger by exactly "
                                   "the judge's own cost_usd")
        self.assertAlmostEqual(passed_cost - cost_without_judge, 0.42, places=6,
                               msg="the close's attempt_outcome cost_usd must also "
                                   "carry the judge's cost")

    def test_judged_event_carries_judge_cost(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9903"
            fdir = self._write_feature(root, feature_id, close_verdict="met")
            self._install_stubs(
                fdir, "met",
                self._judge_usage_runner(
                    _judge_output("met"),
                    {"cost_usd": 0.42, "input_tokens": 100, "output_tokens": 50},
                ),
            )
            self._run()

            judged = _events(fdir, "judged")
            self.assertEqual(len(judged), 1)
            self.assertAlmostEqual(
                float(judged[0]["payload"]["judge_cost_usd"]), 0.42, places=6)

    def test_judge_without_envelope_adds_nothing(self):
        """A judge runner that returns plain text (no usage dict) leaves cost unchanged."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9904"
            fdir = self._write_feature(root, feature_id, close_verdict="met")
            self._install_stubs(
                fdir, "met",
                self._judge_usage_runner("I could not decide. Sorry.\n", None),
            )
            self._run()

            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            cost = float(wu_fm.get("cost_usd"))
            # dispatch's own stub cost, from _install_stubs' fake_dispatch.
            self.assertAlmostEqual(cost, 0.001, places=6)

            judged = _events(fdir, "judged")
            self.assertEqual(len(judged), 1)
            self.assertNotIn("judge_cost_usd", judged[0]["payload"])


if __name__ == "__main__":
    import unittest
    unittest.main()
