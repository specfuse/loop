#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The four package-version sources must agree — enforced every CI run.

specfuse-loop's version lives in four places (pyproject, DRIVER_VERSION, the
canonical .specfuse/VERSION, and the synced specfuse/loop/data/VERSION seed).
The release.yml tag/version-agreement check covers pyproject + DRIVER_VERSION
but (a) omits the two scaffold VERSION files and (b) only runs at TAG time. A
half-bump then sits undetected until release. This test closes both gaps: it
runs on every PR and asserts all four are equal, plus MIN_SCAFFOLD_VERSION is
not ahead of the driver. It also exercises scripts/bump_version.py, the helper
that sets all four in lockstep.
"""

from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()
REPO_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version(root: Path) -> str:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert m, "no version line in pyproject.toml"
    return m.group(1)


def _load_bump():
    path = REPO_ROOT / "scripts" / "bump_version.py"
    spec = importlib.util.spec_from_file_location("bump_version", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bump_version = _load_bump()


class TestVersionConsistency(unittest.TestCase):

    def test_all_four_sources_agree(self):
        pkg = _pyproject_version(REPO_ROOT)
        driver = loop.DRIVER_VERSION
        specfuse_ver = (REPO_ROOT / ".specfuse" / "VERSION").read_text().strip()
        data_ver = (REPO_ROOT / "specfuse" / "loop" / "data" / "VERSION").read_text().strip()
        self.assertEqual(
            {pkg, driver, specfuse_ver, data_ver}, {pkg},
            f"version sources disagree: pyproject={pkg} DRIVER_VERSION={driver} "
            f".specfuse/VERSION={specfuse_ver} data/VERSION={data_ver}. "
            f"Run `python3 scripts/bump_version.py {pkg}` to re-sync.",
        )

    def test_min_scaffold_not_ahead_of_driver(self):
        self.assertLessEqual(
            loop._parse_version(loop.MIN_SCAFFOLD_VERSION),
            loop._parse_version(loop.DRIVER_VERSION),
            "MIN_SCAFFOLD_VERSION must not exceed DRIVER_VERSION",
        )


class TestBumpVersionHelper(unittest.TestCase):

    def _make_tree(self, root: Path, version: str) -> None:
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "specfuse-loop"\nversion = "{version}"\n',
            encoding="utf-8",
        )
        loop_dir = root / "specfuse" / "loop"
        (loop_dir / "data").mkdir(parents=True)
        (loop_dir / "loop.py").write_text(
            f'DRIVER_VERSION = "{version}"\nMIN_SCAFFOLD_VERSION = "0.2.0"\n',
            encoding="utf-8",
        )
        (root / ".specfuse").mkdir()
        (root / ".specfuse" / "VERSION").write_text(version + "\n", encoding="utf-8")
        (loop_dir / "data" / "VERSION").write_text(version + "\n", encoding="utf-8")

    def test_set_version_updates_all_four(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_tree(root, "0.2.0")
            changed = bump_version.set_version(root, "0.9.0")
            self.assertEqual(
                set(changed),
                {"pyproject.toml", "specfuse/loop/loop.py",
                 ".specfuse/VERSION", "specfuse/loop/data/VERSION"},
            )
            self.assertIn('version = "0.9.0"', (root / "pyproject.toml").read_text())
            self.assertIn('DRIVER_VERSION = "0.9.0"',
                          (root / "specfuse/loop/loop.py").read_text())
            self.assertEqual((root / ".specfuse/VERSION").read_text().strip(), "0.9.0")
            self.assertEqual(
                (root / "specfuse/loop/data/VERSION").read_text().strip(), "0.9.0")
            # MIN_SCAFFOLD_VERSION must be left untouched.
            self.assertIn('MIN_SCAFFOLD_VERSION = "0.2.0"',
                          (root / "specfuse/loop/loop.py").read_text())

    def test_set_version_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_tree(root, "0.5.0")
            self.assertEqual(bump_version.set_version(root, "0.5.0"), [])

    def test_main_rejects_bad_version(self):
        self.assertEqual(bump_version.main(["not-a-version"]), 2)
        self.assertEqual(bump_version.main([]), 2)


if __name__ == "__main__":
    unittest.main()
