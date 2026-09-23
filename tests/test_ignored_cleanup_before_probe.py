#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A failed attempt's gitignored output is cleaned before attribution (#3330).

Defect 1. The attempt-failure path resets the tree and then probes the gate set
to ask whether the failure predated the unit's own work. `git reset --hard`
restores tracked files and leaves ignored ones in place, so a check that reads a
build or output directory measures the failed attempt's own leftovers and the
driver blames the integration branch for them.

The mechanism to fix it already existed. #162 snapshots untracked paths at
dispatch and deletes what appeared since, and the attribution path already
passes that snapshot -- but `untracked_paths` runs `git ls-files --others
--exclude-standard`, so gitignored paths were deliberately carved out. The
carve-out is load-bearing: the driver's own `work/` notes are gitignored and
must survive the reset.

So this is the symmetric twin, bounded by two things the naive version gets
wrong:

* **A listing diff cannot see it.** `git status --porcelain --ignored` collapses
  a wholly-ignored directory to one entry (`!! out/`), identical before and
  after files are added inside it -- and that is exactly the reported case, where
  `out/` already existed and the attempt added files under it. `git ls-files
  --others --ignored --exclude-standard` reports file-level, so the snapshot
  diff actually sees the new files.
* **A pre-existing cache must survive.** Snapshot semantics give this for free:
  anything present at dispatch is in the snapshot and is never deleted. Only
  what the attempt itself created is removed, which is the pollution class and
  nothing else.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()


@contextmanager
def _repo():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        run = lambda *a: subprocess.run(  # noqa: E731
            ["git", "-C", str(root), *a], check=True, capture_output=True,
        )
        run("init", "-q", "-b", "main")
        run("config", "commit.gpgSign", "false")
        run("config", "user.email", "test@example.com")
        run("config", "user.name", "Test")
        (root / ".gitignore").write_text("out/\nwork/\n.cache/\n")
        (root / "README.md").write_text("# fixture\n")
        run("add", ".")
        run("commit", "-q", "-m", "init")
        prev = os.getcwd()
        try:
            os.chdir(root)
            yield root, run
        finally:
            os.chdir(prev)


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class IgnoredPathsSeesInsideIgnoredDirectories(unittest.TestCase):
    """The listing the snapshot is built from must be file-level."""

    def test_new_file_in_a_preexisting_ignored_directory_is_reported(self):
        with _repo() as (root, _run):
            _write(root / "out/a/one.txt")
            before = loop.ignored_paths()

            _write(root / "out/a/two.txt")
            after = loop.ignored_paths()

            self.assertIn("out/a/two.txt", after - before)
            self.assertIn("out/a/one.txt", before)

    def test_status_ignored_would_not_have_seen_it(self):
        # Pins the reason ignored_paths exists rather than reusing the
        # status listing: this assertion documents the trap.
        with _repo() as (root, _run):
            _write(root / "out/a/one.txt")
            first = subprocess.run(
                ["git", "status", "--porcelain", "--ignored"],
                capture_output=True, text=True, check=True).stdout
            _write(root / "out/a/two.txt")
            second = subprocess.run(
                ["git", "status", "--porcelain", "--ignored"],
                capture_output=True, text=True, check=True).stdout

            self.assertEqual(first, second)
            self.assertIn("out/", first)


