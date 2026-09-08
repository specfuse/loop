#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tree-hash keying for the baseline record — FEAT-2026-0109/T02.

`gate_baseline_check` used to reuse a record only when `baseline.sha` equalled
the dispatched `head_sha`. Every bookkeeping commit (squash, "baseline probed
clean", "halted for driver restart") moves the sha while leaving the tree
untouched, so the record was discarded and the whole `code` gate set re-ran.
This keys reuse on `HEAD^{tree}` instead, keeping `sha` in the record for
humans and falling back to the old sha comparison for records written before
this field existed.
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


class TestBaselineTreeHashKey(unittest.TestCase):
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

    def _counting_probe(self):
        calls = []

        def probe(feature_dir, cfg=None):
            calls.append(1)
            return []

        return probe, calls

    def test_bookkeeping_commit_preserves_the_record(self):
        """Fails on HEAD: a bookkeeping commit (no content change under
        specfuse/ or tests/) moves head_sha, discarding a sha-only-keyed
        record and forcing a re-probe it shouldn't need."""
        probe, calls = self._counting_probe()
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")

            # A bookkeeping commit: touches only the driver's own .specfuse/
            # bookkeeping directory (events.jsonl), the way a real
            # "halted for driver restart" commit does — nothing under
            # specfuse/ or tests/ changes.
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
                freshly, "a bookkeeping commit must not force a re-probe")
            self.assertEqual(len(calls), 1)
        finally:
            loop.probe_baseline = orig

    def test_a_real_code_change_invalidates_the_record(self):
        probe, calls = self._counting_probe()
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")

            (self.root / "specfuse" / "code.py").write_text("value = 2\n")
            _git(self.root, "add", "specfuse/code.py")
            _git(self.root, "commit", "-q", "-m", "real code change")
            sha2 = _git(self.root, "rev-parse", "HEAD")

            _, freshly = loop.gate_baseline_check(
                self._gate_file(), self.root, cfg, sha2, probed_at="t2")
            self.assertTrue(
                freshly, "a real code change must invalidate the record")
            self.assertEqual(len(calls), 2)
        finally:
            loop.probe_baseline = orig

    def test_legacy_record_without_tree_falls_back_to_sha(self):
        gf = self._gate_file()
        sha1 = _git(self.root, "rev-parse", "HEAD")
        # Legacy shape: no tree key at all.
        loop.write_frontmatter_block(
            gf, "baseline",
            ["baseline:", f"  sha: {sha1}",
             "  probed_at: 2026-01-01T00:00:00+00:00", "  failing: []"],
        )
        record = loop.read_gate_baseline(gf)
        self.assertIsNone(record["tree"])

        probe, calls = self._counting_probe()
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            _, freshly = loop.gate_baseline_check(gf, self.root, cfg, sha1,
                                                    probed_at="t2")
            self.assertFalse(
                freshly,
                "a legacy sha-only record must be honoured on the old terms")
            self.assertEqual(calls, [])
        finally:
            loop.probe_baseline = orig

    def test_record_still_carries_sha_for_human_reading(self):
        probe, _calls = self._counting_probe()
        orig = loop.probe_baseline
        loop.probe_baseline = probe
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")
        finally:
            loop.probe_baseline = orig

        record = loop.read_gate_baseline(self._gate_file())
        self.assertEqual(record["sha"], sha1)
        self.assertIsNotNone(record["tree"])


if __name__ == "__main__":
    unittest.main()
