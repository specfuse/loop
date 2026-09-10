#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A guard refusal keeps the working tree — FEAT-2026-0103/T01, this gate's
walking skeleton.

Today every one of the four bookkeeping-guard refusal sites in `run()`'s
attempt loop (`deliverable_missing`, `no_deliverable_files`,
`produces_not_in_diff`, `files_changed_mismatch`) calls
`reset_preserving_events`, a `git reset --hard` that discards the attempt's
working-tree edits before the retry. This module exercises the
`files_changed_mismatch` site end to end through `loop.run()`: attempt 1
writes a real deliverable but also declares an untouched extra path in
`files_changed`, tripping the guard; with `retain_on_guard_refusal` at its
default (True), the squash is uncommitted via `git reset --mixed` but the
tree survives, so attempt 2 starts with attempt 1's file already on disk and
finishes the job. A second case flips the config default off and asserts
today's discard behavior is unchanged.

Harness follows tests/test_produces_justification.py's minimal shape: one
implementation WU plus one close WU (which collapses the four closing
ceremonies), `dispatch` and `verify` patched at module level, then
`loop.run()`.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def _write_minimal_feature(root: Path, feature_id: str, slug: str,
                           branch: str, produces: list,
                           max_attempts: int = 2) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: {branch}\nroadmap_goal: test\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    produces_yaml = "".join(f"\n  - {p}" for p in produces)
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\nmax_attempts: {max_attempts}\n"
        f"produces:{produces_yaml}\n---\n\n"
        f"# T01{body}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{body}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"], check=True)
    return fdir


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    end = text.find("\n---\n", 4)
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout


class TestGuardRefusalRetainsTree(unittest.TestCase):
    """End to end: loop.run() with stubbed dispatch in a temp git repo."""

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

    def _events(self, fdir: Path, wu_id: str) -> list:
        return [e for e in _read_events(fdir / "events.jsonl")
                if e["event_type"] == "attempt_outcome"
                and e["correlation_id"] == wu_id]

    def test_retained_tree_lets_attempt_2_finish_the_job(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-9601", "guard-repair",
                "feat/guard-repair",
                produces=["src/foo.py", "src/extra.py"])

            calls = []
            failure_notes = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                calls.append(wu.wu_id)
                failure_notes.append(failure_note)
                if wu.wu_id.endswith("/T01"):
                    if len([c for c in calls if c == wu.wu_id]) == 1:
                        # Attempt 1: writes one declared deliverable, but
                        # also declares a SECOND declared deliverable
                        # (`src/extra.py`, also in `produces:`) untouched —
                        # a real gap, not the auto-repairable "stray extra
                        # path" case — the guard's trigger.
                        Path("src").mkdir(exist_ok=True)
                        Path("src/foo.py").write_text("v1\n")
                        return (
                            "```result\nstatus: complete\n"
                            "files_changed:\n"
                            "  - src/foo.py\n"
                            "  - src/extra.py\n"
                            "```\n"
                        )
                    # Attempt 2: attempt 1's file must already be here, and
                    # this attempt finishes the job by delivering extra.py.
                    assert Path("src/foo.py").exists(), (
                        "attempt 1's deliverable must survive into attempt 2"
                    )
                    Path("src/extra.py").write_text("extra\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n"
                        "  - src/foo.py\n"
                        "  - src/extra.py\n"
                        "```\n"
                    )
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            events = self._events(fdir, "FEAT-2026-9601/T01")
            outcomes = [e["payload"]["outcome"] for e in events]
            self.assertEqual(outcomes, ["files_changed_mismatch", "passed"])
            self.assertTrue(events[0]["payload"]["tree_retained"])

            self.assertEqual(
                _read_frontmatter(fdir / "WU-T01.md").get("status"), "done")

            # attempt 2's failure_note (dispatch's 2nd argument) must carry
            # both the guard's complaint and the retained diff.
            self.assertGreaterEqual(len(failure_notes), 2)  # T01 attempt 1 + 2
            note2 = failure_notes[1]
            self.assertIn("files_changed", note2)
            self.assertIn("src/extra.py", note2)
            self.assertIn("Retained diff", note2)
            self.assertIn("+v1", note2)

            log = _git(root, "log", "--format=%H %s", "feat/guard-repair")
            squash_lines = [ln for ln in log.splitlines() if "feat: T01" in ln]
            self.assertEqual(len(squash_lines), 1,
                             "exactly one squash commit for T01")
            squash_sha = squash_lines[0].split()[0]
            base_sha = _git(root, "merge-base", "main",
                            "feat/guard-repair").strip()
            diff = _git(root, "diff", base_sha, squash_sha)
            self.assertIn("src/foo.py", diff)
            self.assertIn("+v1", diff)

    def test_retain_disabled_falls_back_to_todays_reset(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "defaults:\n  retain_on_guard_refusal: false\n"
                "code:\n  - name: noop\n    command: \"true\"\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            fdir = _write_minimal_feature(
                root, "FEAT-2026-9602", "guard-repair-off",
                "feat/guard-repair-off",
                produces=["src/foo.py", "src/extra.py"])

            t01_calls = []
            attempt2_saw_file = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                if wu.wu_id.endswith("/T01"):
                    t01_calls.append(1)
                    if len(t01_calls) == 2:
                        attempt2_saw_file.append(Path("src/foo.py").exists())
                    # Always declares an untouched extra path — this WU
                    # only needs to trip the guard every attempt so the
                    # attempt-2 dispatch is reached under a low
                    # max_attempts; the RESULT contract is otherwise
                    # irrelevant here.
                    Path("src").mkdir(exist_ok=True)
                    Path("src/foo.py").write_text(f"v{len(t01_calls)}\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n"
                        "  - src/foo.py\n"
                        "  - src/extra.py\n"
                        "```\n"
                    )
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            self.assertEqual(attempt2_saw_file, [False],
                             "with retain_on_guard_refusal: false, attempt "
                             "1's deliverable must be gone when attempt 2 "
                             "starts (today's reset, unchanged)")

            events = self._events(fdir, "FEAT-2026-9602/T01")
            self.assertFalse(events[0]["payload"].get("tree_retained"))


if __name__ == "__main__":
    unittest.main()
