#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for `ids migrate --all` (FEAT-2026-0247/T08)."""

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import _filelock, ids, lint_plan, lint_roadmap

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / ".specfuse" / "features" / "FEAT-2026-0001-health-endpoint"

ROADMAP = """# Roadmap

| Feature ID | Title | Status | Folder | Detail |
|---|---|---|---|---|
| FEAT-2026-0042 | Live | active | — | [→ detail](#feat-2026-0042) |
| FEAT-2026-0071 | Other | planned | — | [→ detail](#feat-2026-0071) |

<a id="feat-2026-0042"></a>
## FEAT-2026-0042 — Live

Body.

<a id="feat-2026-0071"></a>
## FEAT-2026-0071 — Other

Body.
"""

ARCHIVE = """# Archive

| Feature ID | Title | Status | Folder | Detail |
|---|---|---|---|---|
| FEAT-2026-0007 | Old | done | — | [→ detail](#feat-2026-0007) |

<a id="feat-2026-0007"></a>
## FEAT-2026-0007 — Old

Done.
"""

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- added: new thing (FEAT-2026-0042).

## [0.1.0] - 2026-01-01

### Added

- added: old thing (FEAT-2026-0007).
"""


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _make(tmp, key="ACME"):
    root = Path(tmp)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "T")
    spec = root / ".specfuse"
    spec.mkdir()
    shutil.copytree(REPO_ROOT / ".specfuse" / "templates", spec / "templates")
    shutil.copy(REPO_ROOT / ".specfuse" / "verification.yml", spec / "verification.yml")
    if key:
        (spec / "layout.yml").write_text(f"ids:\n  key: {key}\n")
    (spec / "roadmap.md").write_text(ROADMAP)
    (spec / "roadmap-archive.md").write_text(ARCHIVE)
    for fid, slug in (("FEAT-2026-0042", "live"), ("FEAT-2026-0071", "other")):
        folder = spec / "features" / f"{fid}-{slug}"
        shutil.copytree(FIXTURE, folder)
        for path in folder.rglob("*.md"):
            text = path.read_text().replace("FEAT-2026-0001", fid)
            if path.name == "PLAN.md":
                text = text.replace("status: done", "status: active")
            if path.name.startswith("GATE-"):
                text = text.replace("status: open\n", 'status: open\nfeature_oracle: "true"\n', 1)
            path.write_text(text)
        event = {"correlation_id": f"{fid}/T01", "event_type": "task_started"}
        (folder / "events.jsonl").write_text(json.dumps(event) + "\n")
    (root / "CHANGELOG.md").write_text(CHANGELOG)
    (root / "NOTES.md").write_text(
        "We saw FEAT-2026-0071 in the partner repo.\nNot FEAT-2026-00711 nor FEAT-ACME-2026-0042.\n"
    )
    (root / "logo.bin").write_bytes(b"\0FEAT-2026-0042\0")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _run(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ids.main(["--repo", str(root), "migrate", "--all", *args])
    return code, out.getvalue(), err.getvalue()


def _snapshot(root):
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts and p.name != ".loop.lock"
    }


class MigrateAll(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            before = _snapshot(root)
            code, out, _ = _run(root)
            self.assertEqual(code, 0)
            self.assertEqual(_snapshot(root), before)
            self.assertIn("FEAT-2026-0042 -> FEAT-ACME-2026-0042", out)
            self.assertIn("FEAT-2026-0007 -> FEAT-ACME-2026-0007", out)
            self.assertIn("FEAT-2026-0042-live -> .specfuse/features/FEAT-ACME-2026-0042-live", out)
            self.assertIn("CHANGELOG.md: released section `## [0.1.0] - 2026-01-01`", out)
            self.assertIn("NOTES.md:1: FEAT-2026-0071", out)
            self.assertNotIn("FEAT-2026-00711", out)
            self.assertFalse((root / ".specfuse" / "id-aliases.yml").exists())

    def test_apply_rewrites_structure_and_leaves_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            code, _, err = _run(root, "--apply")
            self.assertEqual(code, 0, err)
            spec = root / ".specfuse"
            self.assertTrue((spec / "features" / "FEAT-ACME-2026-0042-live").is_dir())
            self.assertFalse((spec / "features" / "FEAT-2026-0042-live").exists())
            roadmap = (spec / "roadmap.md").read_text()
            self.assertIn("| FEAT-ACME-2026-0042 |", roadmap)
            self.assertIn("(#feat-acme-2026-0071)", roadmap)
            self.assertIn("| FEAT-ACME-2026-0007 |", (spec / "roadmap-archive.md").read_text())
            events = (spec / "features" / "FEAT-ACME-2026-0042-live" / "events.jsonl").read_text()
            self.assertEqual(json.loads(events)["correlation_id"], "FEAT-ACME-2026-0042/T01")
            changelog = (root / "CHANGELOG.md").read_text()
            self.assertEqual(changelog, CHANGELOG)
            notes = (root / "NOTES.md").read_text()
            self.assertIn("saw FEAT-2026-0071 in", notes)
            self.assertIn("FEAT-2026-00711", notes)
            self.assertEqual((root / "logo.bin").read_bytes(), b"\0FEAT-2026-0042\0")
            aliases = (spec / "id-aliases.yml").read_text()
            self.assertIn("FEAT-2026-0042: FEAT-ACME-2026-0042\n", aliases)
            self.assertEqual(
                lint_plan.lint(spec / "features" / "FEAT-ACME-2026-0042-live"), []
            )
            errors = [
                f for f in lint_roadmap.lint_roadmap(root)
                if f.severity == lint_roadmap.SEVERITY_ERROR
            ]
            self.assertEqual(errors, [])
            # second run: nothing to do, even with the tree still dirty
            code, out, _ = _run(root, "--apply")
            self.assertEqual(code, 0)
            self.assertIn("nothing to do", out)
            self.assertEqual((spec / "id-aliases.yml").read_text(), aliases)

    def test_include_prose_rewrites_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            code, _, err = _run(root, "--apply", "--include-prose")
            self.assertEqual(code, 0, err)
            notes = (root / "NOTES.md").read_text()
            self.assertIn("saw FEAT-ACME-2026-0071 in", notes)
            self.assertIn("FEAT-2026-00711", notes)
            self.assertIn("FEAT-ACME-2026-0042.", notes)
            changelog = (root / "CHANGELOG.md").read_text()
            self.assertIn("new thing (FEAT-ACME-2026-0042)", changelog)
            self.assertIn("(FEAT-2026-0007)", changelog)

    def test_refuses_without_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp, key=None)
            code, _, err = _run(root, "--apply")
            self.assertNotEqual(code, 0)
            self.assertIn("no project key", err)

    def test_refuses_dirty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            (root / "NOTES.md").write_text("changed\n")
            code, _, err = _run(root, "--apply")
            self.assertNotEqual(code, 0)
            self.assertIn("uncommitted", err)
            self.assertTrue((root / ".specfuse" / "features" / "FEAT-2026-0042-live").is_dir())

    def test_refuses_when_driver_holds_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            held = _filelock.acquire_tree_lock(root / ".specfuse")
            try:
                code, _, err = _run(root, "--apply")
            finally:
                held.close()
            self.assertNotEqual(code, 0)
            self.assertIn(".loop.lock", err)
            self.assertTrue((root / ".specfuse" / "features" / "FEAT-2026-0042-live").is_dir())

    def test_planned_only_and_all_are_exclusive(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            ids.main(["migrate", "--all", "--planned-only"])
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            ids.main(["migrate"])


if __name__ == "__main__":
    unittest.main()
