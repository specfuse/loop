#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Gate-completion driver-editing staleness summary (FEAT-2026-0075/T03).

`format_driver_staleness_warning` (T02) fires immediately at the squash site.
This is the gate-end counterpart: at gate completion, name which unit(s)
edited the driver and which units this same process dispatched afterward —
each of which executed the pre-edit module — and record the fact as a
`driver_staleness_detected` event so a close reads it instead of
reconstructing it from `ps` output and `started_at` timestamps.

Drives the real gate-completion path (`loop.run()` with a stubbed dispatch),
per WU acceptance criterion 5 — calling the formatter alone would not
exercise the gate-completion wiring or the event write.
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


def _write_chained_feature(root: Path, feature_id: str, slug: str,
                            branch: str, wu_ids: list) -> Path:
    """Scaffold a single-gate feature whose work units form a strict chain
    (each depends on the previous), so dispatch order is deterministic."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    wu_entries = []
    for i, short_id in enumerate(wu_ids):
        wu_id = f"{feature_id}/{short_id}"
        deps = f"[{feature_id}/{wu_ids[i - 1]}]" if i > 0 else "[]"
        wu_entries.append(
            f"      - id: {wu_id}\n        file: WU-{short_id}.md\n"
            f"        depends_on: {deps}"
        )
    plan_wus = "\n".join(wu_entries)

    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: {branch}\nroadmap_goal: test\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n{plan_wus}\n```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    for short_id in wu_ids:
        wu_id = f"{feature_id}/{short_id}"
        (fdir / f"WU-{short_id}.md").write_text(
            f"---\nid: {wu_id}\ntype: implementation\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# {short_id}{body}"
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


class TestFormatDriverStalenessSummaryUnit(unittest.TestCase):

    def test_empty_edits_returns_empty_string(self):
        self.assertEqual(loop.format_driver_staleness_summary([], []), "")

    def test_names_editor_paths_and_dispatched_after(self):
        summary = loop.format_driver_staleness_summary(
            [("FEAT-2026-9999/T01", ["specfuse/loop/loop.py"])],
            ["FEAT-2026-9999/T02", "FEAT-2026-9999/T03"],
        )
        self.assertIn("FEAT-2026-9999/T01", summary)
        self.assertIn("specfuse/loop/loop.py", summary)
        self.assertIn("FEAT-2026-9999/T02", summary)
        self.assertIn("FEAT-2026-9999/T03", summary)


class TestDriverStalenessGateSummarySeam(unittest.TestCase):
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

    def test_summary_names_units_dispatched_after(self):
        """T00 precedes the driver edit and must NOT be named as affected;
        T01 edits the driver; T02 and T03 are dispatched after it and must
        both be named as having executed the pre-edit module."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_chained_feature(
                root, "FEAT-2026-9201", "gate-summary",
                "feat/gate-summary", ["T00", "T01", "T02", "T03"])

            def fake_dispatch(wu, fn, ct=True):
                short = wu.wu_id.split("/")[-1]
                if short == "T01":
                    Path("specfuse/loop").mkdir(parents=True, exist_ok=True)
                    Path("specfuse/loop/loop.py").write_text(
                        "# pretend driver edit\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - specfuse/loop/loop.py\n```\n")
                Path("src").mkdir(exist_ok=True)
                path = Path("src") / f"{short.lower()}.py"
                path.write_text(f"# {short}\n")
                return (f"```result\nstatus: complete\n"
                        f"files_changed:\n  - {path.as_posix()}\n```\n")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.run(None, dry_run=False)

            output = buf.getvalue()
            self.assertIn("STALE DRIVER PROCESS (gate summary):", output)

            summary_block = output[output.index(
                "STALE DRIVER PROCESS (gate summary):"):]

            self.assertIn("FEAT-2026-9201/T01", summary_block)
            self.assertIn("specfuse/loop/loop.py", summary_block)
            self.assertIn("FEAT-2026-9201/T02", summary_block)
            self.assertIn("FEAT-2026-9201/T03", summary_block)
            # T00 dispatched BEFORE the driver edit — must not read as affected.
            self.assertNotIn("FEAT-2026-9201/T00", summary_block)

            events = _read_events(fdir)
            staleness_events = [e for e in events
                                 if e["event_type"] == "driver_staleness_detected"]
            self.assertEqual(len(staleness_events), 1)
            payload = staleness_events[0]["payload"]
            edit_ids = [e["wu_id"] for e in payload["edits"]]
            self.assertEqual(edit_ids, ["FEAT-2026-9201/T01"])
            self.assertIn("specfuse/loop/loop.py",
                          payload["edits"][0]["driver_paths"])
            self.assertEqual(
                payload["dispatched_after"],
                ["FEAT-2026-9201/T02", "FEAT-2026-9201/T03"],
            )

    def test_no_driver_edit_no_summary_no_event(self):
        """A gate with no driver-editing unit produces no summary and no
        event, asserted through the same gate-completion harness."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_chained_feature(
                root, "FEAT-2026-9202", "no-staleness",
                "feat/no-staleness", ["T01", "T02"])

            def fake_dispatch(wu, fn, ct=True):
                short = wu.wu_id.split("/")[-1]
                Path("src").mkdir(exist_ok=True)
                path = Path("src") / f"{short.lower()}.py"
                path.write_text(f"# {short}\n")
                return (f"```result\nstatus: complete\n"
                        f"files_changed:\n  - {path.as_posix()}\n```\n")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.run(None, dry_run=False)

            self.assertNotIn("STALE DRIVER PROCESS", buf.getvalue())
            events = _read_events(fdir)
            staleness_events = [e for e in events
                                 if e["event_type"] == "driver_staleness_detected"]
            self.assertEqual(staleness_events, [])


if __name__ == "__main__":
    unittest.main()
