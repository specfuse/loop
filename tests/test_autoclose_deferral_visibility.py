# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Issue #157: the auto-close path marks a close/close-intermediate WU done
# without dispatching its body, so the mandatory "What the loop did NOT verify"
# deferral list is never written. The auto-close stub writers must instead emit
# an explicit deferral-visibility section so the gap is surfaced (direction 2),
# not silently omitted — for BOTH the intermediate and terminal stubs.

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()
from specfuse.loop.gate_eval import AutoCloseDecision  # noqa: E402


def _decision(gate: int) -> AutoCloseDecision:
    return AutoCloseDecision(
        auto=True,
        reasons=[],
        metrics={"gate_total_cost": 1.23, "gate_budget": 5.0},
        gate_id=gate,
        feature_id="FEAT-TEST-0001",
        predicate_version="v1",
    )


class TestAutoCloseDeferralVisibility(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _retro(self) -> str:
        return (self.fd / "RETROSPECTIVE.md").read_text()

    def test_intermediate_stub_flags_deferred_verification_gap(self):
        """The intermediate auto-close stub emits a 'What the loop did NOT
        verify' section pointing reconciliation at the next gate's close."""
        loop.append_stub_retrospective_intermediate(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("## What the loop did NOT verify", retro)
        self.assertIn("Gate 2's close", retro)  # next-gate reconciliation

    def test_terminal_stub_flags_deferred_verification_gap(self):
        """The terminal auto-close stub emits a 'What the loop did NOT verify'
        section pointing reconciliation at the operator (no downstream gate)."""
        loop.write_stub_retrospective_terminal(self.fd, 2, _decision(2))
        retro = self._retro()
        self.assertIn("## What the loop did NOT verify", retro)
        self.assertIn("operator", retro.lower())

    def test_intermediate_stub_still_records_cost_and_gate_heading(self):
        """Existing stub content is preserved (cost, gate heading)."""
        loop.append_stub_retrospective_intermediate(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("## Gate 1 — auto-closed", retro)
        self.assertIn("gate_total_cost: $1.23", retro)


if __name__ == "__main__":
    unittest.main()
