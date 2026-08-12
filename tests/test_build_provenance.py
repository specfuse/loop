# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A command must say when it is measuring a build that is not your tree (#1040).

An installed console script resolves `specfuse.loop` from `site-packages`. In
a checkout of the driver whose source has moved ahead of the wheel, it runs a
different program than the session believes -- and returns a plausible number
rather than an error. Observed three times, twice at real cost: an arming
probe that "would have reported identically had T03 shipped nothing", and a
terminal close producing 14 spurious red results.

Two properties matter and pull against each other, so both are tested here:
the warning must fire in a driver checkout running an out-of-tree build, and
it must stay **completely silent** for a downstream project, where the console
script is the correct thing to run.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop.build_provenance import (
    out_of_tree_warning,
    running_package_dir,
    source_tree_package_dir,
    warn_if_out_of_tree,
)


def _make_source_checkout(root: Path) -> Path:
    """A directory that looks like a checkout of the driver's own source."""
    pkg = root / "specfuse" / "loop"
    pkg.mkdir(parents=True)
    (pkg / "loop.py").write_text("# a source tree's own driver\n")
    return pkg


class TestSourceTreeDetection(unittest.TestCase):
    def test_a_driver_checkout_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = _make_source_checkout(root)

            self.assertEqual(source_tree_package_dir(root), pkg.resolve())

    def test_detection_walks_up_from_a_subdirectory(self):
        """An operator is rarely standing exactly at the repo root."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = _make_source_checkout(root)
            deep = root / "docs" / "concepts"
            deep.mkdir(parents=True)

            self.assertEqual(source_tree_package_dir(deep), pkg.resolve())

    def test_a_project_without_driver_source_is_not_a_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse").mkdir()

            self.assertIsNone(source_tree_package_dir(root))

    def test_this_repository_is_detected_as_a_checkout(self):
        """Real input, not a fixture: this repo IS a driver checkout."""
        self.assertEqual(
            source_tree_package_dir(REPO_ROOT), (REPO_ROOT / "specfuse" / "loop").resolve()
        )


class TestWarningFires(unittest.TestCase):
    def test_out_of_tree_build_in_a_checkout_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_source_checkout(root)

            message = out_of_tree_warning(root)

            self.assertIsNotNone(message)
            self.assertIn("warning:", message)

    def test_the_warning_names_both_builds_and_the_fix(self):
        """A diagnostic that does not say what to do instead is half a fix."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_source_checkout(root)

            message = out_of_tree_warning(root)

            self.assertIn(str(running_package_dir()), message)   # what ran
            self.assertIn(str(Path(tmp).resolve()), message)     # what you meant
            self.assertIn("python3 -m specfuse.loop.loop", message)  # the fix

    def test_warning_goes_to_stderr_not_stdout(self):
        """Several of these commands have stdout a caller parses."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_source_checkout(root)
            stream = io.StringIO()

            returned = warn_if_out_of_tree(root, stream=stream)

            self.assertIsNotNone(returned)
            self.assertIn("warning:", stream.getvalue())


class TestWarningStaysSilent(unittest.TestCase):
    def test_a_downstream_project_is_never_warned(self):
        """The console script is the CORRECT thing to run in a target project.

        This is the property that decides whether the check is shippable at
        all: a false positive here would train every downstream operator to
        ignore the warning, which costs more than the bug.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse" / "features").mkdir(parents=True)

            self.assertIsNone(out_of_tree_warning(root))

    def test_running_in_step_with_the_tree_is_silent(self):
        """Running this repo's own source against this repo: nothing to say."""
        self.assertIsNone(out_of_tree_warning(REPO_ROOT))

    def test_nothing_is_printed_when_silent(self):
        stream = io.StringIO()

        warn_if_out_of_tree(REPO_ROOT, stream=stream)

        self.assertEqual(stream.getvalue(), "")


class TestEveryConsoleScriptIsWired(unittest.TestCase):
    """The hazard is per-entry-point; wiring one and forgetting five leaves
    the same silent wrong answer on the others."""

    ENTRY_MODULES = (
        "specfuse/loop/loop.py",
        "specfuse/loop/lint_plan.py",
        "specfuse/loop/lint_monitoring.py",
        "specfuse/loop/events_stats.py",
        "specfuse/agent/run.py",
        "specfuse/monitor/cli.py",
    )

    def test_each_entry_point_calls_the_check(self):
        for rel in self.ENTRY_MODULES:
            with self.subTest(module=rel):
                text = (REPO_ROOT / rel).read_text()
                self.assertIn("warn_if_out_of_tree()", text)

    def test_the_declared_console_scripts_match_the_wired_set(self):
        """A seventh console script added to pyproject must be wired too."""
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        block = pyproject.split("[project.scripts]", 1)[1].split("[", 1)[0]
        targets = {
            line.split("=", 1)[1].strip().strip('"').split(":")[0]
            for line in block.splitlines()
            if "=" in line and not line.strip().startswith("#")
        }
        wired = {rel[:-3].replace("/", ".") for rel in self.ENTRY_MODULES}

        self.assertEqual(
            targets - wired,
            set(),
            "console script(s) declared in pyproject.toml whose module does "
            "not call warn_if_out_of_tree()",
        )


class TestRealInvocation(unittest.TestCase):
    def test_running_the_repo_source_from_the_repo_prints_no_warning(self):
        """End to end, through an actual process, not a function call."""
        result = subprocess.run(
            [sys.executable, "-m", "specfuse.loop.events_stats", "--help"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, check=False,
        )

        self.assertNotIn("warning:", result.stderr)


if __name__ == "__main__":
    unittest.main()
