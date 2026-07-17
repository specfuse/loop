#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""files_changed diff guard — FEAT-2026-0008/T02.

Covers:
  (a) verify_files_changed unit cases — all-modified, one-untouched,
      missing-on-disk, opt-out shapes (absent / empty / null).
  (b) Integration via stubbed dispatch: an agent that declares
      files_changed: [sentinel.py] but writes nothing causes the WU to
      spin to blocked_human with no squash commit.
  (c) Integration: an agent that omits files_changed retains the
      pre-T02 pass-through behavior — WU completes, gate advances.

The integration tests mirror test_loop_zero_token_guard.py: real git
working tree, scaffolded minimal feature, loop.dispatch patched at
module level so run()'s un-injected call site picks up the stub.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, with_deliverable

loop = load_loop()


# --------------------------------------------------------------------------- #
# Unit tests for verify_files_changed                                         #
# --------------------------------------------------------------------------- #


class TestVerifyFilesChanged(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign",
                        "false"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email",
                        "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"],
                       check=True)
        (root / "a.py").write_text("a\n")
        (root / "b.py").write_text("b\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"],
                       check=True)
        self.head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        os.chdir(root)
        self.root = root

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_all_claimed_paths_modified_returns_empty(self):
        (self.root / "a.py").write_text("a\nchanged\n")
        (self.root / "b.py").write_text("b\nchanged\n")
        result = {"files_changed": ["a.py", "b.py"]}
        self.assertEqual(loop.verify_files_changed(result, self.head), [])

    def test_one_claimed_path_untouched_is_reported(self):
        (self.root / "a.py").write_text("a\nchanged\n")
        # b.py left untouched — must be flagged.
        result = {"files_changed": ["a.py", "b.py"]}
        self.assertEqual(loop.verify_files_changed(result, self.head), ["b.py"])

    def test_claimed_path_not_on_disk_is_reported(self):
        result = {"files_changed": ["nonexistent.py"]}
        self.assertEqual(
            loop.verify_files_changed(result, self.head),
            ["nonexistent.py"],
        )

    def test_files_changed_absent_returns_empty_opt_out(self):
        # AC 4: absence MUST opt out, not into the guard.
        self.assertEqual(loop.verify_files_changed({}, self.head), [])

    def test_files_changed_empty_list_returns_empty_opt_out(self):
        self.assertEqual(
            loop.verify_files_changed({"files_changed": []}, self.head), [])

    def test_files_changed_null_value_returns_empty_opt_out(self):
        # YAML `files_changed:` with no value -> None in the parsed dict.
        self.assertEqual(
            loop.verify_files_changed({"files_changed": None}, self.head), [])

    def test_newly_created_untracked_file_is_not_flagged(self):
        # Regression: `git diff --quiet head_before -- new.sh` returns 0
        # for untracked files (diff ignores them), which used to flag
        # them as unchanged. An agent-created new file IS a change vs
        # head_before — it didn't exist there — so the guard must pass.
        (self.root / "new.sh").write_text("#!/bin/sh\necho hi\n")
        result = {"files_changed": ["new.sh"]}
        self.assertEqual(loop.verify_files_changed(result, self.head), [])

    def test_newly_created_untracked_file_in_subdir_is_not_flagged(self):
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "check.sh").write_text("#!/bin/sh\n")
        result = {"files_changed": ["scripts/check.sh"]}
        self.assertEqual(loop.verify_files_changed(result, self.head), [])

    def test_mixed_new_untracked_and_unchanged_tracked(self):
        # new.md (untracked, new) MUST pass; a.py (tracked, unchanged)
        # MUST still flag — the guard's job stays intact.
        (self.root / "new.md").write_text("fresh\n")
        result = {"files_changed": ["new.md", "a.py"]}
        self.assertEqual(
            loop.verify_files_changed(result, self.head), ["a.py"])

    def test_gitignored_untracked_file_is_still_flagged(self):
        # If the path is excluded by .gitignore, ls-files --others
        # --exclude-standard won't list it, so the guard still flags it.
        # This matches intent: agent declared work on a path git will
        # never commit, which is almost certainly a mistake.
        (self.root / ".gitignore").write_text("ignored.log\n")
        (self.root / "ignored.log").write_text("noise\n")
        result = {"files_changed": ["ignored.log"]}
        self.assertEqual(
            loop.verify_files_changed(result, self.head), ["ignored.log"])


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = list(wus) + [
        (f"{feature_id}/G1-RETRO", "retrospective", "pending"),
        (f"{feature_id}/G1-LESSONS", "lessons", "pending"),
        (f"{feature_id}/G1-DOCS", "docs", "pending"),
        (f"{feature_id}/G1-PLAN", "plan-next", "pending"),
    ]

    plan_wu_rows = []
    for i, (wu_id, _wu_type, _wu_status) in enumerate(all_wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i-1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: files_changed guard fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the files_changed guard under test
status: active
---

# Plan: {slug}

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
{chr(10).join(plan_wu_rows)}
```
"""
    (fdir / "PLAN.md").write_text(plan)
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\n"
            f"model: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
        )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=True
                          ).stdout.strip()


# --------------------------------------------------------------------------- #
# Integration: declared files_changed but agent writes nothing -> spin -> block
# --------------------------------------------------------------------------- #


class TestFilesChangedMismatchSpinsIntegration(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_declared_unchanged_path_spins_to_blocked_human(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9401", "files-mismatch",
                                  "feat/test-files-mismatch", [
                                      ("FEAT-2026-9401/T01", "implementation",
                                       "pending"),
                                  ])

            # Stub dispatch: emit a RESULT block declaring `files_changed:
            # [sentinel.py]` but never write the file. The guard must fire
            # AFTER verify() (which is stubbed to PASS) and BEFORE squash.
            result_block = (
                "```result\n"
                "status: complete\n"
                "summary: claims to have edited sentinel.py\n"
                "files_changed:\n"
                "  - sentinel.py\n"
                "```\n"
            )

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                return (result_block, {"input_tokens": 100,
                                       "output_tokens": 50,
                                       "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                # Verify reports PASS so the guard is exercised on the path
                # that would otherwise have squashed. This is the escalation
                # trigger 3 case (sentinel path the agent never touched).
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1,
                             "3 files_changed mismatches must escalate "
                             "(blocked_human, rc=1)")

            fdir = (root / ".specfuse/features"
                         / "FEAT-2026-9401-files-mismatch")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "blocked_human",
                             "T01 must be blocked_human after 3 mismatches")

            events = _read_events(fdir / "events.jsonl")
            mismatch_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["payload"].get("outcome") == "files_changed_mismatch"
            ]
            self.assertEqual(len(mismatch_events), loop.MAX_ATTEMPTS,
                             "one attempt_outcome per mismatched attempt")
            for ev in mismatch_events:
                self.assertEqual(ev["payload"]["unchanged_paths"],
                                 ["sentinel.py"],
                                 "payload must name the sentinel path")

            types = [e["event_type"] for e in events]
            self.assertNotIn("task_completed", types,
                             "no task_completed must be written when the "
                             "guard fired every attempt")

            # No per-WU squash commit — the chore bookkeeping is the only
            # T01-related commit.
            log = _git(root, "log", "--format=%s", "feat/test-files-mismatch")
            self.assertNotIn("feat: T01", log,
                             "no squash commit must land for T01")
            self.assertIn("chore(loop): FEAT-2026-9401/T01 blocked_human",
                          log)

            # sentinel.py was never created on disk (agent did nothing) and
            # any partial edits a real agent might have made would have
            # been wiped by the per-attempt reset.
            self.assertFalse((root / "sentinel.py").exists(),
                             "sentinel.py never existed and the reset must "
                             "leave the tree clean")


