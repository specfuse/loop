#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0064/T02: the two collection points into CHANGELOG.md.

Bugs have no close ceremony (`1 bug = 1 branch = 1 PR`, no §3 enumeration),
so a close-only collector silently drops every bug fix. This module covers:
the bug-side prescription in `fix-bug`'s SKILL.md (criteria 1-2, load-bearing
— must be red on HEAD before this WU's edits), the close-side rule text
(criteria 3-4), the `close-k` `closing_requirements` check that fires when a
real §3 enumeration lands no matching `Unreleased` entry (criterion 5), and
the no-backfill guarantee over already-`done` features (criterion 6).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop, load_lint
from tests.test_closing_deliverable_guard import DUMMY_HEAD, _make_wu

loop = load_loop()
lint_plan = load_lint()

from specfuse.loop import closing_requirements as creq  # noqa: E402
from specfuse.loop import lint_closing as lc  # noqa: E402
from specfuse.loop import _miniyaml  # noqa: E402
from specfuse.loop.closing_requirements import CLOSING_REQUIREMENTS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
FIX_BUG_SKILL_CANONICAL = REPO_ROOT / "plugins/specfuse/skills/fix-bug/SKILL.md"
FIX_BUG_SKILL_VENDORED = REPO_ROOT / ".specfuse/skills/fix-bug/SKILL.md"
CLOSE_DISCIPLINE_PATH = REPO_ROOT / ".specfuse/rules/close-discipline.md"
FEATURES_DIR = REPO_ROOT / ".specfuse/features"


