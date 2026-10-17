#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A close re-armed the way `/unblock-wu` documents must reach dispatch (#3508).

Re-arming a `close` sets its `attempts` to 0 while `GATE-NN-CRITERIA.md` still
records the superseded attempt. #3279 repairs that mismatch in
`_precreate_criteria_state_stub`, but only at dispatch. The once-per-gate broad
run (FEAT-2026-0109/T06) runs first, and in a repository whose `tests` gate
includes the corpus `close-l` sweep
(`test_lint_closing_criteria.TestCorpusSweepStaysClean`), it went red on exactly
that mismatch:

    close-l: T01#5: broad entry reads state: pass but attempt '1' != current attempt '0'

The gate went back to `awaiting_review` and the close never dispatched, so the
repair that would have cleared it never ran (FEAT-2026-0204, 2026-10-17). The
stale record must be repaired before the broad run measures the tree.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._workspace import integration_workspace
from tests.test_gate_broad_run import _BroadRunTestCase, loop, scaffold_feature

from specfuse.loop import lint_closing

_FEATURE = "FEAT-2026-8508"
_SLUG = "rearm-broad"

_STALE_CRITERIA = (
    "# Gate 1 — per-criterion state\n\n"
    f"Written by `{_FEATURE}/G1-CLOSE`.\n\n"
    "### T01#1\n"
    "- **criterion:** the whole suite still passes\n"
    "- **oracle:** `python3 -m unittest discover`\n"
    "- **kind:** `broad`\n"
    "- **state:** `pass`\n"
    "- **attempt:** `1`\n"
)


def _rearmed_close(root: Path) -> Path:
    """T01 done; the close re-armed to pending/attempts 0 after an attempt-1
    close recorded a criteria artifact — the state `/unblock-wu` leaves."""
    fdir = scaffold_feature(root, _FEATURE, _SLUG, f"feat/{_SLUG}")
    t01 = fdir / "WU-T01.md"
    t01.write_text(t01.read_text().replace("status: pending\nattempts: 0",
                                           "status: done\nattempts: 1"))
    (fdir / "GATE-01-CRITERIA.md").write_text(_STALE_CRITERIA)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "re-armed close with a stale criteria record"], check=True)
    return fdir


class TestRearmedCloseReachesDispatch(_BroadRunTestCase):

    def test_broad_run_sees_no_close_l_finding_for_a_rearmed_close(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n  - name: tests\n    command: \"true\"\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            fdir = _rearmed_close(root)

            # Stands in for the corpus close-l sweep a real `tests` gate runs:
            # what the lint says about this feature at the moment the broad set
            # is measured.
            seen_at_broad_run = []

            def recording(gate_set, feature_dir, _capture_returncodes=None):
                findings, _ = lint_closing.lint_closing(fdir)
                seen_at_broad_run.append([f for f in findings if "close-l" in f])
                return [{"name": g["name"], "ok": True,
                         "report": f"### {g['name']}: PASS"} for g in gate_set]

            self._stub_agent(recording)
            loop.run(None, dry_run=False)

            self.assertTrue(seen_at_broad_run, "the broad run must have run")
            self.assertEqual(seen_at_broad_run[0], [],
                             "a re-armed close's stale criteria record must be "
                             "repaired before the broad run measures the tree")

    def test_the_repair_is_committed_not_left_dirty(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n  - name: tests\n    command: \"false\"\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            fdir = _rearmed_close(root)

            def red(gate_set, feature_dir, _capture_returncodes=None):
                return [{"name": g["name"], "ok": False,
                         "report": f"### {g['name']}: FAIL\n```\nboom\n```"}
                        for g in gate_set]

            self._stub_agent(red)
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "a red broad run halts the gate")

            status = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain", "--",
                 str(fdir / "GATE-01-CRITERIA.md")],
                capture_output=True, text=True, check=True).stdout
            self.assertEqual(status, "", "the repaired criteria record must be "
                             "committed with the halt, not left uncommitted")
            self.assertNotIn("attempt:** `1`",
                             (fdir / "GATE-01-CRITERIA.md").read_text())


if __name__ == "__main__":
    unittest.main()
