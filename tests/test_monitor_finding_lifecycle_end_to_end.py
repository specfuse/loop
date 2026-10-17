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


def _dlq_config():
    config = _config()
    config["environments"]["production"]["broker"] = {
        "provider": "azure_service_bus", "credentials": {"connection_string": "ACME_CONN"},
    }
    config["components"][0]["checks"] = [{
        "type": "dlq",
        "targets": [{"subscription": "orders", "function": "OrderHandler"}],
    }]
    return config


class _DlqTransport:
    def __init__(self, ids):
        self._ids = ids

    def peek_dead_letter_messages(self, *, subscription, max_message_count):
        return [
            SimpleNamespace(
                message_id=i, sequence_number=n,
                dead_letter_reason="MaxDeliveryCountExceeded",
                dead_letter_error_description="System.Exception: boom",
            )
            for n, i in enumerate(self._ids)
        ]


def _drive_dlq(gh, ids):
    with tempfile.TemporaryDirectory() as tmp:
        out = io.StringIO()
        code = cli.run_cycle(
            _dlq_config(), dry_run=False, repo=_REPO,
            transport_resolver=lambda module, check_type, binding: _DlqTransport(ids),
            gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=out,
        )
    return code, out.getvalue()


def _dlq_fingerprint():
    captured = []

    def gh(args, check=True):
        captured.append(args)
        if args[:3] == ["gh", "issue", "create"]:
            return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/1\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    _drive_dlq(gh, ["m1"])
    create = next(c for c in captured if c[:3] == ["gh", "issue", "create"])
    body = create[create.index("--body") + 1]
    return body.split("fingerprint=", 1)[1].split(" ", 1)[0]


def _dlq_issue(fingerprint, messages, *, state="CLOSED"):
    body = (
        f"<!-- specfuse:finding fingerprint={fingerprint} -->\n"
        f"<!-- specfuse:finding-meta occurrences=3 last_seen=1.0 first_seen=1.0 "
        f"messages={','.join(messages)} -->\nbody"
    )
    return {
        "number": 42, "body": body, "title": "t", "state": state,
        "closedAt": _iso(_NOW - timedelta(days=2)) if state == "CLOSED" else None,
    }


class DlqAcknowledgement(unittest.TestCase):
    def test_closed_dlq_with_covered_ids_stays_closed(self):
        fp = _dlq_fingerprint()
        gh = _Gh([_dlq_issue(fp, ["m1"])])
        code, output = _drive_dlq(gh, ["m1"])
        self.assertEqual(code, 0, output)
        self.assertEqual(gh.verbs(), ["list"], gh.calls)

    def test_unseen_message_id_reopens_naming_it(self):
        fp = _dlq_fingerprint()
        gh = _Gh([_dlq_issue(fp, ["m1"])])
        _drive_dlq(gh, ["m1", "m2"])
        self.assertEqual(gh.verbs().count("reopen"), 1, gh.calls)
        comments = [c for c in gh.calls if c[:3] == ["gh", "issue", "comment"]]
        self.assertEqual(len(comments), 1, gh.calls)
        self.assertIn("m2", comments[0][comments[0].index("--body") + 1])
        edit = next(c for c in gh.calls if c[:3] == ["gh", "issue", "edit"])
        self.assertIn("messages=m1,m2", edit[edit.index("--body") + 1])

    def test_fingerprint_ignores_message_id(self):
        from dataclasses import replace
        from specfuse.monitor.artifact import FailureArtifact
        from specfuse.monitor.fingerprint import fingerprint_artifact
        a = FailureArtifact.from_target(
            component="c", check_type="dlq",
            target={"subscription": "s", "function": "f"},
            failure_class="X", failure_signature="E:m", observed_text="t", message_id="a",
        )
        self.assertEqual(fingerprint_artifact(a), fingerprint_artifact(replace(a, message_id="b")))

    def test_non_dlq_artifact_carries_no_message_id(self):
        from specfuse.monitor.artifact import FailureArtifact
        a = FailureArtifact.from_target(
            component="c", check_type="heartbeat", target={"name": "n"},
            failure_class="X", failure_signature="s", observed_text="t", message_id="a",
        )
        self.assertIsNone(a.message_id)


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
