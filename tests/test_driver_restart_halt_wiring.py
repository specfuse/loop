#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Halt the run before dispatching into a stale process (FEAT-2026-0075/T06).

`T02`'s squash-site warning (gate 1) only ever prints; nothing stops the run.
`T05` built the halt mechanism (`_halt_for_driver_restart`,
`HALT_REASON_DRIVER_RESTART`, `EXIT_DRIVER_RESTART_REQUIRED`) but nothing
calls it yet. This unit wires the two together at the `for wu in pending`
brake (sibling of `_should_halt_for_budget`): when a squash lands touching
the driver's own importable surface and the gate still has units left to
dispatch, the driver halts instead of dispatching the next unit into a
process that cannot execute what was just written.

This drives the real outcome path (`loop.run()`) with a stubbed dispatch —
per WU acceptance criterion 2, asserting only `format_driver_restart_halt`
in isolation would not exercise the seam this unit exists to wire.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def _write_feature(root: Path, feature_id: str, slug: str, branch: str,
                    wu_ids: list) -> Path:
    """Scaffold a single-gate feature with a straight-line dependency chain
    over `wu_ids` (each `type: implementation` except the last, `type: close`)."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    work_units_yaml = []
    for i, wu_id in enumerate(wu_ids):
        dep = f"[{wu_ids[i - 1]}]" if i > 0 else "[]"
        fname = "WU-close.md" if wu_id.split("/")[-1].startswith("close") \
            else f"WU-{wu_id.split('/')[-1]}.md"
        work_units_yaml.append(
            f"      - id: {wu_id}\n        file: {fname}\n"
            f"        depends_on: {dep}\n")

    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: {branch}\nroadmap_goal: test\nstatus: active\n"
        f"auto_close_disabled: true\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n" + "".join(work_units_yaml) + "```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    for wu_id in wu_ids:
        fname = "WU-close.md" if wu_id.split("/")[-1].startswith("close") \
            else f"WU-{wu_id.split('/')[-1]}.md"
        wu_type = "close" if wu_id.split("/")[-1].startswith("close") \
            else "implementation"
        model = "opus" if wu_type == "close" else "sonnet"
        (fdir / fname).write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: {model}\n"
            f"status: pending\nattempts: 0\n---\n\n# {wu_id}{body}"
        )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


def _read_events(fdir: Path) -> list:
    events_path = fdir / "events.jsonl"
    if not events_path.is_file():
        return []
    return [json.loads(line) for line in events_path.read_text().splitlines()
            if line.strip()]


class TestDriverRestartHaltWiring(unittest.TestCase):
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

    def test_driver_edit_halts_before_next_dispatch(self):
        """T01 edits the driver; T02 is still pending. The run must halt
        with EXIT_DRIVER_RESTART_REQUIRED, T02 must never be dispatched, and
        the halt message must reach stdout."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9201"
            fdir = _write_feature(
                root, feature_id, "halt-wiring", "feat/halt-wiring",
                [f"{feature_id}/T01", f"{feature_id}/T02",
                 f"{feature_id}/close"])
            t01_id = f"{feature_id}/T01"
            t02_id = f"{feature_id}/T02"

            dispatched = []

            def fake_dispatch(wu, fn, ct=True):
                dispatched.append(wu.wu_id)
                if wu.wu_id == t01_id:
                    Path("specfuse/loop").mkdir(parents=True, exist_ok=True)
                    Path("specfuse/loop/loop.py").write_text(
                        "# pretend driver edit\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - specfuse/loop/loop.py\n```\n")
                if wu.wu_id == t02_id:
                    Path("src").mkdir(exist_ok=True)
                    Path("src/x.py").write_text("# unrelated\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/x.py\n```\n")
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                loop.write_frontmatter_field(wu.file, "verdict", "met_locally")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = loop.run(None, dry_run=False)

            output = buf.getvalue()

            self.assertEqual(rc, loop.EXIT_DRIVER_RESTART_REQUIRED)
            self.assertEqual(dispatched, [t01_id])
            self.assertIn("DRIVER RESTART REQUIRED", output)
            self.assertIn(t01_id, output)

            t01_fm, _ = loop.read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm["status"], "done")

            events = _read_events(fdir)
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == t01_id]
            self.assertEqual(len(completed), 1)

            gate_fm, _ = loop.read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm["status"], "open")

    def test_final_unit_driver_edit_does_not_halt(self):
        """The gate's last unit edits the driver. Nothing is left pending,
        so the run completes normally and the gate-completion summary (T03)
        reports the staleness instead of a halt."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9202"
            fdir = _write_feature(
                root, feature_id, "halt-final-unit", "feat/halt-final-unit",
                [f"{feature_id}/T01", f"{feature_id}/T02"])
            t01_id = f"{feature_id}/T01"

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id == t01_id:
                    Path("src").mkdir(exist_ok=True)
                    Path("src/x.py").write_text("# unrelated\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/x.py\n```\n")
                Path("specfuse/loop").mkdir(parents=True, exist_ok=True)
                Path("specfuse/loop/loop.py").write_text(
                    "# pretend driver edit\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - specfuse/loop/loop.py\n```\n")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = loop.run(None, dry_run=False)

            output = buf.getvalue()

            self.assertNotEqual(rc, loop.EXIT_DRIVER_RESTART_REQUIRED)
            self.assertNotIn("DRIVER RESTART REQUIRED", output)
            self.assertIn("STALE DRIVER PROCESS (gate summary):", output)

            gate_fm, _ = loop.read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm["status"], "awaiting_review")

            t02_fm, _ = loop.read_frontmatter(fdir / "WU-T02.md")
            self.assertEqual(t02_fm["status"], "done")

    def test_dry_run_never_halts(self):
        """A --dry-run pass over the same driver-editing plan never halts —
        dry runs dispatch nothing, so there is no stale dispatch to prevent."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9203"
            _write_feature(
                root, feature_id, "halt-dry-run", "feat/halt-dry-run",
                [f"{feature_id}/T01", f"{feature_id}/T02",
                 f"{feature_id}/close"])

            def fake_dispatch(wu, fn, ct=True):  # pragma: no cover - unreachable
                raise AssertionError("dispatch must not be called in --dry-run")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = loop.run(None, dry_run=True)

            output = buf.getvalue()
            self.assertNotEqual(rc, loop.EXIT_DRIVER_RESTART_REQUIRED)
            self.assertNotIn("DRIVER RESTART REQUIRED", output)

    def test_no_driver_edit_run_uninterrupted(self):
        """No WU's squash diff touches the driver — every unit dispatches,
        the run is never interrupted."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9204"
            fdir = _write_feature(
                root, feature_id, "halt-negative", "feat/halt-negative",
                [f"{feature_id}/T01", f"{feature_id}/T02",
                 f"{feature_id}/T03"])
            t01_id = f"{feature_id}/T01"
            t02_id = f"{feature_id}/T02"
            t03_id = f"{feature_id}/T03"

            dispatched = []

            def fake_dispatch(wu, fn, ct=True):
                dispatched.append(wu.wu_id)
                fname = wu.wu_id.split("/")[-1]
                Path("src").mkdir(exist_ok=True)
                Path(f"src/{fname}.py").write_text("# unrelated\n")
                return ("```result\nstatus: complete\n"
                        f"files_changed:\n  - src/{fname}.py\n```\n")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = loop.run(None, dry_run=False)

            output = buf.getvalue()
            self.assertNotEqual(rc, loop.EXIT_DRIVER_RESTART_REQUIRED)
            self.assertNotIn("DRIVER RESTART REQUIRED", output)
            self.assertEqual(dispatched, [t01_id, t02_id, t03_id])

            gate_fm, _ = loop.read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm["status"], "awaiting_review")


if __name__ == "__main__":
    unittest.main()
