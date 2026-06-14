#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Legacy 4-WU close sequence triggers terminal flips — regression for issue #16.

Pre-FEAT-2026-0015 feature scaffolds use the four-WU closing sequence
(`retrospective` → `lessons` → `docs` → `plan-next`). FEAT-2026-0015 added
the combined `close`/`close-intermediate` types and wired
`fire_terminal_flips` to fire ONLY on `close`-type WUs. The legacy 4-WU
sequence then had no terminating-equivalent trigger: the driver finished
the gate, printed `Terminal — feature ready to wrap.`, but
`fire_terminal_flips` never ran. `GATE-NN.md` stayed `awaiting_review`,
and `/wrap-feature` refused on the hedged-gate state.

This regression covers the legacy-sequence detection helper and verifies
`fire_terminal_flips` works correctly when called with a `plan-next` WU
(its only `wu_id`-derived behavior is feature_id extraction).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _wu(wu_id: str, type_: str, status: str = "done") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path("/dev/null"),
        depends_on=[],
        type=type_,
        model="sonnet",
        effort="medium",
        status=status,
        attempts=1,
        title="x",
        body="",
    )


def _gate(number: int):
    # Minimal gate stub: only `.number` is needed by the helper's
    # terminal-gate identity check (`gate is gates[-1]`).
    class _G:
        pass
    g = _G()
    g.number = number
    g.refs = []
    return g


class TestLegacy4WUDetection(unittest.TestCase):
    """`_legacy_4wu_terminal_close_complete` helper — issue #16."""

    def setUp(self):
        # Build a terminal gate with the four legacy close-type WUs, all done.
        self.gate = _gate(1)
        self.other_gate = _gate(2)
        self.units = [
            _wu("FEAT-2026-0001/T01", "implementation"),
            _wu("FEAT-2026-0001/G1-RETRO", "retrospective"),
            _wu("FEAT-2026-0001/G1-LESSONS", "lessons"),
            _wu("FEAT-2026-0001/G1-DOCS", "docs"),
            _wu("FEAT-2026-0001/G1-PLAN", "plan-next"),
        ]

    def test_plan_next_on_terminal_gate_with_full_set_returns_true(self):
        plan_next = next(u for u in self.units if u.type == "plan-next")
        self.assertTrue(
            loop._legacy_4wu_terminal_close_complete(
                plan_next, self.units, self.gate, [self.gate],
            ),
            "all four legacy close WUs done on terminal gate must trigger",
        )

    def test_plan_next_on_non_terminal_gate_returns_false(self):
        plan_next = next(u for u in self.units if u.type == "plan-next")
        # gate is gate 1; gates list ends with gate 2 → gate 1 is not terminal
        self.assertFalse(
            loop._legacy_4wu_terminal_close_complete(
                plan_next, self.units, self.gate, [self.gate, self.other_gate],
            ),
            "non-terminal gate must not trigger terminal-flips",
        )

    def test_non_plan_next_wu_returns_false(self):
        docs = next(u for u in self.units if u.type == "docs")
        self.assertFalse(
            loop._legacy_4wu_terminal_close_complete(
                docs, self.units, self.gate, [self.gate],
            ),
            "trigger fires only on the last (plan-next) WU of the sequence",
        )

    def test_incomplete_sequence_returns_false(self):
        # Remove the docs WU
        units = [u for u in self.units if u.type != "docs"]
        plan_next = next(u for u in units if u.type == "plan-next")
        self.assertFalse(
            loop._legacy_4wu_terminal_close_complete(
                plan_next, units, self.gate, [self.gate],
            ),
            "missing one of retro/lessons/docs/plan-next must NOT trigger",
        )

    def test_one_required_wu_not_done_returns_false(self):
        # Mark retrospective WU as in_progress
        for u in self.units:
            if u.type == "retrospective":
                u.status = "in_progress"
        plan_next = next(u for u in self.units if u.type == "plan-next")
        self.assertFalse(
            loop._legacy_4wu_terminal_close_complete(
                plan_next, self.units, self.gate, [self.gate],
            ),
            "all four must be DONE for the sequence to be complete",
        )


class TestFireTerminalFlipsWithPlanNextWU(unittest.TestCase):
    """`fire_terminal_flips` works correctly when called with a `plan-next` WU."""

    def test_plan_next_wu_flips_gate_and_roadmap(self):
        """`fire_terminal_flips` is wu-type-agnostic; passing plan-next must flip
        the terminal gate and the roadmap row exactly the same way as a close WU.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = Path(tmp)
            specfuse = repo / ".specfuse"
            specfuse.mkdir()
            feature_id = "FEAT-2026-9999"
            feature_dir = specfuse / "features" / f"{feature_id}-test"
            feature_dir.mkdir(parents=True)

            (feature_dir / "PLAN.md").write_text(
                f"---\nfeature_id: {feature_id}\nstatus: done\n---\n\n"
                f"```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
                f"    work_units: []\n```\n"
            )
            (feature_dir / "GATE-01.md").write_text(
                "---\ngate: 1\nstatus: awaiting_review\n---\n"
            )

            (specfuse / "roadmap.md").write_text(
                "---\nproject: test\n---\n\n# Roadmap\n\n"
                "| Feature ID | Title | Status | Folder | Detail |\n"
                "|------------|-------|--------|--------|--------|\n"
                f"| {feature_id} | Test feature | active | — | — |\n\n"
                f"## {feature_id} — Test feature\n\nContent.\n"
            )
            (specfuse / "roadmap-archive.md").write_text(
                "---\nproject: test\n---\n\n# Archived\n\n"
                "<!-- Archived sections appended below -->\n"
            )

            plan_next_wu = loop.WorkUnit(
                wu_id=f"{feature_id}/G1-PLAN",
                file=feature_dir / "WU-G1-PLAN.md",
                depends_on=[],
                type="plan-next",
                model="opus",
                effort="high",
                status="done",
                attempts=1,
                title="Plan next",
                body="",
            )

            modified = loop.fire_terminal_flips(plan_next_wu, feature_dir, repo)

            # Gate flipped to passed.
            gate_text = (feature_dir / "GATE-01.md").read_text()
            self.assertIn("status: passed", gate_text)
            # Roadmap row flipped active → done.
            roadmap_text = (specfuse / "roadmap.md").read_text()
            self.assertIn(f"| {feature_id} | Test feature | done |", roadmap_text)
            self.assertNotIn(f"| {feature_id} | Test feature | active |", roadmap_text)
            # Modified set is non-empty.
            self.assertTrue(modified, "modified set must be non-empty when flips happen")


if __name__ == "__main__":
    unittest.main()
