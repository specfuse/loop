# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3486: a cycle that yields one fingerprint several times must file one
issue, not one per row. The issue listing `record_finding` looks issues up
through can lag behind an issue this same cycle just created, so the cycle
itself must not hand the same fingerprint to `record_finding` twice.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli

_NOW = datetime(2026, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"


def _config():
    return {
        "environments": {
            "production": {
                "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
            },
        },
        "components": [{
            "name": "web-api",
            "type": "api",
            "runner": "local",
            "diagnose": "manual",
            "autofix": "off",
            "checks": [{"type": "error-logs"}],
        }],
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows

    def run_query(self, query):
        return list(self._rows)


_CANCELLED = {"type": "System.Threading.Tasks.TaskCanceledException", "outerMessage": "A task was canceled."}
_NULL_REF = {"type": "System.NullReferenceException", "outerMessage": "Object reference not set."}


class _LaggingGh:
    """`gh issue list` never shows an issue created in this cycle, as GitHub's
    listing did on the run that filed #1014 and #1015 two seconds apart."""

    def __init__(self):
        self.created = 0

    def __call__(self, args, check=True):
        if args[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        if args[:3] == ["gh", "issue", "create"]:
            self.created += 1
            return SimpleNamespace(
                returncode=0, stdout=f"https://github.com/{_REPO}/issues/{self.created}\n", stderr=""
            )
        if args[:3] == ["gh", "label", "create"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected gh call: {args}")


class TestOneIssuePerFingerprintPerCycle(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _run(self, rows):
        gh = _LaggingGh()
        out = io.StringIO()
        code = cli.run_cycle(
            _config(),
            dry_run=False,
            repo=_REPO,
            transport_resolver=lambda module, check_type, binding: _Transport(rows),
            gh_runner=gh,
            now=_NOW,
            watermark_dir=Path(self._tmpdir.name),
            out=out,
        )
        return code, out.getvalue(), gh

    def test_repeated_rows_file_one_issue(self):
        code, output, gh = self._run([_CANCELLED, _CANCELLED, _CANCELLED])
        self.assertEqual(code, 0)
        self.assertEqual(gh.created, 1, output)
        self.assertIn("created 1", output)

    def test_summary_names_the_merged_repeats(self):
        _, output, _ = self._run([_CANCELLED, _CANCELLED, _CANCELLED])
        self.assertIn("2 repeat(s) of an already-filed fingerprint", output)

    def test_distinct_fingerprints_still_file_separately(self):
        _, output, gh = self._run([_CANCELLED, _NULL_REF, _CANCELLED])
        self.assertEqual(gh.created, 2, output)


if __name__ == "__main__":
    unittest.main()