class ResetCleansTheAttemptsIgnoredOutput(unittest.TestCase):

    def test_ignored_file_created_during_the_attempt_is_deleted(self):
        with _repo() as (root, run):
            _write(root / "out/a/one.txt")
            ignored_before = loop.ignored_paths()
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True,
                text=True, check=True).stdout.strip()

            _write(root / "out/a/orphan.ts")

            loop.reset_preserving_events(
                head, root / "events.jsonl",
                untracked_before=frozenset(), ignored_before=ignored_before)

            self.assertFalse((root / "out/a/orphan.ts").exists())

    def test_ignored_state_that_predates_the_attempt_survives(self):
        # #3371: build caches are gitignored deliberately and are expensive to
        # discard. Snapshot semantics protect them without a config knob.
        with _repo() as (root, run):
            _write(root / ".cache/big.bin")
            _write(root / "out/a/one.txt")
            ignored_before = loop.ignored_paths()
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True,
                text=True, check=True).stdout.strip()

            loop.reset_preserving_events(
                head, root / "events.jsonl",
                untracked_before=frozenset(), ignored_before=ignored_before)

            self.assertTrue((root / ".cache/big.bin").exists())
            self.assertTrue((root / "out/a/one.txt").exists())

    def test_the_features_work_notes_survive(self):
        # The snapshot is taken once per WU, not per attempt, so attempt 1's
        # persisted notes look "new" at attempt 2's reset. Deleting them would
        # undo #168's diagnosability.
        with _repo() as (root, run):
            ignored_before = loop.ignored_paths()
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True,
                text=True, check=True).stdout.strip()

            _write(root / "work/T01/attempt-1.md", "verify output")

            loop.reset_preserving_events(
                head, root / "events.jsonl",
                untracked_before=frozenset(), ignored_before=ignored_before)

            self.assertTrue((root / "work/T01/attempt-1.md").exists())

    def test_absent_snapshot_is_inert(self):
        # Same contract as untracked_before: None means "no snapshot, do not
        # clean", never "the tree had no ignored files".
        with _repo() as (root, run):
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True,
                text=True, check=True).stdout.strip()
            _write(root / "out/a/one.txt")

            loop.reset_preserving_events(
                head, root / "events.jsonl", untracked_before=frozenset())

            self.assertTrue((root / "out/a/one.txt").exists())

    def test_events_file_is_never_deleted(self):
        with _repo() as (root, run):
            ignored_before = loop.ignored_paths()
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True,
                text=True, check=True).stdout.strip()
            events = root / "work" / "events.jsonl"
            _write(events, '{"event_type":"x"}\n')

            loop.reset_preserving_events(
                head, events, untracked_before=frozenset(),
                ignored_before=ignored_before)

            self.assertTrue(events.exists())


class TheProbeNoLongerReadsTheAttemptsOutput(unittest.TestCase):
    """End to end: the clean happens BEFORE attribution reads the tree.

    The unit tests above prove the cleaning. This proves the ordering, which is
    where the defect actually lived -- the mechanism could have been correct and
    still run after the probe, changing nothing.

    `probe_baseline` is patched to report a failure only while the attempt's
    gitignored file is on disk, which is what the reported incident's
    `TypeScriptExportCompletenessTest` did when it walked its `out/` tree and
    found an orphan module.
    """

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _scaffold(self, root: Path) -> Path:
        fdir = root / ".specfuse/features/FEAT-2026-8930-ignored-probe"
        fdir.mkdir(parents=True)
        (fdir / "PLAN.md").write_text(
            "---\nfeature_id: FEAT-2026-8930\ntitle: Ignored probe fixture\n"
            "slug: ignored-probe\nbranch: feat/ignored-probe\n"
            "roadmap_goal: exercise the ignored clean before attribution\n"
            "status: active\n---\n\n# Plan\n\n"
            "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
            "    work_units:\n      - id: FEAT-2026-8930/T01\n"
            "        file: WU-T01.md\n        depends_on: []\n```\n"
        )
        (fdir / "GATE-01.md").write_text(
            "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        (fdir / "WU-T01.md").write_text(
            "---\nid: FEAT-2026-8930/T01\ntype: implementation\n"
            "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
            "---\n\n# T01\n\n**Context.** t\n\n**Acceptance criteria.** t\n\n"
            "**Do not touch.** t\n\n**Verification.** t\n\n"
            "**Escalation triggers.** t\n")
        gitignore = root / ".gitignore"
        existing = gitignore.read_text() if gitignore.exists() else ""
        gitignore.write_text(existing + ".specfuse/.loop.lock\n"
                             ".specfuse/.scratch-*\n"
                             ".specfuse/scripts/__pycache__/\n"
                             "out/\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "scaffold"], check=True)
        return fdir

    def test_the_attempts_ignored_output_is_gone_before_the_probe_runs(self):
        with integration_workspace() as root:
            os.chdir(root)
            self._scaffold(root)

            orphan = root / "out" / "a" / "orphan.ts"
            seen = {}

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                # What the reported incident's attempt did: emit generated
                # code into a gitignored tree, then fail its own gates.
                orphan.parent.mkdir(parents=True, exist_ok=True)
                orphan.write_text("export const orphan = 1;\n")
                return "```result\nstatus: complete\n```\n"

            def fake_probe(feature_dir, cfg=None):
                seen["orphan_present"] = orphan.exists()
                if orphan.exists():
                    return [{"gate": "tests",
                             "failure_class": "test_failure",
                             "failure_signature": "everyModuleIsReachable"}]
                return []

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "gate output"))
            self._patch("probe_baseline", fake_probe)

            loop.run(None, dry_run=False)

            self.assertIn(
                "orphan_present", seen,
                "the attribution probe never ran, so this test proves nothing",
            )
            self.assertFalse(
                seen["orphan_present"],
                "the probe read the failed attempt's own gitignored output — "
                "the clean must happen before attribution, not after (#3330)",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
