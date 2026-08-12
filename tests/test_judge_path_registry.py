# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`JUDGE_PATHS` is an allowlist now, so something must keep it complete.

The blanket `specfuse/loop/` prefix it replaced had one real virtue: it could
not go stale. An allowlist stops protecting the moment someone adds a decision
module and forgets to register it, and nothing at runtime would ever say so --
the guardrail would simply return eligible on a PR editing the merge predicate.

These tests are that missing property. Every module under `specfuse/loop/` and
every top-level entry under its package data must appear in exactly one of the
two registries, so a new file cannot escape classification by omission. The
same shape `DEPENDENCY_MANIFEST_COVERED` / `_NAMED_UNCOVERED` already uses.
"""

from __future__ import annotations

import sys
import unittest

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop import arm_eval, bug_lane

_LOOP_DIR = REPO_ROOT / "specfuse" / "loop"
_DATA_DIR = _LOOP_DIR / "data"


def _module_names() -> set:
    return {p.name for p in _LOOP_DIR.glob("*.py")}


def _registered_judge_module_names() -> set:
    return {p.rsplit("/", 1)[-1] for p in arm_eval.JUDGE_MODULES}


class TestEveryModuleIsClassified(unittest.TestCase):
    def test_no_module_is_unclassified(self):
        classified = _registered_judge_module_names() | set(
            arm_eval.NON_JUDGE_MODULES
        )
        unclassified = _module_names() - classified

        self.assertEqual(
            unclassified,
            set(),
            "new module(s) under specfuse/loop/ are in neither JUDGE_MODULES "
            "nor NON_JUDGE_MODULES. Classify each one: does a merge, arm or "
            "close verdict -- or the evidence a verdict reads -- change "
            "because of an edit to it?",
        )

    def test_no_registry_entry_names_a_module_that_does_not_exist(self):
        registered = _registered_judge_module_names() | set(
            arm_eval.NON_JUDGE_MODULES
        )
        stale = registered - _module_names()

        self.assertEqual(stale, set(), "registry names a deleted module")

    def test_a_module_is_not_in_both_registries(self):
        overlap = _registered_judge_module_names() & set(arm_eval.NON_JUDGE_MODULES)

        self.assertEqual(overlap, set())

    def test_every_non_judge_entry_carries_a_reason(self):
        for name, reason in arm_eval.NON_JUDGE_MODULES.items():
            with self.subTest(module=name):
                self.assertTrue(reason.strip(), f"{name} has no stated reason")


class TestEveryDataEntryIsClassified(unittest.TestCase):
    def _data_entries(self) -> set:
        return {p.name for p in _DATA_DIR.iterdir()}

    def test_no_data_entry_is_unclassified(self):
        judged = {
            p.rsplit("/", 1)[-1] or p.rstrip("/").rsplit("/", 1)[-1]
            for p in arm_eval.JUDGE_DATA_PREFIXES
        }
        classified = judged | set(arm_eval.NON_JUDGE_DATA_ENTRIES)
        unclassified = self._data_entries() - classified

        self.assertEqual(
            unclassified,
            set(),
            "new package-data entr(ies) are unclassified. Package data seeds "
            "target projects, so an entry that becomes a judge surface "
            "downstream belongs in JUDGE_DATA_PREFIXES.",
        )

    def test_shipped_rules_and_workflows_are_still_judged(self):
        """These seed `.specfuse/rules/` and `.github/workflows/` downstream."""
        for expected in (
            "specfuse/loop/data/rules/",
            "specfuse/loop/data/workflows/",
            "specfuse/loop/data/schemas/",
            "specfuse/loop/data/verification.yml.example",
        ):
            self.assertIn(expected, arm_eval.JUDGE_PATHS)

    def test_shipped_documentation_is_not_judged(self):
        """The narrowing's whole point, and its one deliberate exclusion."""
        self.assertNotIn("specfuse/loop/data/docs/", arm_eval.JUDGE_PATHS)
        self.assertFalse(
            arm_eval._matches_judge_path(
                "specfuse/loop/data/docs/concepts/autonomy-stop-classes.md"
            )
        )


class TestTheDecisionModulesAreStillCovered(unittest.TestCase):
    """Spot checks with names, so a careless registry edit is loud."""

    def test_the_predicates_are_judge_paths(self):
        for module in (
            "specfuse/loop/arm_eval.py",
            "specfuse/loop/gate_eval.py",
            "specfuse/loop/bug_lane.py",
            "specfuse/loop/bug_lane_run.py",
            "specfuse/loop/loop.py",
            "specfuse/loop/agent_policy.py",
        ):
            with self.subTest(module=module):
                self.assertTrue(arm_eval._matches_judge_path(module))
                self.assertEqual(bug_lane.judge_paths_touched([module]), [module])

    def test_a_bug_fix_in_a_non_deciding_module_is_no_longer_blocked(self):
        """The case the first unattended run kept declining.

        Issue #240's fix touched `specfuse/loop/loop.py` -- a real judge, and
        still declined. Issue #795's touched `specfuse/loop/gate_eval.py`, also
        a real judge. But a fix to notification or triage code was blocked by
        the same prefix while deciding nothing, and that class is now free.
        """
        for module in (
            "specfuse/loop/notify.py",
            "specfuse/loop/triage.py",
            "specfuse/loop/changelog.py",
            "specfuse/loop/escalation.py",
        ):
            with self.subTest(module=module):
                self.assertFalse(arm_eval._matches_judge_path(module))
                self.assertEqual(bug_lane.judge_paths_touched([module]), [])

    def test_universal_surfaces_are_untouched_by_the_narrowing(self):
        for path in (
            ".specfuse/verification.yml",
            ".specfuse/hooks/",
            ".specfuse/rules/",
            ".github/workflows/",
            "pyproject.toml",
        ):
            self.assertIn(path, arm_eval.JUDGE_PATHS)

    def test_the_blanket_prefix_is_gone(self):
        self.assertNotIn("specfuse/loop/", arm_eval.JUDGE_PATHS)


if __name__ == "__main__":
    unittest.main()
