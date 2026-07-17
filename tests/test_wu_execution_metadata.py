#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The driver stamps resolved execution metadata into a WU's frontmatter.

So the planned/effective model, effort, exit-oracle gate set, driver version,
and dispatch time are visible when you read the WU `.md` — not only on the
console or in events.jsonl. Written at dispatch (after status -> in_progress),
so they ride the WU's squash commit.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import with_deliverable
from tests.test_driver_integration import (
    integration_workspace,
    write_minimal_feature,
    _read_frontmatter,
)

loop = load_loop()


def _write_verification_yml(root: Path) -> None:
    (root / ".specfuse/verification.yml").write_text(
        "code:\n  - name: noop\n    command: \"true\"\n"
        "doc:\n  - name: noop\n    command: \"true\"\n"
        "plannext:\n  - name: noop\n    command: \"true\"\n"
    )
    subprocess.run(["git", "-C", str(root), "add", ".specfuse/verification.yml"],
                   check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "verif"], check=True)


class TestWUExecutionMetadata(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        # Dispatch stubs must write a deliverable or the presence gate
        # (FEAT-2026-0022) rejects the WU as hollow. See #150 —
        # `.specfuse/.loop.lock` used to stand in as the deliverable.
        if name == "dispatch":
            replacement = with_deliverable(replacement)
        setattr(loop, name, replacement)

    def test_dispatch_stamps_model_effort_gateset_driver_started(self):
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root)
            write_minimal_feature(
                root, "FEAT-2026-9301", "exec-meta", "feat/exec-meta",
                [("FEAT-2026-9301/T01", "implementation", "pending")],
            )
            self._patch("dispatch", lambda wu, fn, cost_tracking=True: ("(stub)\n", None))
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fdir = root / ".specfuse/features/FEAT-2026-9301-exec-meta"
            fm = _read_frontmatter(fdir / "WU-T01.md")

            # model = the WU's resolved model (the integration helper authors a
            # concrete haiku id); effort defaults to EFFORT_BY_TYPE[implementation]
            # = medium (helper sets no effort); gate_set = GATES_FOR_TYPE = code.
            self.assertEqual(fm.get("model"), "claude-haiku-4-5-20251001")
            self.assertEqual(fm.get("effort"), "medium")
            self.assertEqual(fm.get("gate_set"), "code")
            self.assertEqual(fm.get("driver_version"), loop.DRIVER_VERSION)
            # started_at is a UTC ISO timestamp.
            self.assertIn("started_at", fm)
            self.assertRegex(fm["started_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_author_model_effort_override_is_preserved(self):
        """An explicit model/effort override survives the stamp (same value)."""
        with integration_workspace() as root:
            os.chdir(root)
            _write_verification_yml(root)
            write_minimal_feature(
                root, "FEAT-2026-9302", "exec-ovr", "feat/exec-ovr",
                [("FEAT-2026-9302/T01", "implementation", "pending")],
            )
            # Override the helper's default model with an alias + set effort.
            wu_path = root / ".specfuse/features/FEAT-2026-9302-exec-ovr/WU-T01.md"
            text = wu_path.read_text()
            text = text.replace("model: claude-haiku-4-5-20251001\n",
                                "model: opus\neffort: high\n", 1)
            wu_path.write_text(text)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "override"],
                           check=True)

            self._patch("dispatch", lambda wu, fn, cost_tracking=True: ("(stub)\n", None))
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            fm = _read_frontmatter(
                root / ".specfuse/features/FEAT-2026-9302-exec-ovr/WU-T01.md")
            self.assertEqual(fm.get("model"), "opus")
            self.assertEqual(fm.get("effort"), "high")


if __name__ == "__main__":
    unittest.main()
