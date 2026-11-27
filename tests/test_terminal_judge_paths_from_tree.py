#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The terminal judge-editing stop reads the judge-path registry of the tree
being closed, not only the running build's (#3551).

The driver runs from the build it pinned at process start. A gate unit that
adds a module to `arm_eval.JUDGE_MODULES` changes the registry in the tree,
not in the pinned build, so a gate whose only judge-surface edit was that
module evaluated clean and could close unacknowledged.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import arm_eval
from tests.test_arm_eval_terminal import _plan, _wu

FEATURE_ID = "FEAT-2026-8802"
_NEW = "specfuse/loop/newmod.py"


def _tree_with_registry_entry(root: Path) -> None:
    """A working tree whose own arm_eval.py lists `newmod.py` as a judge."""
    source = Path(arm_eval.__file__).read_text(encoding="utf-8")
    marker = '        "arm_eval.py",'
    assert marker in source
    (root / "specfuse/loop").mkdir(parents=True)
    (root / "specfuse/loop/arm_eval.py").write_text(
        source.replace(marker, marker + '\n        "newmod.py",', 1),
        encoding="utf-8")


class TerminalCheckReadsTheTreesRegistry(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.feature = self.root / ".specfuse/features" / f"{FEATURE_ID}-x"
        self.feature.mkdir(parents=True)
        t01, close = f"{FEATURE_ID}/T01", f"{FEATURE_ID}/G1-CLOSE"
        _plan(self.feature, [(1, [(t01, "WU-01.md"), (close, "WU-90.md")])])
        _wu(self.feature, "WU-01.md", t01, produces=[_NEW])
        _wu(self.feature, "WU-90.md", close, type_="close", status="pending")

    def test_the_running_build_does_not_list_the_new_module(self):
        self.assertNotIn(_NEW, arm_eval.JUDGE_PATHS)

    def test_a_module_the_tree_adds_to_the_registry_fires(self):
        _tree_with_registry_entry(self.root)
        verdict = arm_eval.evaluate_terminal_judge_editing(self.feature, 1)
        self.assertEqual(verdict.status, "fired", verdict.reason)
        self.assertIn(_NEW, verdict.reason)
        self.assertEqual(
            arm_eval.terminal_judge_edit_ack_keys(self.feature, 1), [_NEW])

    def test_without_a_registry_in_the_tree_the_build_decides(self):
        # A consumer project has no specfuse/loop/arm_eval.py of its own.
        verdict = arm_eval.evaluate_terminal_judge_editing(self.feature, 1)
        self.assertEqual(verdict.status, "clean", verdict.reason)

    def test_an_unloadable_tree_registry_falls_back_to_the_build(self):
        (self.root / "specfuse/loop").mkdir(parents=True)
        (self.root / "specfuse/loop/arm_eval.py").write_text("raise SystemExit(3)\n")
        verdict = arm_eval.evaluate_terminal_judge_editing(self.feature, 1)
        self.assertEqual(verdict.status, "clean", verdict.reason)


if __name__ == "__main__":
    unittest.main()
