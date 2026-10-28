#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""render_link / split_link — the one decision-link builder and parser."""

import unittest

from specfuse.loop.layout import Decisions, Layout, render_link, split_link


def _layout(style, location, link):
    return Layout(decisions=Decisions(style=style, location=location, link=link))


class RenderLink(unittest.TestCase):
    def test_no_layout_adr_matches_skill_example(self):
        layout = _layout("adr", "docs/adr", "{path}")
        got = render_link(
            layout,
            target="docs/adr/0007-event-schema-versioning.md",
            label="ADR-0007: event-schema versioning",
            from_dir=".specfuse",
        )
        self.assertEqual(
            got,
            "[ADR-0007: event-schema versioning](../docs/adr/0007-event-schema-versioning.md)",
        )

    def test_entries_fragment(self):
        layout = _layout("entries", "docs/decisions", "{location}/decisions.md#{id}")
        got = render_link(layout, target="D-0007", label="D", from_dir=".specfuse")
        self.assertEqual(got, "[D](../docs/decisions/decisions.md#D-0007)")

    def test_entries_domain(self):
        layout = _layout("entries", "docs/decisions", "{location}/{domain}.yaml#{id}")
        got = render_link(layout, target="D-0007", label="D", from_dir=".specfuse", domain="billing")
        self.assertEqual(got, "[D](../docs/decisions/billing.yaml#D-0007)")

    def test_missing_domain_raises(self):
        layout = _layout("entries", "docs/decisions", "{location}/{domain}.yaml#{id}")
        with self.assertRaises(ValueError) as ctx:
            render_link(layout, target="D-0007", label="D", from_dir=".specfuse")
        self.assertIn("domain", str(ctx.exception))

    def test_url_not_relativised(self):
        layout = _layout("entries", "docs/decisions", "https://wiki.example.com/decisions/{id}")
        got = render_link(layout, target="D-0007", label="D", from_dir=".specfuse")
        self.assertEqual(got, "[D](https://wiki.example.com/decisions/D-0007)")


class SplitLink(unittest.TestCase):
    def test_path(self):
        self.assertEqual(split_link("../a/b.md"), ("../a/b.md", None, False))

    def test_path_with_fragment(self):
        self.assertEqual(split_link("../a/b.md#D-1"), ("../a/b.md", "D-1", False))

    def test_bare_fragment(self):
        self.assertEqual(split_link("#D-1"), ("", "D-1", False))

    def test_url(self):
        url = "https://wiki.example.com/x#y"
        self.assertEqual(split_link(url), (url, None, True))


if __name__ == "__main__":
    unittest.main()
