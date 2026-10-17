# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3502: `issues.annotate_if_quiet` existed but nothing called it, so a
finding that stopped firing was never marked as a close candidate. A cycle now
annotates each open finding of a component it fully checked whose fingerprint
was not seen this cycle and whose last sighting is older than the quiet
threshold — once per quiet period, never closing anything, and never because a
check errored.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli
from specfuse.monitor import issues

_NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"
_DAY = 24 * 60 * 60


def _component(name, checks=None):
    return {
        "name": name,
        "type": "api",
        "runner": "local",
        "diagnose": "manual",
        "autofix": "off",
        "checks": checks if checks is not None else [{"type": "error-logs"}],
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


def _issue(fingerprint, *, component="web-api", number=7, days_quiet=8, state="OPEN", extra=""):
    last_seen = _NOW.timestamp() - days_quiet * _DAY
    body = (
        f"<!-- specfuse:finding fingerprint={fingerprint} -->\n"
        f"<!-- specfuse:finding-meta occurrences=3 last_seen={last_seen} first_seen={last_seen} -->\n"
        f"{extra}\n**Component:** {component}\n**Check type:** error-logs\n"
    )
    return {"number": number, "body": body, "title": "t", "state": state, "closedAt": None}


class _Transport:
    def __init__(self, rows=(), error=None):
        self._rows = list(rows)
        self._error = error

    def run_query(self, query):
        if self._error is not None:
            raise self._error
        return list(self._rows)


class _Gh:
    """A listing that returns `issues` for every `gh issue list`; records writes."""

    def __init__(self, listed):
        self.listed = listed
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(list(args))
        if args[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.listed), stderr="")
        return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/99\n", stderr="")

    def verbs(self, verb):
        return [c for c in self.calls if c[:3] == ["gh", "issue", verb]]


class TestQuietFindingsAreAnnotated(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _run(self, config, gh, *, rows=(), error=None, dry_run=False):
        out = io.StringIO()
        code = cli.run_cycle(
            config,
            dry_run=dry_run,
            repo=_REPO,
            transport_resolver=lambda module, check_type, binding: _Transport(rows, error),
            gh_runner=gh,
            now=_NOW,
            watermark_dir=Path(self._tmpdir.name),
            out=out,
        )
        return code, out.getvalue()

    def test_quiet_open_finding_is_annotated_once_without_closing(self):
        gh = _Gh([_issue("fp-quiet")])
        _, output = self._run(_config(_component("web-api")), gh)
        comments = gh.verbs("comment")
        self.assertEqual(len(comments), 1, output)
        self.assertIn("candidate for close", comments[0][comments[0].index("--body") + 1])
        edits = gh.verbs("edit")
        self.assertEqual(len(edits), 1)
        self.assertIn(issues._QUIET_MARKER, edits[0][edits[0].index("--body") + 1])
        self.assertEqual(gh.verbs("close"), [])
        self.assertIn("quiet", output)

    def test_recently_seen_finding_is_left_alone(self):
        gh = _Gh([_issue("fp-recent", days_quiet=2)])
        self._run(_config(_component("web-api")), gh)
        self.assertEqual(gh.verbs("comment") + gh.verbs("edit"), [])

    def test_already_annotated_finding_is_not_annotated_again(self):
        gh = _Gh([_issue("fp-done", extra=issues._QUIET_MARKER)])
        self._run(_config(_component("web-api")), gh)
        self.assertEqual(gh.verbs("comment") + gh.verbs("edit"), [])

    def test_closed_finding_is_left_alone(self):
        gh = _Gh([_issue("fp-closed", state="CLOSED")])
        self._run(_config(_component("web-api")), gh)
        self.assertEqual(gh.verbs("comment") + gh.verbs("edit"), [])

    def test_no_annotation_when_the_components_check_errored(self):
        gh = _Gh([_issue("fp-quiet")])
        code, output = self._run(_config(_component("web-api")), gh, error=RuntimeError("workspace down"))
        self.assertEqual(code, 1)
        self.assertEqual(gh.verbs("comment") + gh.verbs("edit"), [], output)

    def test_finding_of_a_component_not_checked_this_cycle_is_left_alone(self):
        gh = _Gh([_issue("fp-other", component="admin-portal")])
        self._run(_config(_component("web-api")), gh)
        self.assertEqual(gh.verbs("comment") + gh.verbs("edit"), [])

    def test_finding_seen_this_cycle_is_not_quiet(self):
        row = {"type": "NullReferenceException", "outerMessage": "boom"}
        # Discover the fingerprint this row produces by running once with no issues.
        probe = _Gh([])
        self._run(_config(_component("web-api")), probe, rows=[row])
        created = probe.verbs("create")[0]
        body = created[created.index("--body") + 1]
        fingerprint = body.split("fingerprint=", 1)[1].split(" ", 1)[0]
        gh = _Gh([_issue(fingerprint)])
        self._run(_config(_component("web-api")), gh, rows=[row])
        self.assertEqual(gh.verbs("comment"), [])

    def test_one_listing_for_the_quiet_pass(self):
        gh = _Gh([_issue("fp-a", number=1), _issue("fp-b", component="worker", number=2)])
        self._run(_config(_component("web-api"), _component("worker")), gh)
        self.assertEqual(len(gh.verbs("list")), 1)
        self.assertEqual(len(gh.verbs("comment")), 2)

    def test_dry_run_only_reports(self):
        gh = _Gh([_issue("fp-quiet")])
        _, output = self._run(_config(_component("web-api")), gh, dry_run=True)
        self.assertEqual(gh.verbs("comment") + gh.verbs("edit"), [])
        self.assertIn("would annotate", output)


class TestRecurrenceClearsTheQuietMarker(unittest.TestCase):
    def test_an_update_after_a_quiet_period_drops_the_marker(self):
        from specfuse.monitor.artifact import FailureArtifact
        from specfuse.monitor.fingerprint import fingerprint_artifact

        artifact = FailureArtifact(
            component="web-api", check_type="error-logs", failure_class="X",
            failure_signature="X:boom", observed_text="boom",
        )
        fingerprint = fingerprint_artifact(artifact)
        gh = _Gh([_issue(fingerprint, extra=issues._QUIET_MARKER)])
        issues.record_finding(fingerprint, artifact, _REPO, runner=gh, now=_NOW.timestamp())
        edits = gh.verbs("edit")
        self.assertEqual(len(edits), 1)
        self.assertNotIn(issues._QUIET_MARKER, edits[0][edits[0].index("--body") + 1])


if __name__ == "__main__":
    unittest.main()
