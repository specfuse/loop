# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0070/T06 shipped auto-close stubs that enumerated every
# acceptance criterion as deferred debt for a downstream close to reconcile.
# FEAT-2026-0085/T02 replaced that enumeration with a pass summary: the stub
# now states what the driver's gates actually proved (which units passed, on
# which gate set) instead of listing every criterion as unverified.

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


class TestAutoCloseStubHasNoDeferralSection(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _retro(self) -> str:
        return (self.fd / "RETROSPECTIVE.md").read_text()

    def test_intermediate_stub_has_no_deferral_heading(self):
        loop.append_stub_retrospective_intermediate(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertNotIn("What the loop did NOT verify", retro)
        self.assertNotIn("deferred:", retro)
        self.assertNotIn("specfuse:autoclose-debt", retro)

    def test_terminal_stub_has_no_deferral_heading(self):
        loop.write_stub_retrospective_terminal(self.fd, 2, _decision(2))
        retro = self._retro()
        self.assertNotIn("What the loop did NOT verify", retro)
        self.assertNotIn("deferred:", retro)
        self.assertNotIn("specfuse:autoclose-debt", retro)

    def test_intermediate_stub_still_records_cost_and_gate_heading(self):
        """Existing stub content is preserved (cost, gate heading)."""
        loop.append_stub_retrospective_intermediate(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("## Gate 1 — auto-closed", retro)
        self.assertIn("gate_total_cost: $1.23", retro)


def _write_plan(fd: Path, gate_number: int, wu_specs: list[dict]) -> None:
    """Write a minimal PLAN.md graph pointing at gate `gate_number`'s WUs."""
    wu_lines = "\n".join(
        f"      - id: FEAT-TEST-0001/{spec['sub_id']}\n"
        f"        file: {spec['file']}\n"
        f"        depends_on: []"
        for spec in wu_specs
    )
    (fd / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-TEST-0001\n"
        "status: active\n"
        "---\n\n"
        "# Plan\n\n"
        "```yaml\n"
        "gates:\n"
        f"  - gate: {gate_number}\n"
        f"    file: GATE-{gate_number:02d}.md\n"
        "    work_units:\n"
        f"{wu_lines}\n"
        "```\n"
    )


def _write_wu(fd: Path, spec: dict) -> None:
    ac_lines = "\n".join(f"{i}. {c}" for i, c in enumerate(spec["criteria"], start=1))
    (fd / spec["file"]).write_text(
        "---\n"
        f"id: FEAT-TEST-0001/{spec['sub_id']}\n"
        f"type: {spec.get('type', 'implementation')}\n"
        "status: done\n"
        "---\n\n"
        f"# {spec['sub_id']}\n\n"
        "**Acceptance criteria.**\n\n"
        f"{ac_lines}\n"
    )


class TestAutoClosePassSummary(unittest.TestCase):
    """FEAT-2026-0085/T02 — the pass-summary builder and its wiring into both
    auto-close stub writers."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _retro(self) -> str:
        return (self.fd / "RETROSPECTIVE.md").read_text()

    def _two_wu_gate(self):
        specs = [
            {
                "sub_id": "T01",
                "file": "WU-01-alpha.md",
                "type": "implementation",
                "criteria": [
                    "Greppable criterion ALPHA-ONE must hold.",
                    "Greppable criterion ALPHA-TWO must hold.",
                ],
            },
            {
                "sub_id": "T02",
                "file": "WU-02-beta.md",
                "type": "docs",
                "criteria": [
                    "Greppable criterion BETA-ONE must hold.",
                ],
            },
        ]
        _write_plan(self.fd, 1, specs)
        for spec in specs:
            _write_wu(self.fd, spec)
        return specs

    def test_intermediate_stub_names_each_substantive_wu_and_gate_set(self):
        self._two_wu_gate()
        loop.append_stub_retrospective_intermediate(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("FEAT-TEST-0001/T01", retro)
        self.assertIn("FEAT-TEST-0001/T02", retro)
        self.assertIn("`code`", retro)
        self.assertIn("`doc`", retro)
        self.assertNotIn("Greppable criterion", retro)

    def test_terminal_stub_names_each_substantive_wu_and_gate_set(self):
        self._two_wu_gate()
        loop.write_stub_retrospective_terminal(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("FEAT-TEST-0001/T01", retro)
        self.assertIn("FEAT-TEST-0001/T02", retro)
        self.assertIn("`code`", retro)
        self.assertIn("`doc`", retro)

    def test_summary_names_the_wu_file(self):
        self._two_wu_gate()
        block = loop.build_autoclose_pass_summary(self.fd, 1)
        self.assertIn("WU-01-alpha.md", block)
        self.assertIn("WU-02-beta.md", block)

    def test_non_substantive_wus_absent_from_summary(self):
        specs = self._two_wu_gate()
        specs.append({
            "sub_id": "G1-CLOSE-INTERMEDIATE",
            "file": "WU-90-close-intermediate.md",
            "type": "close-intermediate",
            "criteria": ["Should never appear ZZZZ."],
        })
        specs.append({
            "sub_id": "G1-PLAN",
            "file": "WU-91-plan-next.md",
            "type": "plan-next",
            "criteria": ["Should also never appear YYYY."],
        })
        _write_plan(self.fd, 1, specs)
        for spec in specs[2:]:
            _write_wu(self.fd, spec)
        block = loop.build_autoclose_pass_summary(self.fd, 1)
        self.assertNotIn("close-intermediate", block)
        self.assertNotIn("plan-next", block)

    def test_missing_wu_file_absent_from_summary(self):
        _write_plan(self.fd, 1, [
            {"sub_id": "T01", "file": "WU-01-missing.md", "criteria": []},
        ])
        block = loop.build_autoclose_pass_summary(self.fd, 1)
        self.assertEqual(block, "")

    def test_symbol_exists(self):
        self.assertTrue(callable(loop.build_autoclose_pass_summary))

    def test_terminal_stub_idempotent_on_second_call(self):
        """FEAT-2026-0070/T06 AC12 — the terminal writer must skip when the
        gate's auto-closed heading already exists, matching the intermediate
        sibling's existing guard."""
        self._two_wu_gate()
        loop.write_stub_retrospective_terminal(self.fd, 1, _decision(1))
        first = self._retro()
        loop.write_stub_retrospective_terminal(self.fd, 1, _decision(1))
        second = self._retro()
        self.assertEqual(first, second)
        self.assertEqual(second.count("## Gate 1 — auto-closed"), 1)
        self.assertEqual(second.count("FEAT-TEST-0001/T01"), 1)


if __name__ == "__main__":
    unittest.main()
