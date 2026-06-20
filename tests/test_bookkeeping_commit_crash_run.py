#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression test for #75 — run() must HANDLE a rejected bookkeeping commit.

Sibling of #71's "fail gracefully, not crash" cluster and of the squash-
rejection handling (issue #51). `commit_bookkeeping` already raises a readable
`BookkeepingCommitError` instead of a bare CalledProcessError (FEAT-2026-0024,
see test_bookkeeping_commit_hook_crash.py). But that error propagated UNCAUGHT
out of `run()` → the driver died with a raw traceback. This test drives a real
`run()` to the spinning-escalation bookkeeping commit with a pre-commit hook
that rejects it, and asserts run() returns 1 (graceful halt) rather than
raising.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** code gates\n\n"
    "**Escalation triggers.** test\n"
)


def _write_impl_feature(root: Path, feature_id: str) -> Path:
    """Scaffold a single-gate feature with one pending implementation WU."""
    slug = "bookkeeping-crash-test"
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    wu_id = f"{feature_id}/T01"

    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nslug: {slug}\n"
        f"branch: feat/{feature_id.lower()}-{slug}\n"
        f"roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n"
        f"```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n      - id: {wu_id}\n        file: WU-01.md\n"
        f"        depends_on: []\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-01.md").write_text(
        f"---\nid: {wu_id}\ntype: implementation\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Do the thing{_WU_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


class TestRunHandlesBookkeepingCommitRejection(unittest.TestCase):

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

    def test_run_halts_gracefully_when_bookkeeping_commit_rejected(self):
        """A pre-commit hook rejecting the spinning-escalation bookkeeping
        commit must produce rc=1 (graceful halt), not an unhandled traceback."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9510"
            _write_impl_feature(root, feature_id)

            # Install a pre-commit hook that rejects EVERY commit. No squash
            # commit occurs (verify always fails → WU never passes), so the
            # first — and only — git commit run() attempts is the spinning-
            # escalation bookkeeping commit. The hook rejects it.
            hook = root / ".git" / "hooks" / "pre-commit"
            hook.write_text("#!/bin/sh\necho 'LEAK-SCAN-REJECT-SENTINEL' 1>&2\nexit 1\n")
            hook.chmod(0o755)

            result_block = (
                "```result\nstatus: complete\nsummary: did the thing\n```\n"
            )

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                (root / "agent-output.txt").write_text("some output\n")
                return (result_block, {"input_tokens": 100,
                                       "output_tokens": 50,
                                       "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return False, "(stub verify fail — force spinning escalation)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            # Must NOT raise BookkeepingCommitError; must return rc=1.
            try:
                rc = loop.run(None, dry_run=False)
            except loop.BookkeepingCommitError as exc:
                self.fail(
                    f"run() crashed on a rejected bookkeeping commit instead of "
                    f"halting gracefully: {exc}"
                )
            self.assertEqual(rc, 1, "rejected bookkeeping commit must halt with rc=1")


if __name__ == "__main__":
    unittest.main()
