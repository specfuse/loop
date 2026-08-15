# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# #1977: /learnings-suggest clusters on the raw
# `(failure_class, failure_signature)` tuple with no filter, so records whose
# signature carries no information — a bare ``` fence being the observed case —
# form giant clusters that outrank every genuine finding. Raising `--min-wus`
# to cut the noise loses the real findings first.
#
# The derivation half of #1977 was already shipped: `parse_gate_failure_signature`
# has skipped fences, whitespace and pure-ANSI lines since #169 (2026-07-20, an
# ancestor of v0.11.0 — the version the report names). What that fix cannot do
# is unwrite history, and this skill reads history. A repo that ran a pre-#169
# driver keeps its poisoned rows forever, so the filter has to live at the
# clustering step too.
#
# Asserted here: §2 excludes non-informative signatures, defers to the driver's
# own `_is_noninformative_signature` rather than restating the rule (a second
# copy is what let the two disagree in the first place), names the exclusions
# in the run output rather than dropping them silently, and says plainly that
# the derivation bug was already fixed so a later reader does not re-file it.
#
# Byte-identity across the canonical and vendored trees is asserted generically
# by tests/test_skills_vendored_in_sync.py and is not re-asserted here.

import pathlib
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = (
    _REPO_ROOT / "plugins" / "specfuse" / "skills" / "learnings-suggest" / "SKILL.md"
)
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "learnings-suggest" / "SKILL.md"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _section_two(text: str) -> str:
    """The §2 Cluster section only — a mention anywhere in the file is not the
    same as the clustering step actually being told to filter."""
    start = text.index("## §2 Cluster")
    end = text.index("## §3", start)
    return text[start:end]


class TestClusteringExcludesNoninformativeSignatures(unittest.TestCase):
    def test_section_two_names_the_exclusion(self):
        for path in (_CANONICAL, _VENDORED):
            with self.subTest(path=path.parent.parent.name):
                body = _section_two(_read(path))
                self.assertIn("non-informative", body)

    def test_section_two_defers_to_the_drivers_predicate(self):
        """Naming the predicate, not re-listing fences/whitespace/ANSI. The
        rule already exists in `loop.py`; a second copy drifts."""
        for path in (_CANONICAL, _VENDORED):
            with self.subTest(path=path.parent.parent.name):
                body = _section_two(_read(path))
                self.assertIn("_is_noninformative_signature", body)

    def test_excluded_records_are_reported_not_silently_dropped(self):
        """A filter that hides its own effect turns one invisible problem into
        another — the operator must be able to see what was excluded."""
        for path in (_CANONICAL, _VENDORED):
            with self.subTest(path=path.parent.parent.name):
                body = _section_two(_read(path))
                self.assertRegex(body, r"(?i)report|print|surface")

    def test_the_shipped_derivation_fix_is_named(self):
        """So a reader who finds fence signatures in old data does not re-file
        the driver bug that was fixed in #169."""
        for path in (_CANONICAL, _VENDORED):
            with self.subTest(path=path.parent.parent.name):
                text = _read(path)
                self.assertIn("#169", text)

    def test_the_cluster_key_itself_is_unchanged(self):
        """The clustering key is not the defect — #1977's own words: 'the
        clustering itself is fine; it is being fed a degenerate key'."""
        for path in (_CANONICAL, _VENDORED):
            with self.subTest(path=path.parent.parent.name):
                body = _section_two(_read(path))
                self.assertIn("payload.failure_class", body)
                self.assertIn("payload.failure_signature", body)


class TestDriverPredicateStillExists(unittest.TestCase):
    """The skill now names a driver symbol. If that symbol is ever renamed,
    this test is what tells us the skill's instruction went stale."""

    def test_the_named_predicate_is_importable(self):
        from specfuse.loop.loop import _is_noninformative_signature

        self.assertTrue(_is_noninformative_signature("```"))
        self.assertTrue(_is_noninformative_signature("   "))
        self.assertTrue(_is_noninformative_signature(None))
        self.assertFalse(
            _is_noninformative_signature("Run 'mvn spotless:apply' to fix these")
        )


if __name__ == "__main__":
    unittest.main()
