#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Orchestration path coverage — FEAT-2026-0002/T01.

Seven test classes, one per uncovered cluster:
  TestSquashCommitSoftReset   — squash_commit soft-reset (line ~518) and
                                no-changes (line ~520) paths.
  TestFindFeatureSelection    — find_feature with 0 / 1 / many active features
                                (lines ~202-204).
  TestRequireGitReady         — non-repo and no-commits error arms
                                (lines ~357, ~361).
  TestDispatchErrorArms       — gate_spent_usd defensive continues
                                (lines ~466, ~469, ~475) + commit_bookkeeping
                                early returns (lines ~508, ~511) + squash_commit
                                soft-reset and no-change returns (lines ~518, ~520).
  TestRunLockContention       — run() BlockingIOError arm (lines ~967-973).
  TestRunGateBudgetHalt       — run() gate-budget halt arm (lines ~1036-1054).
  TestMainArgparse            — main() argparse arms (lines ~1293-1305).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests._loop_loader import load_loop

loop = load_loop()


# --------------------------------------------------------------------------- #
# Shared helpers                                                               #
# --------------------------------------------------------------------------- #


def _make_wu(wu_id: str, title: str = "test WU") -> loop.WorkUnit:
    """Minimal WorkUnit suitable for passing to squash_commit / commit helpers."""
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path(f"WU-{wu_id.split('/')[-1]}.md"),
        depends_on=[],
        type="implementation",
        model="claude-haiku-4-5-20251001",
        effort="medium",
        status="in_progress",
        attempts=1,
        title=title,
        body="",
    )


