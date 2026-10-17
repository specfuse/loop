# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3488: `diagnose: auto` takes effect only through `specfuse agent run`
(the findings-diagnose provider), not through `specfuse monitor run`. A cycle
that files or updates findings for an `auto` component says so in its
summary — one line per component — so an operator who scheduled only the
monitor learns why nothing is being diagnosed.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli

_NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"


def _component(name, diagnose):
    return {
        "name": name,
        "type": "api",
        "runner": "local",
        "diagnose": diagnose,
        "autofix": "off",
        "checks": [{"type": "error-logs"}],
    }


def _config(*components):
    return {
        "environments": {
            "production": {
                "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
            },
        },
        "components": list(components),
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows

    def run_query(self, query):
        return list(self._rows)


_ROWS = [
    {"type": "NullReferenceException", "outerMessage": "boom"},
    {"type": "TimeoutException", "outerMessage": "slow"},
]


def _gh(args, check=True):
    if args[:3] == ["gh", "issue", "list"]:
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")
    return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/1\n", stderr="")


class TestDiagnoseAutoWaitsForTheAgent(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _run(self, config, *, dry_run, rows=_ROWS):
        out = io.StringIO()
        cli.run_cycle(
            config,
            dry_run=dry_run,
            repo=_REPO,
            transport_resolver=lambda module, check_type, binding: _Transport(rows),
            gh_runner=_gh,
            now=_NOW,
            watermark_dir=Path(self._tmpdir.name),
            out=out,
        )
        return out.getvalue()

    def _notes(self, output):
        return [line for line in output.splitlines() if "specfuse-agent" in line]

    def test_auto_component_gets_one_line_not_one_per_finding(self):
        output = self._run(_config(_component("web-api", "auto")), dry_run=False)
        notes = self._notes(output)
        self.assertEqual(len(notes), 1, output)
        self.assertIn("production/web-api", notes[0])
        self.assertIn("diagnose: auto", notes[0])

    def test_dry_run_says_it_too(self):
        output = self._run(_config(_component("web-api", "auto")), dry_run=True)
        self.assertEqual(len(self._notes(output)), 1, output)

    def test_manual_component_gets_no_line(self):
        output = self._run(_config(_component("web-api", "manual")), dry_run=False)
        self.assertEqual(self._notes(output), [], output)

    def test_auto_component_without_findings_gets_no_line(self):
        output = self._run(_config(_component("web-api", "auto")), dry_run=False, rows=[])
        self.assertEqual(self._notes(output), [], output)

    def test_one_line_per_auto_component(self):
        output = self._run(
            _config(_component("web-api", "auto"), _component("worker", "auto"), _component("admin", "manual")),
            dry_run=False,
        )
        notes = self._notes(output)
        self.assertEqual(len(notes), 2, output)
        self.assertTrue(any("production/web-api" in n for n in notes))
        self.assertTrue(any("production/worker" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
