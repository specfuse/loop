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

import contextlib
import io
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
            # GitHub's search tokenizer finds the bare id inside an HTML
            # comment in the body (#2548), so the fake searches both fields.
            matches = [i for i in self._issues if term in i["title"] or term in i["body"]]
            return SimpleNamespace(returncode=0, stdout=json.dumps(matches), stderr="")
        if argv[:3] == ["gh", "issue", "create"]:
            self.create_calls.append(argv)
            self._next_number += 1
            title = argv[argv.index("--title") + 1]
            body = argv[argv.index("--body") + 1]
            self._issues.append({"number": self._next_number, "title": title, "body": body})
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
                marker, _, body = argv[body_idx + 1].partition("\n")
                self.assertRegex(marker, r"^<!-- specfuse:followup id=FEAT-9999-followup-[0-9a-f]{10} -->$")
                self.assertEqual(body, expected_body, "the entry itself is verbatim after the marker")
            titles = [argv[argv.index("--title") + 1] for argv in runner.create_calls]
            self.assertEqual(titles, [
                "[FEAT-9999 follow-up] Criterion one: the widget renders",
                "[FEAT-9999 follow-up] Criterion two: coverage stays >= 90%",
            ])

            # The issue numbers were written back under each heading …
            text = (feature_dir / "FOLLOW-UPS.md").read_text()
            self.assertIn("### Criterion one: the widget renders\n\n**Tracked as #101.**\n\n**Evidence.**", text)
            self.assertIn("### Criterion two: coverage stays >= 90%\n\n**Tracked as #102.**\n\n**Evidence.**", text)
            self.assertEqual(loop.parse_followup_entries(text)[0].count("Tracked as"), 1)

            # … so a second call needs no network at all and files nothing new.
            lists_before = len(runner.list_calls)
            result2 = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(result2["filed"], 0)
            self.assertEqual(result2["already_tracked"], 2)
            self.assertEqual(result2["issue_numbers"], ["101", "102"])
            self.assertEqual(len(runner.create_calls), 2, "second call must not re-create")
            self.assertEqual(len(runner.list_calls), lists_before, "a tracked entry is not searched for")


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


_FOLLOW_UPS_ATTEMPT_TWO = """\
# Follow-ups

### Criterion two: coverage stays >= 90%

**Evidence.** `coverage report` — 88%, one branch still uncovered

**Re-run when.** parser.py's last branch gains a test

### Criterion three: the judge's diff covers the gate

**Evidence.** `git log 7e02525..HEAD` — 4 commits of 34

**Re-run when.** entry_sha is seeded from the merge-base
"""


class TestFollowupIdsAreByContentNotPosition(unittest.TestCase):
    """#3253: positional ids matched a later attempt's new findings to the
    previous attempt's issues, so the judge's findings were never filed."""

    def test_second_attempt_files_new_findings_and_dedupes_repeated_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            runner = _FakeGhRunner()
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_TWO_ENTRIES)
            first = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(first["filed"], 2)
            self.assertEqual(len(runner.create_calls), 2)

            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_ATTEMPT_TWO)
            second = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            # "Criterion two" repeats -> found by its body marker, not re-created;
            # "Criterion three" is new. The rewritten file carried no
            # `Tracked as` lines, so this is the network-side dedup at work.
            self.assertEqual(second["filed"], 2)
            self.assertEqual(second["already_tracked"], 0)
            self.assertEqual(len(runner.create_calls), 3, "exactly one new issue")
            titles = [argv[argv.index("--title") + 1] for argv in runner.create_calls]
            self.assertTrue(any("Criterion three" in t for t in titles), titles)
            self.assertEqual(sum("Criterion two" in t for t in titles), 1)

    def test_correlation_id_is_stable_for_the_same_heading_and_distinct_otherwise(self):
        a = loop.followup_correlation_id("FEAT-2026-0100", "### Criterion two: coverage stays >= 90%\n\nbody")
        b = loop.followup_correlation_id("FEAT-2026-0100", "### Criterion two: coverage stays >= 90%\n\ndifferent body")
        c = loop.followup_correlation_id("FEAT-2026-0100", "### Criterion three: the judge's diff covers the gate\n")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertTrue(a.startswith("FEAT-2026-0100-followup-"))
        self.assertRegex(a, r"-followup-[0-9a-f]{10}$")


_FOLLOW_UPS_AS_THE_CLOSES_WROTE_THEM = """\
# FOLLOW-UPS — FEAT-9999

Prose before the first entry is not an entry.

### 1. `T04#1` — the consumer loop has not run over this gate's output

**The criterion, verbatim:** the loop has run.

### The 83 `# NOTE:` disclosures did not reach zero — 72 survive

**Tracked as [#1721](https://github.com/acme/widget/issues/1721).**

**Criterion (gate 1), verbatim:** they are gone.

## Discharged at this close — recorded, not filed

- **`FEAT-2026-0164` was claimed by two roadmap rows.** Renumbered.
"""


