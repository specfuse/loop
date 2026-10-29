#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""lint_roadmap: with `ids.key` set, an unkeyed `planned` row draws a WARN (FEAT-2026-0247/T04)."""

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import lint_roadmap


def _repo(tmp, status, row_id="FEAT-2026-0003", key="ACME"):
    spec = Path(tmp) / ".specfuse"
    spec.mkdir()
    if key:
        (spec / "layout.yml").write_text(f"ids:\n  key: {key}\n")
    (spec / "roadmap.md").write_text(
        "# Roadmap\n\n| Feature ID | Title | Status | Folder | Detail |\n|---|---|---|---|---|\n"
        f"| {row_id} | T | {status} | — | — |\n"
    )
    return Path(tmp)


def _unkeyed_warns(root):
    return [f for f in lint_roadmap.lint_roadmap(root) if "no project key" in f.message]


class UnkeyedPlannedRow(unittest.TestCase):
    def test_fires_with_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = _unkeyed_warns(_repo(tmp, "planned"))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].severity, lint_roadmap.SEVERITY_WARN)
            self.assertIn("FEAT-2026-0003", found[0].message)
            self.assertIn("ACME", found[0].message)
            self.assertIn("migrate --planned-only", found[0].message)

    def test_silent_without_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_unkeyed_warns(_repo(tmp, "planned", key=None)), [])

    def test_silent_for_other_statuses(self):
        for status in ("done", "active", "abandoned", "blocked", "deferred"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(_unkeyed_warns(_repo(tmp, status)), [])

    def test_silent_for_keyed_planned(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_unkeyed_warns(_repo(tmp, "planned", row_id="FEAT-ACME-2026-0003")), [])


if __name__ == "__main__":
    unittest.main()
