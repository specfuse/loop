#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Sanity guards on the scaffold seed a fresh `specfuse init` writes.

These lock the fixes for the brand-new-project install bugs:
  - the shipped verification.yml gate commands must be runnable on a
    pip-installed project (console scripts, not `python .specfuse/scripts/...`
    which does not exist there);
  - the roadmap template must carry the 5-column header `roadmap-add` requires
    (Detail column), and must NOT pre-populate demo features.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "specfuse" / "loop" / "data"


class TestVerificationSeed(unittest.TestCase):

    def test_gate_commands_reference_no_missing_scripts(self):
        """No shipped gate command may invoke `.specfuse/scripts/...` — that path
        is absent in a pip-installed project; use the console scripts."""
        text = (DATA / "verification.yml.example").read_text(encoding="utf-8")
        offenders = [
            ln.strip() for ln in text.splitlines()
            if "command:" in ln and ".specfuse/scripts/" in ln
        ]
        self.assertEqual(
            offenders, [],
            f"gate commands must not call .specfuse/scripts/* (absent under pip); "
            f"use specfuse-lint / specfuse-loop. Offenders: {offenders}",
        )

    def test_plan_lint_uses_console_script(self):
        text = (DATA / "verification.yml.example").read_text(encoding="utf-8")
        self.assertIn("specfuse-lint", text,
                      "the plan-next lint gate should call `specfuse-lint`")


class TestRoadmapSeed(unittest.TestCase):

    def _table_header(self) -> str:
        text = (DATA / "roadmap.template.md").read_text(encoding="utf-8")
        for ln in text.splitlines():
            if ln.startswith("| Feature ID"):
                return ln
        self.fail("roadmap.template.md has no `| Feature ID` table header")

    def test_header_has_detail_column(self):
        """roadmap-add requires the 5-column order incl. Detail."""
        cols = [c.strip() for c in self._table_header().strip("|").split("|")]
        self.assertEqual(
            cols, ["Feature ID", "Title", "Status", "Folder", "Detail"],
            f"roadmap template header must match roadmap-add's expected columns; "
            f"got {cols}",
        )

    def test_no_demo_feature_rows(self):
        """A fresh project's roadmap must not ship example features."""
        text = (DATA / "roadmap.template.md").read_text(encoding="utf-8")
        feat_rows = [
            ln for ln in text.splitlines()
            if re.match(r"\|\s*FEAT-\d{4}-\d{4}", ln)
        ]
        self.assertEqual(
            feat_rows, [],
            f"roadmap template must start with an empty table; demo rows found: "
            f"{feat_rows}",
        )


if __name__ == "__main__":
    unittest.main()
