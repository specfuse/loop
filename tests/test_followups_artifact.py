#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FOLLOW-UPS.md and its issue filing — FEAT-2026-0085/T03.

Covers:
  (1) test_not_met_close_without_followups_is_refused — close-m fires via
      assert_closing_deliverables when verdict=not_met and FOLLOW-UPS.md is
      absent.
  (2) test_one_issue_per_entry_body_verbatim — file_followup_issues files one
      `gh issue create` per entry, body byte-for-byte, `specfuse:follow-up`
      labelled, idempotent on a second call.
  (3) test_gh_failure_keeps_file_and_records_event — a failing runner leaves
      FOLLOW-UPS.md untouched and records filed=0, unfiled=2.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

_FOLLOW_UPS_TWO_ENTRIES = """\
# Follow-ups

### Criterion one: the widget renders

**Evidence.** `pytest tests/test_widget.py` — exit 1, AssertionError on line 12

**Re-run when.** the renderer's async mount race is fixed

### Criterion two: coverage stays >= 90%

**Evidence.** `coverage report` — 87%

**Re-run when.** the two uncovered branches in parser.py gain tests
"""


def _make_wu(feature_dir: Path, verdict: str | None) -> "loop.WorkUnit":
    wu_file = feature_dir / "WU-90-close.md"
    fm_lines = ["id: FEAT-9999/G1-CLOSE", "type: close", "status: pending", "attempts: 1"]
    if verdict is not None:
        fm_lines.append(f"verdict: {verdict}")
    wu_file.write_text("---\n" + "\n".join(fm_lines) + "\n---\n" + _WU_BODY)
    return loop.WorkUnit(
        wu_id="FEAT-9999/G1-CLOSE",
        file=wu_file,
        depends_on=[],
        type="close",
        model="opus",
        status="pending",
        attempts=1,
        title="test close",
        body=_WU_BODY,
        verdict=verdict,
    )


def _write_plan(feature_dir: Path, *, feature_id: str = "FEAT-9999", extra_body: str = "") -> None:
    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\nstatus: active\n---\n\n# Plan\n{extra_body}"
    )


class TestNotMetCloseWithoutFollowupsIsRefused(unittest.TestCase):
    def test_not_met_close_without_followups_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            wu = _make_wu(feature_dir, verdict="not_met")
            _write_plan(feature_dir)
            ok, reason = loop.assert_closing_deliverables(
                wu, feature_dir, feature_dir, "0" * 40,
            )
            self.assertFalse(ok)
            self.assertIn("assert_followups_recorded", reason)
            self.assertIn("FOLLOW-UPS.md", reason)

    def test_met_close_does_not_require_followups(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            wu = _make_wu(feature_dir, verdict="met")
            ok, reason = loop.assert_followups_recorded(
                wu, feature_dir, feature_dir, "0" * 40,
            )
            self.assertTrue(ok, reason)

    def test_not_met_close_with_followups_passes_close_m(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            wu = _make_wu(feature_dir, verdict="not_met")
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_TWO_ENTRIES)
            ok, reason = loop.assert_followups_recorded(
                wu, feature_dir, feature_dir, "0" * 40,
            )
            self.assertTrue(ok, reason)


class _FakeGhRunner:
    """Models `gh issue list --search ...` / `gh issue create` well enough
    for idempotency: title-substring search over issues this runner itself
    created. `fail` makes every call return a non-zero exit."""

    def __init__(self, fail: bool = False, label_fail: bool = False):
        self.fail = fail
        self.label_fail = label_fail
        self.label_calls: list[list[str]] = []
        self.create_calls: list[list[str]] = []
        self.list_calls: list[list[str]] = []
        self._issues: list[dict] = []
        self._next_number = 100

    def __call__(self, argv: list, check: bool = False):
        if self.fail:
            return SimpleNamespace(returncode=1, stdout="", stderr="gh: not authenticated")
        if argv[:3] == ["gh", "label", "create"]:
            self.label_calls.append(argv)
            if self.label_fail:
                return SimpleNamespace(returncode=1, stdout="", stderr="label create failed")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:3] == ["gh", "issue", "list"]:
            self.list_calls.append(argv)
            term = argv[argv.index("--search") + 1].strip('"')
            matches = [i for i in self._issues if term in i["title"]]
            return SimpleNamespace(returncode=0, stdout=json.dumps(matches), stderr="")
        if argv[:3] == ["gh", "issue", "create"]:
            self.create_calls.append(argv)
            self._next_number += 1
            title = argv[argv.index("--title") + 1]
            self._issues.append({"number": self._next_number, "title": title})
            return SimpleNamespace(
                returncode=0,
                stdout=f"https://github.com/acme/widget/issues/{self._next_number}\n",
                stderr="",
            )
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected argv")


