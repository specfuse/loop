#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Rule imports must converge, not accumulate (#3332).

Four core-owned rules are written into a repo twice: by the loop into
`.specfuse/rules/` and by the umbrella into `.specfuse/methodology/rules/`.
Which path should own them is an open decision (#3332, specfuse/loop#2270) and
is deliberately NOT settled here.

What is a bug either way: `_backfill_rule_imports` matched only the
`@.specfuse/rules/` prefix, so a project whose CLAUDE.md had been pointed at
`methodology/rules/` got the `rules/` lines re-inserted on the next upgrade and
kept **both**. Every dispatched session then pays for those rules twice — the
downstream report measured 3900 words against a 2500-word cap.

`_backfill_rule_imports`' own docstring says the point of the retire/backfill
pair is that `wire_claude` "converges on `_RULES_BLOCK` instead of only ever
growing". A second path for the same rule is exactly the growth it was built to
prevent.
"""
from __future__ import annotations

import unittest

from specfuse.loop import scaffold


HEADING = "## Specfuse binding rules (read before any work-unit dispatch)\n"


def _imports(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.startswith("@")]


class MethodologyPathSatisfiesTheLoopPath(unittest.TestCase):

    def test_a_methodology_import_is_not_duplicated_by_the_rules_import(self):
        existing = (
            "# Notes\n\n" + HEADING
            + "@.specfuse/rules/result-contract.md\n"
            + "@.specfuse/methodology/rules/never-touch.md\n"
            + "@.specfuse/methodology/rules/security-boundaries.md\n"
        )
        out = _imports(scaffold._backfill_rule_imports(existing))
        for rule in ("never-touch.md", "security-boundaries.md"):
            hits = [ln for ln in out if ln.endswith("/" + rule)]
            self.assertEqual(
                1, len(hits),
                f"{rule} is imported {len(hits)} times: {hits}")

    def test_the_project_keeps_the_path_it_chose(self):
        # Convergence must not mean "rewrite the operator's choice": a repo
        # pointed at methodology/rules/ stays pointed there.
        existing = (
            "# Notes\n\n" + HEADING
            + "@.specfuse/rules/result-contract.md\n"
            + "@.specfuse/methodology/rules/never-touch.md\n"
        )
        out = _imports(scaffold._backfill_rule_imports(existing))
        self.assertIn("@.specfuse/methodology/rules/never-touch.md", out)
        self.assertNotIn("@.specfuse/rules/never-touch.md", out)

    def test_a_project_on_the_loop_paths_is_unchanged(self):
        # The control, and the common case: nothing about the default wiring
        # moves. Without this, "never insert anything" would pass the rest.
        existing = (
            "# Notes\n\n" + HEADING
            + "@.specfuse/rules/result-contract.md\n"
            + "@.specfuse/rules/never-touch.md\n"
            + "@.specfuse/rules/security-boundaries.md\n"
        )
        self.assertEqual(existing, scaffold._backfill_rule_imports(existing))

    def test_a_genuinely_missing_rule_is_still_backfilled(self):
        # The other control: convergence must not break the reason backfill
        # exists — a rule absent under BOTH paths is still inserted, or a
        # binding rule silently stops being loaded.
        existing = (
            "# Notes\n\n" + HEADING
            + "@.specfuse/rules/result-contract.md\n"
        )
        out = _imports(scaffold._backfill_rule_imports(existing))
        self.assertIn("@.specfuse/rules/never-touch.md", out)
        self.assertIn("@.specfuse/rules/security-boundaries.md", out)


if __name__ == "__main__":
    unittest.main()