# --------------------------------------------------------------------------- #
# Integration: omitting files_changed preserves pre-T02 behavior              #
# --------------------------------------------------------------------------- #


class TestFilesChangedOmittedPassesIntegration(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        # This class exercises the files_changed guard, not the deliverable
        # guard — but a stub that writes nothing trips the latter first and
        # never reaches the assertion. Give it a deliverable so the WU gets far
        # enough to test what this class is actually about. (#150: the
        # `.specfuse/.loop.lock` that used to serve this purpose is gone.)
        if name == "dispatch":
            replacement = with_deliverable(replacement)
        setattr(loop, name, replacement)

    def test_no_files_changed_in_result_block_runs_squash_as_today(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9402", "files-omitted",
                                  "feat/test-files-omitted", [
                                      ("FEAT-2026-9402/T01", "implementation",
                                       "pending"),
                                  ])

            # Stub dispatch: RESULT block omits files_changed entirely.
            # The guard MUST NOT fire — pre-T02 behavior is preserved.
            result_block = (
                "```result\n"
                "status: complete\n"
                "summary: nothing fancy\n"
                "```\n"
            )

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                return (result_block, {"input_tokens": 100,
                                       "output_tokens": 50,
                                       "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0,
                             "gate must complete normally when the guard "
                             "does not fire")

            fdir = (root / ".specfuse/features"
                         / "FEAT-2026-9402-files-omitted")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done",
                             "T01 must complete normally when files_changed "
                             "is absent from the RESULT block")

            events = _read_events(fdir / "events.jsonl")
            mismatch_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["payload"].get("outcome") == "files_changed_mismatch"
            ]
            self.assertEqual(mismatch_events, [],
                             "guard must NOT fire when files_changed is "
                             "absent (escalation trigger 2)")



