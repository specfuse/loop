#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0067/T03 — the written contract agrees with the converged fold.

Asserts the WU template documents `folded_through_re_arm` and the
unconditional lifetime-accumulator contract, that both template copies stay
byte-identical, that `cost.py`'s module docstring names the pre-migration
fallback as legacy rather than an ongoing second shape, and that
`wu_lifetime_cost_usd`'s behaviour is unchanged by this documentation-only WU.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import cost
from specfuse.loop.cost import wu_lifetime_cost_usd

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CANONICAL_TEMPLATE = _REPO_ROOT / "specfuse/loop/data/templates/WU.template.md"
_VENDORED_TEMPLATE = _REPO_ROOT / ".specfuse/templates/WU.template.md"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _write_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


def _attempt_outcome(correlation_id: str, cost_usd) -> dict:
    return {
        "correlation_id": correlation_id,
        "event_type": "attempt_outcome",
        "payload": {"cost_usd": cost_usd},
    }


class TestFoldContract(unittest.TestCase):
    def test_template_documents_cumulative_as_lifetime(self):
        text = _CANONICAL_TEMPLATE.read_text()
        self.assertIn("folded_through_re_arm", text)
        self.assertIn("every re-arm", text)
        self.assertIn(
            "whose prior cycle cost nothing",
            text,
            "template must state cumulative_* folds even a zero-cost prior cycle",
        )

    def test_vendored_template_documents_cumulative_as_lifetime(self):
        text = _VENDORED_TEMPLATE.read_text()
        self.assertIn("folded_through_re_arm", text)
        self.assertIn("every re-arm", text)
        self.assertIn("whose prior cycle cost nothing", text)

    def test_template_copies_are_byte_identical(self):
        self.assertEqual(
            _CANONICAL_TEMPLATE.read_bytes(),
            _VENDORED_TEMPLATE.read_bytes(),
        )

    def test_cost_docstring_names_migration_not_two_live_shapes(self):
        doc = cost.__doc__ or ""
        self.assertIn("FEAT-2026-0067", doc)
        self.assertIn("pre-migration", doc)
        self.assertNotIn("fold-never-ran", doc)
        self.assertNotIn("fold-ran", doc)


class TestLifetimeCostUnchanged(unittest.TestCase):
    """Criterion 5: same reader behaviour before and after this WU's edits."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.wu_path = self.root / "WU-07-x.md"
        self.events_path = self.root / "events.jsonl"

    def test_events_bearing_wu_unchanged(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0053/WU-07
type: implementation
status: done
cost_usd: 4.281823
---
body
""",
        )
        _write_events(
            self.events_path,
            [
                _attempt_outcome("FEAT-2026-0053/WU-07", 1.0),
                _attempt_outcome("FEAT-2026-0053/WU-07", 2.0),
            ],
        )
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 3.0, delta=0.01)

    def test_frontmatter_only_wu_unchanged(self):
        _write(
            self.wu_path,
            """---
id: FEAT-2026-0099/WU-01
cost_usd: 1.5
cumulative_cost_usd: 2.5
---
body
""",
        )
        _write_events(self.events_path, [])
        result = wu_lifetime_cost_usd(self.wu_path, self.events_path)
        self.assertAlmostEqual(result, 4.0, delta=0.01)


if __name__ == "__main__":
    unittest.main()
