# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0204/T02: finding-meta marker round-trip and fail-closed reader."""

from __future__ import annotations

import io
import json
import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.issues import MESSAGES_CAP, _parse_meta, _render_body, record_finding

_NOW = datetime(2026, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"
_ROW = {"type": "System.NullReferenceException", "outerMessage": "Object reference not set."}


def _meta(fields: str) -> str:
    return f"<!-- specfuse:finding fingerprint=abc -->\n<!-- specfuse:finding-meta {fields} -->\nbody"


def _artifact() -> FailureArtifact:
    return FailureArtifact(
        component="web-api", check_type="error-logs", failure_class="NullRef",
        failure_signature="sig", observed_text="boom", target_coordinates={},
    )


class TestRoundTrip(unittest.TestCase):
    def test_new_fields_round_trip(self):
        body = _render_body(
            "fp", _artifact(), occurrences=4, last_seen=2000.0, first_seen=1000.0,
            messages=("m1", "m2"),
        )
        meta = _parse_meta(body)
        self.assertEqual(meta.occurrences, 4)
        self.assertEqual(meta.last_seen, 2000.0)
        self.assertEqual(meta.first_seen, 1000.0)
        self.assertEqual(meta.messages, ("m1", "m2"))

    def test_head_body_parses_without_new_fields(self):
        meta = _parse_meta(_meta("occurrences=3 last_seen=1000.0"))
        self.assertEqual((meta.occurrences, meta.last_seen), (3, 1000.0))
        self.assertIsNone(meta.first_seen)
        self.assertIsNone(meta.messages)

    def test_messages_capped_to_most_recent(self):
        ids = tuple(f"m{i}" for i in range(80))
        body = _render_body("fp", _artifact(), occurrences=1, last_seen=1.0, messages=ids)
        self.assertEqual(_parse_meta(body).messages, ids[-MESSAGES_CAP:])
        self.assertEqual(len([ln for ln in body.splitlines() if "finding-meta" in ln]), 1)

    def test_body_names_first_and_last_seen_iso(self):
        body = _render_body("fp", _artifact(), occurrences=1, last_seen=2000.0, first_seen=1000.0)
        self.assertIn("**First seen:** 1970-01-01T00:16:40Z", body)
        self.assertIn("**Last seen:** 1970-01-01T00:33:20Z", body)


class TestFailClosed(unittest.TestCase):
    def test_bad_required_fields_yield_none(self):
        for fields in (
            "occurrences=abc last_seen=1.0",
            "occurrences=1 last_seen=",
            "occurrences=1 occurrences=2 last_seen=1.0",
            "occurrences=1 last_seen=1.0 last_seen=2.0",
            "occurrences=1 last_seen=nan",
            "occurrences=-1 last_seen=1.0",
        ):
            with self.subTest(fields=fields):
                self.assertIsNone(_parse_meta(_meta(fields)))

    def test_bad_optional_fields_are_absent(self):
        self.assertIsNone(_parse_meta(_meta("occurrences=1 last_seen=1.0 first_seen=x")).first_seen)
        self.assertIsNone(_parse_meta(_meta("occurrences=1 last_seen=1.0 first_seen=1 first_seen=2")).first_seen)
        for value in ("", "a,,b", ",a"):
            with self.subTest(value=value):
                self.assertIsNone(_parse_meta(_meta(f"occurrences=1 last_seen=1.0 messages={value}")).messages)
        ok = _parse_meta(_meta("occurrences=1 last_seen=1.0 first_seen=x messages=a,b"))
        self.assertEqual(ok.messages, ("a", "b"))

    def test_unterminated_marker_is_none(self):
        self.assertIsNone(_parse_meta("<!-- specfuse:finding-meta occurrences=1 last_seen=1.0"))

    def test_none_body(self):
        self.assertIsNone(_parse_meta(None))


class TestUpdatePreservesFirstSeen(unittest.TestCase):
    def _run(self, state):
        calls = []

        def gh(args, check=True):
            calls.append(list(args))
            if args[:3] == ["gh", "issue", "list"]:
                row = {
                    "number": 7, "title": "t", "state": state,
                    "closedAt": "2026-10-16T00:00:00Z" if state == "CLOSED" else None,
                    "body": "<!-- specfuse:finding fingerprint=fp -->\n"
                            "<!-- specfuse:finding-meta occurrences=2 last_seen=1000.0 first_seen=500.0 messages=a,b -->",
                }
                return SimpleNamespace(returncode=0, stdout=json.dumps([row]), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        record_finding("fp", _artifact(), _REPO, runner=gh, now=_NOW.timestamp())
        return calls

    def test_update_keeps_first_seen(self):
        edit = next(c for c in self._run("OPEN") if c[:3] == ["gh", "issue", "edit"])
        meta = _parse_meta(edit[edit.index("--body") + 1])
        self.assertEqual((meta.first_seen, meta.occurrences, meta.messages), (500.0, 3, ("a", "b")))

    def test_reopen_keeps_first_seen_and_comments_iso(self):
        calls = self._run("CLOSED")
        comment = next(c for c in calls if c[:3] == ["gh", "issue", "comment"])
        text = comment[comment.index("--body") + 1]
        self.assertRegex(text, r"first seen 1970-01-01T00:08:20Z, last seen 2026-10-17T01:00:00Z\.")
        edit = next(c for c in calls if c[:3] == ["gh", "issue", "edit"])
        self.assertEqual(_parse_meta(edit[edit.index("--body") + 1]).first_seen, 500.0)


class TestCycleSurvivesMalformedMeta(unittest.TestCase):
    def test_cycle_survives_a_malformed_meta(self):
        captured = {}

        def probe(args, check=True):
            captured.setdefault("calls", []).append(args)
            if args[:3] == ["gh", "issue", "create"]:
                return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/1\n", stderr="")
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        def drive(gh):
            with tempfile.TemporaryDirectory() as tmp:
                out = io.StringIO()
                code = cli.run_cycle(
                    {
                        "environments": {"production": {"telemetry": {
                            "provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}}}},
                        "components": [{
                            "name": "web-api", "type": "api", "runner": "local",
                            "diagnose": "manual", "autofix": "off", "checks": [{"type": "error-logs"}],
                        }],
                    },
                    dry_run=False, repo=_REPO,
                    transport_resolver=lambda m, c, b: SimpleNamespace(run_query=lambda q: [dict(_ROW)]),
                    gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=out,
                )
            return code

        drive(probe)
        create = next(c for c in captured["calls"] if c[:3] == ["gh", "issue", "create"])
        fp = create[create.index("--body") + 1].split("fingerprint=", 1)[1].split(" ", 1)[0]

        calls = []

        def gh(args, check=True):
            calls.append(list(args))
            if args[:3] == ["gh", "issue", "list"]:
                row = {
                    "number": 42, "title": "t", "state": "OPEN", "closedAt": None,
                    "body": f"<!-- specfuse:finding fingerprint={fp} -->\n"
                            "<!-- specfuse:finding-meta occurrences=abc last_seen=1.0 -->\nbody",
                }
                return SimpleNamespace(returncode=0, stdout=json.dumps([row]), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        self.assertEqual(drive(gh), 0)
        edit = next(c for c in calls if c[:3] == ["gh", "issue", "edit"])
        body = edit[edit.index("--body") + 1]
        self.assertEqual(_parse_meta(body).occurrences, 1)
        self.assertTrue(re.search(r"\*\*Occurrences:\*\* 1\b", body))


if __name__ == "__main__":
    unittest.main()