class TestTitlesTrackingAndBoundaries(unittest.TestCase):
    """What the driver filed for FEAT-2026-0155 and FEAT-2026-0162 on
    2026-09-08: titles that were raw `### 1. …` heading lines (#1716–#1730),
    four entries filed twice because nothing recorded that they had been
    filed once (#1721–#1728), and a `## Discharged` section shipped as the
    tail of the last entry's issue body (#1729)."""

    def test_title_is_the_heading_text_not_the_heading_line(self):
        entry = "### 1. `T04#1` — the consumer loop has not run\n\nbody\n"
        self.assertEqual(loop.followup_heading(entry), "`T04#1` — the consumer loop has not run")
        self.assertEqual(
            loop.followup_issue_title("FEAT-2026-0162", loop.followup_heading(entry), "specfuse:follow-up"),
            "[FEAT-2026-0162 follow-up] `T04#1` — the consumer loop has not run",
        )
        self.assertEqual(loop.followup_heading("###   2)   spaced   out  \n"), "spaced out")
        self.assertEqual(loop.followup_heading("### - bulleted\n"), "bulleted")
        # The correlation id keys off the same cleaned heading, so `### 1. X`
        # on one attempt and `### X` on the next are one entry, not two.
        self.assertEqual(
            loop.followup_correlation_id("F", "### 1. T04#4\n"),
            loop.followup_correlation_id("F", "### T04#4\n"),
        )

    def test_hand_tracked_entry_is_skipped_and_discharged_section_is_not_filed(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            _write_plan(feature_dir)
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_AS_THE_CLOSES_WROTE_THEM)
            entries = loop.parse_followup_entries(_FOLLOW_UPS_AS_THE_CLOSES_WROTE_THEM)
            self.assertEqual(len(entries), 2)
            self.assertNotIn("Discharged", entries[1], "an entry ends at the next heading, any level")

            runner = _FakeGhRunner()
            result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(result["filed"], 1)
            self.assertEqual(result["already_tracked"], 1)
            self.assertEqual(result["issue_numbers"], ["1721", "101"])
            self.assertEqual(len(runner.create_calls), 1)
            argv = runner.create_calls[0]
            self.assertEqual(
                argv[argv.index("--title") + 1],
                "[FEAT-9999 follow-up] `T04#1` — the consumer loop has not run over this gate's output",
            )
            body = argv[argv.index("--body") + 1]
            self.assertNotIn("Discharged", body)
            self.assertNotIn("83 `# NOTE:`", body)

            text = (feature_dir / "FOLLOW-UPS.md").read_text()
            self.assertIn(
                "### 1. `T04#1` — the consumer loop has not run over this gate's output\n\n**Tracked as #101.**\n\n**The criterion",
                text,
            )
            self.assertEqual(text.count("Tracked as"), 2, "the hand-written line is left alone")
            self.assertIn("## Discharged at this close", text, "nothing below the entries is rewritten")

    def test_post_merge_checklist_gets_a_named_title_and_a_tracked_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)
            (feature_dir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\nstatus: done\nverdict: met\n---\n\n# Plan\n\n"
                "## Post-merge checklist\n\n- **`gatecheck.py --forbid-no-changes` exits 0 on merged HEAD.**\n"
            )
            runner = _FakeGhRunner()
            result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual(result["filed"], 1)
            argv = runner.create_calls[0]
            self.assertEqual(argv[argv.index("--title") + 1], "[FEAT-9999 post-merge] Post-merge checklist")
            self.assertEqual(argv[argv.index("--label") + 1], "specfuse:post-merge")
            plan = (feature_dir / "PLAN.md").read_text()
            self.assertIn("## Post-merge checklist\n\n**Tracked as #101.**\n\n- **`gatecheck.py", plan)
            # And the tracked line makes the next call a no-op.
            again = loop.file_followup_issues(feature_dir, feature_dir, runner=runner)
            self.assertEqual((again["filed"], again["already_tracked"]), (0, 1))
            self.assertEqual(len(runner.create_calls), 1)


class TestTrackedLineIsReadUnderTheHeadingOnly(unittest.TestCase):
    def test_a_foreign_tracked_line_quoted_in_the_evidence_does_not_skip_the_entry(self):
        entry = (
            "### The consumer gate failure is FEAT-2026-0160's\n\n"
            "**Evidence.** FEAT-2026-0160's entry reads:\n\n"
            "> **Tracked as #1700.**\n"
        )
        self.assertIsNone(loop.followup_tracked_issue(entry))
        self.assertEqual(loop.followup_tracked_issue("### X\n\n**Tracked as #7.**\n\nbody\n"), "7")
        self.assertEqual(loop.followup_tracked_issue("### X\n**Tracked as [#8](u).**\n"), "8")
        # A post-merge section has no heading line of its own.
        self.assertEqual(loop.followup_tracked_issue("\n**Tracked as #9.**\n\n- item\n"), "9")

    def test_write_back_commit_failure_is_printed_not_swallowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir = Path(tmp)  # not a git repository: commit_bookkeeping raises
            _write_plan(feature_dir)
            (feature_dir / "FOLLOW-UPS.md").write_text(_FOLLOW_UPS_AS_THE_CLOSES_WROTE_THEM)
            runner = _FakeGhRunner()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                result = loop.file_followup_issues(feature_dir, feature_dir, runner=runner, commit=True)
            self.assertEqual(result["filed"], 1)
            self.assertFalse(result["writeback_committed"])
            self.assertEqual(result["written_back"], ["FOLLOW-UPS.md"])
            self.assertIn("WARNING: follow-up write-back not committed", buf.getvalue())
            self.assertIn("FOLLOW-UPS.md", buf.getvalue())
            event = json.loads((feature_dir / "events.jsonl").read_text().splitlines()[-1])
            self.assertEqual(event["payload"]["written_back"], ["FOLLOW-UPS.md"])
