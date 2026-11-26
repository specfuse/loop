#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-LOOP-2026-0251 gate 1 oracle — a missing deliverable is refused before
the verification gates run. One class per Definition-of-done clause in
GATE-01.md.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import lint_plan
from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

FEATURE_ID = "FEAT-2026-9251"
T01 = f"{FEATURE_ID}/T01"

_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
_COMPLETE = "```result\nstatus: complete\n```\n"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _write_feature(root: Path) -> Path:
    fdir = root / f".specfuse/features/{FEATURE_ID}-fail-fast"
    fdir.mkdir(parents=True)
    close_id = f"{FEATURE_ID}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {FEATURE_ID}\ntitle: Fixture\nslug: fail-fast\n"
        "branch: feat/fail-fast\nroadmap_goal: test\nstatus: active\n---\n\n"
        "# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {T01}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{T01}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# G\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {T01}\ntype: implementation\nmodel: sonnet\n"
        "status: pending\nattempts: 0\nproduces:\n  - src/rule.py\n---\n\n"
        f"# T01{_BODY}")
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{_BODY}")
    Path(root, "src").mkdir(exist_ok=True)
    Path(root, "src/rule.py").write_text("SEVERITY = 'WARNING'\n")
    _git("add", ".")
    _git("commit", "-q", "-m", "scaffold")
    return fdir


