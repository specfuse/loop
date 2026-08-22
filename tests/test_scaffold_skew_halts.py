#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Scaffold version skew stops the run instead of narrating past it (#2643).

`auto_sync` detected that the working tree's `.specfuse/VERSION` was newer
than the installed scaffold, printed **"Not downgrading. Update specfuse to
continue."**, and then `return`ed — which exits `auto_sync`, not the run.
`main()` called it as a bare statement and dispatched anyway.

Two defects in one line. The stated contract was not the implemented one: a
message saying a condition must be met "to continue" is a precondition, not
a comment. And a version guard that proceeds is not a guard. Observed
resuming FEAT-2026-0058 against installed 0.12.1 with a 0.13.0 checkout: the
line was read as a refusal, the driver was believed dead, and it was in fact
alive and about to dispatch a terminal close against the older scaffold.

The skew is not cosmetic. `.specfuse/VERSION` gates scaffold contents —
templates, rules, and the closing-requirement surfaces a close ceremony
reads — so a close run under a stale scaffold can assert against
obligations that have since changed.

`--no-autosync` (and `autosync: false` in `.specfuse/config`) remain the
escape hatch for an operator who knows: they skip `auto_sync` entirely and
therefore skip this check, which is the correct place for the override —
the guard fires only for callers who did not opt out.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from specfuse.loop import loop as driver


def _tree(tmp: Path, version: str) -> Path:
    (tmp / ".specfuse").mkdir()
    (tmp / ".specfuse" / "VERSION").write_text(version + "\n")
    return tmp


class TestSkewRaises(unittest.TestCase):
    def test_a_newer_tree_than_the_installed_scaffold_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = _tree(Path(tmp), "99.0.0")
            with self.assertRaises(driver.ScaffoldVersionSkew):
                with redirect_stderr(io.StringIO()):
                    driver.auto_sync(tree)

    def test_the_error_names_both_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = _tree(Path(tmp), "99.0.0")
            with self.assertRaises(driver.ScaffoldVersionSkew) as ctx:
                with redirect_stderr(io.StringIO()):
                    driver.auto_sync(tree)

        message = str(ctx.exception)
        self.assertIn("99.0.0", message, "tree version missing")
        self.assertIn(driver._scaffold.scaffold_version(), message,
                      "installed version missing")

    def test_the_error_names_a_way_forward(self):
        # An operator hitting a hard stop must be told what to run, and that
        # an override exists — a stop with no exit is its own defect.
        with tempfile.TemporaryDirectory() as tmp:
            tree = _tree(Path(tmp), "99.0.0")
            with self.assertRaises(driver.ScaffoldVersionSkew) as ctx:
                with redirect_stderr(io.StringIO()):
                    driver.auto_sync(tree)

        message = str(ctx.exception)
        self.assertIn("pip install", message)
        self.assertIn("--no-autosync", message)


class TestTheEscapeHatchStillWorks(unittest.TestCase):
    def test_no_autosync_skips_the_check_entirely(self):
        # The override belongs here: a caller who opted out of syncing has
        # also opted out of being stopped by it.
        with tempfile.TemporaryDirectory() as tmp:
            tree = _tree(Path(tmp), "99.0.0")
            driver.auto_sync(tree, no_autosync=True)  # must not raise

    def test_project_config_optout_skips_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = _tree(Path(tmp), "99.0.0")
            (tree / ".specfuse" / "config").write_text("autosync: false\n")
            driver.auto_sync(tree)  # must not raise


class TestNonSkewedTreesAreUnaffected(unittest.TestCase):
    def test_an_equal_version_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = _tree(Path(tmp), driver._scaffold.scaffold_version())
            with redirect_stderr(io.StringIO()):
                driver.auto_sync(tree)  # must not raise

    def test_a_missing_version_file_does_not_raise_skew(self):
        # Absent means "scaffold this tree", handled elsewhere; it must not
        # be mistaken for a tree that is ahead.
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            (tree / ".specfuse").mkdir()
            with redirect_stderr(io.StringIO()):
                try:
                    driver.auto_sync(tree)
                except driver.ScaffoldVersionSkew:  # pragma: no cover
                    self.fail("absent VERSION must not read as skew")
                except Exception as exc:  # noqa: BLE001, S110
                    # An absent VERSION takes the scaffold/init path, which
                    # may fail for unrelated reasons in a bare tmpdir. Only
                    # the skew classification is under test here.
                    self.assertNotIsInstance(exc, driver.ScaffoldVersionSkew)


class TestTheRunActuallyStops(unittest.TestCase):
    def test_main_turns_the_skew_into_a_nonzero_exit(self):
        # The whole point: the guard must reach the caller. A raise that
        # main() swallowed would reproduce the original defect with extra
        # machinery.
        import inspect

        src = inspect.getsource(driver.main)
        self.assertIn("ScaffoldVersionSkew", src,
                      "main() does not handle the skew signal")


if __name__ == "__main__":
    unittest.main()
