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
            f"use the `specfuse` subcommands. Offenders: {offenders}",
        )

    def test_plan_lint_uses_console_script(self):
        text = (DATA / "verification.yml.example").read_text(encoding="utf-8")
        self.assertIn("specfuse lint", text,
                      "the plan-next lint gate should call `specfuse lint`")


class TestSkillsNameRunnableCommands(unittest.TestCase):
    """A skill must not tell the user to run a path that does not exist.

    `.specfuse/scripts/` is a dogfood shim directory in THIS repo's checkout;
    `init_specfuse` never writes it, so in a scaffolded project the path is
    absent. Skills nevertheless printed `python3 .specfuse/scripts/loop.py` as
    the next command — the same defect `test_gate_commands_reference_no_missing_scripts`
    already guards for `verification.yml`, on a surface that guard never
    covered. Every command a skill hands the user must be one they can paste:
    a `specfuse` subcommand, or `python3 -m specfuse.loop.<module>` for the
    helpers that have no console script.

    Checked on both copies — the vendored one is what a scaffolded project
    actually reads.
    """

    _SKILL_DIRS = (
        REPO_ROOT / "plugins" / "specfuse" / "skills",
        REPO_ROOT / ".specfuse" / "skills",
    )
    _FORBIDDEN = re.compile(r"\.specfuse/scripts/[A-Za-z_-]+\.py")

    # Known-unpackaged helpers, exempted deliberately and visibly rather than
    # by loosening the pattern. `learnings_query.py` and `upgrade_merge_gate.py`
    # exist ONLY as repo-local dogfood scripts: no console script, no module
    # under `specfuse/loop/`, and `init_specfuse` does not seed them. So the
    # skills naming them are broken for a scaffolded project exactly as the
    # `loop.py` references were — but unlike those, there is no packaged
    # command to point at yet, and inventing one is a public-API decision, not
    # a docs fix. Tracked in #1076; delete an entry here when its helper ships.
    _KNOWN_UNPACKAGED = ("learnings_query.py", "upgrade_merge_gate.py")

    def test_skill_dirs_resolve(self):
        """Vacuity guard: a moved skills tree would otherwise assert nothing."""
        for d in self._SKILL_DIRS:
            with self.subTest(path=str(d)):
                self.assertTrue(d.is_dir(), f"{d} is not a directory")
                self.assertTrue(any(d.glob("*/SKILL.md")), f"no SKILL.md under {d}")

    def test_no_skill_references_a_scripts_path(self):
        offenders: list[str] = []
        for d in self._SKILL_DIRS:
            for skill in sorted(d.glob("*/SKILL.md")):
                for lineno, line in enumerate(
                    skill.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    hit = self._FORBIDDEN.search(line)
                    if hit and not hit.group(0).endswith(self._KNOWN_UNPACKAGED):
                        rel = skill.relative_to(REPO_ROOT)
                        offenders.append(f"{rel}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "skills reference `.specfuse/scripts/*.py`, which is absent in a "
            "scaffolded project; use a `specfuse` subcommand or "
            "`python3 -m specfuse.loop.<module>`. Offenders:\n  "
            + "\n  ".join(offenders),
        )


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
