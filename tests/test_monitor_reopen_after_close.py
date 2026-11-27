#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A closed finding is reopened only for an occurrence after its close (#3615).

`record_finding` reopened every closed finding whose fingerprint appeared in
the harvested rows, without comparing those rows' timestamps with the issue's
`closedAt`. A run whose harvest window reached back before the close reopened
364 issues on one production run, none of which had recurred, and each
reopen comment reported the run time as "last seen".
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.issues import SeenThisRun, record_finding

_NOW = datetime(2026, 11, 26, 14, 9, 21, tzinfo=timezone.utc).timestamp()
_REPO = "acme-widget/repo"
_CLOSED_AT = "2026-11-17T12:00:00Z"


def _artifact(check_type: str = "error-logs", message_id: str = "") -> FailureArtifact:
    return FailureArtifact(
        component="web-api", check_type=check_type, failure_class="NullRef",
        failure_signature="sig", observed_text="boom", target_coordinates={},
        message_id=message_id or None,
    )


def _run(seen, *, artifact=None, message_ids=()):
    calls = []

    def gh(args, check=True):
        calls.append(list(args))
        if args[:3] == ["gh", "issue", "list"]:
            row = {
                "number": 7, "title": "t", "state": "CLOSED",
                "closedAt": _CLOSED_AT,
                "body": "<!-- specfuse:finding fingerprint=fp -->\n"
                        "<!-- specfuse:finding-meta occurrences=2 "
                        "last_seen=1000.0 first_seen=500.0 messages=a -->",
            }
            return SimpleNamespace(returncode=0, stdout=json.dumps([row]), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    number = record_finding(
        "fp", artifact or _artifact(), _REPO, runner=gh, now=_NOW, seen=seen,
        message_ids=message_ids)
    writes = [c for c in calls if c[:2] == ["gh", "issue"] and c[2] != "list"]
    return number, writes


class TestReopenOnlyAfterClose(unittest.TestCase):

    def test_occurrences_all_before_the_close_stay_closed(self):
        seen = SeenThisRun(count=8, first="2026-11-06T23:47:04Z",
                           last="2026-11-06T23:47:09Z")
        number, writes = _run(seen)
        self.assertEqual(number, "7")
        self.assertEqual(writes, [], "nothing recurred after the close")

    def test_an_occurrence_after_the_close_reopens(self):
        seen = SeenThisRun(count=3, first="2026-11-06T23:47:04Z",
                           last="2026-11-20T08:00:00Z")
        _, writes = _run(seen)
        self.assertEqual([w[2] for w in writes], ["reopen", "comment", "edit"])
        comment = writes[1][writes[1].index("--body") + 1]
        self.assertIn("last seen 2026-11-20T08:00:00Z", comment,
                      "the comment names the real latest occurrence, not the run time")

    def test_rows_without_timestamps_keep_todays_behaviour(self):
        _, writes = _run(SeenThisRun(count=2))
        self.assertEqual([w[2] for w in writes], ["reopen", "comment", "edit"])

    def test_no_seen_record_keeps_todays_behaviour(self):
        _, writes = _run(None)
        self.assertEqual([w[2] for w in writes], ["reopen", "comment", "edit"])

    def test_a_new_dead_lettered_message_still_reopens(self):
        seen = SeenThisRun(count=1, first="2026-11-06T23:47:04Z",
                           last="2026-11-06T23:47:09Z")
        _, writes = _run(seen, artifact=_artifact("dlq", "b"), message_ids=("b",))
        self.assertEqual([w[2] for w in writes], ["reopen", "comment", "edit"])


if __name__ == "__main__":
    unittest.main()
