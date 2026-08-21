#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#593 — a directory in `produces:` must be caught before a session runs.

`assert_declared_deliverables` refuses a `produces:` entry that resolves to a
directory. The verdict is right; the timing was not. It ran after a full
`claude -p` session, three times, for a fact that is a `Path.is_dir()` call on
static frontmatter: $6.42 and 20.6 minutes observed on a real feature, with
`specfuse lint` reporting `OK — structurally valid` throughout.

Two surfaces, one contract:
  - `lint_plan` must ERROR at draft/arm/conformance time, before the loop runs;
  - the driver must refuse at dispatch, before a token is spent.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.loop import produces_shape_error
from tests._loop_loader import load_lint
from tests.test_lint_boundary_consistency import _build_feature

lint_plan = load_lint()


class TestProducesShapeError(unittest.TestCase):
    """The shared predicate both surfaces call — pure, no session input."""

    def test_trailing_slash_is_refused_without_touching_the_filesystem(self):
        err = produces_shape_error("src/main/java/dev/example/regression/")
        self.assertIsNotNone(err)
        self.assertIn("directory", err)

    def test_existing_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "pkg"
            d.mkdir()
            self.assertIsNotNone(produces_shape_error(str(d)))

    def test_plain_file_path_is_accepted(self):
        self.assertIsNone(produces_shape_error("specfuse/loop/loop.py"))

    def test_glob_is_accepted(self):
        self.assertIsNone(produces_shape_error("src/**/Regression*.java"))

    def test_nonexistent_file_path_is_accepted(self):
        """Shape only. Presence is the dispatch gate's job, not this one."""
        self.assertIsNone(produces_shape_error("does/not/exist/yet.py"))


class TestLintCatchesProducesShape(unittest.TestCase):
    """Surface 1: the pre-dispatch checklist must not pass a doomed WU."""

    def _lint(self, produces: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                [{
                    "id": "FEAT-2026-0099/T01", "file": "WU-01.md",
                    "type": "implementation", "status": "pending",
                    "do_not_touch": "- nothing relevant.",
                    "produces": [produces],
                }],
            )
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                errs = lint_plan.lint(feat)
            return [str(e) for e in errs] + buf.getvalue().splitlines()

    def test_directory_produces_is_an_error_finding(self):
        found = [f for f in self._lint("src/regression/") if "directory" in f]
        self.assertTrue(
            found,
            "lint passed a produces: entry the driver is guaranteed to refuse "
            "- that is the $6.42 in #593",
        )
        self.assertTrue(
            any(f.startswith("ERROR") for f in found),
            f"directory produces: must be ERROR, not WARN: {found}",
        )

    def test_the_error_names_the_guard_it_preempts(self):
        """Earlier-enforcer-names-the-later-one, per FEAT-2026-0070."""
        found = [f for f in self._lint("src/regression/") if "directory" in f]
        self.assertTrue(any("assert_declared_deliverables" in f for f in found))

    def test_file_produces_is_not_flagged(self):
        self.assertEqual(
            [f for f in self._lint("src/Regression.java") if "directory" in f], [],
        )

    def test_glob_produces_is_not_flagged(self):
        self.assertEqual(
            [f for f in self._lint("src/**/*.java") if "directory" in f], [],
        )



class TestDispatchRefusesBeforeSpending(unittest.TestCase):
    """Surface 2: the driver must refuse without opening a session."""

    def test_shape_gate_is_wired_before_the_attempt_loop(self):
        """The guard is worthless if it is defined but never reached.

        Asserts the call site sits BEFORE `head_before = git("rev-parse",
        "HEAD")`, which is where dispatch state starts changing. A guard
        placed after that point would still cost the session it exists to
        prevent.
        """
        src = (
            Path(__file__).resolve().parents[1]
            / "specfuse" / "loop" / "loop.py"
        ).read_text()
        call = src.index("shape_ok, shape_reason = assert_produces_shape(wu)")
        head = src.index('head_before = git("rev-parse", "HEAD")')
        # The ceiling became per-unit in #2651, so the loop reads a resolved
        # local rather than the module constant. Anchored on `for attempt in
        # range(` alone: the assertion is about ORDER, and pinning the exact
        # bound re-breaks this test every time that expression is touched.
        attempt_loop = src.index("for attempt in range(")
        self.assertLess(call, head, "shape gate runs after dispatch begins")
        self.assertLess(call, attempt_loop, "shape gate runs inside the attempt loop")

    def test_refusal_escalates_immediately_rather_than_retrying(self):
        """A retry cannot help: the agent cannot edit its own frontmatter."""
        src = (
            Path(__file__).resolve().parents[1]
            / "specfuse" / "loop" / "loop.py"
        ).read_text()
        block = src[src.index("shape_ok, shape_reason = assert_produces_shape(wu)"):][:1200]
        self.assertIn('backend.set_wu(wu, "status", "blocked_human")', block)
        self.assertIn("produces_shape_invalid", block)

    def test_refusal_carries_a_failure_class_so_it_clusters(self):
        """#593's smaller finding: guard refusals were invisible to
        learnings-suggest because failure_class/failure_signature were null."""
        src = (
            Path(__file__).resolve().parents[1]
            / "specfuse" / "loop" / "loop.py"
        ).read_text()
        block = src[src.index("shape_ok, shape_reason = assert_produces_shape(wu)"):][:1200]
        self.assertIn('"failure_class": "guard_refusal"', block)
        self.assertIn('"failure_signature": "assert_produces_shape"', block)

    def test_shape_guard_and_dispatch_guard_render_one_message(self):
        """Three surfaces, one wording -- they must not drift apart."""
        from specfuse.loop.loop import WorkUnit, assert_produces_shape
        wu = WorkUnit.__new__(WorkUnit)
        object.__setattr__(wu, "produces", ["src/regression/"]) if hasattr(
            WorkUnit, "__slots__") else setattr(wu, "produces", ["src/regression/"])
        ok, reason = assert_produces_shape(wu)
        self.assertFalse(ok)
        self.assertEqual(reason, produces_shape_error("src/regression/"))


if __name__ == "__main__":
    unittest.main()
