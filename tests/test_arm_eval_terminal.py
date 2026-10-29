#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for arm_eval.evaluate_terminal_judge_editing (FEAT-2026-0246/T01).

Each fixture is a self-contained temp feature directory: PLAN.md plus the
unit files of the gate under test. The check reads nothing else.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import arm_eval
from specfuse.loop.arm_eval import evaluate_terminal_judge_editing

FEATURE_ID = "FEAT-2026-8802"


def _plan(feature: Path, gates: "list[tuple[int, list[tuple[str, str]]]]") -> None:
    graph = "```yaml\ngates:\n"
    for gnum, wus in gates:
        graph += f"  - gate: {gnum}\n    file: GATE-{gnum:02d}.md\n    work_units:\n"
        for wid, wfile in wus:
            graph += f"      - id: {wid}\n        file: {wfile}\n        depends_on: []\n"
    graph += "```\n"
    (feature / "PLAN.md").write_text(
        f"---\nfeature_id: {FEATURE_ID}\ntitle: t\nstatus: active\n---\n\n# Plan\n\n{graph}"
    )


def _wu(feature: Path, filename: str, wid: str, *, type_: str = "implementation",
        status: str = "done", produces: "list[str] | None" = None,
        helper: "list[str] | None" = None) -> None:
    lines = [f"id: {wid}", f"type: {type_}", f"status: {status}"]
    if produces is not None:
        lines.append("produces:")
        lines += [f"  - {p}" for p in produces]
    if helper is not None:
        lines.append("produces_driver_helper:")
        lines += [f"  - {h}" for h in helper]
    (feature / filename).write_text("---\n" + "\n".join(lines) + "\n---\n\n# Unit\n\nbody\n")


class TerminalJudgeEditingTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.feature = Path(self._tmp.name)
        self.t01 = f"{FEATURE_ID}/T01"
        self.close = f"{FEATURE_ID}/G1-CLOSE"

    def _single_gate(self, **wu_kwargs) -> "arm_eval.ClassVerdict":
        _plan(self.feature, [(1, [(self.t01, "WU-01.md"), (self.close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", self.t01, **wu_kwargs)
        _wu(self.feature, "WU-90.md", self.close, type_="close", status="pending")
        return evaluate_terminal_judge_editing(self.feature, 1)

    def test_judge_module_path_fires(self):
        v = self._single_gate(produces=["specfuse/loop/arm_eval.py"])
        self.assertEqual(v.status, "fired")
        self.assertEqual(v.reason, f"{self.t01} produces specfuse/loop/arm_eval.py")

    def test_universal_path_fires(self):
        v = self._single_gate(produces=[".github/workflows/ci.yml"])
        self.assertEqual(v.status, "fired")
        self.assertIn(".github/workflows/ci.yml", v.reason)

    def test_shipped_docs_are_clean(self):
        v = self._single_gate(produces=["specfuse/loop/data/docs/x.md"])
        self.assertEqual(v.status, "clean")

    def test_shipped_rules_fire(self):
        v = self._single_gate(produces=["specfuse/loop/data/rules/x.md"])
        self.assertEqual(v.status, "fired")

    def test_ordinary_path_is_clean(self):
        v = self._single_gate(produces=["docs/x.md", "tests/test_x.py"])
        self.assertEqual(v.status, "clean")

    def test_driver_helper_fires(self):
        v = self._single_gate(produces=["docs/x.md"], helper=["specfuse/loop/helper.py"])
        self.assertEqual(v.status, "fired")
        self.assertIn(f"{self.t01} declares produces_driver_helper", v.reason)

    def test_close_unit_is_ignored(self):
        _plan(self.feature, [(1, [(self.t01, "WU-01.md"), (self.close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", self.t01, produces=["docs/x.md"])
        _wu(self.feature, "WU-90.md", self.close, type_="close", status="done",
            produces=["specfuse/loop/arm_eval.py"])
        self.assertEqual(evaluate_terminal_judge_editing(self.feature, 1).status, "clean")

    def test_pending_and_abandoned_units_are_ignored(self):
        for status in ("pending", "abandoned"):
            with self.subTest(status=status):
                v = self._single_gate(status=status, produces=["specfuse/loop/arm_eval.py"])
                self.assertEqual(v.status, "clean")

    def test_multi_gate_checks_only_the_named_gate(self):
        t02 = f"{FEATURE_ID}/T02"
        g1_close = f"{FEATURE_ID}/G1-CLOSE"
        g2_close = f"{FEATURE_ID}/G2-CLOSE"
        _plan(self.feature, [
            (1, [(self.t01, "WU-01.md"), (g1_close, "WU-90.md")]),
            (2, [(t02, "WU-02.md"), (g2_close, "WU-91.md")]),
        ])
        _wu(self.feature, "WU-01.md", self.t01, produces=["specfuse/loop/arm_eval.py"])
        _wu(self.feature, "WU-90.md", g1_close, type_="close")
        _wu(self.feature, "WU-02.md", t02, produces=["docs/x.md"])
        _wu(self.feature, "WU-91.md", g2_close, type_="close", status="pending")
        self.assertEqual(evaluate_terminal_judge_editing(self.feature, 2).status, "clean")
        self.assertEqual(evaluate_terminal_judge_editing(self.feature, 1).status, "fired")

    def test_unknown_gate_is_clean(self):
        self._single_gate(produces=["specfuse/loop/arm_eval.py"])
        self.assertEqual(evaluate_terminal_judge_editing(self.feature, 9).status, "clean")

    def _acked(self, paths, **wu_kwargs):
        _plan(self.feature, [(1, [(self.t01, "WU-01.md"), (self.close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", self.t01, **wu_kwargs)
        _wu(self.feature, "WU-90.md", self.close, type_="close", status="pending")
        wu90 = self.feature / "WU-90.md"
        wu90.write_text(wu90.read_text().replace(
            "status: pending\n",
            "status: pending\njudge_edit_acknowledged:\n"
            f"  paths: [{', '.join(paths)}]\n  reason: \"seen\"\n", 1))
        return evaluate_terminal_judge_editing(self.feature, 1)

    def test_full_coverage_is_clean(self):
        v = self._acked(["specfuse/loop/arm_eval.py"],
                        produces=["specfuse/loop/arm_eval.py"])
        self.assertEqual(v.status, "clean")
        self.assertIn("specfuse/loop/arm_eval.py", v.reason)

    def test_partial_coverage_fires_naming_only_uncovered(self):
        v = self._acked(["specfuse/loop/arm_eval.py"],
                        produces=["specfuse/loop/arm_eval.py", "specfuse/loop/judge.py"])
        self.assertEqual(v.status, "fired")
        self.assertIn("specfuse/loop/judge.py", v.reason)
        self.assertNotIn("arm_eval.py", v.reason)

    def test_driver_helper_hit_covered_by_literal_entry(self):
        v = self._acked(["produces_driver_helper"],
                        produces=["docs/x.md"], helper=["specfuse/loop/helper.py"])
        self.assertEqual(v.status, "clean")
        v = self._acked(["specfuse/loop/helper.py"],
                        produces=["docs/x.md"], helper=["specfuse/loop/helper.py"])
        self.assertEqual(v.status, "fired")

    def test_acknowledgement_without_hits_is_clean_and_unacknowledged(self):
        v = self._acked(["specfuse/loop/arm_eval.py"], produces=["docs/x.md"])
        self.assertEqual(v.status, "clean")
        self.assertFalse(v.reason.startswith(arm_eval.ACKNOWLEDGED_REASON_PREFIX))

    def test_ack_keys_name_paths_and_the_driver_helper_entry(self):
        _plan(self.feature, [(1, [(self.t01, "WU-01.md"), (f"{FEATURE_ID}/T02", "WU-02.md"),
                                  (self.close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", self.t01,
            produces=["specfuse/loop/arm_eval.py", "docs/x.md"],
            helper=["specfuse/loop/helper.py"])
        _wu(self.feature, "WU-02.md", f"{FEATURE_ID}/T02",
            produces=["specfuse/loop/arm_eval.py"], helper=["specfuse/loop/other.py"])
        _wu(self.feature, "WU-90.md", self.close, type_="close", status="pending")
        keys = arm_eval.terminal_judge_edit_ack_keys(self.feature, 1)
        self.assertEqual(keys, ["produces_driver_helper", "specfuse/loop/arm_eval.py"])

    def test_acknowledging_exactly_the_ack_keys_is_clean(self):
        _plan(self.feature, [(1, [(self.t01, "WU-01.md"), (self.close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", self.t01,
            produces=["specfuse/loop/arm_eval.py"], helper=["specfuse/loop/helper.py"])
        _wu(self.feature, "WU-90.md", self.close, type_="close", status="pending")
        keys = arm_eval.terminal_judge_edit_ack_keys(self.feature, 1)
        v = self._acked(keys, produces=["specfuse/loop/arm_eval.py"],
                        helper=["specfuse/loop/helper.py"])
        self.assertEqual(v.status, "clean")

    def test_ack_keys_empty_without_hits(self):
        _plan(self.feature, [(1, [(self.t01, "WU-01.md"), (self.close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", self.t01, produces=["docs/x.md"])
        _wu(self.feature, "WU-90.md", self.close, type_="close", status="pending")
        self.assertEqual(arm_eval.terminal_judge_edit_ack_keys(self.feature, 1), [])

    def test_not_a_successor_arm_class(self):
        self.assertNotIn("terminal_judge_editing", arm_eval.CLASS_NAMES)


if __name__ == "__main__":
    unittest.main()