def _minimal_git_repo(root: Path) -> None:
    """Init a git repo at `root` with one initial commit."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "commit.gpgSign", "false"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "Test"], check=True
    )
    (root / "README.md").write_text("# fixture\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True
    )


_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _write_feature(
    root: Path,
    feature_id: str,
    slug: str,
    branch: str,
    wus: list,
    gate_budget: float | None = None,
) -> Path:
    """Write a minimal feature dir (PLAN.md, GATE-01.md, WU files).

    `wus` is a list of (wu_id, wu_type, wu_status) tuples.  No closing
    sequence is written — callers that need it (lock-contention test, full
    integration tests) add it themselves.
    """
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    wu_rows = []
    for i, (wu_id, _wu_type, _wu_status) in enumerate(wus):
        tnn = wu_id.split("/")[-1]
        deps = "[]" if i == 0 else f"[{wus[i - 1][0]}]"
        wu_rows.append(
            f"      - id: {wu_id}\n"
            f"        file: WU-{tnn}.md\n"
            f"        depends_on: {deps}"
        )

    (fdir / "PLAN.md").write_text(
        f"---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test fixture\n"
        f"slug: {slug}\n"
        f"branch: {branch}\n"
        f"roadmap_goal: orchestration coverage test\n"
        f"status: active\n"
        f"---\n\n"
        f"# Plan: {slug}\n\n"
        f"```yaml\n"
        f"gates:\n"
        f"  - gate: 1\n"
        f"    file: GATE-01.md\n"
        f"    work_units:\n"
        + "\n".join(wu_rows)
        + "\n"
        "```\n"
    )

    gate_lines = ["---", "gate: 1", "status: open"]
    if gate_budget is not None:
        gate_lines.append(f"cost_budget_usd: {gate_budget}")
    gate_lines += ["---", "", "# Gate 1", ""]
    (fdir / "GATE-01.md").write_text("\n".join(gate_lines))

    for wu_id, wu_type, wu_status in wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\n"
            f"model: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n"
            f"---\n\n# {tnn}{_WU_BODY}"
        )

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


# --------------------------------------------------------------------------- #
# TestSquashCommitSoftReset                                                   #
# --------------------------------------------------------------------------- #


class TestSquashCommitSoftReset(unittest.TestCase):
    """AC 2: squash_commit soft-reset and no-changes paths."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        _minimal_git_repo(root)
        os.chdir(root)
        self.root = root

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    def test_soft_reset_folds_agent_commits_into_one_wu_commit(self):
        """Agent made two intermediate commits; squash_commit produces exactly one."""
        head_before = self._head()

        (self.root / "file1.py").write_text("# file1\n")
        subprocess.run(
            ["git", "add", "file1.py"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "agent commit 1"],
            check=True, capture_output=True,
        )

        (self.root / "file2.py").write_text("# file2\n")
        subprocess.run(
            ["git", "add", "file2.py"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "agent commit 2"],
            check=True, capture_output=True,
        )

        wu = _make_wu("FEAT-2026-9501/T01", "squash test")
        sha = loop.squash_commit(wu, head_before)

        self.assertIsNotNone(sha)
        new_head = self._head()
        self.assertNotEqual(new_head, head_before)

        # Exactly one commit since head_before
        log_out = subprocess.run(
            ["git", "log", "--format=%s", f"{head_before}..HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        commits = [ln for ln in log_out.splitlines() if ln.strip()]
        self.assertEqual(
            len(commits), 1, f"Expected exactly 1 squashed commit, got: {commits}"
        )

        # Commit message carries the WU trailer
        full_msg = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("Feature: FEAT-2026-9501/T01", full_msg)

        # Both agent-authored files survived the squash
        self.assertTrue((self.root / "file1.py").exists())
        self.assertTrue((self.root / "file2.py").exists())

    def test_returns_none_when_no_changes_since_head_before(self):
        """squash_commit returns None when HEAD == head_before and tree is clean."""
        head_before = self._head()
        wu = _make_wu("FEAT-2026-9501/T02", "no-change WU")
        result = loop.squash_commit(wu, head_before)
        self.assertIsNone(result)
        self.assertEqual(self._head(), head_before)


# --------------------------------------------------------------------------- #
# TestFindFeatureSelection                                                    #
# --------------------------------------------------------------------------- #


class TestFindFeatureSelection(unittest.TestCase):
    """AC 3-5: find_feature with 0 / 1 / many active features."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._features_dir = self.root / ".specfuse" / "features"
        self._features_dir.mkdir(parents=True)
        self._orig_features_dir = loop.FEATURES_DIR
        loop.FEATURES_DIR = self._features_dir
        os.chdir(self.root)

    def tearDown(self):
        loop.FEATURES_DIR = self._orig_features_dir
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _write_plan(self, name: str, status: str) -> Path:
        fdir = self._features_dir / name
        fdir.mkdir(parents=True)
        (fdir / "PLAN.md").write_text(
            f"---\nfeature_id: FEAT-2026-9502\nstatus: {status}\n---\n\n# Plan\n"
        )
        return fdir

    def test_zero_actives_exits_with_active_message(self):
        """AC 3: 0 active features → SystemExit with message about 'active'."""
        self._write_plan("FEAT-2026-9502-done", "complete")
        with self.assertRaises(SystemExit) as ctx:
            loop.find_feature(None)
        self.assertIn("active", str(ctx.exception.code).lower())

    def test_one_active_returns_its_path(self):
        """AC 4: exactly 1 active feature → returns its directory."""
        fdir = self._write_plan("FEAT-2026-9502-active", "active")
        result = loop.find_feature(None)
        self.assertEqual(result, fdir)

    def test_many_actives_exits_naming_both_dirs(self):
        """AC 5: multiple active features → SystemExit naming conflicting dirs."""
        self._write_plan("FEAT-2026-9502-alpha", "active")
        self._write_plan("FEAT-2026-9502-beta", "active")
        with self.assertRaises(SystemExit) as ctx:
            loop.find_feature(None)
        msg = str(ctx.exception.code)
        self.assertIn("FEAT-2026-9502-alpha", msg)
        self.assertIn("FEAT-2026-9502-beta", msg)

    def test_explicit_arg_with_plan_returns_path(self):
        """Lines 188, 191: explicit dir name with PLAN.md → returns absolute path."""
        fdir = self._write_plan("FEAT-2026-9502-explicit", "active")
        result = loop.find_feature("FEAT-2026-9502-explicit")
        self.assertEqual(result, fdir)

    def test_explicit_arg_without_plan_exits(self):
        """Lines 188-190: explicit dir name with no PLAN.md → sys.exit."""
        orphan = self._features_dir / "FEAT-2026-9502-orphan"
        orphan.mkdir()
        with self.assertRaises(SystemExit) as ctx:
            loop.find_feature("FEAT-2026-9502-orphan")
        self.assertIn("No PLAN.md", str(ctx.exception.code))


# --------------------------------------------------------------------------- #
# TestRequireGitReady                                                         #
# --------------------------------------------------------------------------- #


class TestRequireGitReady(unittest.TestCase):
    """AC 6-7: require_git_ready non-repo and no-commits error arms."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_non_repo_exits_with_not_a_git_message(self):
        """AC 6: non-repo directory → SystemExit containing 'not a git'."""
        # TemporaryDirectory is in /tmp or /var/folders — not inside any git repo
        os.chdir(self._tmp.name)
        with self.assertRaises(SystemExit) as ctx:
            loop.require_git_ready()
        self.assertIn("not a git", str(ctx.exception.code).lower())

    def test_no_commits_exits_with_no_commits_message(self):
        """AC 7: empty git repo (init but no commit) → SystemExit containing 'no commit'."""
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "t@t.com"], check=True
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "Test"], check=True
        )
        os.chdir(root)
        with self.assertRaises(SystemExit) as ctx:
            loop.require_git_ready()
        self.assertIn("no commit", str(ctx.exception.code).lower())


