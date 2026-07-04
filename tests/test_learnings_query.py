#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/learnings_query.py (FEAT-2026-0025/T01).

`parse_entries` splits LEARNINGS.md's `- [tag] text` bullets (which may wrap
across lines) into entries, excluding header/Format/heading prose. `rank`
scores those entries against a query with a stdlib BM25 implementation. Loaded
by file path, matching the pattern other `.specfuse/scripts` helpers use in
this test suite (see test_leak_scan_content.py) since this module is not part
of the `specfuse` package.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".specfuse" / "scripts"


def _load(name: str):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lq = _load("learnings_query")


class TestRank(unittest.TestCase):
    def test_ranks_relevant_entry_first(self):
        entries = [
            {"tag": "meta/a", "text": "Coverage gates must run before commit."},
            {"tag": "meta/b", "text": "BM25 ranking helps retrieve relevant learnings entries fast."},
            {"tag": "meta/c", "text": "Never touch the driver internals directly."},
        ]
        ranked = lq.rank("BM25 ranking learnings retrieval", entries)
        self.assertEqual(ranked[0]["tag"], "meta/b")

    def test_empty_query_returns_all_entries_deterministically(self):
        entries = [
            {"tag": "meta/a", "text": "alpha rule"},
            {"tag": "meta/b", "text": "beta rule"},
        ]
        ranked = lq.rank("", entries)
        self.assertEqual([e["tag"] for e in ranked], ["meta/a", "meta/b"])

    def test_no_match_returns_all_entries_in_stable_order(self):
        entries = [
            {"tag": "meta/a", "text": "alpha rule about routers"},
            {"tag": "meta/b", "text": "beta rule about gates"},
            {"tag": "meta/c", "text": "gamma rule about secrets"},
        ]
        ranked = lq.rank("zzznomatchzzz", entries)
        self.assertEqual([e["tag"] for e in ranked], ["meta/a", "meta/b", "meta/c"])

    def test_top_n_truncates(self):
        entries = [
            {"tag": "meta/a", "text": "alpha rule about routers"},
            {"tag": "meta/b", "text": "beta rule about gates"},
            {"tag": "meta/c", "text": "gamma rule about secrets"},
        ]
        ranked = lq.rank("rule", entries, top_n=2)
        self.assertEqual(len(ranked), 2)

    def test_rank_handles_empty_entries_list(self):
        self.assertEqual(lq.rank("anything", []), [])


class TestParseEntries(unittest.TestCase):
    def test_parses_simple_bullet(self):
        text = (
            "# LEARNINGS\n\n"
            "## Format\n\n"
            "```\n"
            "- [FEAT-2026-0001/G1] Example bullet that must be excluded.\n"
            "```\n\n"
            "## Entries\n\n"
            "<!-- lessons work units append below this line -->\n\n"
            "- [meta/foo] This is a rule.\n"
        )
        entries = lq.parse_entries(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["tag"], "meta/foo")
        self.assertEqual(entries[0]["text"], "This is a rule.")

    def test_joins_wrapped_multiline_bullet(self):
        text = (
            "## Entries\n\n"
            "<!-- lessons work units append below this line -->\n\n"
            "- [meta/foo] This rule wraps across\n"
            "  several lines of prose\n"
            "  before it ends.\n"
        )
        entries = lq.parse_entries(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["text"],
            "This rule wraps across several lines of prose before it ends.",
        )

    def test_section_heading_ends_entry_and_is_excluded(self):
        text = (
            "## Entries\n\n"
            "<!-- lessons work units append below this line -->\n\n"
            "- [meta/foo] First rule.\n\n"
            "## FEAT-2026-0001/G1-CLOSE — some retro title\n\n"
            "- [FEAT-2026-0001/G1-CLOSE] Second rule.\n"
        )
        entries = lq.parse_entries(text)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["text"], "First rule.")
        self.assertEqual(entries[1]["text"], "Second rule.")

    def test_blank_line_separates_entries(self):
        text = (
            "## Entries\n\n"
            "<!-- lessons work units append below this line -->\n\n"
            "- [meta/a] Rule one.\n\n"
            "- [meta/b] Rule two.\n"
        )
        entries = lq.parse_entries(text)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["tag"], "meta/a")
        self.assertEqual(entries[1]["tag"], "meta/b")

    def test_real_learnings_file_round_trip(self):
        learnings_path = REPO_ROOT / ".specfuse" / "LEARNINGS.md"
        text = learnings_path.read_text(encoding="utf-8")
        entries = lq.parse_entries(text)
        self.assertGreater(len(entries), 1)
        for entry in entries:
            self.assertTrue(entry["text"])
            self.assertTrue(entry["tag"])


if __name__ == "__main__":
    unittest.main()
