# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3448: a terminal gate auto-closes only once the feature has a CHANGELOG entry.

The terminal auto-close path writes a stub retrospective and marks the close
WU done without dispatching it, so `assert_changelog_entry_for_contract_changes`
(close-k) never runs -- and `evaluate_auto_close` asks nothing about the
changelog. A feature whose terminal gate auto-closed therefore shipped with no
CHANGELOG entry whatever it changed (generator FEAT-2026-0199, 0.14.0).

The terminal gate now auto-closes only when `CHANGELOG.md`'s Unreleased
section already carries an entry tracing to the feature. Otherwise it falls
back to the full close, where close-k runs and an explicit `n/a` is still
available to a feature with no consumer-visible change.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests import test_gate_eval_terminal_wiring as fx

loop = fx.loop

_FEATURE = "FEAT-2026-9981"


def _changelog(unreleased_entries: str) -> str:
    return (
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        f"{unreleased_entries}"
        "## [0.1.0] - 2026-01-01\n\n"
        "### Added\n\n"
        "- **Something older.** Shipped before. (FEAT-2026-0001)\n"
    )


class TestTerminalAutoCloseNeedsChangelogEntry(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        fdir = self.root
        fx._write_plan_md(fdir, _FEATURE, 1)
        fx._write_wu_impl(fdir, f"{_FEATURE}/T01")
        fx._write_wu_close(fdir, f"{_FEATURE}/G1-CLOSE")
        fx._write_gate_file(fdir, 1)
        fx._write_task_completed_event(fdir, f"{_FEATURE}/T01")
        self.gate = fx._make_gate_node(fdir, _FEATURE, 1)
        self.close_wu = fx._make_close_wu(fdir, f"{_FEATURE}/G1-CLOSE")
        self.events_path = fdir / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self):
        return loop.maybe_auto_close_terminal(
            self.root, _FEATURE, self.gate, [self.gate],
            self.events_path, self.close_wu, repo_root=self.root,
        )

    def _assert_falls_back_to_full_close(self):
        auto, decision = self._call()

        self.assertFalse(auto)
        self.assertTrue(
            any(r.startswith("no_changelog_entry") for r in decision.reasons),
            decision.reasons,
        )
        fm, _ = loop.read_frontmatter(self.close_wu.file)
        self.assertEqual(fm.get("status"), "pending")
        self.assertFalse((self.root / "RETROSPECTIVE.md").exists())

    def test_no_changelog_file_falls_back_to_full_close(self):
        self._assert_falls_back_to_full_close()

    def test_unreleased_without_this_feature_falls_back_to_full_close(self):
        (self.root / "CHANGELOG.md").write_text(_changelog(
            "### Fixed\n\n- **Another fix.** Unrelated. (#12)\n\n"
        ))

        self._assert_falls_back_to_full_close()

    def test_unreleased_entry_for_this_feature_auto_closes(self):
        (self.root / "CHANGELOG.md").write_text(_changelog(
            f"### Added\n\n- **The feature.** What it adds. ({_FEATURE})\n\n"
        ))

        auto, decision = self._call()

        self.assertTrue(auto, decision.reasons)


if __name__ == "__main__":
    unittest.main()
