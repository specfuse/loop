#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
""""Tests touching changed files" — FEAT-2026-0109/T05.

Covers `select_tests_for_changed_files` (the map-driven selector),
`resolve_narrow_test_selection` (the union with T04's declared-test half),
and the fail-safe triggers `GATE-02.md` names: no map, a stale map, and an
unmapped changed path all fall back to the gate's full command rather than
narrowing on incomplete information.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _real_head_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
    ).stdout.strip()


class ChangedFileTestSelectionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._map_path = Path(self._tmp.name) / "map.json"
        self._orig_map_path = loop.CHANGED_FILE_TEST_MAP_PATH
        loop.CHANGED_FILE_TEST_MAP_PATH = self._map_path

    def tearDown(self):
        loop.CHANGED_FILE_TEST_MAP_PATH = self._orig_map_path
        self._tmp.cleanup()

    def _write_map(self, files: dict, sha: "str | None" = None):
        data = {
            "sha": sha if sha is not None else _real_head_sha(),
            "tree": "irrelevant-for-these-tests",
            "files": files,
        }
        self._map_path.write_text(json.dumps(data))

    # -- test_a_changed_line_selects_the_tests_that_executed_it ----------- #

    def test_a_changed_line_selects_the_tests_that_executed_it(self):
        with tempfile.TemporaryDirectory() as cov_root_str:
            cov_root = Path(cov_root_str)
            pkg = cov_root / "pkgx"
            pkg.mkdir()
            (pkg / "__init__.py").write_text("")
            # foo()'s body is line 2; bar()'s body is line 6. Coverage
            # contexts tag each body line with whichever test called it.
            (pkg / "mod.py").write_text(
                "def foo():\n"
                "    return 1\n"
                "\n"
                "\n"
                "def bar():\n"
                "    return 2\n"
            )
            tests_dir = cov_root / "tests_x"
            tests_dir.mkdir()
            (tests_dir / "__init__.py").write_text("")
            (tests_dir / "test_one.py").write_text(
                "import unittest\n"
                "from pkgx.mod import foo\n"
                "class OneTest(unittest.TestCase):\n"
                "    def test_foo(self):\n"
                "        self.assertEqual(foo(), 1)\n"
            )
            (tests_dir / "test_two.py").write_text(
                "import unittest\n"
                "from pkgx.mod import bar\n"
                "class TwoTest(unittest.TestCase):\n"
                "    def test_bar(self):\n"
                "        self.assertEqual(bar(), 2)\n"
            )
            (cov_root / ".coveragerc").write_text(
                "[run]\ndynamic_context = test_function\n"
            )
            proc = subprocess.run(
                [sys.executable, "-m", "coverage", "run",
                 "--rcfile=.coveragerc", "--source=pkgx",
                 "-m", "unittest", "discover", "-s", "tests_x", "-v", "-b"],
                cwd=cov_root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                proc.returncode, 0,
                f"fixture coverage run failed:\n{proc.stdout}\n{proc.stderr}")

            map_data = loop.build_changed_file_test_map(
                coverage_data_path=str(cov_root / ".coverage"),
                test_root="tests_x")
            self.assertIn("pkgx/mod.py", map_data["files"])

            self._map_path.write_text(json.dumps(map_data))

            selected = loop.select_tests_for_changed_files(
                {"pkgx/mod.py": [2]})
            self.assertEqual(selected, ["tests_x.test_one"])
            self.assertNotIn("tests_x.test_two", selected)

            selected_bar = loop.select_tests_for_changed_files(
                {"pkgx/mod.py": [6]})
            self.assertEqual(selected_bar, ["tests_x.test_two"])

    # -- fail-safe triggers ------------------------------------------------ #

    def test_an_unmapped_new_source_file_falls_back_to_the_full_command(self):
        self._write_map(files={"specfuse/known.py": {"10": ["tests.test_known"]}})
        gate = {"name": "tests", "command": "FULLCMD",
                "narrow_command": "python3 -m unittest {selected_test_modules}"}
        wu = loop.WorkUnit(
            wu_id="X/T1", file=Path("WU-1.md"), depends_on=[],
            type="implementation", model="m", status="pending", attempts=0,
            title="t", body="",
        )
        command = loop.resolve_narrow_command(
            gate, wu, {"specfuse/brand_new_file.py": None})
        self.assertEqual(
            command, "FULLCMD",
            "a changed path absent from the map must run the gate's full "
            "command, not a narrower guess")

    def test_a_missing_map_falls_back_to_the_full_command(self):
        # No map written at all — self._map_path does not exist on disk.
        selected = loop.select_tests_for_changed_files(
            {"specfuse/anything.py": [1]})
        self.assertIsNone(selected)

        gate = {"name": "tests", "command": "FULLCMD",
                "narrow_command": "python3 -m unittest {selected_test_modules}"}
        wu = loop.WorkUnit(
            wu_id="X/T2", file=Path("WU-2.md"), depends_on=[],
            type="implementation", model="m", status="pending", attempts=0,
            title="t", body="",
        )
        command = loop.resolve_narrow_command(
            gate, wu, {"specfuse/anything.py": [1]})
        self.assertEqual(command, "FULLCMD")

    def test_a_stale_map_is_refused_rather_than_trusted(self):
        self._write_map(
            files={"specfuse/known.py": {"10": ["tests.test_known"]}},
            sha="0" * 40,  # a well-formed but non-existent commit
        )
        map_data = loop.read_changed_file_test_map()
        self.assertIsNotNone(map_data)
        self.assertTrue(
            loop.is_map_stale(map_data),
            "a sha git cannot resolve as an ancestor must be treated as stale")

        selected = loop.select_tests_for_changed_files(
            {"specfuse/known.py": [10]})
        self.assertIsNone(
            selected,
            "a stale map must not be consulted, even for a path it maps")

    def test_selection_is_the_union_with_the_declared_paths(self):
        self._write_map(files={
            "specfuse/thing.py": {"42": ["tests.test_from_map"]},
        })
        wu = loop.WorkUnit(
            wu_id="X/T3", file=Path("WU-3.md"), depends_on=[],
            type="implementation", model="m", status="pending", attempts=0,
            title="t", body="",
            produces=["tests/test_declared.py", "specfuse/thing.py"],
        )
        selection = loop.resolve_narrow_test_selection(
            wu, {"specfuse/thing.py": [42]})
        self.assertEqual(
            selection, ["tests.test_declared", "tests.test_from_map"],
            "the final selection must union the declared test paths with "
            "everything the map resolved")

        gate = {"name": "tests", "command": "FULLCMD",
                "narrow_command": "python3 -m unittest {selected_test_modules}"}
        command = loop.resolve_narrow_command(gate, wu, {"specfuse/thing.py": [42]})
        self.assertEqual(
            command,
            "python3 -m unittest tests.test_declared tests.test_from_map")


if __name__ == "__main__":
    unittest.main()
