# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`docs/flows.html` is an interactive companion to `docs/lifecycles.md` and
`docs/concepts/monitoring-to-fix.md`, shipped into every project as
`.specfuse/docs/flows.html`. The Markdown stays the source of truth; these
tests fail when the page drifts from it or from the code its monitoring
simulator imitates, so a behaviour change cannot ship with a stale page.

The byte match between `docs/flows.html` and its vendored copy under
`specfuse/loop/data/docs/` is `test_scaffold_data_in_sync.py`'s job.
"""

from __future__ import annotations

import pathlib
import re
import unittest

from specfuse.monitor import autofix, issues
from specfuse.monitor.diagnosis import FIX_SCOPES

REPO_ROOT = pathlib.Path(__file__).parent.parent
DOCS = REPO_ROOT / "docs"
PAGE = (DOCS / "flows.html").read_text(encoding="utf-8")
LIFECYCLES = (DOCS / "lifecycles.md").read_text(encoding="utf-8")

# Tabs on the page that are not lifecycles in lifecycles.md's table.
_NON_LIFECYCLE_TABS = {"attention", "choose"}


def _page_flows() -> dict:
    """Map each FLOWS entry's id to its display name."""
    return dict(re.findall(r'\{\s*id: "([a-z]+)", name: "([^"]+)"', PAGE))


class TestLifecyclesMatchTheMarkdown(unittest.TestCase):
    def test_every_lifecycle_in_the_table_has_a_tab_and_no_more(self):
        # The table's first column: | [Feature](#1-the-feature-lifecycle) | ...
        table = set(re.findall(r"^\| \[([A-Za-z]+)\]\(#\d+-the-", LIFECYCLES, re.M))
        self.assertTrue(table, "lifecycles.md's lifecycle table was not found")
        tabs = {
            name for fid, name in _page_flows().items() if fid not in _NON_LIFECYCLE_TABS
        }
        self.assertEqual(tabs, table)

    def test_lifecycles_md_links_the_page(self):
        self.assertIn("(flows.html)", LIFECYCLES)


class TestMonitoringSimulatorMatchesTheCode(unittest.TestCase):
    def test_confidence_threshold(self):
        match = re.search(r"SIM\.conf < ([0-9.]+)\)", PAGE)
        self.assertIsNotNone(match, "simulator's confidence comparison not found")
        self.assertEqual(float(match.group(1)), autofix.CONFIDENCE_THRESHOLD)
        self.assertIn(f"{autofix.CONFIDENCE_THRESHOLD:.2f} threshold", PAGE)

    def test_fix_scope_options_and_routing(self):
        options = re.findall(r'<option value="([a-z]+)">', PAGE)
        self.assertEqual(tuple(options), FIX_SCOPES)
        # The page routes every scope except "small" to a human.
        self.assertIn('SIM.scope !== "small"', PAGE)
        self.assertEqual(set(FIX_SCOPES) - set(autofix._ROUTE_SCOPES), {"small"})

    def test_occurrence_throttle(self):
        hours = issues.DEFAULT_THROTTLE_SECONDS / 3600
        self.assertEqual(hours, int(hours))
        self.assertIn(f"at most every {int(hours)} hours", PAGE)

    def test_closed_finding_behaviour_is_described_as_shipped(self):
        # Until the monitor looks up closed issues, the page must say a closed
        # finding is refiled and mark reopening as planned. When the lookup
        # changes (FEAT-2026-0204), this fails until the page is updated.
        source = pathlib.Path(issues.__file__).read_text(encoding="utf-8")
        open_only = '"--state", "open"' in source and '"--state", "all"' not in source
        if open_only:
            self.assertIn("today: a new issue is filed", PAGE)
        else:
            self.assertNotIn("today: a new issue is filed", PAGE)


class TestPageLinks(unittest.TestCase):
    def test_relative_links_resolve_next_to_the_page(self):
        for href in re.findall(r'href="(?!https?://|#)([^"]+)"', PAGE):
            with self.subTest(href=href):
                self.assertTrue((DOCS / href).is_file(), f"{href} does not resolve from docs/")

    def test_no_external_script(self):
        # The page is opened straight from disk in a project; it must work with
        # nothing but the browser. Fonts may load from Google Fonts and fall back.
        self.assertNotRegex(PAGE, r"<script[^>]+src=")


if __name__ == "__main__":
    unittest.main()
