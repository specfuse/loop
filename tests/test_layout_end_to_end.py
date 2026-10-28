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


@unittest.skip("owned by FEAT-2026-0224/T05")
class LintChecksDecisionLinks(unittest.TestCase):
    pass


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


@unittest.skip("owned by FEAT-2026-0224/T07")
class TemplateFollowsStyle(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
