# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The promotion ledger: which triaged feature issues became roadmap rows.

`triage.py` has routed `feature` to `roadmap-add` since it shipped, and
nothing ever recorded when a human walked that route. So a triaged feature
issue had one observable state forever: labelled, open, and
indistinguishable from every other one whether or not its work was already
on the roadmap. Thirteen accumulated with nobody able to say which were
live.

Every test injects a runner; none reaches GitHub.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.promotion import (
    is_promoted,
    list_promoted,
    list_unpromoted,
    main,
    parse_marker,
    record_promotion,
    render_marker,
)

_REPO = "acme-widget/example"


class _ListRunner:
    """Replays one `gh issue list` payload; records every call."""

    def __init__(self, issues, returncode=0, stdout=None):
        self._payload = SimpleNamespace(
            returncode=returncode,
            stdout=json.dumps(issues) if stdout is None else stdout,
            stderr="",
        )
        self.calls = []

    def __call__(self, args, check=False):
        self.calls.append(args)
        return self._payload


class _EditRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, args, check=False):
        self.calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")


def _issue(number, body="", title="a request"):
    return {"number": number, "title": title, "body": body, "labels": []}


class TestTheMarker(unittest.TestCase):
    def test_round_trips(self):
        self.assertEqual(parse_marker(render_marker("FEAT-2026-0099")), "FEAT-2026-0099")

    def test_absent_marker_reads_as_unpromoted(self):
        self.assertIsNone(parse_marker("just an issue body"))
        self.assertFalse(is_promoted("just an issue body"))
        self.assertFalse(is_promoted(""))

    def test_a_malformed_id_is_refused_at_render_time(self):
        """A typo'd ID is a permanent broken link that reads as a valid one,
        so it must never reach an issue body."""
        for bad in ("nope", "FEAT-26-0001", "FEAT-2026-1", "", "FEAT-2026-0001/T01"):
            with self.subTest(feature_id=bad):
                with self.assertRaises(ValueError):
                    render_marker(bad)

    def test_the_marker_survives_surrounding_prose(self):
        body = f"# Title\n\nsome text\n\n{render_marker('FEAT-2026-0001')}\n\nmore"
        self.assertEqual(parse_marker(body), "FEAT-2026-0001")


class TestTheBacklogQuestion(unittest.TestCase):
    """"Which feature requests still need a roadmap decision" — the question
    that was unanswerable before this module."""

    def test_unpromoted_issues_are_returned(self):
        runner = _ListRunner([_issue(1), _issue(2)])

        rows = list_unpromoted(runner, _REPO)

        self.assertEqual([r["number"] for r in rows], [1, 2])
        self.assertTrue(all(r["promoted"] is False for r in rows))

    def test_a_promoted_issue_is_excluded(self):
        runner = _ListRunner([
            _issue(1),
            _issue(2, body=render_marker("FEAT-2026-0050")),
        ])

        self.assertEqual([r["number"] for r in list_unpromoted(runner, _REPO)], [1])

    def test_promoted_issues_carry_the_id_they_became(self):
        runner = _ListRunner([
            _issue(1),
            _issue(2, body=render_marker("FEAT-2026-0050")),
        ])

        rows = list_promoted(runner, _REPO)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["feature_id"], "FEAT-2026-0050")

    def test_the_two_lists_partition_the_labelled_set(self):
        issues = [_issue(1), _issue(2, body=render_marker("FEAT-2026-0050")), _issue(3)]

        up = list_unpromoted(_ListRunner(issues), _REPO)
        pr = list_promoted(_ListRunner(issues), _REPO)

        self.assertEqual(len(up) + len(pr), len(issues))
        self.assertFalse({r["number"] for r in up} & {r["number"] for r in pr})

    def test_it_queries_the_triage_feature_label(self):
        runner = _ListRunner([])
        list_unpromoted(runner, _REPO)

        self.assertIn("--label", runner.calls[0])
        self.assertIn("triage:feature", runner.calls[0])

    def test_a_gh_failure_yields_empty_rather_than_raising(self):
        self.assertEqual(list_unpromoted(_ListRunner([], returncode=1), _REPO), [])
        self.assertEqual(
            list_unpromoted(_ListRunner([], stdout="not json"), _REPO), [])


class TestRecording(unittest.TestCase):
    def test_a_promotion_appends_the_marker(self):
        runner = _EditRunner()

        report = record_promotion(runner, _REPO, 7, "FEAT-2026-0099", "body text")

        self.assertTrue(report["written"])
        body = next(c[c.index("--body") + 1] for c in runner.calls if "--body" in c)
        self.assertEqual(parse_marker(body), "FEAT-2026-0099")
        self.assertIn("body text", body, "the original body must survive")

    def test_recording_twice_writes_once(self):
        runner = _EditRunner()
        body = f"text\n\n{render_marker('FEAT-2026-0099')}"

        report = record_promotion(runner, _REPO, 7, "FEAT-2026-0099", body)

        self.assertFalse(report["written"])
        self.assertEqual(runner.calls, [], "no gh call on an already-recorded issue")

    def test_a_conflicting_id_is_reported_not_silently_repointed(self):
        """Rewriting the marker would erase the only record of where the work
        actually went."""
        runner = _EditRunner()
        body = f"text\n\n{render_marker('FEAT-2026-0050')}"

        report = record_promotion(runner, _REPO, 7, "FEAT-2026-0099", body)

        self.assertFalse(report["written"])
        self.assertEqual(report["already"], "FEAT-2026-0050")
        self.assertEqual(runner.calls, [])

    def test_a_bad_id_is_refused_before_any_write(self):
        runner = _EditRunner()

        with self.assertRaises(ValueError):
            record_promotion(runner, _REPO, 7, "not-an-id", "body")

        self.assertEqual(runner.calls, [])

    def test_an_empty_body_still_gets_a_marker(self):
        runner = _EditRunner()

        record_promotion(runner, _REPO, 7, "FEAT-2026-0099", "")

        body = next(c[c.index("--body") + 1] for c in runner.calls if "--body" in c)
        self.assertEqual(parse_marker(body), "FEAT-2026-0099")


class TestTheLedgerIsReachable(unittest.TestCase):
    """A ledger nothing can write to is the hollow shape from
    `[FEAT-2026-0008/G1-CLOSE]`: tests pass, tracked state never changes."""

    def test_list_subcommand_reports_the_backlog(self):
        runner = _ListRunner([_issue(1), _issue(2)])

        self.assertEqual(main(["list", _REPO], runner=runner), 0)

    def test_record_subcommand_writes_through(self):
        class _R:
            def __init__(self):
                self.calls = []

            def __call__(self, args, check=False):
                self.calls.append(args)
                if "view" in args:
                    return SimpleNamespace(
                        returncode=0, stdout=json.dumps({"body": "text"}), stderr="")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

        runner = _R()
        self.assertEqual(
            main(["record", _REPO, "7", "FEAT-2026-0099"], runner=runner), 0)

        body = next(c[c.index("--body") + 1] for c in runner.calls if "--body" in c)
        self.assertEqual(parse_marker(body), "FEAT-2026-0099")

    def test_record_rejects_a_bad_id_with_a_distinct_exit_code(self):
        class _R:
            def __call__(self, args, check=False):
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps({"body": ""}), stderr="")

        self.assertEqual(main(["record", _REPO, "7", "nope"], runner=_R()), 2)

    def test_usage_on_no_arguments(self):
        self.assertEqual(main([], runner=_EditRunner()), 2)


if __name__ == "__main__":
    unittest.main()
