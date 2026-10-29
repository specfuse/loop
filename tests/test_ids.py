#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unit tests for specfuse.loop.ids (FEAT-2026-0247/T01)."""

import re
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import ids, layout

REPO_ROOT = Path(__file__).resolve().parent.parent
_LEGACY = re.compile(r"FEAT-(?:[A-Z][A-Z0-9]{1,5}-)?\d{4}-\d{4}")  # reference grammar under test: either shape


def _repo(tmp, rows=(), key=None, plans=()):
    root = Path(tmp)
    (root / ".specfuse" / "features").mkdir(parents=True)
    table = "".join(f"| {r} | t | planned | — | x |\n" for r in rows)
    (root / ".specfuse" / "roadmap.md").write_text("| Feature ID |\n|---|\n" + table)
    for name, fid in plans:
        d = root / ".specfuse" / "features" / name
        d.mkdir()
        (d / "PLAN.md").write_text(f"---\nfeature_id: {fid}\n---\n")
    if key:
        (root / ".specfuse" / "layout.yml").write_text(f"ids:\n  key: {key}\n")
    return root


class Parse(unittest.TestCase):
    def test_legacy_and_keyed(self):
        self.assertEqual(ids.parse("FEAT-2026-0007"), ids.FeatureId(None, 2026, 7))
        self.assertEqual(ids.parse("FEAT-ACME-2026-0008"), ids.FeatureId("ACME", 2026, 8))

    def test_folder_name(self):
        self.assertEqual(ids.parse("FEAT-2026-0007-some-slug").ordinal, 7)
        self.assertEqual(ids.parse("FEAT-A1-2026-0007-some-slug").key, "A1")

    def test_rejects(self):
        for text in ("0008", "FEAT-26-0008", "feat-2026-0008", "FEAT-acme-2026-0008", "", None):
            self.assertIsNone(ids.parse(text), text)

    def test_str_roundtrip_and_anchor(self):
        for text in ("FEAT-2026-0007", "FEAT-ACME-2026-0008"):
            self.assertEqual(str(ids.parse(text)), text)
            self.assertEqual(ids.anchor(text), text.lower())

    def test_pattern(self):
        self.assertTrue(ids.FEATURE_ID_RE.match("FEAT-ACME-2026-0008"))
        self.assertTrue(ids.FEATURE_ID_RE.match("FEAT-2026-0008"))
        self.assertFalse(ids.FEATURE_ID_RE.match("FEAT-2026-0008-slug"))


class RealCorpus(unittest.TestCase):
    def test_every_feature_folder(self):
        folders = [p.name for p in (REPO_ROOT / ".specfuse" / "features").iterdir() if p.is_dir()]
        checked = 0
        for name in folders:
            m = _LEGACY.match(name)
            if not m:
                continue
            checked += 1
            self.assertEqual(str(ids.parse(name)), m.group(0), name)
        self.assertGreater(checked, 50)

    def test_every_roadmap_row(self):
        checked = 0
        for fname in ("roadmap.md", "roadmap-archive.md"):
            for line in (REPO_ROOT / ".specfuse" / fname).read_text().splitlines():
                if not line.startswith("| FEAT-"):
                    continue
                cell = line.split("|")[1].strip()
                m = _LEGACY.match(cell)
                if not m:
                    continue
                checked += 1
                self.assertEqual(str(ids.parse(cell)), m.group(0), line)
        self.assertGreater(checked, 50)


class NextId(unittest.TestCase):
    def test_unkeyed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, rows=["FEAT-2026-0007", "FEAT-2026-0003"])
            self.assertEqual(ids.next_id(root, 2026), "FEAT-2026-0008")

    def test_keyed_counts_both_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, rows=["FEAT-2026-0007", "FEAT-ACME-2026-0009"], key="ACME")
            self.assertEqual(ids.next_id(root, 2026), "FEAT-ACME-2026-0010")

    def test_plan_feature_id_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, plans=[("FEAT-2026-0012-x", "FEAT-2026-0012")])
            self.assertEqual(ids.next_id(root, 2026), "FEAT-2026-0013")

    def test_other_year_ignored_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, rows=["FEAT-2025-0099"])
            self.assertEqual(ids.next_id(root, 2026), "FEAT-2026-0001")


class LayoutKey(unittest.TestCase):
    def _validate(self, key):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, key=key)
            return layout.validate(root)

    def test_malformed_key_is_error(self):
        for bad in ("acme", "A", "TOOLONG1", "1ABC"):
            findings = self._validate(bad)
            self.assertTrue(any(f.severity == "error" and "ids.key" in f.message for f in findings), bad)

    def test_valid_key_round_trips(self):
        self.assertEqual(self._validate("ACME"), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, key="ACME")
            self.assertEqual(layout.get(layout.load(root), "ids.key"), "ACME")

    def test_unset_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(layout.get(layout.load(tmp), "ids.key"), "")


if __name__ == "__main__":
    unittest.main()
