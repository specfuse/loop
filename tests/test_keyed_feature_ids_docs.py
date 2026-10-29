#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0247/T06 — shipped docs explain the ID key and grandfathering."""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SURFACES = [
    "docs/methodology.md",
    "docs/glossary.md",
    "docs/getting-started.md",
    ".specfuse/roadmap.template.md",
]


class KeyedFeatureIdDocs(unittest.TestCase):
    def test_each_surface_explains_key(self):
        for rel in SURFACES:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(surface=rel):
                self.assertIn("ids.key", text)
                self.assertIn("FEAT-<KEY>-YYYY-NNNN", text)
                self.assertIn("never renamed", text)

    def test_methodology_covers_details(self):
        text = (REPO_ROOT / "docs/methodology.md").read_text(encoding="utf-8")
        for needle in ("FEAT-<key>-YYYY-NNNN", "ids migrate --planned-only",
                       "highest ordinal", "distinct across the repos"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_schema_comment_names_ids_module(self):
        path = REPO_ROOT / "specfuse/loop/data/schemas/driver-event.schema.json"
        comment = json.loads(path.read_text(encoding="utf-8"))["$comment"]
        self.assertIn("specfuse.loop.ids", comment)


if __name__ == "__main__":
    unittest.main()
