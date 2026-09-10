#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""auto_repair_files_changed — FEAT-2026-0103/T03.

A RESULT declaring one real change and one untouched path OUTSIDE
`produces:` must not spin the attempt to a `files_changed_mismatch` retry
just to delete a line from a list. `execute_unit_attempt` calls
`auto_repair_files_changed` when `verify_files_changed` finds unchanged
paths; when repair applies, the attempt passes, the dropped paths are gone
from the parsed RESULT's `files_changed`, and the passed `attempt_outcome`
names them under `extras["auto_repaired_files_changed"]`.

An unchanged path that IS a declared deliverable (`produces:`) is a real
gap, not a clerical slip — that case still refuses via
`files_changed_mismatch`, exactly as before T03.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


class _GitRepoCase(unittest.TestCase):
    """A real git working tree with one committed file (`kept.py`) and one
    RESULT-eligible untouched sibling (`extra.py`), mirroring the shape
    `verify_files_changed`'s own tests use."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)],
                       check=True)
        subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign",
                        "false"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email",
                        "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name",
                        "Test"], check=True)
        (root / "kept.py").write_text("kept\n")
        (root / "extra.py").write_text("extra\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "init"], check=True)
        self.head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.root = root
        os.chdir(root)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _make_wu(self, produces: list[str]) -> "loop.WorkUnit":
        return loop.WorkUnit(
            wu_id="FEAT-2026-9999/T03",
            file=self.root / "WU-T03.md",
            depends_on=[],
            type="implementation",
            model="sonnet",
            effort="medium",
            status="pending",
            attempts=0,
            title="Test WU",
            body=_WU_BODY,
            produces=produces,
        )


class TestAutoRepairFilesChangedUnit(_GitRepoCase):
    """Direct unit tests of `auto_repair_files_changed`."""

    def test_untouched_non_deliverable_is_dropped_and_the_attempt_passes(self):
        (self.root / "kept.py").write_text("kept\nchanged\n")
        wu = self._make_wu(produces=["kept.py"])
        parsed = {"files_changed": ["kept.py", "extra.py"]}
        unchanged = ["extra.py"]
        dropped = loop.auto_repair_files_changed(wu, parsed, unchanged)
        self.assertEqual(dropped, ["extra.py"])
        self.assertEqual(parsed["files_changed"], ["kept.py"])

    def test_untouched_deliverable_still_refuses(self):
        (self.root / "kept.py").write_text("kept\nchanged\n")
        wu = self._make_wu(produces=["extra.py"])
        parsed = {"files_changed": ["kept.py", "extra.py"]}
        unchanged = ["extra.py"]
        dropped = loop.auto_repair_files_changed(wu, parsed, unchanged)
        self.assertIsNone(dropped)
        self.assertEqual(parsed["files_changed"], ["kept.py", "extra.py"])

    def test_all_declared_paths_unchanged_still_refuses(self):
        wu = self._make_wu(produces=["kept.py"])
        parsed = {"files_changed": ["extra.py"]}
        unchanged = ["extra.py"]
        dropped = loop.auto_repair_files_changed(wu, parsed, unchanged)
        self.assertIsNone(dropped)
        self.assertEqual(parsed["files_changed"], ["extra.py"])


class TestExecuteUnitAttemptAutoRepair(_GitRepoCase):
    """Through `execute_unit_attempt`, with a stubbed dispatch/verify."""

    def _run(self, wu, stdout: str):
        def fake_dispatch(wu, failure_note):
            return stdout, {"input_tokens": 100, "output_tokens": 50,
                            "cost_usd": 0.001}

        def fake_verify(wu, feature_dir, cfg=None):
            return True, "(stub verify pass)"

        return loop.execute_unit_attempt(
            wu, self.root, None,
            dispatch_fn=fake_dispatch, verify_fn=fake_verify,
            head_before=self.head,
        )

    def test_untouched_non_deliverable_is_dropped_and_the_attempt_passes(self):
        (self.root / "kept.py").write_text("kept\nchanged\n")
        wu = self._make_wu(produces=["kept.py"])
        stdout = (
            "```result\nstatus: complete\nfiles_changed:\n"
            "  - kept.py\n  - extra.py\n```\n"
        )
        outcome, _evidence, _usage = self._run(wu, stdout)
        self.assertEqual(outcome, "passed")
        self.assertEqual(wu.result_block["files_changed"], ["kept.py"])
        self.assertEqual(wu.auto_repaired_files_changed, ["extra.py"])

    def test_untouched_deliverable_still_refuses(self):
        (self.root / "kept.py").write_text("kept\nchanged\n")
        wu = self._make_wu(produces=["extra.py"])
        stdout = (
            "```result\nstatus: complete\nfiles_changed:\n"
            "  - kept.py\n  - extra.py\n```\n"
        )
        outcome, payload, _usage = self._run(wu, stdout)
        self.assertEqual(outcome, "files_changed_mismatch")
        self.assertEqual(payload, ["extra.py"])
        self.assertIsNone(wu.auto_repaired_files_changed)

    def test_nothing_to_repair_is_a_plain_pass(self):
        (self.root / "kept.py").write_text("kept\nchanged\n")
        wu = self._make_wu(produces=["kept.py"])
        stdout = (
            "```result\nstatus: complete\nfiles_changed:\n"
            "  - kept.py\n```\n"
        )
        outcome, _evidence, _usage = self._run(wu, stdout)
        self.assertEqual(outcome, "passed")
        self.assertIsNone(wu.auto_repaired_files_changed)


if __name__ == "__main__":
    unittest.main()
