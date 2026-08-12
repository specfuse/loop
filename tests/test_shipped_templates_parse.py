#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every shipped template's frontmatter must parse with `_miniyaml`.

`.specfuse/templates/*.md` are the files every feature author is seeded
from, and `init.sh` copies them into every target project. Nothing fed
their frontmatter to the parser that reads it in practice, so a template
could ship with a construct `_miniyaml` does not support (issue #1984:
`PLAN.template.md`'s `roadmap_goal` wrapped across three lines, which
`_miniyaml` rejects — real YAML allows it, the mini parser does not).

This test parses the frontmatter of every template under
`.specfuse/templates/` with `_miniyaml.parse` so the next such template
fails at authoring time, in CI, instead of at a newcomer's first
`/draft-feature`.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import REPO_ROOT, load_miniyaml

miniyaml = load_miniyaml()

TEMPLATES_DIR = REPO_ROOT / ".specfuse" / "templates"


def _frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


class TestShippedTemplatesParse(unittest.TestCase):

    def test_every_template_frontmatter_parses(self):
        template_files = sorted(TEMPLATES_DIR.glob("*.md"))
        self.assertTrue(template_files, f"no templates found under {TEMPLATES_DIR}")

        for path in template_files:
            fm = _frontmatter(path.read_text())
            if fm is None:
                continue
            with self.subTest(template=path.name):
                try:
                    miniyaml.parse(fm)
                except miniyaml.MiniYAMLError as exc:
                    self.fail(f"{path.name} frontmatter failed to parse: {exc}")


if __name__ == "__main__":
    unittest.main()
