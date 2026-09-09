#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A red baseline record is never reused — FEAT-2026-0109/T10.

`gate_baseline_check` (T02) keys reuse on `HEAD^{tree}`, deliberately
excluding `.specfuse/` so bookkeeping commits do not invalidate a cached
record. But the `code` gate set reads `.specfuse/` (corpus lint, roadmap-link,
arm-sweep, event-type gates), so a failure recorded there can never be
invalidated by a `.specfuse/`-only fix — and T07's "at most once per tree
state per gate" bound then makes the stale red verdict sticky (gate 3's
livelock, fixed by hand in `8bc2c82`).

This adds one condition to the reuse decision: a record whose `failing` is
non-empty is never reused, only re-probed. A `failing: []` record remains a
real cache.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        check=True,
    ).stdout.strip()


class TestRedBaselineNeverReused(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "Test")
        (self.root / "specfuse").mkdir()
        (self.root / "specfuse" / "code.py").write_text("value = 1\n")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_stub.py").write_text("# stub\n")
        (self.root / ".specfuse").mkdir()
        (self.root / ".specfuse" / "events.jsonl").write_text("")
        (self.root / "GATE-01.md").write_text(
            "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
        )
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-q", "-m", "initial")
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self._cwd)
        self._td.cleanup()

    def _gate_file(self) -> Path:
        return self.root / "GATE-01.md"

    def _scripted_probe(self, results):
        calls = []

        def probe(feature_dir, cfg=None):
            calls.append(1)
            idx = min(len(calls), len(results)) - 1
            return results[idx]

        return probe, calls

    def test_a_red_record_is_re_probed_even_at_the_same_tree(self):
        """Fails on HEAD: a red record with an unchanged tree key is reused
        instead of re-probed, so a fix that never touches specfuse/ or
        tests/ (e.g. a .specfuse/-only fix) can never clear it."""
        red = [{"gate": "code", "failure_class": "lint",
                "failure_signature": "boom"}]
        probe, calls = self._scripted_probe([red, red])
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")
            self.assertEqual(len(calls), 1)

            # Same tree key, no commit at all in between.
            _, freshly = loop.gate_baseline_check(
                self._gate_file(), self.root, cfg, sha1, probed_at="t2")
            self.assertTrue(
                freshly,
                "a red record must never be reused — it must re-probe")
            self.assertEqual(len(calls), 2)
        finally:
            loop.probe_baseline = orig

    def test_a_green_record_is_still_reused_at_the_same_tree(self):
        probe, calls = self._scripted_probe([[]])
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")
            self.assertEqual(len(calls), 1)

            _, freshly = loop.gate_baseline_check(
                self._gate_file(), self.root, cfg, sha1, probed_at="t2")
            self.assertFalse(
                freshly, "a green record at an unchanged tree is a cache")
            self.assertEqual(len(calls), 1)
        finally:
            loop.probe_baseline = orig

    def test_a_green_record_still_survives_a_bookkeeping_commit(self):
        probe, calls = self._scripted_probe([[]])
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")

            (self.root / ".specfuse" / "events.jsonl").write_text(
                '{"event": "gate 1 halted for driver restart"}\n'
            )
            _git(self.root, "add", ".specfuse/events.jsonl")
            _git(self.root, "commit", "-q", "-m", "bookkeeping commit")
            sha2 = _git(self.root, "rev-parse", "HEAD")
            self.assertNotEqual(sha1, sha2)

            _, freshly = loop.gate_baseline_check(
                self._gate_file(), self.root, cfg, sha2, probed_at="t2")
            self.assertFalse(
                freshly,
                "a bookkeeping commit must not invalidate a green record")
            self.assertEqual(len(calls), 1)
        finally:
            loop.probe_baseline = orig

    def test_a_fixed_red_record_clears_without_hand_editing(self):
        """The exact sequence that livelocked gate 3: a red record, a fix
        landed as a .specfuse/-only change (tree key unchanged), and the
        next attribution must go green on its own -- no hand-clearing."""
        red = [{"gate": "code", "failure_class": "lint",
                "failure_signature": "boom"}]
        probe, calls = self._scripted_probe([red, []])
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.attribute_failure_to_baseline(
                self._gate_file(), self.root, cfg, sha1, "T09",
                probed_at="t1")
            record = loop.read_gate_baseline(self._gate_file())
            self.assertEqual(len(record["failing"]), 1)

            # A .specfuse/-only fix: tree key (which excludes .specfuse/)
            # stays the same, no new commit needed to exercise the bug.
            (self.root / ".specfuse" / "events.jsonl").write_text(
                '{"event": "fixed the lint error"}\n'
            )
            _git(self.root, "add", ".specfuse/events.jsonl")
            _git(self.root, "commit", "-q", "-m", "fix recorded via .specfuse")
            sha2 = _git(self.root, "rev-parse", "HEAD")

            failing, freshly = loop.attribute_failure_to_baseline(
                self._gate_file(), self.root, cfg, sha2, "T09b",
                probed_at="t2")
            self.assertTrue(freshly)
            self.assertEqual(failing, [])
            record = loop.read_gate_baseline(self._gate_file())
            self.assertEqual(record["failing"], [])
        finally:
            loop.probe_baseline = orig


