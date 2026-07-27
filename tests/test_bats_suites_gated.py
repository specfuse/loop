#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every tests/*.bats suite must be wired into a verification.yml gate (#257).

A bats suite that exists, is wired to nothing, and drifts red is worse than no
suite at all: it reads as coverage in the tree while asserting nothing in CI.
Two suites had already reached that state before anyone noticed —
``init_skills_idempotent.bats`` (silently red until #121 gated it) and
``init_leak_exclusion.bats`` (silently red until #257 deleted it as stale).
Both were found by hand, months late.

The reconciliation the issue asked for is only durable if something enforces
it, so this test is the enforcement: it diffs ``tests/*.bats`` against the
``bats`` commands in ``.specfuse/verification.yml`` and fails on a suite in
neither list. Adding a suite without a gate now fails the ``tests`` gate on the
very first run, which is the moment it is cheapest to fix.

Deliberately not gating a suite stays possible — add it to
``_INTENTIONALLY_UNGATED`` with the reason inline. The point is that the
omission becomes a recorded decision instead of an accident.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
VERIFICATION_YML = REPO_ROOT / ".specfuse" / "verification.yml"

# Suite basename -> why it is deliberately not gated. Empty by design: as of
# #257 every suite is gated. An entry here is a decision, not a backlog item.
_INTENTIONALLY_UNGATED: dict[str, str] = {}

# `bats tests/<name>.bats` inside a gate command, however the YAML quotes it.
_BATS_CMD_RE = re.compile(r"bats\s+tests/([A-Za-z0-9_.-]+\.bats)")


def _suites_on_disk() -> set[str]:
    return {p.name for p in TESTS_DIR.glob("*.bats")}


def _suites_gated() -> set[str]:
    return set(_BATS_CMD_RE.findall(VERIFICATION_YML.read_text()))


class TestBatsSuitesGated(unittest.TestCase):

    def test_every_bats_suite_is_gated(self):
        """No suite exists on disk without a verification.yml gate running it."""
        ungated = _suites_on_disk() - _suites_gated() - set(_INTENTIONALLY_UNGATED)
        self.assertEqual(
            ungated, set(),
            f"bats suite(s) present in tests/ but not run by any "
            f"verification.yml gate: {sorted(ungated)}. Add a gate entry, or "
            f"record the suite in _INTENTIONALLY_UNGATED with the reason. An "
            f"ungated suite asserts nothing in CI while reading as coverage.")

    def test_every_gate_points_at_a_suite_that_exists(self):
        """The reverse drift: a gate naming a suite that was renamed or deleted."""
        missing = _suites_gated() - _suites_on_disk()
        self.assertEqual(
            missing, set(),
            f"verification.yml gate(s) reference bats suite(s) that do not "
            f"exist: {sorted(missing)}. The gate would fail on every run.")

    def test_intentionally_ungated_entries_carry_a_reason(self):
        """An opt-out is only a decision if it says why."""
        for name, reason in _INTENTIONALLY_UNGATED.items():
            self.assertTrue(
                reason and reason.strip(),
                f"_INTENTIONALLY_UNGATED[{name!r}] must carry a non-empty "
                f"reason explaining why the suite is not gated")

    def test_intentionally_ungated_entries_exist_on_disk(self):
        """A stale opt-out for a deleted suite is drift of its own."""
        stale = set(_INTENTIONALLY_UNGATED) - _suites_on_disk()
        self.assertEqual(
            stale, set(),
            f"_INTENTIONALLY_UNGATED names suite(s) not present in tests/: "
            f"{sorted(stale)}. Remove the entry.")


if __name__ == "__main__":
    unittest.main()
