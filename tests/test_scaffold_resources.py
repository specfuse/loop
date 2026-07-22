# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import unittest

from specfuse.loop.scaffold import (
    iter_scaffold_files,
    read_scaffold,
    scaffold_version,
)

_EXPECTED_RELPATHS = {
    "VERSION",
    "gitignore.snippet",
    "verification.yml.example",
    "roadmap.template.md",
    "LEARNINGS.template.md",
    "templates/GATE.template.md",
    "templates/PLAN.template.md",
    "templates/WU.template.md",
    "rules/correlation-ids.md",
    "rules/never-touch.md",
    "rules/planning-discipline.md",
    "rules/result-contract.md",
    "rules/security-boundaries.md",
    "rules/verification-discipline.md",
    "schemas/event.schema.json",
    "schemas/events/initiative_created.schema.json",
    "schemas/events/spec_validated.schema.json",
    "schemas/events/spec_issue_resolved.schema.json",
    "schemas/events/spec_issue_routed.schema.json",
    "docs/getting-started.md",
    "docs/methodology.md",
    "docs/skills.md",
    "docs/concepts/ralph-lineage.md",
    "docs/concepts/architecture-addendum-gates-and-iterative-planning.md",
}


class TestScaffoldResources(unittest.TestCase):
    def test_iter_scaffold_files_lists_all_seed(self):
        result = iter_scaffold_files()
        self.assertIsInstance(result, list)
        relpaths = {relpath for relpath, _ in result}
        self.assertEqual(relpaths, _EXPECTED_RELPATHS)
        for relpath, content in result:
            self.assertIsInstance(content, bytes)
            self.assertGreater(len(content), 0, f"{relpath} is empty")

    def test_scaffold_version_matches_canonical(self):
        import pathlib

        canonical = (
            pathlib.Path(__file__).parent.parent / ".specfuse" / "VERSION"
        ).read_text(encoding="utf-8").strip()
        self.assertEqual(scaffold_version(), canonical)

    def test_read_scaffold_returns_bytes(self):
        content = read_scaffold("VERSION")
        self.assertIsInstance(content, bytes)
        self.assertGreater(len(content), 0)

    def test_read_scaffold_nested(self):
        content = read_scaffold("templates/PLAN.template.md")
        self.assertIsInstance(content, bytes)
        self.assertGreater(len(content), 0)

    def test_no_filesystem_path_in_module(self):
        import inspect

        import specfuse.loop.scaffold as mod

        src = inspect.getsource(mod)
        self.assertNotIn("__file__", src)


if __name__ == "__main__":
    unittest.main()
