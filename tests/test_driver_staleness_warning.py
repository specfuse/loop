#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Immediate driver-editing staleness warning (FEAT-2026-0075/T02).

`squash_commit`'s diff is ground truth for what a work unit changed. The
moment that squash lands touching the driver's own importable surface, this
process's `sys.modules` still holds the pre-edit code, so anything dispatched
next — including a close — silently executes stale modules. The warning must
print immediately after the squash, not only at gate completion (the window
between the driver-editing unit's squash and the next dispatch is where the
real losses happened).

This drives the real outcome path (`loop.run()`) with a stubbed dispatch, per
WU acceptance criterion 5 — asserting only `format_driver_staleness_warning`
in isolation would not exercise the seam this unit wires.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def _write_minimal_feature(root: Path, feature_id: str, slug: str,
                            branch: str) -> Path:
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
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n---\n\n# T01{body}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{body}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


class TestFormatDriverStalenessWarningUnit(unittest.TestCase):

    def test_empty_paths_returns_empty_string(self):
        self.assertEqual(
            loop.format_driver_staleness_warning("FEAT-2026-9999/T01", []),
            "")

    def test_names_wu_id_and_paths_and_restart_requirement(self):
        msg = loop.format_driver_staleness_warning(
            "FEAT-2026-9999/T01", ["specfuse/loop/loop.py", "specfuse/loop/x.py"])
        self.assertIn("FEAT-2026-9999/T01", msg)
        self.assertIn("specfuse/loop/loop.py", msg)
        self.assertIn("specfuse/loop/x.py", msg)
        self.assertIn("fresh driver process", msg)
        self.assertIn("close", msg)


class TestDriverStalenessWarningSeam(unittest.TestCase):
    """End-to-end: loop.run() with stubbed dispatch in a temp git repo."""

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

    def test_driver_edit_warns_at_squash(self):
        """A WU whose squash diff touches specfuse/loop/ must print the
        staleness warning immediately after that squash — not deferred to
        gate completion."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-9101", "warn-shape", "feat/warn-shape")

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("specfuse/loop").mkdir(parents=True, exist_ok=True)
                    Path("specfuse/loop/loop.py").write_text(
                        "# pretend driver edit\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - specfuse/loop/loop.py\n```\n")
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.run(None, dry_run=False)

            output = buf.getvalue()
            self.assertIn("STALE DRIVER PROCESS", output)
            self.assertIn("FEAT-2026-9101/T01", output)
            self.assertIn("specfuse/loop/loop.py", output)

    def test_no_driver_edit_no_warning(self):
        """A WU whose squash diff touches no driver path must produce no
        warning — asserted through the same harness as the positive case."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-9102", "no-warn-shape", "feat/no-warn-shape")

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src").mkdir(exist_ok=True)
                    Path("src/rule.py").write_text("# unrelated change\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/rule.py\n```\n")
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.run(None, dry_run=False)

            self.assertNotIn("STALE DRIVER PROCESS", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
