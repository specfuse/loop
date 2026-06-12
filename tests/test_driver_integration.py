#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Integration tests for the driver — Bug 1 (state-flip vs reset) and
Bug 2 (feature branch checkout). These tests stand up a real git working
tree, scaffold a minimal feature into it, stub dispatch and verify, then
invoke `loop.run()` and assert post-state of frontmatter, events log,
and git history.

Heavier than the unit tests but the right shape for these bugs — neither
shows up without a real working tree and real `git reset --hard`.

Stubbing rule: dispatch_fn and verify_fn are injectable into
execute_unit_attempt; here we patch loop.dispatch and loop.verify
directly at module level so the un-injected callers in run() see the
stubs too.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD_SRC = REPO_ROOT / ".specfuse"


@contextmanager
def integration_workspace():
    """Build a temp git repo with a minimal .specfuse/ scaffold and yield its path."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        # git init with main as default branch + one initial commit
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email",
                        "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"],
                       check=True)
        subprocess.run(["git", "-C", str(root), "config", "gc.auto", "0"],
                       check=True)
        (root / "README.md").write_text("# fixture\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"],
                       check=True)
        # Scaffold .specfuse/
        shutil.copytree(SCAFFOLD_SRC / "scripts", root / ".specfuse/scripts")
        shutil.copytree(SCAFFOLD_SRC / "templates", root / ".specfuse/templates")
        shutil.copytree(SCAFFOLD_SRC / "rules", root / ".specfuse/rules")
        (root / ".specfuse/verification.yml").write_text(
            "code:\n  - name: noop\n    command: \"true\"\n"
            "doc:\n  - name: noop\n    command: \"true\"\n"
            "plannext:\n  - name: noop\n    command: \"true\"\n"
        )
        (root / ".specfuse/features").mkdir(parents=True)
        try:
            yield root
        finally:
            subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True, capture_output=True,
            )


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list) -> Path:
    """Write a feature folder with PLAN.md, GATE-01.md, and per-WU files.

    `wus` is a list of (wu_id, type, status) tuples for the substantive WUs.
    The four closing-sequence WUs are added automatically so lint_plan would
    accept the structure if invoked.
    """
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
title: Integration test fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the driver under test conditions
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
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
        )
    # Stage and commit the scaffold so the driver starts from a clean tree.
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


def _read_frontmatter(path: Path) -> dict:
    """Tiny YAML-subset reader for tests (key: value, scalars only)."""
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
                          capture_output=True, text=True, check=True).stdout.strip()


# --------------------------------------------------------------------------- #
# Bug 1 — state-flip vs reset                                                 #
# --------------------------------------------------------------------------- #


class TestBug1StatusFlipSurvivesReset(unittest.TestCase):
    """The status flip to `done` (PASS) or `blocked_human` (BLOCKED/SPINNING)
    must be present in the on-disk frontmatter after the driver returns —
    even when subsequent WUs reset the working tree."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        # Restore patched module-level functions.
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_passed_then_blocked_flips_persist(self):
        """T01 PASSES, T02 BLOCKS — both status flips must be on disk."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9001", "passed-then-blocked",
                                  "feat/test-pb", [
                                      ("FEAT-2026-9001/T01", "implementation", "pending"),
                                      ("FEAT-2026-9001/T02", "implementation", "pending"),
                                  ])

            # Stub dispatch: T01 returns a benign stdout; T02 emits status: blocked.
            def fake_dispatch(wu, failure_note, cost_tracking=True):
                if wu.wu_id.endswith("/T02"):
                    return ("```result\nstatus: blocked\n"
                            "blocked_reason: simulated agent block\n```\n")
                return "(simulated agent output)\n"

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "blocked WU should cause exit 1")

            fdir = root / ".specfuse/features/FEAT-2026-9001-passed-then-blocked"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            t02_fm = _read_frontmatter(fdir / "WU-T02.md")
            self.assertEqual(t01_fm.get("status"), "done",
                             "T01 status must be 'done' on disk (Bug 1)")
            self.assertEqual(t02_fm.get("status"), "blocked_human",
                             "T02 status must be 'blocked_human' on disk (Bug 1)")

    def test_events_log_captures_both_outcomes(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9002", "events",
                                  "feat/test-events", [
                                      ("FEAT-2026-9002/T01", "implementation", "pending"),
                                      ("FEAT-2026-9002/T02", "implementation", "pending"),
                                  ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                if wu.wu_id.endswith("/T02"):
                    return ("```result\nstatus: blocked\n"
                            "blocked_reason: simulated\n```\n")
                return "(simulated)\n"

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)
            loop.run(None, dry_run=False)

            events = _read_events(
                root / ".specfuse/features/FEAT-2026-9002-events/events.jsonl")
            types = [(e["event_type"], e["correlation_id"]) for e in events]
            # T01: task_started + task_completed; T02: task_started +
            # human_escalation. Both outcomes must persist past T02's reset.
            self.assertIn(("task_started", "FEAT-2026-9002/T01"), types)
            self.assertIn(("task_completed", "FEAT-2026-9002/T01"), types)
            self.assertIn(("task_started", "FEAT-2026-9002/T02"), types)
            self.assertIn(("human_escalation", "FEAT-2026-9002/T02"), types)

    def test_blocked_human_creates_bookkeeping_commit(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9003", "chore-commit",
                                  "feat/test-chore", [
                                      ("FEAT-2026-9003/T01", "implementation", "pending"),
                                  ])

            self._patch("dispatch", lambda wu, fn, ct=True:
                        "```result\nstatus: blocked\nblocked_reason: stub\n```\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            loop.run(None, dry_run=False)

            # A chore(loop) commit must exist on the feature branch.
            log = _git(root, "log", "--format=%s", "feat/test-chore")
            self.assertIn("chore(loop): FEAT-2026-9003/T01 blocked_human", log)


# --------------------------------------------------------------------------- #
# Bug 2 — feature branch checkout                                             #
# --------------------------------------------------------------------------- #


class TestBug2FeatureBranchCheckout(unittest.TestCase):
    """The driver must ensure HEAD is on the feature's declared branch before
    dispatching any WU — so per-WU squash commits land on the right branch."""

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

    def test_driver_switches_to_declared_branch(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9101", "branch-create",
                                  "feat/declared-branch", [
                                      ("FEAT-2026-9101/T01", "implementation", "pending"),
                                  ])
            self.assertEqual(_git(root, "branch", "--show-current"), "main")

            self._patch("dispatch", lambda wu, fn, ct=True: "(stub)\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            loop.run(None, dry_run=False)

            self.assertEqual(_git(root, "branch", "--show-current"),
                             "feat/declared-branch")

    def test_squashed_commit_lands_on_feature_branch_not_main(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9102", "branch-isolation",
                                  "feat/iso", [
                                      ("FEAT-2026-9102/T01", "implementation", "pending"),
                                  ])

            self._patch("dispatch", lambda wu, fn, ct=True: "(stub)\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            loop.run(None, dry_run=False)

            # %s%n%b → subject + body so we see the `Feature: ...` trailer.
            iso_log = _git(root, "log", "--format=%s%n%b", "feat/iso")
            main_log = _git(root, "log", "--format=%s%n%b", "main")
            self.assertIn("FEAT-2026-9102/T01", iso_log,
                          "T01's commit must be on feat/iso")
            self.assertNotIn("FEAT-2026-9102/T01", main_log,
                             "T01's commit must NOT be on main")

    def test_driver_idempotent_when_already_on_branch(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9103", "already-on",
                                  "feat/already", [
                                      ("FEAT-2026-9103/T01", "implementation", "pending"),
                                  ])
            # Pre-create and check out the branch.
            subprocess.run(["git", "-C", str(root), "checkout", "-q", "-B",
                            "feat/already"], check=True)

            self._patch("dispatch", lambda wu, fn, ct=True: "(stub)\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)
            self.assertEqual(_git(root, "branch", "--show-current"),
                             "feat/already")


if __name__ == "__main__":
    unittest.main()
