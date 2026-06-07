#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""T03 — adopt_feature.py: scaffold a loop-feature folder from a picked issue.

Covers: orchestrated INIT candidate (with initiative), component-local FEAT
candidate (no initiative), lint_plan integration for both, CLI main(), and
a malformed-body candidate that lint_plan rejects.  No live gh call.
"""

from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".specfuse/scripts"


def _load(module_name: str, rel_path: str):
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


adopt_feature_mod = _load("adopt_feature_under_test", ".specfuse/scripts/adopt_feature.py")
lint_plan_mod = _load("lint_plan_under_test", ".specfuse/scripts/lint_plan.py")

adopt_feature = adopt_feature_mod.adopt_feature
make_slug = adopt_feature_mod._make_slug
read_frontmatter = lint_plan_mod.read_frontmatter

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_FIVE_SECTIONS = (
    "**Context.**\n\nTest context.\n\n"
    "**Acceptance criteria.**\n\n- Test criterion.\n\n"
    "**Do not touch.**\n\nNothing.\n\n"
    "**Verification.**\n\nRun tests.\n\n"
    "**Escalation triggers.**\n\nBlock on failure."
)

_MISSING_ESCALATION_BODY = (
    "**Context.**\n\nTest context.\n\n"
    "**Acceptance criteria.**\n\n- Test criterion.\n\n"
    "**Do not touch.**\n\nNothing.\n\n"
    "**Verification.**\n\nRun tests."
)

_ORCHESTRATED_CANDIDATE = {
    "feature_id": "INIT-2026-0001/F06",
    "title": "Conform publishRoster to validated spec",
    "initiative": "INIT-2026-0001",
    "task_type": "implementation",
    "autonomy": "review",
    "url": "https://github.com/example/repo/issues/42",
    "number": 42,
    "body": _FIVE_SECTIONS,
}

_FEAT_CANDIDATE = {
    "feature_id": "FEAT-2027-0001",
    "title": "Add GitHub feature pick",
    "initiative": None,
    "task_type": "implementation",
    "autonomy": "review",
    "url": "https://github.com/example/repo/issues/7",
    "number": 7,
    "body": _FIVE_SECTIONS,
}


# ---------------------------------------------------------------------------
# AC8a — orchestrated candidate (INIT-2026-0001/F06, with initiative)
# ---------------------------------------------------------------------------

class TestOrchestratedCandidate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.folder = adopt_feature(_ORCHESTRATED_CANDIDATE, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_folder_name(self):
        slug = make_slug(_ORCHESTRATED_CANDIDATE["title"])
        self.assertEqual(self.folder.name, f"INIT-2026-0001-F06-{slug}")

    def test_plan_frontmatter_initiative_present(self):
        fm, _ = read_frontmatter(self.folder / "PLAN.md")
        self.assertIn("initiative", fm)
        self.assertEqual(fm["initiative"], "INIT-2026-0001")

    def test_plan_frontmatter_required_keys(self):
        fm, _ = read_frontmatter(self.folder / "PLAN.md")
        for key in ("feature_id", "title", "branch", "roadmap_goal", "status"):
            self.assertIn(key, fm)

    def test_wu01_frontmatter_id(self):
        slug = make_slug(_ORCHESTRATED_CANDIDATE["title"])
        fm, _ = read_frontmatter(self.folder / f"WU-01-{slug}.md")
        self.assertEqual(fm["id"], "INIT-2026-0001/F06/T01")

    def test_wu01_body_has_five_sections(self):
        slug = make_slug(_ORCHESTRATED_CANDIDATE["title"])
        _, body = read_frontmatter(self.folder / f"WU-01-{slug}.md")
        for sec in [
            "Context", "Acceptance criteria", "Do not touch",
            "Verification", "Escalation triggers",
        ]:
            self.assertIn(sec, body, msg=f"missing section: {sec}")

    def test_exactly_eight_files(self):
        files = list(self.folder.iterdir())
        self.assertEqual(len(files), 8)

    def test_lint_passes(self):
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "lint_plan.py"), str(self.folder)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


# ---------------------------------------------------------------------------
# AC8b — component-local candidate (FEAT-2027-0001, no initiative)
# ---------------------------------------------------------------------------

class TestComponentLocalCandidate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.folder = adopt_feature(_FEAT_CANDIDATE, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_folder_name(self):
        slug = make_slug(_FEAT_CANDIDATE["title"])
        self.assertEqual(self.folder.name, f"FEAT-2027-0001-{slug}")

    def test_initiative_absent_from_plan_frontmatter(self):
        fm, _ = read_frontmatter(self.folder / "PLAN.md")
        self.assertNotIn("initiative", fm)

    def test_lint_passes(self):
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "lint_plan.py"), str(self.folder)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


# ---------------------------------------------------------------------------
# AC8e — malformed body: adopt still writes; lint_plan rejects
# ---------------------------------------------------------------------------

class TestMalformedBody(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        candidate = dict(_FEAT_CANDIDATE, body=_MISSING_ESCALATION_BODY)
        self.folder = adopt_feature(candidate, self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_adopt_still_writes_folder(self):
        self.assertTrue(self.folder.exists())

    def test_lint_fails_on_malformed_body(self):
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "lint_plan.py"), str(self.folder)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0, "expected lint to fail on missing section")


# ---------------------------------------------------------------------------
# AC8d — CLI: main() with injected runner produces folder + stdout
# ---------------------------------------------------------------------------

class TestCLIMain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _stub_runner(self, issues):
        def runner(repo):
            return issues
        return runner

    def _issues_for(self, candidate):
        return [{
            "number": candidate["number"],
            "title": f"[{candidate['feature_id']}] {candidate['title']}",
            "labels": [
                {"name": "specfuse:feature"},
                *(
                    [{"name": f"initiative:{candidate['initiative']}"}]
                    if candidate.get("initiative") else []
                ),
                {"name": f"type:{candidate.get('task_type', 'implementation')}"},
                {"name": f"autonomy:{candidate.get('autonomy', 'review')}"},
            ],
            "url": candidate["url"],
            "body": candidate["body"],
        }]

    def test_cli_creates_folder_and_prints_path(self):
        issues = self._issues_for(_ORCHESTRATED_CANDIDATE)
        runner = self._stub_runner(issues)
        saved = sys.argv[:]
        out = io.StringIO()
        sys.argv = ["adopt_feature.py", "example/repo", "42"]
        try:
            with redirect_stdout(out):
                adopt_feature_mod.main(_runner=runner, _root=self.root)
        finally:
            sys.argv = saved
        printed = out.getvalue().strip()
        slug = make_slug(_ORCHESTRATED_CANDIDATE["title"])
        expected_name = f"INIT-2026-0001-F06-{slug}"
        self.assertIn(expected_name, printed)
        self.assertTrue((self.root / expected_name).exists())

    def test_cli_no_match_exits_nonzero(self):
        issues = self._issues_for(_ORCHESTRATED_CANDIDATE)
        runner = self._stub_runner(issues)
        saved = sys.argv[:]
        sys.argv = ["adopt_feature.py", "example/repo", "999"]
        try:
            with self.assertRaises(SystemExit) as ctx:
                adopt_feature_mod.main(_runner=runner, _root=self.root)
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            sys.argv = saved


if __name__ == "__main__":
    unittest.main()
