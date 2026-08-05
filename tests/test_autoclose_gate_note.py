#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""An auto-closed gate must say so in the file a reviewer opens (#294).

When `evaluate_auto_close` closes a gate, `GATE-NN.md` reads `status: passed`
and nothing in it distinguishes *"verified and passed"* from *"the predicate
skipped the ceremony."*

The honest signal exists — the `specfuse:autoclose-debt` marker and the
auto-close section in `RETROSPECTIVE.md`, plus `auto_close: true` on the close
WU's frontmatter — but every piece of it is in a **different file** from the one
a reviewer opens at the arm-gate checkpoint to answer *"did this gate actually
pass, and on what evidence?"*

Verified still reproducing before this was written: FEAT-2026-0021 auto-closed,
and its `GATE-01.md` carries `status: passed`, a Definition of done, and an
unwritten Reflection notes placeholder — no indication the ceremony was skipped.

**The issue's literal anchor has expired.** It was filed against scaffold 0.6.0,
whose `GATE.template.md` carried a `## Verdict` section holding
`<Written at gate close.>`, and proposed stamping that placeholder. The current
template has no `## Verdict` section at all. Removing it did not fix the gap; it
removed the only hint that something was missing. So the note is appended under
its own heading rather than filling a section that no longer exists.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

from specfuse.loop.loop import (  # noqa: E402  (after sys.path setup above)
    AutoCloseDecision,
    stamp_gate_auto_close_note,
)

_GATE_BODY = (
    "---\ngate: 1\nstatus: passed\ncost_budget_usd: 6.0\n---\n\n"
    "# Gate 1 — a milestone\n\n"
    "## Definition of done\n\n- Everything is done.\n\n"
    "## Reflection notes\n\n<Written by the human at review.>\n"
)


def _decision(cost: float = 7.26, budget: float | None = 29.50) -> AutoCloseDecision:
    return AutoCloseDecision(
        auto=True,
        reasons=[],
        metrics={"gate_total_cost": cost, "gate_budget": budget},
        gate_id=1,
        feature_id="FEAT-2026-9100",
        predicate_version="v1",
    )


class TestGateAutoCloseNote(unittest.TestCase):
    def _gate(self, tmp: Path) -> Path:
        g = tmp / "GATE-01.md"
        g.write_text(_GATE_BODY)
        return g

    def test_the_note_is_written_into_the_gate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))

            stamp_gate_auto_close_note(Path(tmp), 1, _decision())

            text = g.read_text()
            self.assertIn("## Auto-close note", text)

    def test_the_note_says_the_ceremony_did_not_run(self):
        # The single fact a reviewer needs and cannot currently get from this
        # file: passed != verified-by-a-close-agent.
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))
            stamp_gate_auto_close_note(Path(tmp), 1, _decision())
            text = g.read_text()
            self.assertIn("did not run", text)
            self.assertIn("predicate=v1", text)

    def test_the_note_carries_cost_against_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))
            stamp_gate_auto_close_note(Path(tmp), 1, _decision(cost=7.26, budget=29.50))
            text = g.read_text()
            self.assertIn("$7.26", text)
            self.assertIn("$29.50", text)

    def test_an_unset_budget_renders_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))
            stamp_gate_auto_close_note(Path(tmp), 1, _decision(budget=None))
            self.assertIn("<unset>", g.read_text())

    def test_it_points_at_where_the_deferred_list_actually_lives(self):
        # The whole complaint is that the evidence is in another file. The note
        # must name that file rather than merely asserting the gap.
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))
            stamp_gate_auto_close_note(Path(tmp), 1, _decision())
            text = g.read_text()
            self.assertIn("RETROSPECTIVE.md", text)
            self.assertIn("specfuse:autoclose-debt", text)

    def test_the_existing_gate_content_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))
            stamp_gate_auto_close_note(Path(tmp), 1, _decision())
            text = g.read_text()
            self.assertIn("## Definition of done", text)
            self.assertIn("## Reflection notes", text)
            self.assertIn("status: passed", text)

    def test_it_is_idempotent(self):
        # Same guard the retrospective stub writers use: a re-arm or re-entry
        # must not stack duplicate notes.
        with tempfile.TemporaryDirectory() as tmp:
            g = self._gate(Path(tmp))
            stamp_gate_auto_close_note(Path(tmp), 1, _decision())
            stamp_gate_auto_close_note(Path(tmp), 1, _decision())
            self.assertEqual(g.read_text().count("## Auto-close note"), 1)

    def test_a_missing_gate_file_is_a_no_op(self):
        # Legacy features and odd layouts must not crash the auto-close path
        # over a legibility nicety.
        with tempfile.TemporaryDirectory() as tmp:
            stamp_gate_auto_close_note(Path(tmp), 1, _decision())  # no GATE-01.md
            self.assertFalse((Path(tmp) / "GATE-01.md").exists())


if __name__ == "__main__":
    unittest.main()
