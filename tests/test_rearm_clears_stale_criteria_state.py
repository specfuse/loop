#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A re-armed close does not inherit a superseded attempt's criteria state (#3279).

Re-arming a `close` resets its `attempts` to 0, but `GATE-NN-CRITERIA.md`
keeps recording the attempt that ran before the re-arm. The two disagree and
`check_criteria_state_well_formed` refuses the tree:

    close-l: G3-CLOSE#1: broad entry reads state: pass but attempt '1'
             != current attempt '0'

The gate then cannot progress — the broad run goes red on the corpus lint, the
close never dispatches, and every restart repeats it. During FEAT-2026-0109
this recurred three times across two closes and was only ever cleared by
deleting the artifact by hand; it cost more of that session than any code
defect did.

The fix lives at dispatch rather than in `/unblock-wu`'s prose so that it
covers every re-arm path — the skill, a hand edit, or future tooling. An entry
whose recorded `attempt` is greater than the WU's current `attempts` was
measured in a cycle that no longer exists, so it is reset to `unverified`.
Entries at or below the current attempt keep the additive behaviour
`_precreate_criteria_state_stub`'s docstring protects.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _feature_with_criteria(tmp: Path, recorded_attempt: str) -> Path:
    """A gate-1 feature whose criteria artifact records `recorded_attempt`."""
    fdir = tmp / "feature"
    (fdir / ".").mkdir(parents=True, exist_ok=True)

    (fdir / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9999\ntitle: t\nslug: s\n"
        "branch: feat/x\nroadmap_goal: g\nstatus: active\n---\n\n"
        "# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units:\n      - id: FEAT-2026-9999/T01\n"
        "        file: WU-01-x.md\n        depends_on: []\n"
        "      - id: FEAT-2026-9999/G1-CLOSE\n"
        "        file: WU-90-close.md\n        depends_on: []\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-01-x.md").write_text(
        "---\nid: FEAT-2026-9999/T01\ntype: implementation\nstatus: done\n"
        "attempts: 1\n---\n\n# T01\n\n**Acceptance criteria.**\n\n"
        "- the thing works\n"
    )
    (fdir / "WU-90-close.md").write_text(
        "---\nid: FEAT-2026-9999/G1-CLOSE\ntype: close\nstatus: pending\n"
        "attempts: 0\n---\n\n# Close\n"
    )

    (fdir / "GATE-01-CRITERIA.md").write_text(
        "# Gate 1 — per-criterion state\n\n"
        "Written by `FEAT-2026-9999/G1-CLOSE`.\n\n"
        "### T01#1\n"
        "- **criterion:** the thing works\n"
        "- **kind:** `narrow`\n"
        "- **state:** `pass`\n"
        f"- **attempt:** `{recorded_attempt}`\n"
    )
    return fdir


class TestRearmClearsStaleCriteriaState(unittest.TestCase):

    def _close_wu(self, fdir: Path, attempts: int):
        wu = loop.load_work_unit(fdir / "WU-90-close.md") if hasattr(
            loop, "load_work_unit") else None
        if wu is None:                       # construct directly if no loader
            wu = loop.WorkUnit(
                wu_id="FEAT-2026-9999/G1-CLOSE", file=fdir / "WU-90-close.md",
                depends_on=[], type="close", model="opus", status="pending",
                attempts=attempts, title="Close", body="",
            )
        else:
            wu.attempts = attempts
        return wu

    def test_an_entry_from_a_superseded_attempt_is_reset(self):
        with tempfile.TemporaryDirectory() as td:
            # Recorded attempt 1; the re-arm set the WU back to attempts 0.
            fdir = _feature_with_criteria(Path(td), "1")
            wu = self._close_wu(fdir, attempts=0)

            loop.precreate_dispatch_skeleton(wu, fdir)

            text = (fdir / "GATE-01-CRITERIA.md").read_text()
            self.assertNotIn(
                "**state:** `pass`", text,
                "an entry recorded against attempt 1 is stale once the WU is "
                "back at attempt 0 — leaving it makes the corpus lint refuse "
                "the tree and the gate cannot progress (#3279)")
            self.assertIn("**state:** `unverified`", text)

    def test_an_entry_at_the_current_attempt_is_untouched(self):
        """The additive behaviour the stub's docstring protects.

        A close re-running inside one attempt cycle must keep the state it
        already recorded; only a SUPERSEDED cycle's entry is stale.
        """
        with tempfile.TemporaryDirectory() as td:
            fdir = _feature_with_criteria(Path(td), "1")
            wu = self._close_wu(fdir, attempts=1)

            loop.precreate_dispatch_skeleton(wu, fdir)

            text = (fdir / "GATE-01-CRITERIA.md").read_text()
            self.assertIn(
                "**state:** `pass`", text,
                "an entry at the current attempt is not stale and must keep "
                "the state the close recorded")

    def test_an_entry_with_no_recorded_attempt_is_untouched(self):
        """A seeded-but-unverified entry has no attempt and is not stale."""
        with tempfile.TemporaryDirectory() as td:
            fdir = _feature_with_criteria(Path(td), "1")
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "# Gate 1 — per-criterion state\n\n### T01#1\n"
                "- **criterion:** the thing works\n"
                "- **state:** `unverified`\n"
            )
            wu = self._close_wu(fdir, attempts=0)

            loop.precreate_dispatch_skeleton(wu, fdir)

            text = (fdir / "GATE-01-CRITERIA.md").read_text()
            self.assertIn("**state:** `unverified`", text)


if __name__ == "__main__":
    unittest.main()
