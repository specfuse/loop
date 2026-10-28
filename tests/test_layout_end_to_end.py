#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""End-to-end oracle for FEAT-2026-0224: `python3 -m specfuse.loop.layout`.

Every invocation is a subprocess of the source module, never an installed
console script. Classes owned by later units are skipped, each naming its owner.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ENTRIES_LAYOUT = """decisions:
  style: entries
  location: docs/decisions
  link: "{location}/decisions.md#{id}"
"""


def run_layout(repo, *args):
    return subprocess.run(
        [sys.executable, "-m", "specfuse.loop.layout", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env=_env(),
        check=False,
    )


def _env():
    import os

    env = dict(os.environ)
    root = str(Path(__file__).resolve().parent.parent)
    env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
    return env


class NoLayoutGetIsToday(unittest.TestCase):
    def test_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            for key, want in (
                ("decisions.style", "adr"),
                ("decisions.location", "docs/adr"),
                ("decisions.link", "{path}"),
            ):
                r = run_layout(tmp, "get", key)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), want)


class EntriesLayoutGet(unittest.TestCase):
    def test_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".specfuse").mkdir()
            (Path(tmp) / ".specfuse" / "layout.yml").write_text(ENTRIES_LAYOUT)
            for key, want in (
                ("decisions.style", "entries"),
                ("decisions.location", "docs/decisions"),
                ("decisions.link", "{location}/decisions.md#{id}"),
            ):
                r = run_layout(tmp, "get", key)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), want)


class EntriesLinkRenders(unittest.TestCase):
    def test_link_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".specfuse").mkdir()
            (Path(tmp) / ".specfuse" / "layout.yml").write_text(ENTRIES_LAYOUT)
            r = run_layout(tmp, "link", "--target", "D-0007", "--label", "D-0007: x")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "[D-0007: x](../docs/decisions/decisions.md#D-0007)")


class NoLayoutGoldens(unittest.TestCase):
    def test_blocked_dangling_lint_matches_golden(self):
        from tests.test_layout_no_layout_goldens import (
            FIXTURES,
            GOLDEN_LINT,
            render_lint,
            write_fixture,
        )

        self.assertIn("blocked_dangling", FIXTURES)
        with tempfile.TemporaryDirectory() as tmp:
            write_fixture(tmp, "blocked_dangling")
            self.assertEqual(render_lint(tmp), GOLDEN_LINT["blocked_dangling"])


class LintChecksDecisionLinks(unittest.TestCase):
    def test_missing_anchor_and_outside_location_are_errors(self):
        from specfuse.loop.lint_roadmap import SEVERITY_ERROR, lint_roadmap

        roadmap = (
            "# Roadmap\n\n| Feature ID | Title | Status | Folder | Detail |\n|---|---|---|---|---|\n"
            "| FEAT-2026-0001 | T | blocked | — | — |\n\n"
            '<a id="feat-2026-0001"></a>\n## FEAT-2026-0001 — T\n\n'
            "**Blocked by.** [D-1](../docs/decisions/decisions.md#D-9) [x](../docs/other.md)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse").mkdir()
            (root / ".specfuse" / "layout.yml").write_text(ENTRIES_LAYOUT)
            (root / ".specfuse" / "roadmap.md").write_text(roadmap)
            (root / "docs" / "decisions").mkdir(parents=True)
            (root / "docs" / "decisions" / "decisions.md").write_text("## D-1\n")
            (root / "docs" / "other.md").write_text("x\n")
            msgs = [f.message for f in lint_roadmap(root) if f.severity == SEVERITY_ERROR]
        self.assertTrue(any("no anchor 'D-9'" in m for m in msgs), msgs)
        self.assertTrue(any("docs/decisions" in m and "other.md" in m for m in msgs), msgs)


class InvalidLayoutIsReported(unittest.TestCase):
    def _repo(self, tmp, text):
        (Path(tmp) / ".specfuse").mkdir()
        (Path(tmp) / ".specfuse" / "layout.yml").write_text(text)

    def test_absolute_location_exits_1_naming_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, "decisions:\n  style: entries\n  location: /abs/dir\n")
            r = run_layout(tmp, "check")
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertIn("/abs/dir", r.stdout)

    def test_paths_block_exits_0_with_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, ENTRIES_LAYOUT + "paths:\n  specs: specs\n")
            r = run_layout(tmp, "check")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("WARN", r.stdout)
            self.assertIn("`paths:` is not supported yet", r.stdout)


class TemplateFollowsStyle(unittest.TestCase):
    def test_entries_template_has_no_adr_and_lints_clean(self):
        import re

        from specfuse.loop import layout
        from specfuse.loop.lint_roadmap import SEVERITY_ERROR, lint_roadmap

        text = (Path(__file__).resolve().parent.parent / "specfuse/loop/data/roadmap.template.md").read_text(
            encoding="utf-8"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse").mkdir()
            (root / ".specfuse" / "layout.yml").write_text(ENTRIES_LAYOUT)
            out = layout.render_roadmap_template(text, layout.load(root))
            self.assertNotIn("docs/adr", out)
            self.assertNotIn("layout:decisions-example", out)
            example = re.search(r"^\*\*Blocked by\.\*\*.*$", out, re.M).group(0)
            roadmap = (
                "# Roadmap\n\n| Feature ID | Title | Status | Folder | Detail |\n|---|---|---|---|---|\n"
                "| FEAT-2026-0001 | T | blocked | — | [→ detail](#feat-2026-0001) |\n"
                "| FEAT-2026-0011 | U | active | — | [→ detail](#feat-2026-0011) |\n\n"
                '<a id="feat-2026-0001"></a>\n## FEAT-2026-0001 — T\n\n' + example + "\n\n"
                '<a id="feat-2026-0011"></a>\n## FEAT-2026-0011 — U\n\nBody.\n'
            )
            (root / ".specfuse" / "roadmap.md").write_text(roadmap)
            (root / "docs" / "decisions").mkdir(parents=True)
            (root / "docs" / "decisions" / "decisions.md").write_text('<a id="D-0007"></a>\n## D-0007\n')
            errs = [f.message for f in lint_roadmap(root) if f.severity == SEVERITY_ERROR]
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
