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


class TestAutoCloseDebtEnumeration(unittest.TestCase):
    """FEAT-2026-0070/T06 — the enumeration builder and its wiring into both
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
                "criteria": [
                    "Greppable criterion ALPHA-ONE must hold.",
                    "Greppable criterion ALPHA-TWO must hold.",
                ],
            },
            {
                "sub_id": "T02",
                "file": "WU-02-beta.md",
                "criteria": [
                    "Greppable criterion BETA-ONE must hold.",
                ],
            },
        ]
        _write_plan(self.fd, 1, specs)
        for spec in specs:
            _write_wu(self.fd, spec)
        return specs

    def test_intermediate_stub_enumerates_each_substantive_wu_criteria(self):
        self._two_wu_gate()
        loop.append_stub_retrospective_intermediate(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("FEAT-TEST-0001/T01", retro)
        self.assertIn("FEAT-TEST-0001/T02", retro)
        self.assertIn("Greppable criterion ALPHA-ONE must hold.", retro)
        self.assertIn("Greppable criterion ALPHA-TWO must hold.", retro)
        self.assertIn("Greppable criterion BETA-ONE must hold.", retro)

    def test_terminal_stub_enumerates_each_substantive_wu_criteria(self):
        self._two_wu_gate()
        loop.write_stub_retrospective_terminal(self.fd, 1, _decision(1))
        retro = self._retro()
        self.assertIn("FEAT-TEST-0001/T01", retro)
        self.assertIn("Greppable criterion BETA-ONE must hold.", retro)

    def test_enumeration_carries_machine_readable_marker(self):
        self._two_wu_gate()
        block = loop.build_autoclose_debt_enumeration(self.fd, 1)
        self.assertTrue(block.startswith("<!-- specfuse:autoclose-debt gate=1 "))
        self.assertIn("wus=T01,T02", block)
        self.assertIn("criteria=3", block)
        self.assertIn("predicate=v1", block)

    def test_non_substantive_wus_absent_from_enumeration(self):
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
        block = loop.build_autoclose_debt_enumeration(self.fd, 1)
        self.assertNotIn("close-intermediate", block)
        self.assertNotIn("ZZZZ", block)
        self.assertNotIn("YYYY", block)

    def test_missing_wu_file_degrades_to_not_parseable_line(self):
        _write_plan(self.fd, 1, [
            {"sub_id": "T01", "file": "WU-01-missing.md", "criteria": []},
        ])
        block = loop.build_autoclose_debt_enumeration(self.fd, 1)
        self.assertIn("deferred: <criteria not parseable>", block)
        self.assertIn("WU-01-missing.md", block)

    def test_wu_with_no_acceptance_criteria_section_degrades(self):
        spec = {"sub_id": "T01", "file": "WU-01-no-ac.md", "criteria": []}
        _write_plan(self.fd, 1, [spec])
        (self.fd / spec["file"]).write_text(
            "---\nid: FEAT-TEST-0001/T01\ntype: implementation\nstatus: done\n---\n\n"
            "# T01\n\nNo acceptance criteria section here at all.\n"
        )
        block = loop.build_autoclose_debt_enumeration(self.fd, 1)
        self.assertIn("deferred: <criteria not parseable>", block)

    def test_over_40_criteria_lists_first_40_and_announces_the_rest(self):
        criteria = [f"Criterion number {i}." for i in range(1, 46)]
        specs = [{"sub_id": "T01", "file": "WU-01-many.md", "criteria": criteria}]
        _write_plan(self.fd, 1, specs)
        for spec in specs:
            _write_wu(self.fd, spec)
        block = loop.build_autoclose_debt_enumeration(self.fd, 1)
        self.assertEqual(block.count("deferred:"), 40)
        self.assertIn("… 5 further criteria not listed; read the WU files", block)

    def test_long_criterion_truncated_at_200_chars(self):
        long_text = "X" * 250
        specs = [{"sub_id": "T01", "file": "WU-01-long.md", "criteria": [long_text]}]
        _write_plan(self.fd, 1, specs)
        for spec in specs:
            _write_wu(self.fd, spec)
        block = loop.build_autoclose_debt_enumeration(self.fd, 1)
        self.assertIn("X" * 200 + "…", block)
        self.assertNotIn("X" * 201, block)

    def test_symbol_exists(self):
        self.assertTrue(callable(loop.build_autoclose_debt_enumeration))

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
        self.assertEqual(second.count("Greppable criterion ALPHA-ONE"), 1)


if __name__ == "__main__":
    unittest.main()
