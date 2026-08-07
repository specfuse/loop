# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0056/T02 — precreate_dispatch_skeleton scaffolds
# GATE-NN-CRITERIA.md for close/close-intermediate dispatches, seeded from
# the gate's substantive WUs' acceptance criteria via extract_wu_criteria
# (hoisted out of build_autoclose_debt_enumeration). The seeded artifact
# must survive fold_cumulative_on_rearm — that's the load-bearing half.

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()
from specfuse.loop import criteria_state  # noqa: E402

_WU_BODY_TAIL = (
    "\n\n**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _write_plan(fd: Path, gate_number: int, wu_specs: list[dict]) -> None:
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


def _make_wu(wu_id: str, file: Path, wu_type: str, body: str = "") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=file,
        depends_on=[],
        type=wu_type,
        model="sonnet",
        status="pending",
        attempts=0,
        title=wu_id,
        body=body or ("**Objective.** test" + _WU_BODY_TAIL),
    )


class TestCriteriaArtifactPrecreation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _criteria_path(self, gate_n: int) -> Path:
        return self.fd / f"GATE-{gate_n:02d}-CRITERIA.md"

    def _two_wu_gate(self, gate_n: int = 1):
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
        _write_plan(self.fd, gate_n, specs)
        for spec in specs:
            _write_wu(self.fd, spec)
        return specs

    def test_close_dispatch_precreates_criteria_artifact(self):
        self._two_wu_gate(gate_n=1)
        close_wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90-close.md", "close")
        loop.precreate_dispatch_skeleton(close_wu, self.fd)

        path = self._criteria_path(1)
        self.assertTrue(path.is_file(), "GATE-01-CRITERIA.md must be pre-created")
        entries = criteria_state.parse_criteria_state(path.read_text())
        ids = {e.criterion_id for e in entries}
        self.assertEqual(
            ids,
            {"T01#1", "T01#2", "T02#1"},
            "seeded entries must be keyed by producing WU sub-ID + ordinal",
        )
        for e in entries:
            self.assertEqual(e.state, "unverified")
            self.assertIsNone(e.oracle)
            self.assertIsNone(e.kind)
            self.assertIsNone(e.proved_at_sha)
            self.assertIsNone(e.attempt)

    def test_close_intermediate_dispatch_precreates_criteria_artifact(self):
        self._two_wu_gate(gate_n=1)
        wu = _make_wu(
            "FEAT-TEST-0001/G1-CLOSE-INTERMEDIATE",
            self.fd / "WU-90-close-intermediate.md",
            "close-intermediate",
        )
        loop.precreate_dispatch_skeleton(wu, self.fd)
        self.assertTrue(self._criteria_path(1).is_file())

    def test_no_artifact_for_other_wu_types(self):
        self._two_wu_gate(gate_n=1)
        for wu_type in ("plan-next", "implementation", "retrospective", "lessons", "docs"):
            with self.subTest(wu_type=wu_type):
                with tempfile.TemporaryDirectory() as td:
                    fd = Path(td)
                    self._two_wu_gate_in(fd, gate_n=1)
                    wu = _make_wu(f"FEAT-TEST-0001/G1-{wu_type.upper()}", fd / f"WU-90-{wu_type}.md", wu_type)
                    loop.precreate_dispatch_skeleton(wu, fd)
                    self.assertFalse(
                        (fd / "GATE-01-CRITERIA.md").is_file(),
                        f"wu.type={wu_type} must not precreate a criteria artifact",
                    )

    def _two_wu_gate_in(self, fd: Path, gate_n: int = 1):
        specs = [
            {
                "sub_id": "T01",
                "file": "WU-01-alpha.md",
                "criteria": ["Greppable criterion ALPHA-ONE must hold."],
            },
        ]
        _write_plan(fd, gate_n, specs)
        for spec in specs:
            _write_wu(fd, spec)
        return specs

    def test_reseed_is_additive_and_preserves_recorded_state(self):
        specs = self._two_wu_gate(gate_n=1)
        close_wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90-close.md", "close")
        loop.precreate_dispatch_skeleton(close_wu, self.fd)

        path = self._criteria_path(1)
        entries = criteria_state.parse_criteria_state(path.read_text())
        updated = [
            criteria_state.CriterionStateEntry(
                criterion_id=e.criterion_id,
                criterion=e.criterion,
                oracle="tests/test_alpha.py::test_one" if e.criterion_id == "T01#1" else e.oracle,
                kind="narrow" if e.criterion_id == "T01#1" else e.kind,
                state="pass" if e.criterion_id == "T01#1" else e.state,
                proved_at_sha="deadbeef" if e.criterion_id == "T01#1" else e.proved_at_sha,
                attempt="1" if e.criterion_id == "T01#1" else e.attempt,
            )
            for e in entries
        ]
        path.write_text(criteria_state.render_criteria_state(updated))

        # A new criterion appears on WU T02 between attempts.
        specs[1]["criteria"].append("Greppable criterion BETA-TWO must hold.")
        _write_wu(self.fd, specs[1])

        loop.precreate_dispatch_skeleton(close_wu, self.fd)

        reparsed = {e.criterion_id: e for e in criteria_state.parse_criteria_state(path.read_text())}
        self.assertEqual(reparsed["T01#1"].state, "pass")
        self.assertEqual(reparsed["T01#1"].oracle, "tests/test_alpha.py::test_one")
        self.assertEqual(reparsed["T01#1"].kind, "narrow")
        self.assertEqual(reparsed["T01#1"].attempt, "1")
        self.assertIn("T02#2", reparsed)
        self.assertEqual(reparsed["T02#2"].state, "unverified")
        self.assertIsNone(reparsed["T02#2"].oracle)

    def test_criteria_artifact_survives_rearm_fold(self):
        self._two_wu_gate(gate_n=1)
        close_wu_file = self.fd / "WU-90-close.md"
        close_wu_file.write_text(
            "---\nid: FEAT-TEST-0001/G1-CLOSE\ntype: close\nmodel: sonnet\n"
            "status: pending\nattempts: 0\nre_arm_count: 1\ncost_usd: 3.0\n"
            "input_tokens: 100\noutput_tokens: 50\n"
            "re_arm_history:\n"
            "  - at: 2026-08-01T00:00:00Z\n"
            "    reason: \"re-arm\"\n"
            "    prior_attempts: 2\n"
            "---\n\n# close-a" + _WU_BODY_TAIL
        )
        close_wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", close_wu_file, "close")
        loop.precreate_dispatch_skeleton(close_wu, self.fd)

        path = self._criteria_path(1)
        before = criteria_state.parse_criteria_state(path.read_text())

        loop.fold_cumulative_on_rearm(close_wu, loop.Backend())

        after = criteria_state.parse_criteria_state(path.read_text())
        self.assertEqual(before, after, "re-arm fold must not alter the criteria artifact")


if __name__ == "__main__":
    unittest.main()