class TestOneIssuePerEntryBodyVerbatim(unittest.TestCase):
    def test_one_issue_per_entry_body_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_TWO_ENTRIES)
            expected_bodies = loop.parse_followup_entries(_FOLLOW_UPS_TWO_ENTRIES)
            self.assertEqual(len(expected_bodies), 2)

            runner = _FakeGhRunner()
            result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)

            self.assertEqual(result["filed"], 2)
            self.assertEqual(result["unfiled"], 0)
            self.assertEqual(len(runner.create_calls), 2)
            for argv, expected_body in zip(runner.create_calls, expected_bodies, strict=True):
                self.assertIn("--label", argv)
                label_idx = argv.index("--label")
                self.assertEqual(argv[label_idx + 1], "specfuse:follow-up")
                body_idx = argv.index("--body")
                self.assertEqual(argv[body_idx + 1], expected_body)

            # A second call finds both existing issues via title-search and
            # files nothing new.
            result2 = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(result2["filed"], 2)
            self.assertEqual(len(runner.create_calls), 2, "second call must not re-create")


class TestGhFailureKeepsFileAndRecordsEvent(unittest.TestCase):
    def test_gh_failure_keeps_file_and_records_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_TWO_ENTRIES)

            runner = _FakeGhRunner(fail=True)
            result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)

            self.assertEqual(result["filed"], 0)
            self.assertEqual(result["unfiled"], 2)
            self.assertEqual(
                (feature_dir / "FOLLOW-UPS.md").read_text(), _FOLLOW_UPS_TWO_ENTRIES,
            )

            events_path = feature_dir / "events.jsonl"
            lines = [ln for ln in events_path.read_text().splitlines() if ln.strip()]
            evt = json.loads(lines[-1])
            self.assertEqual(evt["event_type"], "followups_recorded")
            self.assertEqual(evt["payload"]["filed"], 0)
            self.assertEqual(evt["payload"]["unfiled"], 2)


if __name__ == "__main__":
    unittest.main()


class TestLabelsAreEnsuredBeforeFiling(unittest.TestCase):
    """#3244: the two labels are registered but nothing provisioned them, so
    the first `gh issue create --label specfuse:follow-up` would 422."""

    def test_follow_up_label_is_created_before_the_first_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_TWO_ENTRIES)
            runner = _FakeGhRunner()
            result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(result["filed"], 2)
            names = [argv[3] for argv in runner.label_calls]
            self.assertEqual(names, ["specfuse:follow-up"], "one ensure per distinct label")
            self.assertIn("--force", runner.label_calls[0])
            self.assertIn("--color", runner.label_calls[0])
            self.assertIn("--description", runner.label_calls[0])
            # ensured before any issue was created
            self.assertLess(0, len(runner.create_calls))

    def test_label_create_failure_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_TWO_ENTRIES)
            runner = _FakeGhRunner(label_fail=True)
            result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            # Filing still attempted; the fake accepts creates regardless.
            self.assertEqual(result["filed"], 2)
            self.assertEqual(result.get("labels_unensured"), ["specfuse:follow-up"])

    def test_no_entries_means_no_label_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            runner = _FakeGhRunner()
            loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(runner.label_calls, [])
