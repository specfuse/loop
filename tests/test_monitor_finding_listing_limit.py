# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3579: `specfuse monitor run` crashed with `TruncatedListingError` once the
findings repo held 100 or more finding issues, and that one error aborted the
whole cycle.

Two properties: the default listing reads well past 100 finding issues, so a
repo with 102 of them files a new fingerprint instead of raising; and a filing
error is isolated per component like a check error (#3478) — reported in the
summary, other components still file, the watermark is held, exit non-zero."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli
from specfuse.monitor.autofix_state import has_prior_attempt
from specfuse.monitor.issues import find_finding_issue

_NOW = datetime(2026, 10, 16, 10, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"
_ENVIRONMENT = {
    "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
    "broker": {"provider": "azure_service_bus", "credentials": {"connection_string": "ACME_CONN"}},
}


def _stored_rows(count):
    return [
        {
            "number": i,
            "body": f"<!-- specfuse:finding fingerprint=fp-{i} -->\nbody",
            "title": f"[monitor:fp-{i}] x",
            "state": "OPEN",
            "closedAt": None,
        }
        for i in range(1, count + 1)
    ]


class _GhRepo:
    """A fake `gh` over a repo holding `stored` finding issues. Honours
    `--limit` the way `gh issue list` does: returns at most that many rows."""

    def __init__(self, stored, fail_create_for=()):
        self._stored = stored
        self._fail_create_for = set(fail_create_for)
        self.created = 0

    def __call__(self, args, check=True):
        if args[:3] == ["gh", "issue", "list"]:
            limit = int(args[args.index("--limit") + 1])
            return SimpleNamespace(returncode=0, stdout=json.dumps(self._stored[:limit]), stderr="")
        if args[:3] == ["gh", "issue", "create"]:
            title = args[args.index("--title") + 1] if "--title" in args else ""
            if any(name in title for name in self._fail_create_for):
                raise RuntimeError("gh issue create failed: HTTP 502")
            self.created += 1
            return SimpleNamespace(
                returncode=0, stdout=f"https://github.com/{_REPO}/issues/{900 + self.created}\n", stderr=""
            )
        if args[:3] == ["gh", "label", "create"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected gh call: {args}")


class TestListingReadsPastOneHundredFindings(unittest.TestCase):
    def test_absent_fingerprint_is_not_found_in_a_repo_of_102_findings(self):
        gh = _GhRepo(_stored_rows(102))

        self.assertIsNone(find_finding_issue(gh, _REPO, "fp-new", now=_NOW.timestamp()))

    def test_fingerprint_past_the_first_hundred_rows_is_found(self):
        gh = _GhRepo(_stored_rows(102))

        found = find_finding_issue(gh, _REPO, "fp-101", now=_NOW.timestamp())

        self.assertEqual(found["number"], 101)

    def test_autofix_prior_attempt_lookup_reads_past_one_hundred_findings(self):
        # has_prior_attempt fails closed (True) on a truncated listing, which
        # would block autofix for every fingerprint in a busy repo.
        gh = _GhRepo(_stored_rows(102))

        self.assertFalse(has_prior_attempt(gh, _REPO, "fp-new"))


def _component(name):
    return {
        "name": name,
        "type": "api",
        "runner": "local",
        "diagnose": "manual",
        "autofix": "off",
        "checks": [{"type": "error-logs"}],
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows

    def run_query(self, query):
        return list(self._rows)


def _resolver(module, check_type, binding):
    return _Transport([{"type": "NullReferenceException", "outerMessage": "boom at line 5"}])


class TestFilingErrorIsIsolated(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.watermark_dir = Path(tmp.name)

    def _run(self, gh):
        out = io.StringIO()
        config = {
            "environments": {"production": _ENVIRONMENT},
            "components": [_component("order-worker"), _component("web-api")],
        }
        code = cli.run_cycle(
            config,
            dry_run=False,
            repo=_REPO,
            transport_resolver=_resolver,
            gh_runner=gh,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        return code, out.getvalue()

    def test_other_components_still_file_and_the_error_is_reported(self):
        gh = _GhRepo([], fail_create_for=("order-worker",))

        code, output = self._run(gh)

        self.assertEqual(code, 1)
        self.assertEqual(gh.created, 1)
        self.assertIn("production/order-worker: filing errored — RuntimeError: gh issue create failed: HTTP 502", output)
        self.assertIn("production/web-api: 1 finding(s) — created 1", output)
        self.assertFalse((self.watermark_dir / "production.json").exists())


if __name__ == "__main__":
    unittest.main()
