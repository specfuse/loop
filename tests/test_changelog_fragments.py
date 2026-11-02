#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature oracle for FEAT-LOOP-2026-0249 gate 1 — one class per Definition-of-done clause.

Temp git repositories driven through the real writer. Clause 1 and clause 5's
writer half are implemented by T01; the rest are skipped naming their owner.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT, load_loop
from tests.test_closing_deliverable_guard import DUMMY_HEAD, _make_wu

from specfuse.loop import lint_closing as lc
from specfuse.loop.changelog import parse_changelog
from specfuse.loop.closing_requirements import CLOSING_REQUIREMENTS

loop = load_loop()

_SEED = "# Changelog\n\n## [Unreleased]\n\n## [0.1.0+umbrella.0.1.0] - 2026-01-01\n\n### Added\n\n- first (#1)\n"
_GIT = ("git", "-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@example.com")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*_GIT, *args], cwd=repo, capture_output=True, text=True, check=False
    )


def _add(repo: Path, *, trace: str, summary: str, entry_class: str = "added"):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [
            sys.executable, "-m", "specfuse.loop.changelog_fragments",
            "--repo", str(repo), "add",
            "--class", entry_class, "--trace", trace, "--summary", summary,
        ],
        capture_output=True, text=True, env=env, check=False,
    )


def _init_repo(root: Path, mode: str | None) -> None:
    assert _git(root, "init", "-q", "-b", "main").returncode == 0
    (root / "CHANGELOG.md").write_text(_SEED, encoding="utf-8")
    if mode is not None:
        (root / ".specfuse").mkdir()
        (root / ".specfuse" / "layout.yml").write_text(
            f"changelog:\n  mode: {mode}\n", encoding="utf-8"
        )
    _git(root, "add", "-A")
    assert _git(root, "commit", "-q", "-m", "init").returncode == 0


def _two_branch_merge(root: Path, mode: str | None) -> subprocess.CompletedProcess:
    _init_repo(root, mode)
    for name, trace, summary in (("a", "#101", "alpha change"), ("b", "#102", "beta change")):
        assert _git(root, "checkout", "-q", "-b", name, "main").returncode == 0
        done = _add(root, trace=trace, summary=summary)
        assert done.returncode == 0, done.stderr
        _git(root, "add", "-A")
        assert _git(root, "commit", "-q", "-m", name).returncode == 0
    assert _git(root, "checkout", "-q", "main").returncode == 0
    assert _git(root, "merge", "-q", "--no-edit", "a").returncode == 0
    return _git(root, "merge", "--no-edit", "b")


class TestClause1ConcurrentPrsDoNotConflict(unittest.TestCase):
    def test_fragments_mode_second_merge_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            merged = _two_branch_merge(root, "fragments")
            self.assertEqual(merged.returncode, 0, merged.stdout + merged.stderr)
            self.assertEqual(
                sorted(p.name for p in (root / "changelog.d").iterdir()),
                ["101-alpha-change.md", "102-beta-change.md"],
            )

    def test_single_mode_control_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            merged = _two_branch_merge(Path(tmp), "single")
            self.assertNotEqual(merged.returncode, 0, "control: single mode must conflict")

    def test_add_refuses_bad_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root, "fragments")
            self.assertNotEqual(_add(root, trace="#1", summary="x", entry_class="nope").returncode, 0)
            self.assertNotEqual(_add(root, trace="not-a-trace", summary="x").returncode, 0)
            self.assertNotEqual(_add(root, trace="#1", summary="two\nlines").returncode, 0)
            self.assertEqual(_add(root, trace="#1", summary="same").returncode, 0)
            self.assertNotEqual(_add(root, trace="#1", summary="same").returncode, 0)


_FEATURE = "FEAT-2026-9999"
_RETRO = (
    "# Retrospective\n\n## Consumer-visible contract changes\n\n"
    "1. **New CLI flag `--foo`.** Additive.\n\n## Cost analysis\n\nCheap.\n"
)