class _Case(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in reversed(self._patches):
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _workspace(self):
        ws = integration_workspace()
        root = ws.__enter__()
        self.addCleanup(ws.__exit__, None, None, None)
        os.chdir(root)
        return root, _write_feature(root)


class TestProducesNotInDiffEarly(_Case):
    """Clause 1 — refused before `verify_fn`, same record as the late path."""

    def _attempt(self, touch: str, stdout: str = _COMPLETE):
        _, fdir = self._workspace()
        wu = loop.load_wu(fdir, {"id": T01, "file": "WU-T01.md",
                                 "depends_on": []})
        head = _git("rev-parse", "HEAD")
        calls = []

        def dispatch_fn(w, note):
            Path(touch).parent.mkdir(exist_ok=True)
            Path(touch).write_text("changed\n")
            return stdout

        def verify_fn(w, fd):
            calls.append(w.wu_id)
            return True, "(stub)"

        outcome, payload, usage = loop.execute_unit_attempt(
            wu, fdir, None, dispatch_fn=dispatch_fn, verify_fn=verify_fn,
            cost_tracking=False, head_before=head, prerun_cfg={},
            untracked_before=loop.untracked_paths())
        return wu, outcome, payload, usage, calls

    def test_untouched_path_is_refused_without_verifying(self):
        wu, outcome, payload, usage, calls = self._attempt("docs/notes.md")
        self.assertEqual(outcome, "produces_not_in_diff")
        self.assertEqual(payload["remaining"], ["src/rule.py"])
        self.assertIn("docs/notes.md", payload["touched"])
        self.assertEqual(calls, [])
        self.assertEqual(usage["verify_seconds"], 0)
        self.assertEqual(loop.build_attempt_gate_events(wu, 1), [])

    def test_changed_path_verifies_once_and_passes(self):
        _, outcome, _, _, calls = self._attempt("src/rule.py")
        self.assertEqual(outcome, "passed")
        self.assertEqual(calls, [T01])

    def test_justified_path_still_verifies(self):
        _, outcome, _, _, calls = self._attempt(
            "docs/notes.md",
            "```result\nstatus: complete\nproduces_unchanged:\n"
            "  - path: src/rule.py\n    justification: already holds\n```\n")
        self.assertEqual(outcome, "passed")
        self.assertEqual(calls, [T01])

    def test_index_is_left_alone(self):
        self._attempt("docs/notes.md")
        self.assertEqual(_git("diff", "--cached", "--name-only"), "")

    def _run_driver(self, early: bool):
        """`loop.run()` over an attempt that never touches `src/rule.py`.
        `early=False` silences the pre-verify check, leaving the late site."""
        _, fdir = self._workspace()
        verified = []

        def dispatch(wu, note, ct=True):
            if wu.wu_id == T01:
                Path("docs").mkdir(exist_ok=True)
                Path("docs/notes.md").write_text("notes\n")
            return _COMPLETE

        def verify(wu, fd, cfg=None):
            verified.append(wu.wu_id)
            return True, "(stub)"

        self._patch("dispatch", dispatch)
        self._patch("verify", verify)
        if not early:
            self._patch("early_produces_refusal", lambda *a, **k: None)
        self.assertEqual(loop.run(None, dry_run=False), 1)
        events = [json.loads(line) for line in
                  (fdir / "events.jsonl").read_text().splitlines() if line]
        refusals = [
            e["payload"] for e in events
            if e["event_type"] == "attempt_outcome"
            and e["payload"]["outcome"] == "produces_not_in_diff"]
        self.assertTrue(refusals)
        self.assertEqual(
            [e for e in events if e["event_type"] == "gate_result"
             and e["correlation_id"] == T01
             and e["payload"]["phase"] == "attempt"], [])
        return refusals[0], verified

    def test_early_record_equals_late_record(self):
        early, early_verified = self._run_driver(early=True)
        late, late_verified = self._run_driver(early=False)
        self.assertEqual(early_verified, [])
        self.assertIn(T01, late_verified)
        self.assertEqual(early["verify_seconds"], 0)
        for key in ("failure_class", "failure_signature", "summary"):
            self.assertEqual(early[key], late[key], key)


def _delete_rule(fdir: Path) -> None:
    Path("src/rule.py").unlink(missing_ok=True)


def _empty_rule(fdir: Path) -> None:
    Path("src/rule.py").write_text("")


def _bookkeeping_only(fdir: Path) -> None:
    for name in ("WU-T01.md", "events.jsonl"):
        with (fdir / name).open("a") as handle:
            handle.write("\n")


def _notes_only(fdir: Path) -> None:
    Path("docs").mkdir(exist_ok=True)
    Path("docs/notes.md").write_text("notes\n")


class TestPresenceEarly(_Case):
    """Clause 2 — `deliverable_missing` / `no_deliverable_files` early."""

    def _assert_early(self, act, expected: str):
        _, fdir = self._workspace()
        wu = loop.load_wu(fdir, {"id": T01, "file": "WU-T01.md",
                                 "depends_on": []})
        head = _git("rev-parse", "HEAD")
        calls = []

        def dispatch_fn(w, note):
            act(fdir)
            return _COMPLETE

        def verify_fn(w, fd):
            calls.append(w.wu_id)
            return True, "(stub)"

        outcome, payload, usage = loop.execute_unit_attempt(
            wu, fdir, None, dispatch_fn=dispatch_fn, verify_fn=verify_fn,
            cost_tracking=False, head_before=head, prerun_cfg={},
            untracked_before=loop.untracked_paths())
        self.assertEqual(outcome, expected)
        self.assertTrue(payload["summary"])
        self.assertEqual(calls, [])
        self.assertEqual(usage["verify_seconds"], 0)

    def test_absent_path_is_refused_without_verifying(self):
        self._assert_early(_delete_rule, "deliverable_missing")

    def test_empty_path_is_refused_without_verifying(self):
        self._assert_early(_empty_rule, "deliverable_missing")

    def test_bookkeeping_only_diff_is_refused_without_verifying(self):
        self._assert_early(_bookkeeping_only, "no_deliverable_files")


class TestOptOut(_Case):
    """Clause 3 — `defaults.fail_fast_deliverables: false`."""

    _REFUSALS = ("deliverable_missing", "no_deliverable_files",
                 "produces_not_in_diff")

    def test_key_defaults_to_true(self):
        self.assertTrue(loop.resolve_fail_fast_deliverables({}))
        self.assertFalse(loop.resolve_fail_fast_deliverables(
            {"defaults": {"fail_fast_deliverables": False}}))

    def _first_refusal(self, act, fail_fast: bool):
        """`loop.run()`; returns the first refusal record and how many times
        the unit was verified before the second dispatch."""
        _, fdir = self._workspace()
        seen = []
        load = loop.load_verification

        def load_cfg(*args, **kwargs):
            cfg = dict(load(*args, **kwargs))
            if not fail_fast:
                cfg["defaults"] = {"fail_fast_deliverables": False}
            return cfg

        def dispatch(wu, note, ct=True):
            if wu.wu_id == T01:
                seen.append("dispatch")
                act(fdir)
            return _COMPLETE

        def verify(wu, fd, cfg=None):
            if wu.wu_id == T01:
                seen.append("verify")
            return True, "(stub)"

        self._patch("load_verification", load_cfg)
        self._patch("dispatch", dispatch)
        self._patch("verify", verify)
        self.assertEqual(loop.run(None, dry_run=False), 1)
        for name, original in reversed(self._patches):
            setattr(loop, name, original)
        self._patches.clear()
        refusals = [
            e["payload"] for e in map(
                json.loads,
                filter(None, (fdir / "events.jsonl").read_text().splitlines()))
            if e["event_type"] == "attempt_outcome"
            and e["payload"]["outcome"] in self._REFUSALS]
        self.assertTrue(refusals)
        first_attempt = seen[1:]
        if "dispatch" in first_attempt:
            first_attempt = first_attempt[:first_attempt.index("dispatch")]
        return refusals[0], first_attempt.count("verify")

    def _assert_opt_out(self, act, expected: str):
        default, default_verified = self._first_refusal(act, fail_fast=True)
        late, late_verified = self._first_refusal(act, fail_fast=False)
        self.assertEqual(default_verified, 0)
        self.assertEqual(late_verified, 1)
        self.assertEqual(late["outcome"], expected)
        for key in ("outcome", "failure_class", "failure_signature",
                    "summary"):
            self.assertEqual(default[key], late[key], key)

    def test_deliverable_missing_verifies_first(self):
        self._assert_opt_out(_delete_rule, "deliverable_missing")

    def test_no_deliverable_files_verifies_first(self):
        self._assert_opt_out(_bookkeeping_only, "no_deliverable_files")

    def test_produces_not_in_diff_verifies_first(self):
        self._assert_opt_out(_notes_only, "produces_not_in_diff")


class TestTreeAndNote(_Case):
    """Clause 4 — tree handling and retry note."""

    def _retry_note(self, act, retain: bool = True,
                    fail_fast: bool = True):
        """`loop.run()`; returns the note handed to the second T01 attempt and
        whether the first attempt's work was still on disk at that point."""
        self._workspace()
        notes, kept = [], []
        load = loop.load_verification

        def load_cfg(*args, **kwargs):
            cfg = dict(load(*args, **kwargs))
            cfg["defaults"] = {"retain_on_guard_refusal": retain,
                               "fail_fast_deliverables": fail_fast}
            return cfg

        def dispatch(wu, note, cost_tracking=True):
            if wu.body.startswith(loop._REPLAN_BRIEF_MARKER):
                # An early refusal re-plans before the last attempt too.
                return "# T01\n\nRe-planned body.\n"
            if wu.wu_id == T01:
                notes.append(note)
                if len(notes) == 1:
                    act()
                elif len(notes) == 2:
                    kept.append(Path("docs/notes.md").exists())
            return _COMPLETE

        self._patch("load_verification", load_cfg)
        self._patch("dispatch", dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
        self.assertEqual(loop.run(None, dry_run=False), 1)
        for name, original in reversed(self._patches):
            setattr(loop, name, original)
        self._patches.clear()
        self.assertGreaterEqual(len(notes), 2)
        return notes[1], kept[0]

    @staticmethod
    def _two_files():
        Path("docs").mkdir(exist_ok=True)
        Path("docs/notes.md").write_text("notes\n")
        Path("docs/other.md").write_text("other\n")

    def _assert_note(self, note):
        self.assertIn("src/rule.py", note)
        self.assertIn("- `docs/notes.md`", note)
        self.assertIn("- `docs/other.md`", note)
        self.assertIn("verification did not run", note)
        self.assertNotIn("verification already PASSED", note)

    def test_retained_tree_and_note(self):
        note, kept = self._retry_note(self._two_files, retain=True)
        self._assert_note(note)
        self.assertTrue(kept)

    def test_reset_tree_and_note(self):
        note, kept = self._retry_note(self._two_files, retain=False)
        self._assert_note(note)
        self.assertFalse(kept)

    def test_attempt_that_changed_nothing_says_so(self):
        note, _ = self._retry_note(lambda: None)
        self.assertIn("this attempt changed no files", note)

    def test_presence_refusals_list_changed_paths_early_and_late(self):
        def delete_rule_and_write():
            self._two_files()
            Path("src/rule.py").unlink()

        for fail_fast in (True, False):
            with self.subTest("deliverable_missing", fail_fast=fail_fast):
                note, _ = self._retry_note(delete_rule_and_write,
                                           fail_fast=fail_fast)
                self.assertIn("- `docs/notes.md`", note)
                self.assertIn("- `docs/other.md`", note)
            with self.subTest("no_deliverable_files", fail_fast=fail_fast):
                note, _ = self._retry_note(lambda: None, fail_fast=fail_fast)
                self.assertIn("this attempt changed no files", note)

    def test_late_produces_refusal_lists_changed_paths(self):
        note, _ = self._retry_note(self._two_files, fail_fast=False)
        self.assertIn("- `docs/notes.md`", note)
        self.assertIn("- `docs/other.md`", note)
        self.assertNotIn("verification did not run", note)

    def test_list_is_capped_at_twenty(self):
        def thirty():
            Path("docs").mkdir(exist_ok=True)
            for i in range(30):
                Path(f"docs/f{i:02}.md").write_text("x\n")

        note, _ = self._retry_note(thirty, retain=False)
        self.assertEqual(note.count("- `docs/f"), 20)
        self.assertIn("and 10 more", note)


class TestArmTimeWarning(_Case):
    """Clause 5 — arm-time WARN for an unmentioned `produces:` path."""

    PATH = "docs/guides/widget-notes.md"

    def _lint(self, status: str, body: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "WU-T01.md").write_text(
                f"---\nid: {T01}\nstatus: {status}\nproduces:\n"
                f"  - {self.PATH}\n---\n\n{body}\n"
            )
            gates = [{"gate": 1, "work_units": [
                {"id": T01, "file": "WU-T01.md"}]}]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                lint_plan.check_produces_mentioned(fdir, gates)
            return out.getvalue()

    def test_pending_unmentioned_warns(self):
        out = self._lint("pending", "Write the notes.")
        self.assertIn("WARN:", out)
        self.assertIn(T01, out)
        self.assertIn(self.PATH, out)
        self.assertIn("produces_not_in_diff", out)

    def test_file_name_mention_is_silent(self):
        self.assertEqual(self._lint("pending", "Write widget-notes.md."), "")

    def test_full_path_mention_is_silent(self):
        self.assertEqual(self._lint("pending", f"Write {self.PATH}."), "")

    def test_parent_directory_mention_is_silent(self):
        self.assertEqual(self._lint("pending", "Add under docs/guides."), "")

    def test_done_and_abandoned_are_silent(self):
        for status in ("done", "abandoned"):
            with self.subTest(status=status):
                self.assertEqual(self._lint(status, "Write the notes."), "")

    def test_lint_runs_the_check(self):
        _, fdir = self._workspace()
        wu = fdir / "WU-T01.md"
        wu.write_text(wu.read_text().replace(
            "src/rule.py", "zzz/unnamed-thing.md"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            lint_plan.lint(fdir)
        self.assertIn("zzz/unnamed-thing.md", out.getvalue())


class TestEarlyRefusalRecovery(_Case):
    """Review follow-up: an early refusal keeps the recovery paths a failed
    verification had — re-planning before the last attempt, and the
    repeated-refusal halt firing only on a tree that really did not move."""

    def _run(self, act):
        """`loop.run()` with T01 calling *act(n)* on its n-th attempt and never
        touching `src/rule.py`. Returns (attempt count, re-plan turns, T01
        frontmatter text)."""
        _, fdir = self._workspace()
        Path("a.py").write_text("A = 0\n")
        Path("b.py").write_text("B = 0\n")
        _git("add", ".")
        _git("commit", "-q", "-m", "tracked files")
        attempts, replans = [], []

        def dispatch(wu, note, cost_tracking=True):
            if wu.body.startswith(loop._REPLAN_BRIEF_MARKER):
                replans.append(wu.wu_id)
                return "# T01\n\nRe-planned body: write src/rule.py.\n"
            if wu.wu_id == T01:
                attempts.append(note)
                act(len(attempts))
            return _COMPLETE

        self._patch("dispatch", dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(loop.run(None, dry_run=False), 1)
        return len(attempts), replans, (fdir / "WU-T01.md").read_text()

    def test_early_refusal_replans_before_the_last_attempt(self):
        def new_note(n):
            Path("docs").mkdir(exist_ok=True)
            Path(f"docs/notes-{n}.md").write_text(f"{n}\n")

        count, replans, _ = self._run(new_note)
        self.assertEqual(replans, [T01])
        self.assertEqual(count, 3)

    def test_tracked_edits_are_not_an_untouched_tree(self):
        def edit_tracked(n):
            Path("a.py" if n == 1 else "b.py").write_text(f"X = {n}\n")

        count, _, wu_text = self._run(edit_tracked)
        self.assertNotIn("deterministic_refusal_repeat", wu_text)
        self.assertEqual(count, 3)

    def test_untouched_tree_still_halts_without_replanning(self):
        count, replans, wu_text = self._run(lambda n: None)
        self.assertIn("escalation_reason: deterministic_refusal_repeat",
                      wu_text)
        self.assertEqual(count, 2)
        self.assertEqual(replans, [])


class TestEarlyRetainedNoteWording(unittest.TestCase):
    """Review follow-up: a retained tree that was never verified is not
    'correct work to leave alone' — the missing deliverable IS the work."""

    def test_early_retained_note_asks_for_the_missing_work(self):
        for fc in ("produces_not_in_diff", "guard_refusal"):
            with self.subTest(failure_class=fc):
                lead = loop.synthesize_retry_directive(
                    fc, retained=True, verification_ran=False)
                self.assertIn("NOT been verified", lead)
                self.assertIn("missing deliverable", lead)
                self.assertNotIn("re-authoring them is the one thing", lead)
                self.assertNotIn("only the mechanical fix", lead)
                self.assertNotIn("refused this attempt's pass", lead)

    def test_late_retained_note_is_unchanged(self):
        lead = loop.synthesize_retry_directive(
            "produces_not_in_diff", retained=True, verification_ran=True)
        self.assertIn("verification already PASSED", lead)
        self.assertIn("only the mechanical fix", lead)


if __name__ == "__main__":
    unittest.main()
