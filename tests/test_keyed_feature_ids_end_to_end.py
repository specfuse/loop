#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature oracle for FEAT-2026-0247 gate 1 — a keyed feature works end to end.

One class per Definition-of-done clause in GATE-01.md, driven through the real
modules in a temporary repository. Clauses 1, 2 and 8 are live (T01), clause 3 (T02), clause 4 (T03), clause 5 (T04); the rest
are skipped naming their owner. A skip surviving to the close is a hollow oracle.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import lint_plan, lint_roadmap

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / ".specfuse" / "features" / "FEAT-2026-0001-health-endpoint"
SLUG = "health-endpoint"


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run(repo, *args):
    return subprocess.run(
        [sys.executable, "-m", *args], cwd=repo, capture_output=True, text=True,
        env=_env(), check=False,
    )


def make_repo(tmp, *, key=None, legacy_through=7, feature_id=None):
    """Temp repo: roadmap rows up to `legacy_through`; optional key; optional feature."""
    root = Path(tmp)
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    spec = root / ".specfuse"
    (spec / "features").mkdir(parents=True)
    for sub in ("rules", "templates"):
        shutil.copytree(REPO_ROOT / ".specfuse" / sub, spec / sub)
    shutil.copy(REPO_ROOT / ".specfuse" / "verification.yml", spec / "verification.yml")
    if key:
        (spec / "layout.yml").write_text(f"ids:\n  key: {key}\n")
    rows = [f"| FEAT-2026-{n:04d} | legacy {n} | done | — | x |" for n in range(1, legacy_through + 1)]
    body = ""
    if feature_id:
        rows.append(f"| {feature_id} | Health | planned | — | [→ detail](#{feature_id.lower()}) |")
        body = (
            f'\n<a id="{feature_id.lower()}"></a>\n## {feature_id} — Health\n\n'
            "**Status: planned.**\n\nBody.\n"
        )
        folder = spec / "features" / f"{feature_id}-{SLUG}"
        shutil.copytree(FIXTURE, folder)
        for path in folder.rglob("*.md"):
            text = path.read_text().replace("FEAT-2026-0001", feature_id)
            if path.name == "PLAN.md":
                text = text.replace("status: done", "status: active")
            if path.name.startswith("GATE-"):
                text = text.replace("status: open\n", 'status: open\nfeature_oracle: "true"\n', 1)
            path.write_text(text)
    (spec / "roadmap.md").write_text(
        "# Roadmap\n\n| Feature ID | Title | Status | Folder | Detail |\n"
        "|---|---|---|---|---|\n" + "\n".join(rows) + "\n" + body
    )
    return root


def lint_errors(root, feature_id):
    plan = lint_plan.lint(root / ".specfuse" / "features" / f"{feature_id}-{SLUG}")
    roadmap = [f for f in lint_roadmap.lint_roadmap(root) if f.severity == lint_roadmap.SEVERITY_ERROR]
    return plan, roadmap


def dry_run(root, feature_arg):
    return _run(root, "specfuse.loop.loop", "--dry-run", "--no-autosync", "--feature", feature_arg)


class Clause1AllocationContinuesLegacyNumbering(unittest.TestCase):
    def test_keyed_next(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, key="ACME")
            r = _run(root, "specfuse.loop.ids", "next", "--year", "2026")
            self.assertEqual(r.stdout.strip(), "FEAT-ACME-2026-0008", r.stderr)

    def test_unkeyed_next_is_todays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            r = _run(root, "specfuse.loop.ids", "next", "--year", "2026")
            self.assertEqual(r.stdout.strip(), "FEAT-2026-0008", r.stderr)

    def test_key_round_trips_through_layout_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, key="ACME")
            self.assertEqual(_run(root, "specfuse.loop.layout", "get", "ids.key").stdout.strip(), "ACME")


