#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/upgrade_merge_gate.py (FEAT-2026-0029/T01).

`decide` turns (CI status, per-feature lint_plan.py results) into a merge/halt
verdict; `collect_reports` produces those per-feature results by shelling out
to lint_plan.py once per `.specfuse/features/*/` folder. Loaded by file path,
matching the pattern other `.specfuse/scripts` helpers use in this test suite
(see test_leak_scan_content.py) since this module is not part of the
`specfuse` package.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".specfuse" / "scripts"


def _load(name: str):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


umg = _load("upgrade_merge_gate")

_VALID_FM = """\
---
feature_id: FEAT-2026-0099
title: Test Feature
branch: feat/test
roadmap_goal: Test goal
status: active
---
"""

_CLOSING_WUS = [
    ("FEAT-2026-0099/G1-RETRO", "WU-90-retro.md", "retrospective"),
    ("FEAT-2026-0099/G1-LESSONS", "WU-91-lessons.md", "lessons"),
    ("FEAT-2026-0099/G1-DOCS", "WU-92-docs.md", "docs"),
    ("FEAT-2026-0099/G1-PLAN", "WU-93-plan-next.md", "plan-next"),
]


def _wu_fm(wid: str, wu_type: str, status: str = "done") -> str:
    return "\n".join(["---", f"id: {wid}", f"type: {wu_type}", f"status: {status}", "---"]) + "\n"


def _make_graph(work_units: list[dict]) -> str:
    parts = ["```yaml", "gates:", "  - gate: 1", "    work_units:"]
    for wu in work_units:
        parts.append(f"      - id: {wu['id']}")
        parts.append(f"        file: {wu['file']}")
        parts.append("        depends_on: []")
    parts.append("```")
    return "\n".join(parts)


def _build_valid_feature(features_dir: Path, name: str) -> Path:
    """A feature folder that passes lint_plan.py cleanly."""
    feat = features_dir / name
    feat.mkdir()
    impl_id = "FEAT-2026-0099/T01"
    impl_file = "WU-01-impl.md"
    all_wus = [{"id": impl_id, "file": impl_file}] + [
        {"id": wid, "file": wfile} for wid, wfile, _ in _CLOSING_WUS
    ]
    (feat / "PLAN.md").write_text(_VALID_FM + "\n" + _make_graph(all_wus) + "\n")
    (feat / impl_file).write_text(_wu_fm(impl_id, "implementation"))
    for wid, wfile, wtype in _CLOSING_WUS:
        (feat / wfile).write_text(_wu_fm(wid, wtype))
    return feat


def _build_invalid_feature(features_dir: Path, name: str) -> Path:
    """A feature folder with no PLAN.md — fails lint_plan.py."""
    feat = features_dir / name
    feat.mkdir()
    return feat


class TestDecide(unittest.TestCase):

    def test_halts_when_a_feature_fails_conformance(self):
        verdict, reason = umg.decide(
            True,
            [
                {"feature": "FEAT-2026-0001-a", "ok": True, "detail": ""},
                {"feature": "FEAT-2026-0002-b", "ok": False, "detail": "missing PLAN.md"},
            ],
        )
        self.assertEqual(verdict, "halt")
        self.assertIn("FEAT-2026-0002-b", reason)

    def test_merge_when_all_ok_and_ci_green(self):
        verdict, reason = umg.decide(
            True,
            [
                {"feature": "a", "ok": True, "detail": ""},
                {"feature": "b", "ok": True, "detail": ""},
            ],
        )
        self.assertEqual(verdict, "merge")
        self.assertEqual(reason, "")

    def test_halt_when_ci_not_green_even_if_all_ok(self):
        verdict, reason = umg.decide(
            False,
            [{"feature": "a", "ok": True, "detail": ""}],
        )
        self.assertEqual(verdict, "halt")
        self.assertIn("CI not green", reason)

    def test_halt_when_ci_green_but_a_report_not_ok(self):
        verdict, reason = umg.decide(
            True,
            [{"feature": "a", "ok": True, "detail": ""}, {"feature": "b", "ok": False, "detail": "x"}],
        )
        self.assertEqual(verdict, "halt")
        self.assertIn("b", reason)

    def test_empty_reports_fails_safe_to_halt(self):
        verdict, reason = umg.decide(True, [])
        self.assertEqual(verdict, "halt")
        self.assertIn("no feature folders", reason)


class TestCollectReports(unittest.TestCase):

    def test_no_feature_folders_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            reports = umg.collect_reports(repo_root)
        self.assertEqual(reports, [])

    def test_marks_valid_and_invalid_feature_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            features_dir = repo_root / ".specfuse" / "features"
            features_dir.mkdir(parents=True)
            _build_valid_feature(features_dir, "FEAT-2026-0001-good")
            _build_invalid_feature(features_dir, "FEAT-2026-0002-bad")

            scripts_dir = repo_root / ".specfuse" / "scripts"
            scripts_dir.mkdir(parents=True)
            # A minimal shim (not a copy of the repo's own lint_plan.py shim,
            # whose path-insert logic assumes it lives 2 levels under the real
            # repo root) that runs the real specfuse.loop.lint_plan CLI against
            # this tmp repo's feature folders.
            (scripts_dir / "lint_plan.py").write_text(
                "import sys\n"
                f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
                "from specfuse.loop.lint_plan import main\n"
                "if __name__ == '__main__':\n"
                "    raise SystemExit(main())\n"
            )

            reports = umg.collect_reports(repo_root)

        by_name = {r["feature"]: r for r in reports}
        self.assertEqual(len(reports), 2)
        self.assertTrue(by_name["FEAT-2026-0001-good"]["ok"])
        self.assertFalse(by_name["FEAT-2026-0002-bad"]["ok"])
        self.assertTrue(by_name["FEAT-2026-0002-bad"]["detail"])


if __name__ == "__main__":
    unittest.main()
