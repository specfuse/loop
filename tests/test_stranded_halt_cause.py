#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A gate halt must name the cause that applies (#3323).

The `stranded` block printed one message for every non-`done`, non-`abandoned`
unit: "This usually means one of their dependencies was abandoned". It
special-cased a `human`-type unit at `blocked_human` (FEAT-2026-0085/T04) and
nothing else, so a gate halted by an escalated implementation unit, or by a
unit left `in_progress` when a run was killed, sent the operator to inspect a
dependency graph that was correct and named no cause that applied.

Reported from a real 0.19.0 run whose feature had no abandoned unit at all.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests._loop_loader import load_loop

loop = load_loop()


def _wu(tmp: Path, wu_id: str, *, status: str, type_: str = "implementation",
        depends_on=None, escalation_reason: str | None = None) -> "loop.WorkUnit":
    path = tmp / f"{wu_id.split('/')[-1]}.md"
    fm = [f"id: {wu_id}", f"type: {type_}", f"status: {status}", "attempts: 1"]
    if escalation_reason:
        fm.append(f"escalation_reason: {escalation_reason}")
    path.write_text("---\n" + "\n".join(fm) + "\n---\n\n# T\n", encoding="utf-8")
    wu = loop.WorkUnit.__new__(loop.WorkUnit)
    for k, v in dict(wu_id=wu_id, file=path, depends_on=depends_on or [],
                     type=type_, model="sonnet", status=status, attempts=1,
                     title="T", body="").items():
        object.__setattr__(wu, k, v)
    return wu


class HaltNamesTheCauseThatApplies(unittest.TestCase):

    def test_an_escalated_implementation_unit_is_named_as_the_cause(self):
        with TemporaryDirectory() as t:
            tmp = Path(t)
            blocked = _wu(tmp, "F/T02", status="blocked_human",
                          escalation_reason="spinning_signature_repeat")
            msg = loop.describe_stranded_units([blocked], gate_number=1)
            self.assertIn("F/T02", msg)
            self.assertIn("spinning_signature_repeat", msg)
            self.assertIn("/unblock-wu", msg)
            self.assertNotIn("abandoned", msg)

    def test_a_unit_left_in_progress_is_named_as_an_interrupted_run(self):
        with TemporaryDirectory() as t:
            tmp = Path(t)
            stuck = _wu(tmp, "F/T03", status="in_progress")
            msg = loop.describe_stranded_units([stuck], gate_number=1)
            self.assertIn("F/T03", msg)
            self.assertIn("in_progress", msg)
            self.assertIn("pending", msg)          # the recovery it names
            self.assertNotIn("abandoned", msg)

    def test_a_dependent_pending_unit_is_not_reported_as_its_own_cause(self):
        with TemporaryDirectory() as t:
            tmp = Path(t)
            blocked = _wu(tmp, "F/T02", status="blocked_human",
                          escalation_reason="spinning_signature_repeat")
            downstream = _wu(tmp, "F/T04", status="pending", depends_on=["F/T02"])
            msg = loop.describe_stranded_units([blocked, downstream], gate_number=1)
            # T04 is waiting, not broken: it must be attributed, not listed as
            # a separate thing for the operator to diagnose.
            self.assertIn("F/T02", msg)
            head, _, tail = msg.partition("F/T02")
            self.assertIn("F/T04", tail, "the dependent should follow its cause")
            self.assertNotIn("abandoned", msg)

    def test_an_abandoned_dependency_still_gets_the_original_message(self):
        # The control: the one case the old message was right about.
        with TemporaryDirectory() as t:
            tmp = Path(t)
            waiting = _wu(tmp, "F/T05", status="pending", depends_on=["F/T01"])
            msg = loop.describe_stranded_units(
                [waiting], gate_number=1, abandoned_ids={"F/T01"})
            self.assertIn("abandoned", msg)
            self.assertIn("F/T01", msg)


if __name__ == "__main__":
    unittest.main()