class Clause2KeyedFeatureLints(unittest.TestCase):
    def _check(self, key, feature_id):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, key=key, feature_id=feature_id)
            plan, roadmap = lint_errors(root, feature_id)
            self.assertEqual(roadmap, [])
            self.assertEqual(plan, [])
            r = dry_run(root, f"{feature_id}-{SLUG}")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn(f"{feature_id}/T01", r.stdout)

    def test_keyed_feature_lints_and_loads(self):
        self._check("ACME", "FEAT-ACME-2026-0008")

    def test_legacy_positive_control(self):
        self._check(None, "FEAT-2026-0008")

    def test_keyed_feature_in_legacy_roadmap_lints(self):
        self._check(None, "FEAT-ACME-2026-0008")


class Clause3EverySiteAcceptsKeyedForm(unittest.TestCase):
    """The per-site cases live in tests/test_ids_call_sites.py; this ties them in."""

    def test_call_site_suite_is_live(self):
        from tests import test_ids_call_sites

        self.assertTrue(test_ids_call_sites.CallSiteCases.SITES)


class Clause4SkillsAllocateThroughIdsNext(unittest.TestCase):
    def _skill(self, name):
        return (REPO_ROOT / "plugins" / "specfuse" / "skills" / name / "SKILL.md").read_text()

    def test_roadmap_add_names_ids_next_and_a_keyed_example(self):
        text = self._skill("roadmap-add")
        self.assertIn("specfuse.loop.ids next", text)
        self.assertIn("FEAT-ACME-2026-0003", text)

    def test_draft_feature_points_at_ids_next(self):
        self.assertIn("specfuse.loop.ids next", self._skill("draft-feature"))


class Clause5UnkeyedPlannedRowWarns(unittest.TestCase):
    def test_unkeyed_planned_row_warns_with_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, key="ACME", feature_id="FEAT-2026-0008")
            warns = [f for f in lint_roadmap.lint_roadmap(root) if f.severity == lint_roadmap.SEVERITY_WARN]
            self.assertEqual(len(warns), 1, warns)
            self.assertIn("FEAT-2026-0008", warns[0].message)
            self.assertIn("ACME", warns[0].message)
            self.assertIn("migrate --planned-only", warns[0].message)

    def test_silent_without_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, feature_id="FEAT-2026-0008")
            self.assertEqual(lint_roadmap.lint_roadmap(root), [])


@unittest.skip("owned by FEAT-2026-0247/T05")
class Clause6MigratePlannedOnly(unittest.TestCase):
    pass


@unittest.skip("owned by FEAT-2026-0247/T07")
class Clause7KeyedCorrelationIdValidatesAgainstEnvelope(unittest.TestCase):
    pass


class Clause8UnkeyedRepoIsUnchanged(unittest.TestCase):
    def test_no_layout_surfaces_are_todays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, feature_id="FEAT-2026-0008")
            self.assertFalse((root / ".specfuse" / "layout.yml").exists())
            self.assertEqual(_run(root, "specfuse.loop.layout", "get", "ids.key").stdout, "\n")
            self.assertEqual(
                _run(root, "specfuse.loop.layout", "get", "decisions.style").stdout.strip(), "adr"
            )
            self.assertEqual(_run(root, "specfuse.loop.layout", "check").returncode, 0)
            self.assertEqual(
                _run(root, "specfuse.loop.ids", "next", "--year", "2026").stdout.strip(),
                "FEAT-2026-0009",
            )
            plan, roadmap = lint_errors(root, "FEAT-2026-0008")
            self.assertEqual((plan, roadmap), ([], []))

    def test_layout_without_ids_block_is_unkeyed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            (root / ".specfuse" / "layout.yml").write_text("decisions:\n  style: adr\n")
            r = _run(root, "specfuse.loop.ids", "next", "--year", "2026")
            self.assertEqual(r.stdout.strip(), "FEAT-2026-0008")


if __name__ == "__main__":
    unittest.main()
