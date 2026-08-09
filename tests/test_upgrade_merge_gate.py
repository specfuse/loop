#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.upgrade_merge_gate (FEAT-2026-0029/T01).

`decide` turns (CI status, per-feature lint results) into a merge/halt
verdict; `collect_reports` produces those per-feature results by shelling out
to the plan linter once per `.specfuse/features/*/` folder.

Imported from the package, not loaded by file path: `/scaffold-upgrade` calls
`collect_reports` and `decide` as functions against a *target* project, where
`.specfuse/scripts/` does not exist (#1076).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import upgrade_merge_gate as umg

REPO_ROOT = Path(__file__).resolve().parent.parent

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


class TestPackageEraTarget(unittest.TestCase):
    """#309 — a package-era target has no in-repo lint shim.

    `collect_reports` invoked `<target>/.specfuse/scripts/lint_plan.py`
    directly. Post-package targets do not ship it (the scripts come from the
    installed `specfuse-loop`), so every folder reported a garbled FAIL whose
    detail was Python's own "can't open file" message, and `decide` returned a
    **false halt** on a perfectly conformant repo.
    """

    _GOOD_PLAN = _VALID_FM + """
```yaml
gates:
  - gate: 1
    work_units: []
```
"""

    def _target(self, tmp: str, *, with_shim: bool = False,
                extra_dirs: tuple = ()) -> Path:
        root = Path(tmp)
        feat = root / ".specfuse" / "features" / "FEAT-2026-0099-real"
        feat.mkdir(parents=True)
        (feat / "PLAN.md").write_text(self._GOOD_PLAN)
        for name in extra_dirs:
            (root / ".specfuse" / "features" / name).mkdir(parents=True)
        if with_shim:
            shim = root / ".specfuse" / "scripts"
            shim.mkdir(parents=True)
            # A shim that always passes, so its use is observable: if the
            # fallback is not taken, the package path runs instead and this
            # test's marker never appears.
            (shim / "lint_plan.py").write_text(
                "import sys\nprint('SHIM MARKER')\nsys.exit(0)\n"
            )
        return root

    def test_conformant_feature_passes_without_an_in_target_shim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._target(tmp)
            reports = umg.collect_reports(root)
            self.assertEqual(len(reports), 1, reports)
            self.assertTrue(
                reports[0]["ok"],
                f"false FAIL on a package-era target: {reports[0]['detail']!r}",
            )

    def test_decide_does_not_falsely_halt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._target(tmp)
            verdict, reason = umg.decide(True, umg.collect_reports(root))
            self.assertEqual((verdict, reason), ("merge", ""))

    def test_non_feature_directories_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._target(tmp, extra_dirs=(".claude", "notes"))
            names = [r["feature"] for r in umg.collect_reports(root)]
            self.assertEqual(names, ["FEAT-2026-0099-real"], names)

    def test_pre_package_shim_is_still_honoured(self):
        """Old targets that DO ship the shim must keep using it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._target(tmp, with_shim=True)
            reports = umg.collect_reports(root)
            self.assertTrue(reports[0]["ok"])
            self.assertTrue(
                reports[0].get("used_shim"),
                "in-target shim present but not used — pre-package repos "
                "would silently switch linters on upgrade",
            )

    def test_a_genuinely_broken_feature_still_fails(self):
        """Guard the guard: the fix must not make everything pass."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._target(tmp)
            bad = root / ".specfuse" / "features" / "FEAT-2026-0098-broken"
            bad.mkdir()
            (bad / "PLAN.md").write_text("---\nnot: a valid plan\n---\n")
            reports = {r["feature"]: r for r in umg.collect_reports(root)}
            self.assertTrue(reports["FEAT-2026-0099-real"]["ok"])
            self.assertFalse(reports["FEAT-2026-0098-broken"]["ok"])
            self.assertTrue(reports["FEAT-2026-0098-broken"]["detail"].strip())

    def test_an_unrunnable_linter_says_so_instead_of_blaming_features(self):
        """The #309 failure shape, generalised.

        If the linter cannot run at all, every feature fails with the same
        interpreter-level error and `decide` blames the features by name. That
        is precisely how the original bug read in the field. The gate must
        distinguish "this repo is non-conformant" from "I could not check".
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = self._target(tmp)
            reports = umg.collect_reports(root, python=str(Path(tmp) / "no-python"))
            verdict, reason = umg.decide(True, reports)
            self.assertEqual(verdict, "halt")
            self.assertNotIn(
                "FEAT-2026-0099-real", reason,
                "blamed a conformant feature for a broken linter",
            )
            self.assertIn("could not", reason.lower())
