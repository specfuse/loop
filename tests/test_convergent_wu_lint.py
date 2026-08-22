#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A convergent work unit must be armed with a feedback channel (#2652).

#2652 asked whether the loop should host spec authoring at all, or refuse it
and redirect to the authoring skills. The answer taken: **support it, and
refuse only the misconfigured case** — a prohibition would keep the work
happening and lose only the record of it, which is the artifact the
methodology exists to produce.

This is that refusal. `iterate_on_failure` (#2650) only works when each
attempt can see what the validator currently reports, which is what an
`oracles` set delivers pre-dispatch. Declared without one, a unit iterates
*blind*: it keeps its tree and learns nothing new about it, which is worse
than the discard it opted out of, because it also compounds.

ERROR, not WARN, on `check_closing_guard_literals`' own stated rule — the
signal is structural (frontmatter fields, not a prose match) and an ERROR
must be satisfiable on a populated tree. Measured 2026-08-22: **zero**
existing work units in this repository declare `iterate_on_failure`, so the
live tree is clean by construction and this cannot redden anyone's build
retroactively.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

_GRAPH = (
    "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
    "      - id: FEAT-2026-9999/T01\n        file: WU-01.md\n"
    "        depends_on: []\n```\n"
)


def _feature(tmp: Path, wu_fm_extra: str) -> Path:
    feat = tmp / "feat"
    feat.mkdir()
    (feat / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9999\ntitle: T\nbranch: feat/t\n"
        "roadmap_goal: g\nstatus: planned\n---\n\n" + _GRAPH)
    (feat / "WU-01.md").write_text(
        "---\nid: FEAT-2026-9999/T01\ntype: implementation\nstatus: pending\n"
        + wu_fm_extra + "---\n\n# Unit\n\nBody.\n")
    (feat / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
    return feat


def _findings(feat: Path) -> list:
    return lint_plan.check_convergent_wu_wiring(
        feat, {"status": "planned"},
        [{"file": "GATE-01.md",
          "work_units": [{"id": "FEAT-2026-9999/T01", "file": "WU-01.md"}]}])


class TestAConvergentUnitNeedsAnOracle(unittest.TestCase):
    def test_iterating_without_an_oracles_set_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), "iterate_on_failure: true\n")
            out = _findings(feat)

        self.assertTrue(out, "expected a finding")
        self.assertTrue(out[0].startswith("ERROR:"), out)
        self.assertIn("oracles", out[0])

    def test_the_message_names_the_work_unit_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), "iterate_on_failure: true\n")
            out = _findings(feat)

        self.assertIn("WU-01.md", out[0])

    def test_iterating_with_an_oracles_set_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(
                Path(tmp), "iterate_on_failure: true\noracles: specs-validate\n")
            out = _findings(feat)

        self.assertEqual(out, [])


class TestTheContradictoryCeilingIsCaught(unittest.TestCase):
    def test_iterating_with_a_single_attempt_is_an_error(self):
        # One attempt cannot iterate: there is no second pass to continue
        # into, so the flag is a no-op the author plainly did not intend.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(
                Path(tmp),
                "iterate_on_failure: true\noracles: v\nmax_attempts: 1\n")
            out = _findings(feat)

        self.assertTrue(out, "expected a finding")
        self.assertTrue(any("max_attempts" in ln for ln in out), out)

    def test_iterating_with_room_to_iterate_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(
                Path(tmp),
                "iterate_on_failure: true\noracles: v\nmax_attempts: 8\n")

            self.assertEqual(_findings(feat), [])


class TestTheCheckStaysOutOfTheWayOtherwise(unittest.TestCase):
    def test_a_unit_not_declaring_the_flag_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), "")

            self.assertEqual(_findings(feat), [])

    def test_a_unit_with_oracles_but_not_iterating_is_untouched(self):
        # `oracles` is useful on its own; it does not imply convergence.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), "oracles: v\nmax_attempts: 1\n")

            self.assertEqual(_findings(feat), [])

    def test_a_done_unit_is_sealed_history(self):
        # Backfilling arming rules onto completed work is pointless, and the
        # repo skips `done` units in every sibling check.
        with tempfile.TemporaryDirectory() as tmp:
            feat = tmp_feat = _feature(Path(tmp), "iterate_on_failure: true\n")
            wu = tmp_feat / "WU-01.md"
            wu.write_text(wu.read_text().replace(
                "status: pending", "status: done"))

            self.assertEqual(_findings(feat), [])


class TestTheLiveTreeStaysClean(unittest.TestCase):
    def test_the_real_repository_passes_this_check(self):
        # An ERROR must be satisfiable on a populated tree
        # (`[FEAT-2026-0015/G2-CLOSE]`). Runs the real check over every real
        # feature folder rather than asserting the measurement in prose.
        from tests._loop_loader import REPO_ROOT

        found = []
        root = REPO_ROOT / ".specfuse" / "features"
        for feat in sorted(p for p in root.iterdir() if p.is_dir()):
            plan = feat / "PLAN.md"
            if not plan.is_file():
                continue
            try:
                fm, body = lint_plan.read_frontmatter(plan)
                graph = lint_plan._find_task_graph_block(body)
            except Exception:  # noqa: BLE001 - another check's finding
                continue
            if graph is None:
                continue
            found.extend(lint_plan.check_convergent_wu_wiring(
                feat, fm, graph.get("gates", [])))
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
