#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Baseline record provenance — FEAT-2026-0109/T03.

`write_gate_baseline` used to record only what a probe found, never how it
was reached. This adds a `source` field distinguishing the gate-entry probe
path from `attribute_failure_to_baseline`'s retroactive path (carrying the
triggering `wu_id`), while keeping a record written before this field
existed readable.
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


class TestBaselineProvenance(unittest.TestCase):
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
            "---\n"
            "gate: 1\n"
            "status: open\n"
            "feature_oracle: echo ok\n"
            "cost_budget_usd: 5.0\n"
            "---\n\n# Gate 1\n"
        )
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-q", "-m", "initial")
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self._cwd)
        self._td.cleanup()

    def _gate_file(self) -> Path:
        return self.root / "GATE-01.md"

    def _stub_probe(self):
        orig = loop.probe_baseline
        loop.probe_baseline = lambda feature_dir, cfg=None: []
        return orig

    def test_entry_probe_records_its_source(self):
        orig = self._stub_probe()
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(self._gate_file(), self.root, cfg, sha1,
                                      probed_at="t1")
        finally:
            loop.probe_baseline = orig

        record = loop.read_gate_baseline(self._gate_file())
        self.assertEqual(record["source"], "entry_probe")

    def test_attribution_records_the_triggering_unit(self):
        orig = self._stub_probe()
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.attribute_failure_to_baseline(
                self._gate_file(), self.root, cfg, sha1, "T02",
                probed_at="t1")
        finally:
            loop.probe_baseline = orig

        record = loop.read_gate_baseline(self._gate_file())
        self.assertEqual(record["source"], "attributed:T02")

    def test_legacy_record_without_source_still_reads(self):
        gf = self._gate_file()
        sha1 = _git(self.root, "rev-parse", "HEAD")
        loop.write_frontmatter_block(
            gf, "baseline",
            ["baseline:", f"  sha: {sha1}",
             "  probed_at: 2026-01-01T00:00:00+00:00", "  failing: []"],
        )
        record = loop.read_gate_baseline(gf)
        self.assertIsNotNone(record)
        self.assertIsNone(record["source"])

    def test_source_does_not_disturb_other_frontmatter(self):
        gf = self._gate_file()
        before = gf.read_text()
        orig = self._stub_probe()
        try:
            cfg = {"code": []}
            sha1 = _git(self.root, "rev-parse", "HEAD")
            loop.gate_baseline_check(gf, self.root, cfg, sha1,
                                      probed_at="t1")
        finally:
            loop.probe_baseline = orig

        after_lines = gf.read_text().splitlines()
        before_lines = [
            line for line in before.splitlines()
            if not line.startswith("status:")
        ]
        for line in before_lines:
            if line in ("gate: 1", "feature_oracle: echo ok",
                         "cost_budget_usd: 5.0"):
                self.assertIn(line, after_lines)


if __name__ == "__main__":
    unittest.main()