class TestChangelogCollection(unittest.TestCase):
    # -- criteria 1/2: bug path is a collection point --

    def test_bug_path_is_a_collection_point(self):
        text = FIX_BUG_SKILL_CANONICAL.read_text()
        self.assertIn("CHANGELOG.md", text)
        self.assertIn("Unreleased", text)
        self.assertIn("#<issue-number>", text)
        changelog_idx = text.index("CHANGELOG.md")
        pr_create_idx = text.index("gh pr create")
        self.assertLess(
            changelog_idx, pr_create_idx,
            "the CHANGELOG.md append must be prescribed before the PR is opened",
        )

    def test_fix_bug_skill_copies_are_byte_identical(self):
        canonical = FIX_BUG_SKILL_CANONICAL.read_text()
        vendored = FIX_BUG_SKILL_VENDORED.read_text()
        self.assertEqual(
            canonical, vendored,
            "plugins/specfuse/skills/fix-bug/SKILL.md and "
            ".specfuse/skills/fix-bug/SKILL.md have drifted",
        )

    # -- criterion 3: close side reuses the same §3 material --

    def test_close_discipline_instructs_unreleased_append(self):
        text = CLOSE_DISCIPLINE_PATH.read_text()
        self.assertIn("CHANGELOG.md", text)
        self.assertIn("Unreleased", text)
        self.assertIn("FEAT-YYYY-NNNN", text)
        self.assertIn("classified", text)
        self.assertIn("not a second write", text)

    # -- criterion 4: an n/a close appends nothing, and the rule says so --

    def test_close_discipline_says_na_appends_nothing(self):
        text = CLOSE_DISCIPLINE_PATH.read_text()
        self.assertIn("appends nothing", text)
        self.assertIn("noise", text)

    def test_na_section_is_recognised(self):
        self.assertTrue(
            creq.consumer_visible_section_is_na(
                "\n`n/a — no consumer-visible contract change`\n"
            )
        )
        self.assertFalse(
            creq.consumer_visible_section_is_na(
                "\n1. **New CLI flag `--foo`.** Additive.\n"
            )
        )

    # -- criterion 5: the check fires on enumeration-without-append, silent on n/a --

    def test_registry_has_close_k_requirement(self):
        req = next(
            r for r in CLOSING_REQUIREMENTS["close"] if r.id == "close-k"
        )
        self.assertEqual(req.enforced_by, "assert_changelog_entry_for_contract_changes")
        self.assertTrue(hasattr(loop, req.enforced_by))

    def test_finding_when_enumeration_has_no_matching_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text(
                "## [Unreleased]\n\n### Added\n"
                "- unrelated change (FEAT-9999/T01)\n"
            )
            fdir = root / "feature"
            fdir.mkdir()
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n"
                "## Consumer-visible contract changes\n\n"
                "1. **New CLI flag `--foo`.** Additive, no removal.\n\n"
                "## Cost analysis\n\nAll cheap.\n"
            )
            wu = _make_wu(file=fdir / "WU-close.md", wu_id="FEAT-2026-9999/G1-CLOSE")
            ok, reason = loop.assert_changelog_entry_for_contract_changes(
                wu, fdir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_changelog_entry_for_contract_changes", reason)
            self.assertIn("FEAT-2026-9999", reason)

            req = next(
                r for r in CLOSING_REQUIREMENTS["close"] if r.id == "close-k"
            )
            ctx = lc.ClosingContext(
                feature_dir=fdir, repo_root=root, plan_fm={}, gates=[],
                wu_id="FEAT-2026-9999/G1-CLOSE", wu_type="close", gate_num=1,
                wfm={"verdict": "met"}, wbody="",
            )
            lint_ok, lint_reason = lc._check_changelog_entry_for_contract_changes(req, ctx)
            self.assertFalse(lint_ok)
            self.assertIn("FEAT-2026-9999", lint_reason)

    def test_no_finding_when_enumeration_is_na(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text("## [Unreleased]\n\n### Added\n\n")
            fdir = root / "feature"
            fdir.mkdir()
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n"
                "## Consumer-visible contract changes\n\n"
                "`n/a — no consumer-visible contract change`\n\n"
                "## Cost analysis\n\nAll cheap.\n"
            )
            wu = _make_wu(file=fdir / "WU-close.md", wu_id="FEAT-2026-9999/G1-CLOSE")
            ok, reason = loop.assert_changelog_entry_for_contract_changes(
                wu, fdir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, reason)

            req = next(
                r for r in CLOSING_REQUIREMENTS["close"] if r.id == "close-k"
            )
            ctx = lc.ClosingContext(
                feature_dir=fdir, repo_root=root, plan_fm={}, gates=[],
                wu_id="FEAT-2026-9999/G1-CLOSE", wu_type="close", gate_num=1,
                wfm={"verdict": "met"}, wbody="",
            )
            lint_ok, lint_reason = lc._check_changelog_entry_for_contract_changes(req, ctx)
            self.assertTrue(lint_ok, lint_reason)

    def test_finding_clears_once_a_matching_entry_lands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CHANGELOG.md").write_text(
                "## [Unreleased]\n\n### Added\n"
                "- new CLI flag --foo (FEAT-2026-9999/G1-CLOSE)\n"
            )
            fdir = root / "feature"
            fdir.mkdir()
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n"
                "## Consumer-visible contract changes\n\n"
                "1. **New CLI flag `--foo`.** Additive, no removal.\n\n"
                "## Cost analysis\n\nAll cheap.\n"
            )
            wu = _make_wu(file=fdir / "WU-close.md", wu_id="FEAT-2026-9999/G1-CLOSE")
            ok, reason = loop.assert_changelog_entry_for_contract_changes(
                wu, fdir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, reason)

    # -- criterion 6: no backfill over already-`done` features --

    def test_no_finding_for_any_already_done_feature(self):
        checked = 0
        for fdir in sorted(FEATURES_DIR.iterdir()):
            if not fdir.is_dir() or not (fdir / "PLAN.md").is_file():
                continue
            plan_fm, _ = lc.read_frontmatter(fdir / "PLAN.md")
            if plan_fm.get("status") != "done":
                continue
            checked += 1
            # Scoped to close-k: an already-done feature may carry unrelated,
            # pre-existing lint debt (e.g. a stale plan-next gap, or even a
            # WU file lint_closing can't parse) that is not this WU's
            # concern. What must never happen is close-k itself re-flagging
            # a close that predates it — holding PLAN.md's satisfiability
            # answer (no backfill) rather than restating it.
            try:
                findings, notes = lc.lint_closing(fdir)
            except _miniyaml.MiniYAMLError:
                continue
            close_k_findings = [f for f in findings if f.startswith("close-k:")]
            self.assertEqual(
                close_k_findings, [],
                f"{fdir.name}: already-done feature produced a close-k finding "
                "— close-k must never re-flag a feature whose close predates it",
            )
        self.assertGreater(checked, 0, "expected at least one already-done feature")


if __name__ == "__main__":
    unittest.main()