# --------------------------------------------------------------------------- #
# Integration: agent creates a NEW untracked file declared in files_changed   #
# — guard must pass (regression for FEAT-2026-0012 false-positive)            #
# --------------------------------------------------------------------------- #


class TestFilesChangedNewUntrackedFilePassesIntegration(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_agent_creates_new_file_and_declares_it_completes(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9403", "files-new-untracked",
                                  "feat/test-files-new-untracked", [
                                      ("FEAT-2026-9403/T01", "implementation",
                                       "pending"),
                                  ])

            # Stub dispatch: agent creates a brand-new file (.sh, would be
            # untracked) AND declares it in files_changed. Before the fix
            # the guard misfired because `git diff` ignores untracked.
            result_block = (
                "```result\n"
                "status: complete\n"
                "summary: created a brand-new script\n"
                "files_changed:\n"
                "  - scripts/check-image-architectures.sh\n"
                "```\n"
            )

            plain_block = (
                "```result\n"
                "status: complete\n"
                "summary: closing WU, no files_changed\n"
                "```\n"
            )

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                if wu.wu_id.endswith("/T01"):
                    target = Path("scripts/check-image-architectures.sh")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("#!/bin/sh\necho hi\n")
                    return (result_block, {"input_tokens": 100,
                                           "output_tokens": 50,
                                           "cost_usd": 0.001})
                return (plain_block, {"input_tokens": 100,
                                      "output_tokens": 50,
                                      "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0,
                             "WU must complete on attempt 1 — declared "
                             "files_changed naming a freshly-created "
                             "untracked file is a real change vs HEAD")

            fdir = (root / ".specfuse/features"
                         / "FEAT-2026-9403-files-new-untracked")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done")

            events = _read_events(fdir / "events.jsonl")
            mismatch_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["payload"].get("outcome") == "files_changed_mismatch"
            ]
            self.assertEqual(mismatch_events, [],
                             "guard MUST NOT fire on legitimately-new "
                             "untracked deliverable")

            log = _git(root, "log", "--format=%s",
                       "feat/test-files-new-untracked")
            self.assertIn("feat: T01", log,
                          "squash commit must land for T01")


if __name__ == "__main__":
    unittest.main()