# --------------------------------------------------------------------------- #
# TestDispatchErrorArms                                                       #
# --------------------------------------------------------------------------- #


class TestDispatchErrorArms(unittest.TestCase):
    """AC 8: defensive branches in gate_spent_usd, commit_bookkeeping, squash_commit.

    Covers lines ~466 (no 'file' key), ~469 (wu_path missing), ~475 (bool cost),
    ~508 (commit_bookkeeping empty paths), ~511 (commit_bookkeeping no diff),
    ~518 (squash soft-reset), ~520 (squash no-changes).
    """

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        _minimal_git_repo(root)
        # Second commit: a file whose content is already committed (no diff later)
        (root / "committed.txt").write_text("unchanged content\n")
        subprocess.run(
            ["git", "-C", str(root), "add", "."], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "add committed file"],
            check=True,
        )
        os.chdir(root)
        self.root = root

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    # ----- gate_spent_usd defensive branches ---------------------------------

    def test_gate_spent_skips_ref_missing_file_key(self):
        """Line ~466: ref dict has no 'file' key → skip, total stays 0."""
        gate = {"work_units": [{"id": "X"}]}
        self.assertEqual(loop.gate_spent_usd({}, gate, self.root), 0.0)

    def test_gate_spent_skips_nonexistent_wu_path(self):
        """Line ~469: ref points to a file that does not exist → skip, total stays 0."""
        gate = {"work_units": [{"id": "X", "file": "WU-ghost.md"}]}
        self.assertEqual(loop.gate_spent_usd({}, gate, self.root), 0.0)

    def test_gate_spent_skips_bool_cost_usd(self):
        """Line ~475: WU frontmatter has cost_usd: true (YAML bool) → skip, total 0."""
        wu_path = self.root / "WU-T01.md"
        wu_path.write_text(
            "---\nid: X/T01\ntype: implementation\nmodel: sonnet\n"
            "status: done\nattempts: 1\ncost_usd: true\n---\n\n# WU\n"
        )
        gate = {"work_units": [{"id": "X/T01", "file": "WU-T01.md"}]}
        self.assertEqual(loop.gate_spent_usd({}, gate, self.root), 0.0)

    # ----- commit_bookkeeping early-return arms ------------------------------

    def test_commit_bookkeeping_no_existing_paths_returns_none(self):
        """Line ~508: every path in the list is non-existent → return None early."""
        result = loop.commit_bookkeeping(
            [str(self.root / "nonexistent.md")], "test: no-op"
        )
        self.assertIsNone(result)

    def test_commit_bookkeeping_no_diff_returns_none(self):
        """Line ~511: file exists and is already committed with no changes → None."""
        result = loop.commit_bookkeeping(
            [str(self.root / "committed.txt")], "test: no-diff"
        )
        self.assertIsNone(result)

    # ----- squash_commit arms ------------------------------------------------

    def test_squash_commit_applies_soft_reset_on_agent_commit(self):
        """Line ~518: HEAD moved past head_before → soft-reset before squash."""
        head_before = self._head()
        (self.root / "agent_new.py").write_text("# agent wrote this\n")
        subprocess.run(
            ["git", "add", "agent_new.py"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-q", "-m", "agent commit"],
            check=True, capture_output=True,
        )
        sha = loop.squash_commit(
            _make_wu("FEAT-2026-9501/T03", "soft-reset arm"), head_before
        )
        self.assertIsNotNone(sha)
        # After squash there is exactly one commit since head_before
        log = subprocess.run(
            ["git", "log", "--oneline", f"{head_before}..HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(len(log.splitlines()), 1)

    def test_squash_commit_returns_none_when_clean_tree(self):
        """Line ~520: HEAD == head_before, no working-tree changes → return None."""
        head_before = self._head()
        result = loop.squash_commit(
            _make_wu("FEAT-2026-9501/T04", "clean tree"), head_before
        )
        self.assertIsNone(result)


# --------------------------------------------------------------------------- #
# TestRunLockContention                                                       #
# --------------------------------------------------------------------------- #


class TestRunLockContention(unittest.TestCase):
    """AC 9: run() BlockingIOError arm — second acquire on the same lock file."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        self._held_fd = None
        root = Path(self._tmp.name)

        # Minimal feature dir so find_feature / load_graph succeed before the
        # lock attempt.  No git repo needed — require_git_ready() is only
        # reached after a successful lock; we never get there.
        fdir = root / ".specfuse/features/FEAT-2026-9503-lock-test"
        fdir.mkdir(parents=True)
        (fdir / "PLAN.md").write_text(
            "---\n"
            "feature_id: FEAT-2026-9503\n"
            "title: Lock contention fixture\n"
            "slug: lock-test\n"
            "branch: feat/FEAT-2026-9503-lock-test\n"
            "roadmap_goal: test lock contention path\n"
            "status: active\n"
            "---\n\n"
            "# Plan\n\n"
            "```yaml\n"
            "gates:\n"
            "  - gate: 1\n"
            "    file: GATE-01.md\n"
            "    work_units:\n"
            "      - id: FEAT-2026-9503/T01\n"
            "        file: WU-T01.md\n"
            "        depends_on: []\n"
            "```\n"
        )
        (fdir / "GATE-01.md").write_text(
            "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
        )
        (fdir / "WU-T01.md").write_text(
            "---\nid: FEAT-2026-9503/T01\ntype: implementation\n"
            "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
            f"---\n\n# T01{_WU_BODY}"
        )
        os.chdir(root)
        self.root = root

    def tearDown(self):
        if self._held_fd is not None:
            self._held_fd.close()
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_run_returns_1_and_prints_to_stderr_when_lock_held(self):
        """AC 9: second acquire raises BlockingIOError → run() returns 1, stderr names the lock."""
        # Pre-acquire the lock that run() will attempt to acquire
        self._held_fd = loop.acquire_tree_lock(Path(".specfuse"))

        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = loop.run(None, dry_run=False)

        self.assertEqual(rc, 1, "run() must return 1 when the tree lock is held")
        err = buf.getvalue()
        self.assertIn("loop driver", err.lower(),
                      "stderr must mention 'loop driver'")
        self.assertIn(".loop.lock", err,
                      "stderr must name the lock file")


# --------------------------------------------------------------------------- #
# TestRunGateBudgetHalt                                                       #
# --------------------------------------------------------------------------- #


class TestRunGateBudgetHalt(unittest.TestCase):
    """AC 10: run() gate-budget halt arm — spent >= budget before the next WU."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_gate_budget_halt_after_first_wu_passes(self):
        """T01 passes with cost > budget → gate flips awaiting_review, T02 never dispatched, rc=1."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_git_repo(root)
            os.chdir(root)

            fdir = _write_feature(
                root,
                feature_id="FEAT-2026-9504",
                slug="budget-halt",
                branch="feat/FEAT-2026-9504-budget-halt",
                wus=[
                    ("FEAT-2026-9504/T01", "implementation", "pending"),
                    ("FEAT-2026-9504/T02", "implementation", "pending"),
                ],
                gate_budget=0.0001,  # 0.1 milli-cent — T01 will exceed this
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                check=True,
            )

            dispatched_ids: list[str] = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                dispatched_ids.append(wu.wu_id)
                # cost_usd=0.001 far exceeds the gate budget of 0.0001
                return (
                    "",
                    {"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.001},
                )

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            # --- assertions ---

            self.assertEqual(rc, 1, "gate-budget halt must return 1")

            # Gate must have flipped to awaiting_review
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(
                gate_fm.get("status"),
                "awaiting_review",
                "GATE-01.md status must be awaiting_review after budget halt",
            )

            # events.jsonl must contain a gate_budget_exceeded escalation
            events = _read_events(fdir / "events.jsonl")
            budget_events = [
                e
                for e in events
                if e["event_type"] == "human_escalation"
                and e["payload"].get("reason") == "gate_budget_exceeded"
            ]
            self.assertEqual(
                len(budget_events),
                1,
                f"expected exactly 1 gate_budget_exceeded event; got: {budget_events}",
            )

            # T01 must have been dispatched; T02 must NOT (halted before T02)
            self.assertIn(
                "FEAT-2026-9504/T01",
                dispatched_ids,
                "T01 must have been dispatched before the budget check",
            )
            self.assertNotIn(
                "FEAT-2026-9504/T02",
                dispatched_ids,
                "T02 must NOT have been dispatched — budget halted the gate",
            )


# --------------------------------------------------------------------------- #
# TestMainArgparse                                                             #
# --------------------------------------------------------------------------- #


class TestMainArgparse(unittest.TestCase):
    """AC 11: main() --feature, --dry-run, no-args multi-active, and --help arms."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._orig_features_dir = loop.FEATURES_DIR
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        loop.FEATURES_DIR = self._orig_features_dir
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_help_exits_zero(self):
        """--help causes argparse to print usage and sys.exit(0)."""
        with patch.object(sys, "argv", ["loop", "--help"]):
            with self.assertRaises(SystemExit) as ctx:
                loop.main()
        self.assertEqual(ctx.exception.code, 0)

    def test_missing_features_dir_exits_with_path_message(self):
        """main() exits when FEATURES_DIR does not exist, message names the path."""
        nonexistent = Path(self._tmp.name) / "no-such-dir"
        loop.FEATURES_DIR = nonexistent
        os.chdir(self._tmp.name)
        with patch.object(sys, "argv", ["loop"]):
            with self.assertRaises(SystemExit) as ctx:
                loop.main()
        # The exit message contains the FEATURES_DIR path which includes ".specfuse"
        self.assertIsNotNone(ctx.exception.code)
        self.assertIn(
            "no-such-dir",
            str(ctx.exception.code),
            "exit message must name the missing directory",
        )

    def test_feature_flag_forwarded_to_run(self):
        """--feature <name> is forwarded as the first argument to run()."""
        features_dir = Path(self._tmp.name) / ".specfuse" / "features"
        features_dir.mkdir(parents=True)
        loop.FEATURES_DIR = features_dir
        os.chdir(self._tmp.name)
        with patch.object(loop, "auto_sync"):
            with patch.object(loop, "run", return_value=0) as mock_run:
                with patch.object(sys, "argv", ["loop", "--feature", "my-feature"]):
                    result = loop.main()
        self.assertEqual(result, 0)
        mock_run.assert_called_once_with("my-feature", False, force_full_close=None, prepare=False, prepare_only=False)

    def test_dry_run_flag_forwarded_to_run(self):
        """--dry-run is forwarded as dry_run=True to run()."""
        features_dir = Path(self._tmp.name) / ".specfuse" / "features"
        features_dir.mkdir(parents=True)
        loop.FEATURES_DIR = features_dir
        os.chdir(self._tmp.name)
        with patch.object(loop, "auto_sync"):
            with patch.object(loop, "run", return_value=0) as mock_run:
                with patch.object(sys, "argv", ["loop", "--dry-run"]):
                    loop.main()
        mock_run.assert_called_once_with(None, True, force_full_close=None, prepare=False, prepare_only=False)

    def test_multi_active_error_propagates_from_run(self):
        """main() with no args propagates the find_feature multi-active SystemExit."""
        features_dir = Path(self._tmp.name) / ".specfuse" / "features"
        for name in ("FEAT-2026-9502-alpha", "FEAT-2026-9502-beta"):
            d = features_dir / name
            d.mkdir(parents=True)
            (d / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9502\nstatus: active\n---\n\n# Plan\n"
            )
        loop.FEATURES_DIR = features_dir
        os.chdir(self._tmp.name)
        with patch.object(loop, "auto_sync"):
            with patch.object(sys, "argv", ["loop"]):
                with self.assertRaises(SystemExit) as ctx:
                    loop.main()
        self.assertIn("Multiple", str(ctx.exception.code))


# --------------------------------------------------------------------------- #
# TestRunDryRun                                                               #
# --------------------------------------------------------------------------- #


class TestRunDryRun(unittest.TestCase):
    """Covers dry_run WU-dispatch path (lines ~1058-1061) and dry_run gate-complete
    return (lines ~1269-1270).  Also covers done_ids.add (line ~1018) by starting
    with a feature where T01 is already done and T02 is pending."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._orig_features_dir = loop.FEATURES_DIR
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        loop.FEATURES_DIR = self._orig_features_dir
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_dry_run_dispatches_nothing_and_returns_0(self):
        """dry_run=True walks the gate without dispatching; prints '(dry run)' per WU."""
        root = Path(self._tmp.name)
        features_dir = root / ".specfuse" / "features"

        # T01 already done (loads into done_ids at line ~1018),
        # T02 pending + depends on T01 (ready immediately, exercises dry_run block).
        _write_feature(
            root,
            feature_id="FEAT-2026-9507",
            slug="dry-run",
            branch="feat/FEAT-2026-9507-dry-run",
            wus=[
                ("FEAT-2026-9507/T01", "implementation", "done"),
                ("FEAT-2026-9507/T02", "implementation", "pending"),
            ],
        )
        # T01 needs cost_usd absent (which is fine — dry_run never writes it)
        loop.FEATURES_DIR = features_dir
        os.chdir(root)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = loop.run(None, dry_run=True)

        self.assertEqual(rc, 0, "dry_run must return 0 when gate completes")
        out = buf.getvalue()
        self.assertIn("dry run", out.lower(),
                      "dry_run output must mention 'dry run'")


# --------------------------------------------------------------------------- #
# TestDispatchFunctionBody                                                    #
# --------------------------------------------------------------------------- #


class TestDispatchFunctionBody(unittest.TestCase):
    """Covers the dispatch() function body (lines ~590-606) via subprocess mock.

    dispatch() is always patched in integration tests, so its body is never
    executed there.  These unit tests call it directly with subprocess.run
    stubbed so no real claude CLI is invoked.
    """

    def _make_dispatch_wu(self) -> loop.WorkUnit:
        wu = _make_wu("FEAT-2026-9501/T06", "dispatch body test")
        wu.body = "# WU body"
        wu.effort = "medium"
        return wu

    def test_dispatch_cost_tracking_off_returns_raw_text(self):
        """Lines 590, 592, 598-605: cost_tracking=False returns stdout as-is, usage=None."""
        wu = self._make_dispatch_wu()
        mock_proc = MagicMock()
        mock_proc.stdout = "raw agent output"
        with patch("subprocess.run", return_value=mock_proc):
            result_text, usage = loop.dispatch(wu, None, cost_tracking=False)
        self.assertEqual(result_text, "raw agent output")
        self.assertIsNone(usage)

    def test_dispatch_failure_note_appended_to_prompt(self):
        """Lines 593-597: failure_note present → prompt includes retry context."""
        wu = self._make_dispatch_wu()
        mock_proc = MagicMock()
        mock_proc.stdout = "output"
        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            loop.dispatch(wu, "previous attempt exploded", cost_tracking=False)
        prompt_sent = mock_run.call_args.kwargs["input"]
        self.assertIn("previous attempt exploded", prompt_sent)
        self.assertIn("Previous attempt failed", prompt_sent)

    def test_dispatch_cost_tracking_on_parses_json_usage(self):
        """Lines 600-601, 606: cost_tracking=True adds --output-format json and parses."""
        wu = self._make_dispatch_wu()
        payload = {
            "result": "agent said this",
            "total_cost_usd": 0.002,
            "usage": {"input_tokens": 200, "output_tokens": 80},
        }
        mock_proc = MagicMock()
        mock_proc.stdout = json.dumps(payload)
        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            result_text, usage = loop.dispatch(wu, None, cost_tracking=True)
        cmd_used = mock_run.call_args.args[0]
        self.assertIn("--output-format", cmd_used)
        self.assertIn("json", cmd_used)
        self.assertEqual(result_text, "agent said this")
        self.assertIsNotNone(usage)
        self.assertAlmostEqual(usage["cost_usd"], 0.002)


if __name__ == "__main__":
    unittest.main()
