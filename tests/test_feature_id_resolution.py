#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for `--feature` accepting a bare FEAT-ID (issue #244).

`find_feature` treated its argument as a literal directory name, so the
correlation ID alone did not resolve:

    loop.py --feature FEAT-2026-0039                  -> No PLAN.md under ...
    loop.py --feature FEAT-2026-0039-monitoring-schema -> works

The FEAT-ID is the identifier in the roadmap row, in PLAN.md frontmatter, in
every WU id, in every correlation ID, and in commit subjects. The folder name is
the one place it is *not* the identifier, so reaching for the ID first is the
natural move.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from specfuse.loop import loop  # noqa: E402


class TestFeatureIdResolution(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._features_dir = self.root / ".specfuse" / "features"
        self._features_dir.mkdir(parents=True)
        self._orig = loop.FEATURES_DIR
        loop.FEATURES_DIR = self._features_dir
        os.chdir(self.root)

    def tearDown(self):
        loop.FEATURES_DIR = self._orig
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _write_plan(self, name: str, status: str = "active") -> Path:
        fdir = self._features_dir / name
        fdir.mkdir(parents=True)
        feature_id = "-".join(name.split("-")[:3])
        (fdir / "PLAN.md").write_text(
            f"---\nfeature_id: {feature_id}\nstatus: {status}\n---\n\n# Plan\n"
        )
        return fdir

    # --- the reported bug -------------------------------------------------

    def test_bare_feature_id_resolves(self):
        """#244: the correlation ID alone must resolve to its folder."""
        expected = self._write_plan("FEAT-2026-0039-monitoring-schema")
        self.assertEqual(loop.find_feature("FEAT-2026-0039"), expected)

    def test_full_folder_name_still_resolves(self):
        """The existing spelling must keep working — this is additive."""
        expected = self._write_plan("FEAT-2026-0039-monitoring-schema")
        self.assertEqual(
            loop.find_feature("FEAT-2026-0039-monitoring-schema"), expected
        )

    # --- boundaries -------------------------------------------------------

    def test_ambiguous_prefix_lists_candidates(self):
        """Two folders sharing a prefix must not silently pick one.

        Cannot happen with well-formed IDs, but a half-renamed or duplicated
        folder is exactly when a silent wrong pick would be most expensive.
        """
        self._write_plan("FEAT-2026-0039-monitoring-schema")
        self._write_plan("FEAT-2026-0039-monitoring-schema-old")
        with self.assertRaises(SystemExit) as ctx:
            loop.find_feature("FEAT-2026-0039")
        msg = str(ctx.exception)
        self.assertIn("ambiguous", msg.lower())
        self.assertIn("FEAT-2026-0039-monitoring-schema", msg)
        self.assertIn("FEAT-2026-0039-monitoring-schema-old", msg)

    def test_unknown_id_names_the_available_features(self):
        """The old error named only the path it failed to find.

        An operator who mistyped an ID learns nothing from that; listing what
        exists turns a dead end into a correction.
        """
        self._write_plan("FEAT-2026-0039-monitoring-schema")
        with self.assertRaises(SystemExit) as ctx:
            loop.find_feature("FEAT-2026-9999")
        msg = str(ctx.exception)
        self.assertIn("FEAT-2026-9999", msg)
        self.assertIn("FEAT-2026-0039-monitoring-schema", msg)

    def test_partial_non_id_prefix_does_not_resolve(self):
        """Prefix matching is anchored to the FEAT-ID, not arbitrary strings.

        `--feature monitoring` must not resolve, or a typo could dispatch a
        feature the operator never named.
        """
        self._write_plan("FEAT-2026-0039-monitoring-schema")
        with self.assertRaises(SystemExit):
            loop.find_feature("monitoring")

    def test_explicit_path_argument_is_unchanged(self):
        """A dot-prefixed arg is a literal path and bypasses ID resolution."""
        fdir = self._write_plan("FEAT-2026-0039-monitoring-schema")
        rel = os.path.relpath(fdir, self.root)
        self.assertEqual(loop.find_feature(f"./{rel}"), Path(f"./{rel}"))

    def test_deferred_feature_still_refused_via_bare_id(self):
        """The #183 deferred guard must not be bypassed by the new path."""
        self._write_plan("FEAT-2026-0039-monitoring-schema", status="deferred")
        with self.assertRaises(SystemExit) as ctx:
            loop.find_feature("FEAT-2026-0039")
        self.assertIn("deferred", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
