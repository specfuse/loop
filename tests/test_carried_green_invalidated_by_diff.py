#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A carried green is invalidated when the gate diff touches a path it covers
(FEAT-2026-0117/T02).

`derive_criterion_covers` seeds each criteria entry with the paths its proof
depends on; `invalidate_carried_entries` resets a carried entry whose
`covers` intersects the gate diff since `proved_at_sha` back to `unverified`
with `invalidated_by` naming the touched path. A carry-forward that survives
a code change to the thing it measured would be worse than no carry-forward
at all (#3313).
"""

from __future__ import annotations

import os
import subprocess
import types
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()
criteria_state = loop.criteria_state

_T01_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.**\n\n"
    "1. the first narrow thing works\n"
    "2. the second narrow thing works\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
_CLOSE_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


class TestDeriveCriterionCovers(unittest.TestCase):

    def test_unittest_oracle_maps_dotted_module_to_test_file(self):
        wu = types.SimpleNamespace(produces=["src/impl.py"])
        covers = criteria_state.derive_criterion_covers(
            wu, "python3 -m unittest tests.test_narrow_one -v -b")
        self.assertEqual(covers, ["src/impl.py", "tests/test_narrow_one.py"])

    def test_unittest_oracle_with_no_produces(self):
        wu = types.SimpleNamespace(produces=[])
        covers = criteria_state.derive_criterion_covers(
            wu, "python3 -m unittest tests.test_narrow_two -v -b")
        self.assertEqual(covers, ["tests/test_narrow_two.py"])

    def test_maven_dtest_oracle_resolves_existing_class_file(self):
        with integration_workspace() as root:
            os.chdir(root)
            test_dir = root / "src/test/java/com/example"
            test_dir.mkdir(parents=True)
            (test_dir / "FooBarTest.java").write_text("class FooBarTest {}\n")
            wu = types.SimpleNamespace(produces=[])
            covers = criteria_state.derive_criterion_covers(
                wu, "mvn test -Dtest=FooBarTest")
            self.assertEqual(
                covers, ["src/test/java/com/example/FooBarTest.java"])

    def test_maven_dtest_oracle_with_no_matching_file(self):
        with integration_workspace() as root:
            os.chdir(root)
            wu = types.SimpleNamespace(produces=["src/impl.py"])
            covers = criteria_state.derive_criterion_covers(
                wu, "mvn test -Dtest=NoSuchTest")
            self.assertEqual(covers, ["src/impl.py"])

    def test_no_oracle_yet_returns_only_produces(self):
        wu = types.SimpleNamespace(produces=["src/impl.py", "src/other.py"])
        covers = criteria_state.derive_criterion_covers(wu, None)
        self.assertEqual(covers, ["src/impl.py", "src/other.py"])


class TestEmptyCoversNeverCarried(unittest.TestCase):
    """A `carried_from_attempt` entry with an empty `covers` is never carried:
    `invalidate_carried_entries` resets it, and the reset lands it in
    `build_reverification_worklist`'s `reverify` — same as any other
    `unverified` entry, no special-case check needed there."""

    def test_carried_entry_with_empty_covers_ends_up_in_reverify(self):
        carried_no_covers = criteria_state.CriterionStateEntry(
            criterion_id="T01#1",
            criterion="the narrow thing works",
            oracle="python3 -m unittest tests.test_narrow_one",
            kind="narrow",
            state="pass",
            proved_at_sha="abc123",
            attempt="1",
            carried_from_attempt="1",
            covers=[],
        )
        refreshed = loop.invalidate_carried_entries([carried_no_covers], set())
        worklist = criteria_state.build_reverification_worklist(
            refreshed, current_attempt="2")
        self.assertEqual(refreshed[0].state, "unverified")
        self.assertIsNone(refreshed[0].carried_from_attempt)
        self.assertEqual(
            [e.criterion_id for e in worklist.reverify], ["T01#1"])
        self.assertEqual(worklist.carry_forward, [])

    def test_carried_entry_with_covers_is_carried(self):
        entry = criteria_state.CriterionStateEntry(
            criterion_id="T01#1",
            criterion="the narrow thing works",
            oracle="python3 -m unittest tests.test_narrow_one",
            kind="narrow",
            state="pass",
            proved_at_sha="abc123",
            attempt="1",
            carried_from_attempt="1",
            covers=["tests/test_narrow_one.py"],
        )
        refreshed = loop.invalidate_carried_entries([entry], set())
        worklist = criteria_state.build_reverification_worklist(
            refreshed, current_attempt="2")
        self.assertIn(entry, worklist.carry_forward)


class TestInvalidateCarriedEntries(unittest.TestCase):
    """Direct, non-e2e coverage of `loop.invalidate_carried_entries`."""

    def test_touched_covered_path_invalidates_carried_entry(self):
        touched = {"tests/test_narrow_one.py"}
        carried = criteria_state.CriterionStateEntry(
            criterion_id="T01#1", criterion="c1", oracle="python3 -m unittest tests.test_narrow_one",
            kind="narrow", state="pass", proved_at_sha="sha1", attempt="1",
            carried_from_attempt="1", covers=["tests/test_narrow_one.py"],
        )
        untouched = criteria_state.CriterionStateEntry(
            criterion_id="T01#2", criterion="c2", oracle="python3 -m unittest tests.test_narrow_two",
            kind="narrow", state="pass", proved_at_sha="sha1", attempt="1",
            carried_from_attempt="1", covers=["tests/test_narrow_two.py"],
        )
        refreshed = loop.invalidate_carried_entries([carried, untouched], touched)

        invalidated, kept = refreshed
        self.assertEqual(invalidated.state, "unverified")
        self.assertEqual(invalidated.invalidated_by, "tests/test_narrow_one.py")
        self.assertIsNone(invalidated.carried_from_attempt)
        self.assertIsNone(invalidated.oracle)

        self.assertEqual(kept.state, "pass")
        self.assertEqual(kept.carried_from_attempt, "1")
        self.assertIsNone(kept.invalidated_by)

    def test_carried_entry_with_no_covers_is_reset_with_no_named_path(self):
        entry = criteria_state.CriterionStateEntry(
            criterion_id="T01#3", criterion="c3", oracle="python3 -m unittest tests.test_narrow_three",
            kind="narrow", state="pass", proved_at_sha="sha1", attempt="1",
            carried_from_attempt="1", covers=[],
        )
        refreshed = loop.invalidate_carried_entries(
            [entry], {"tests/test_narrow_three.py"})
        self.assertEqual(refreshed[0].state, "unverified")
        self.assertIsNone(refreshed[0].carried_from_attempt)
        self.assertIsNone(refreshed[0].invalidated_by)

    def test_entry_not_carried_is_left_alone_even_if_covered_path_touched(self):
        entry = criteria_state.CriterionStateEntry(
            criterion_id="T01#4", criterion="c4", oracle="python3 -m unittest tests.test_narrow_four",
            kind="narrow", state="pass", proved_at_sha="sha1", attempt="1",
            covers=["tests/test_narrow_four.py"],
        )
        refreshed = loop.invalidate_carried_entries(
            [entry], {"tests/test_narrow_four.py"})
        self.assertEqual(refreshed, [entry])


def _write_feature(root: Path, feature_id: str, slug: str) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: feat/{slug}\nroadmap_goal: test\nstatus: active\n"
        f"judge_disabled: true\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n---\n\n# T01{_T01_BODY}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close-intermediate\nmodel: opus\n"
        f"status: pending\nattempts: 0\nauto_close_disabled: true\n"
        f"---\n\n# Close{_CLOSE_BODY}"
    )
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests/test_narrow_one.py").write_text("VALUE = 1\n")
    (root / "tests/test_narrow_two.py").write_text("VALUE = 2\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


def _head_sha(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


class TestCarriedGreenInvalidatedByCoveredPathDiffE2E(unittest.TestCase):

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

    def _run_first_close_to_pass(self, root, fdir, close_id, feature_id):
        criteria_path = fdir / "GATE-01-CRITERIA.md"
        close_calls = {"n": 0}

        def fake_dispatch(wu, failure_note, ct=True):
            if wu.wu_id.endswith("/T01"):
                Path("src").mkdir(exist_ok=True)
                Path("src/impl.py").write_text("VALUE = 1\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - src/impl.py\n```\n")
            close_calls["n"] += 1
            if close_calls["n"] == 1:
                return "```result\nstatus: complete\n```\n"
            sha = _head_sha(root)
            attempt = wu.attempts
            criteria_path.write_text(
                "# Gate 1 — per-criterion state\n\n"
                f"Written by `{close_id}`.\n\n"
                "### T01#1\n"
                "- **criterion:** the first narrow thing works\n"
                "- **oracle:** `python3 -m unittest tests.test_narrow_one`\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                f"- **proved_at_sha:** `{sha}`\n"
                f"- **attempt:** `{attempt}`\n\n"
                "### T01#2\n"
                "- **criterion:** the second narrow thing works\n"
                "- **oracle:** `python3 -m unittest tests.test_narrow_two`\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                f"- **proved_at_sha:** `{sha}`\n"
                f"- **attempt:** `{attempt}`\n"
            )
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Gate 1\n\n## Measurements\n\nn/a\n\n"
                "nothing generalizes from this gate.\n"
            )
            return (
                "```result\nstatus: complete\nfiles_changed:\n"
                f"  - {criteria_path.relative_to(root)}\n"
                f"  - {(fdir / 'RETROSPECTIVE.md').relative_to(root)}\n```\n"
            )

        def fake_verify(wu, fd, cfg=None):
            if wu.wu_id.endswith("/G1-CLOSE") and close_calls["n"] < 2:
                return (False, "### tests: FAIL\nFAIL: test_boom")
            return (True, "(stub)")

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", fake_verify)

        loop.run(feature_id, dry_run=False)

        fm, _ = loop.read_frontmatter(fdir / "WU-close.md")
        self.assertEqual(fm.get("status"), "done")

    def _edit_covered_path_and_commit(self, root: Path):
        (root / "tests/test_narrow_one.py").write_text("VALUE = 999\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                         "edit a covered path"], check=True)

    def _rearm(self, root: Path, fdir: Path):
        loop.write_frontmatter_field(fdir / "WU-close.md", "status", "pending")
        loop.write_frontmatter_field(fdir / "WU-close.md", "attempts", 0)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                         "chore: re-arm close"], check=True)

    def _dispatch_and_capture_second_close_prompt(self, root, fdir, feature_id):
        captured = {}
        retro_path = fdir / "RETROSPECTIVE.md"

        def fake_dispatch(wu, failure_note, ct=True):
            if wu.wu_id.endswith("/G1-CLOSE") and "body" not in captured:
                captured["body"] = wu.body
            retro_path.write_text(
                retro_path.read_text() + "\n(re-verified on re-arm)\n")
            return (
                "```result\nstatus: complete\nfiles_changed:\n"
                f"  - {retro_path.relative_to(root)}\n```\n"
            )

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

        loop.run(feature_id, dry_run=False)
        return captured.get("body", "")

    def test_covered_path_edit_invalidates_only_the_entry_that_covers_it(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9991"
            fdir = _write_feature(root, feature_id, "invalidate-covered")
            close_id = f"{feature_id}/G1-CLOSE"

            self._run_first_close_to_pass(root, fdir, close_id, feature_id)
            self._edit_covered_path_and_commit(root)
            self._rearm(root, fdir)

            prompt = self._dispatch_and_capture_second_close_prompt(
                root, fdir, feature_id)

            text = (fdir / "GATE-01-CRITERIA.md").read_text()
            block_one = text.split("### T01#1", 1)[1].split("### T01#2", 1)[0]
            block_two = text.split("### T01#2", 1)[1]

            self.assertIn("**state:** `unverified`", block_one)
            self.assertIn(
                "**invalidated_by:** tests/test_narrow_one.py", block_one)
            self.assertNotIn("**carried_from_attempt:**", block_one)

            self.assertIn("**state:** `pass`", block_two)
            self.assertIn("**carried_from_attempt:**", block_two)
            self.assertNotIn("**invalidated_by:**", block_two)

            self.assertIn(
                "invalidated by change to `tests/test_narrow_one.py`", prompt)
            self.assertIn("### Carried forward", prompt)
            carried_section = prompt.split("### Carried forward", 1)[1].split(
                "### Re-verify", 1)[0]
            self.assertIn("T01#2", carried_section)
            self.assertNotIn("T01#1", carried_section)


if __name__ == "__main__":
    unittest.main()
