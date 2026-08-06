#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0056/T08 — render T07's re-verification worklist into a
`close` / `close-intermediate` dispatch's session prompt.

`format_reverification_worklist` (specfuse/loop/loop.py) renders
`criteria_state.build_reverification_worklist`'s partition into a section
appended to `wu.body` by `execute_unit_attempt`, at the same site
`format_oracle_capture` already uses (`loop.py:3353`-area) — right after
`precreate_dispatch_skeleton` seeds the artifact that reads, and before
`dispatch`.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()
from specfuse.loop import criteria_state  # noqa: E402


def _make_wu(wu_id: str, file: Path, wu_type: str, *, attempts: int = 1,
             body: str = "") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=file,
        depends_on=[],
        type=wu_type,
        model="sonnet",
        status="pending",
        attempts=attempts,
        title=wu_id,
        body=body or "**Objective.** test",
    )


_CARRY_FORWARD_ENTRY = (
    "### T01#1\n\n"
    "- **criterion:** Alpha holds.\n"
    "- **oracle:** python3 -m unittest tests.test_alpha\n"
    "- **kind:** `narrow`\n"
    "- **state:** `pass`\n"
    "- **proved_at_sha:** `deadbeef`\n"
    "- **attempt:** `1`\n"
)

_REVERIFY_ENTRY_A = (
    "### T02#1\n\n"
    "- **criterion:** Beta holds.\n"
    "- **oracle:** python3 -m unittest tests.test_beta\n"
    "- **kind:** `narrow`\n"
    "- **state:** `fail`\n"
    "- **attempt:** `1`\n"
)

_REVERIFY_ENTRY_B = (
    "### T02#2\n\n"
    "- **criterion:** Beta also holds.\n"
    "- **oracle:** python3 -m unittest tests.test_beta\n"
    "- **kind:** `narrow`\n"
    "- **state:** `fail`\n"
    "- **attempt:** `1`\n"
)

_BROAD_PASS_ENTRY = (
    "### T03#1\n\n"
    "- **criterion:** Full suite passes.\n"
    "- **oracle:** python3 -m unittest discover -s tests\n"
    "- **kind:** `broad`\n"
    "- **state:** `pass`\n"
    "- **proved_at_sha:** `deadbeef`\n"
    "- **attempt:** `1`\n"
)


class TestFormatReverificationWorklist(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_artifact(self, gate_n: int, text: str) -> Path:
        path = self.fd / criteria_state.criteria_filename(gate_n)
        path.write_text(text)
        return path

    # Criterion 2, case 1: wu.type not close/close-intermediate.
    def test_empty_for_non_close_type(self):
        self._write_artifact(1, _CARRY_FORWARD_ENTRY)
        wu = _make_wu("FEAT-TEST-0001/T09", self.fd / "WU-09.md", "implementation")
        self.assertEqual(loop.format_reverification_worklist(wu, self.fd), "")

    # Criterion 2, case 2: GATE-NN-CRITERIA.md absent.
    def test_empty_when_artifact_missing(self):
        wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90.md", "close")
        self.assertEqual(loop.format_reverification_worklist(wu, self.fd), "")

    # Criterion 2, case 3: artifact exists, parses to zero entries.
    def test_empty_when_artifact_parses_to_zero_entries(self):
        self._write_artifact(1, "# Gate 1 criteria\n\nNo entries yet.\n")
        wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90.md", "close")
        self.assertEqual(loop.format_reverification_worklist(wu, self.fd), "")

    # Criteria 3, 4: counts, carry-forward listing, grouped oracle listing.
    def test_carry_forward_and_reverify_are_rendered(self):
        self._write_artifact(
            1, _CARRY_FORWARD_ENTRY + "\n" + _REVERIFY_ENTRY_A + "\n" + _REVERIFY_ENTRY_B,
        )
        wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90.md", "close", attempts=2)

        section = loop.format_reverification_worklist(wu, self.fd)

        self.assertIn("1 criterion/criteria carried forward", section)
        self.assertIn("2 require re-verification", section)
        self.assertIn("`T01#1`", section)
        self.assertIn("python3 -m unittest tests.test_alpha", section)
        self.assertIn("proved on attempt `1`", section)
        # T02#1 and T02#2 share one oracle command -> one grouped line naming both.
        self.assertEqual(
            section.count("python3 -m unittest tests.test_beta"), 1,
            "a shared oracle command must appear once, not once per criterion",
        )
        self.assertIn("T02#1", section)
        self.assertIn("T02#2", section)

    # Criterion 5: unconditional feature-level-question statement.
    def test_feature_level_question_statement_present(self):
        self._write_artifact(1, _CARRY_FORWARD_ENTRY)
        wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90.md", "close")
        section = loop.format_reverification_worklist(wu, self.fd)
        self.assertIn("never carried forward", section)
        self.assertIn("runs this attempt regardless", section)

    # Criterion 6: a `broad` entry, even state: pass at the current attempt,
    # never appears in the carried-forward list.
    def test_broad_pass_entry_never_carried_forward(self):
        self._write_artifact(1, _BROAD_PASS_ENTRY)
        wu = _make_wu("FEAT-TEST-0001/G1-CLOSE", self.fd / "WU-90.md", "close", attempts=1)
        section = loop.format_reverification_worklist(wu, self.fd)
        self.assertNotIn("### Carried forward", section)
        self.assertIn("1 require re-verification", section)
        self.assertIn("T03#1", section)


class TestExecuteUnitAttemptCarriesWorklist(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_close_dispatch_prompt_carries_worklist(self):
        (self.fd / criteria_state.criteria_filename(1)).write_text(
            _CARRY_FORWARD_ENTRY + "\n" + _REVERIFY_ENTRY_A,
        )
        wu = _make_wu(
            "FEAT-TEST-0001/G1-CLOSE-INTERMEDIATE", self.fd / "WU-90.md",
            "close-intermediate", attempts=2,
        )
        seen_bodies = []

        def _dispatch_fn(wu, failure_note):
            seen_bodies.append(wu.body)
            return "STOP", None

        def _verify_fn(wu, feature_dir):
            return True, "ok"

        loop.execute_unit_attempt(
            wu, self.fd, None, dispatch_fn=_dispatch_fn, verify_fn=_verify_fn,
        )

        self.assertEqual(len(seen_bodies), 1)
        self.assertIn("## Re-verification worklist (gate 1)", seen_bodies[0])
        self.assertIn("T01#1", seen_bodies[0])

    def test_plan_next_dispatch_prompt_is_unchanged(self):
        (self.fd / criteria_state.criteria_filename(1)).write_text(_CARRY_FORWARD_ENTRY)
        (self.fd / "PLAN.md").write_text(
            "---\nfeature_id: FEAT-TEST-0001\nstatus: active\n---\n\n"
            "# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
            "    work_units: []\n```\n"
        )
        wu = _make_wu(
            "FEAT-TEST-0001/G1-PLAN", self.fd / "WU-91.md", "plan-next", attempts=1,
        )
        original_body = wu.body
        seen_bodies = []

        def _dispatch_fn(wu, failure_note):
            seen_bodies.append(wu.body)
            return "STOP", None

        def _verify_fn(wu, feature_dir):
            return True, "ok"

        loop.execute_unit_attempt(
            wu, self.fd, None, dispatch_fn=_dispatch_fn, verify_fn=_verify_fn,
        )

        self.assertEqual(seen_bodies, [original_body])
        self.assertNotIn("## Re-verification worklist", seen_bodies[0])


if __name__ == "__main__":
    unittest.main()
