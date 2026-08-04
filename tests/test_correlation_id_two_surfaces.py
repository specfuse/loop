#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#581 — the two correlation-ID enforcement surfaces must stay in step.

`lint_plan.CORRELATION_ID_RE` governs PLAN.md graphs and WU frontmatter; the
driver-local registry's `closing_names` widens the vendored event envelope.
A `<NAME>` added to one and not the other produces IDs the linter accepts and
envelope validation rejects.

This lived as prose in `rules/correlation-ids.md` until the sync reverted it:
that file is vendored from the methodology core, so a loop-local addition to
it does not survive `sync-scaffold.sh`. The invariant is asserted here and
noted at both change sites instead.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from specfuse.loop.lint_plan import CORRELATION_ID_RE

REPO_ROOT = Path(__file__).resolve().parents[1]
_REGISTRY = REPO_ROOT / "specfuse" / "loop" / "data" / "schemas" / "driver-event.schema.json"


def _registry_closing_names() -> list[str]:
    raw = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    return raw["correlation_id"]["closing_names"]


def _regex_closing_names() -> set[str]:
    """The `<NAME>` alternatives the linter's pattern admits after `G<n>-`."""
    found: set[str] = set()
    for group in re.findall(r"G\\d\+-\(([A-Z|\-]+)\)", CORRELATION_ID_RE.pattern):
        found.update(group.split("|"))
    return found


class TestCorrelationIdTwoSurfaces(unittest.TestCase):
    def test_regex_names_were_extracted(self):
        """Guard the guard: an extraction returning nothing would pass vacuously."""
        self.assertTrue(_regex_closing_names(), "extracted no names from the pattern")

    def test_every_regex_closing_name_is_in_the_registry(self):
        missing = _regex_closing_names() - set(_registry_closing_names())
        self.assertEqual(
            missing, set(),
            "lint_plan.CORRELATION_ID_RE accepts closing names the driver-event "
            "registry's closing_names omits, so envelope validation will reject "
            "IDs the linter passed",
        )

    def test_every_registry_closing_name_is_in_the_regex(self):
        missing = set(_registry_closing_names()) - _regex_closing_names()
        self.assertEqual(
            missing, set(),
            "the driver-event registry admits closing names lint_plan rejects",
        )

    def test_both_change_sites_carry_the_pointer(self):
        """The note must sit where the change is made, not in a vendored rule."""
        lint = (REPO_ROOT / "specfuse" / "loop" / "lint_plan.py").read_text()
        validate = (REPO_ROOT / "specfuse" / "loop" / "validate_event.py").read_text()
        self.assertIn("closing_names", lint)
        self.assertIn("CORRELATION_ID_RE", validate)

    def test_vendored_rule_carries_no_loop_local_block(self):
        """`rules/correlation-ids.md` is core-owned; loop-local edits get reverted."""
        rule = (REPO_ROOT / ".specfuse" / "rules" / "correlation-ids.md").read_text()
        self.assertNotIn("driver-event.schema.json", rule)


if __name__ == "__main__":
    unittest.main()
