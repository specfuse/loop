#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression test for #100 — the plan-next-draft lint hook must use a
package-relative import.

`loop.py`'s plan-next hook imported `from lint_plan import lint_plan_next_draft`
(flat). That only resolved when the scripts were copied side-by-side (pre-pip);
in the installed package it raises `No module named 'lint_plan'`, so the
plan-next gate logs a warning and the draft lint never runs. The import is
function-local on purpose (lint_plan imports `from .loop import VERDICT_VALUES`,
so a module-top import would be circular) — the fix is to make the local import
package-relative, not to hoist it.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOOP_SRC = REPO_ROOT / "specfuse" / "loop" / "loop.py"


class TestLintPlanRelativeImport(unittest.TestCase):

    def test_loop_uses_package_relative_lint_plan_import(self):
        src = LOOP_SRC.read_text(encoding="utf-8")
        self.assertNotIn(
            "from lint_plan import", src,
            "flat `from lint_plan import` breaks in the installed package (#100)",
        )
        self.assertIn(
            "from .lint_plan import lint_plan_next_draft", src,
            "the plan-next hook must import lint_plan_next_draft package-relative",
        )

    def test_lint_plan_next_draft_importable_outside_repo_root(self):
        """Resolvable as a package member even when CWD is not the repo root
        (so a flat `lint_plan.py` on the path can't mask the bug)."""
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, "-c",
                 "from specfuse.loop.lint_plan import lint_plan_next_draft; "
                 "print('ok')"],
                capture_output=True, text=True, cwd=tmp,
            )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok", r.stdout)


if __name__ == "__main__":
    unittest.main()
