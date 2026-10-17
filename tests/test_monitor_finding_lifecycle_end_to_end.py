# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0204 gate 1 oracle: finding lifecycle, driven through `run_cycle`
over a stub transport and a stub `gh`. One class per lifecycle clause; a class
skipped here names the unit that owns it and that unit removes the skip."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli
from specfuse.monitor.issues import CLOSED_LOOKUP_DAYS, find_finding_issue

_NOW = datetime(2026, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"
_ROW = {"type": "System.NullReferenceException", "outerMessage": "Object reference not set."}


def _config():
    return {
        "environments": {
            "production": {
                "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
            },
        },
        "components": [{
            "name": "web-api", "type": "api", "runner": "local",
            "diagnose": "manual", "autofix": "off",
            "checks": [{"type": "error-logs"}],
        }],
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows

    def run_query(self, query):
        return list(self._rows)


class _Gh:
    def __init__(self, listing=None):
        self.listing = listing or []
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(list(args))
        if args[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.listing), stderr="")
        if args[:3] == ["gh", "issue", "create"]:
            return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/900\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def verbs(self):
        return [c[2] for c in self.calls if c[:2] == ["gh", "issue"]]


def _fingerprint():
    captured = {}

    def gh(args, check=True):
        captured.setdefault("calls", []).append(args)
        if args[:3] == ["gh", "issue", "create"]:
            return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/1\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    _drive(gh, [_ROW])
    create = next(c for c in captured["calls"] if c[:3] == ["gh", "issue", "create"])
    body = create[create.index("--body") + 1]
    return body.split("fingerprint=", 1)[1].split(" ", 1)[0]


def _drive(gh, rows):
    with tempfile.TemporaryDirectory() as tmp:
        out = io.StringIO()
        code = cli.run_cycle(
            _config(), dry_run=False, repo=_REPO,
            transport_resolver=lambda module, check_type, binding: _Transport(rows),
            gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=out,
        )
    return code, out.getvalue()


def _issue(fingerprint, *, state, closed_at=None, last_seen=1.0, number=42):
    body = (
        f"<!-- specfuse:finding fingerprint={fingerprint} -->\n"
        f"<!-- specfuse:finding-meta occurrences=3 last_seen={last_seen} -->\nbody"
    )
    return {"number": number, "body": body, "title": "t", "state": state, "closedAt": closed_at}


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class ClosedFindingReopens(unittest.TestCase):
    def test_closed_issue_is_reopened_not_refiled(self):
        fp = _fingerprint()
        closed = _issue(fp, state="CLOSED", closed_at=_iso(_NOW - timedelta(days=2)))
        gh = _Gh([closed])
        code, output = _drive(gh, [_ROW])
        self.assertEqual(code, 0, output)
        self.assertEqual(gh.verbs().count("reopen"), 1, gh.calls)
        self.assertEqual(gh.verbs().count("comment"), 1, gh.calls)
        self.assertNotIn("create", gh.verbs())
        self.assertNotIn("close", gh.verbs())

    def test_open_issue_still_updates(self):
        fp = _fingerprint()
        gh = _Gh([_issue(fp, state="OPEN", last_seen=1.0)])
        _drive(gh, [_ROW])
        self.assertEqual(gh.verbs(), ["list", "edit"])

    def test_new_fingerprint_still_files(self):
        gh = _Gh([])
        _drive(gh, [_ROW])
        self.assertEqual(gh.verbs(), ["list", "create"])

    def test_listing_is_bounded(self):
        fp = _fingerprint()
        gh = _Gh([_issue(fp, state="CLOSED", closed_at=_iso(_NOW - timedelta(days=CLOSED_LOOKUP_DAYS + 5)))])
        _drive(gh, [_ROW])
        listing = next(c for c in gh.calls if c[:3] == ["gh", "issue", "list"])
        bound = (_NOW - timedelta(days=CLOSED_LOOKUP_DAYS)).strftime("%Y-%m-%d")
        self.assertIn(bound, " ".join(listing))
        self.assertEqual(gh.verbs(), ["list", "create"])
        self.assertIsNone(find_finding_issue(gh, _REPO, fp, now=_NOW.timestamp()))


@unittest.skip("owned by FEAT-2026-0204/T03")
class DlqAcknowledgement(unittest.TestCase):
    def test_closed_dlq_with_covered_ids_stays_closed(self):
        self.fail("T03")


class HeartbeatGrace(unittest.TestCase):
    def test_target_before_first_heartbeat_is_not_silent(self):
        config = _config()
        config["components"][0]["checks"] = [{
            "type": "heartbeat",
            "targets": [{
                "name": "weekly-job", "cron": "0 8 * * 1",
                "dialect": "standard-5", "timezone": "Etc/UTC",
            }],
        }]
        rows = [{
            "name": "other-schedule",
            "last_heartbeat": "2026-10-16T09:00:00Z",
            "first_heartbeat": "2026-10-14T13:50:00Z",
        }]
        gh = _Gh([])
        with tempfile.TemporaryDirectory() as tmp:
            code = cli.run_cycle(
                config, dry_run=False, repo=_REPO,
                transport_resolver=lambda module, check_type, binding: _Transport(rows),
                gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=io.StringIO(),
            )
        self.assertEqual(code, 0)
        self.assertNotIn("create", gh.verbs(), gh.calls)


if __name__ == "__main__":
    unittest.main()