class TestClause2GuardsReadFragments(unittest.TestCase):
    """close-k, `lint --closing` and the auto-close guard all read one helper."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.fdir = self.root / "feature"
        self.fdir.mkdir()
        (self.fdir / "RETROSPECTIVE.md").write_text(_RETRO, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _fragment(self, name: str, text: str) -> None:
        (self.root / "changelog.d").mkdir(exist_ok=True)
        (self.root / "changelog.d" / name).write_text(text, encoding="utf-8")

    def _good(self, trace: str = _FEATURE) -> None:
        self._fragment(
            f"{trace.replace('/', '-')}-entry.md",
            f"---\nclass: added\ntrace: {trace}\n---\nA new flag.\n",
        )

    def _verdicts(self) -> dict:
        wu = _make_wu(file=self.fdir / "WU-close.md", wu_id=f"{_FEATURE}/G1-CLOSE")
        close_k, close_k_reason = loop.assert_changelog_entry_for_contract_changes(
            wu, self.fdir, self.root, DUMMY_HEAD
        )
        req = next(r for r in CLOSING_REQUIREMENTS["close"] if r.id == "close-k")
        ctx = lc.ClosingContext(
            feature_dir=self.fdir, repo_root=self.root, plan_fm={}, gates=[],
            wu_id=f"{_FEATURE}/G1-CLOSE", wu_type="close", gate_num=1,
            wfm={"verdict": "met"}, wbody="",
        )
        lint, lint_reason = lc._check_changelog_entry_for_contract_changes(req, ctx)
        return {
            "close-k": close_k,
            "lint --closing": lint,
            "auto-close guard": loop._unreleased_has_entry_for(self.root, _FEATURE),
            "reasons": (close_k_reason, lint_reason),
        }

    def _assert_all(self, expected: bool) -> None:
        verdicts = self._verdicts()
        reasons = verdicts.pop("reasons")
        for guard, got in verdicts.items():
            with self.subTest(guard=guard):
                self.assertEqual(got, expected, reasons)

    def test_fragment_only_without_changelog_md_passes_every_guard(self):
        self._good()
        self._assert_all(True)

    def test_fragment_for_a_sub_wu_of_the_feature_counts(self):
        self._good(f"{_FEATURE}/T01")
        self._assert_all(True)

    def test_fragment_alongside_changelog_md_passes_every_guard(self):
        (self.root / "CHANGELOG.md").write_text(_SEED, encoding="utf-8")
        self._good()
        self._assert_all(True)

    def test_changelog_md_entry_still_passes_in_every_guard(self):
        (self.root / "CHANGELOG.md").write_text(
            f"## [Unreleased]\n\n### Added\n\n- a flag ({_FEATURE})\n", encoding="utf-8"
        )
        self._assert_all(True)

    def test_no_entry_in_either_form_fails_every_guard(self):
        (self.root / "CHANGELOG.md").write_text(_SEED, encoding="utf-8")
        self._fragment(
            "other.md", "---\nclass: added\ntrace: FEAT-2026-1111\n---\nOther.\n"
        )
        self._assert_all(False)

    def test_neither_form_keeps_the_does_not_exist_message(self):
        verdicts = self._verdicts()
        self.assertFalse(verdicts["close-k"])
        for reason in verdicts["reasons"]:
            self.assertIn("does not exist", reason)

    def test_malformed_fragments_do_not_count(self):
        bad = {
            "no-frontmatter.md": "A new flag.\n",
            "unclosed.md": f"---\nclass: added\ntrace: {_FEATURE}\nA new flag.\n",
            "bad-class.md": f"---\nclass: nope\ntrace: {_FEATURE}\n---\nA flag.\n",
            "bad-trace.md": "---\nclass: added\ntrace: oops\n---\nA flag.\n",
            "empty-body.md": f"---\nclass: added\ntrace: {_FEATURE}\n---\n",
            "two-lines.md": f"---\nclass: added\ntrace: {_FEATURE}\n---\none\ntwo\n",
        }
        for name, text in bad.items():
            self._fragment(name, text)
        self._assert_all(False)

    def test_refusals_name_both_locations(self):
        (self.root / "CHANGELOG.md").write_text(_SEED, encoding="utf-8")
        for reason in self._verdicts()["reasons"]:
            self.assertIn("CHANGELOG.md", reason)
            self.assertIn("changelog.d/", reason)
        description = next(
            r for r in CLOSING_REQUIREMENTS["close"] if r.id == "close-k"
        ).description
        self.assertIn("CHANGELOG.md", description)
        self.assertIn("changelog.d/", description)


def _bump_version():
    import importlib.util

    path = REPO_ROOT / "scripts" / "bump_version.py"
    spec = importlib.util.spec_from_file_location("bump_version_oracle", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _release_tree(root: Path, mode: str | None) -> None:
    (root / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n', encoding="utf-8")
    (root / "specfuse" / "loop" / "data").mkdir(parents=True)
    (root / "specfuse" / "loop" / "loop.py").write_text('DRIVER_VERSION = "0.1.0"\n', encoding="utf-8")
    (root / ".specfuse").mkdir(exist_ok=True)
    (root / ".specfuse" / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (root / "specfuse" / "loop" / "data" / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(_SEED, encoding="utf-8")
    if mode is not None:
        (root / ".specfuse" / "layout.yml").write_text(
            f"changelog:\n  mode: {mode}\n", encoding="utf-8"
        )


class TestClause3CollateAtRelease(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.bump = _bump_version()

    def _fragments(self, mode: str = "fragments") -> None:
        _release_tree(self.root, mode)
        for trace, summary, cls in (
            ("#102", "beta change", "added"),
            ("#101", "alpha change", "fixed"),
            ("#103", "gamma change", "added"),
        ):
            done = _add(self.root, trace=trace, summary=summary, entry_class=cls)
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_release_folds_every_fragment_and_removes_them(self):
        self._fragments()
        self.bump.release(self.root, "0.2.0", "0.2.0", date="2026-11-02")
        result = parse_changelog((self.root / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertTrue(result.ok, result.findings)
        released = [s for s in result.sections if not s.is_unreleased]
        self.assertEqual(
            sorted(e.trace for e in released[0].entries if e.summary.endswith("change")),
            ["#101", "#102", "#103"],
        )
        self.assertEqual(result.unreleased().entries, [])
        self.assertEqual(list((self.root / "changelog.d").glob("*.md")) if (self.root / "changelog.d").exists() else [], [])

    def test_collation_runs_whatever_the_mode(self):
        self._fragments("fragments")
        (self.root / ".specfuse" / "layout.yml").write_text(
            "changelog:\n  mode: single\n", encoding="utf-8"
        )
        self.bump.release(self.root, "0.2.0", "0.2.0", date="2026-11-02")
        text = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("alpha change (#101)", text)
        self.assertFalse((self.root / "changelog.d").exists())

    def test_output_is_deterministic_in_filename_order(self):
        self._fragments()
        self.bump.release(self.root, "0.2.0", "0.2.0", date="2026-11-02")
        text = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertLess(text.index("beta change"), text.index("gamma change"))

    def test_invalid_fragment_refuses_naming_it_and_touches_nothing(self):
        self._fragments()
        (self.root / "changelog.d" / "bad.md").write_text("no frontmatter\n", encoding="utf-8")
        before = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            self.bump.release(self.root, "0.2.0", "0.2.0", date="2026-11-02")
        self.assertIn("bad.md", str(ctx.exception))
        self.assertEqual((self.root / "CHANGELOG.md").read_text(encoding="utf-8"), before)
        self.assertEqual(len(list((self.root / "changelog.d").glob("*.md"))), 4)
        self.assertIn('"0.1.0"', (self.root / "pyproject.toml").read_text(encoding="utf-8"))

    def test_double_stamp_refusal_leaves_every_fragment(self):
        self._fragments()
        self.bump.release(self.root, "0.2.0", "0.2.0", date="2026-11-02")
        self._fragments_again = _add(self.root, trace="#104", summary="delta change")
        self.assertEqual(self._fragments_again.returncode, 0)
        before = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            self.bump.release(self.root, "0.2.0", "0.2.0", date="2026-11-03")
        self.assertEqual(len(list((self.root / "changelog.d").glob("*.md"))), 1)
        self.assertEqual((self.root / "CHANGELOG.md").read_text(encoding="utf-8"), before)

    def test_collate_subcommand(self):
        self._fragments()
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        done = subprocess.run(
            [sys.executable, "-m", "specfuse.loop.changelog_fragments",
             "--repo", str(self.root), "collate"],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse((self.root / "changelog.d").exists())
        result = parse_changelog((self.root / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertEqual(len(result.unreleased().entries), 3)


@unittest.skip("T04 owns clause 4: the check gate")
class TestClause4CheckGate(unittest.TestCase):
    def test_pending(self):
        pass


class TestClause5NoModeKeyBehavesAsBefore(unittest.TestCase):
    def test_add_without_mode_edits_changelog_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root, None)
            done = _add(root, trace="#7", summary="plain entry")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertFalse((root / "changelog.d").exists())
            result = parse_changelog((root / "CHANGELOG.md").read_text(encoding="utf-8"))
            self.assertTrue(result.ok, result.findings)
            self.assertEqual([e.trace for e in result.unreleased().entries], ["#7"])

    def test_release_without_fragments_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _release_tree(root, None)
            bump = _bump_version()
            expected = bump._changelog.stamp_release(
                _SEED, version="0.2.0", date="2026-11-02", umbrella_version="0.2.0"
            )
            bump.release(root, "0.2.0", "0.2.0", date="2026-11-02")
            self.assertEqual((root / "CHANGELOG.md").read_text(encoding="utf-8"), expected)
            self.assertFalse((root / "changelog.d").exists())


if __name__ == "__main__":
    unittest.main()