if __name__ == "__main__":
    unittest.main()


class TestRedBroadRunIsNeverReused(unittest.TestCase):
    """The same rule for the once-per-gate broad run (FEAT-2026-0109).

    T10 fixed red-record reuse for `gate_baseline_check` and was scoped to
    that function. `gate_broad_run_check` cached verdicts the same way and had
    the identical defect: a red broad run recorded against `.specfuse/`
    content could not be invalidated by the `.specfuse/`-side change that
    fixed it, because the tree key excludes `.specfuse/` while the `code` set
    reads it. Gate 3 livelocked on this a second time, replaying a failure
    that no longer existed without re-running a single gate.
    """

    def _gate_file(self, tmp: Path) -> Path:
        gf = tmp / "GATE-01.md"
        gf.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        return gf

    def test_a_red_broad_run_is_re_run_rather_than_replayed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            calls = {"n": 0}

            def red_then_green(feature_dir, cfg=None):
                calls["n"] += 1
                if calls["n"] == 1:
                    return False, [{"gate": "tests", "failure_class": "tests",
                                    "failure_signature": "sig"}]
                return True, []          # fixed between the two calls

            orig_run = loop.run_gate_broad_set
            orig_tree = loop._current_tree_hash
            loop.run_gate_broad_set = red_then_green
            loop._current_tree_hash = lambda: "same-tree"
            try:
                ok1, failing1, ran1 = loop.gate_broad_run_check(gf, Path(td), {})
                ok2, failing2, ran2 = loop.gate_broad_run_check(gf, Path(td), {})
            finally:
                loop.run_gate_broad_set = orig_run
                loop._current_tree_hash = orig_tree

            self.assertFalse(ok1)
            self.assertTrue(ran1)
            self.assertEqual(
                calls["n"], 2,
                "a red broad run must re-run at an unchanged tree — replaying "
                "it lets a recorded failure outlive the fix, which livelocked "
                "gate 3")
            self.assertTrue(ok2, "the re-run observes the fix")
            self.assertTrue(ran2)

    def test_a_green_broad_run_is_still_reused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            calls = {"n": 0}

            def green_then_crash(feature_dir, cfg=None):
                calls["n"] += 1
                if calls["n"] > 1:
                    raise AssertionError("a green broad run must not re-run")
                return True, []

            orig_run = loop.run_gate_broad_set
            orig_tree = loop._current_tree_hash
            loop.run_gate_broad_set = green_then_crash
            loop._current_tree_hash = lambda: "same-tree"
            try:
                loop.gate_broad_run_check(gf, Path(td), {})
                ok2, _, ran2 = loop.gate_broad_run_check(gf, Path(td), {})
            finally:
                loop.run_gate_broad_set = orig_run
                loop._current_tree_hash = orig_tree

            self.assertTrue(ok2)
            self.assertFalse(ran2, "the green record was reused, not re-run")
            self.assertEqual(calls["n"], 1)
