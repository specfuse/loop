# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for `specfuse.loop.decisions_format` (FEAT-2026-0058/T01)."""

from __future__ import annotations

import sys
import unittest

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop import decisions_format as df


_VALID_ENTRY = """\
### D1

- **statement:** Widgets ship blue by default.
- **owner:** platform-team
- **status:** `ratified`
- **provenance:** PLAN.md D1
"""

_OVERRIDDEN_RATIFIED_ENTRY = """\
### D2

- **statement:** Widgets ship blue by default.
- **owner:** platform-team
- **status:** `ratified`
- **provenance:** PLAN.md D2
- **overridden_from:** `proposed`
- **signed_off_by:** alice
- **signed_off_at:** 2026-08-20
"""

_NEVER_OVERRIDDEN_RATIFIED_ENTRY = """\
### D3

- **statement:** Widgets ship blue by default.
- **owner:** platform-team
- **status:** `ratified`
- **provenance:** PLAN.md D3
"""


class TestDecisionsFormat(unittest.TestCase):
    def test_status_is_a_closed_set(self):
        text = """\
### D1

- **statement:** Something happened.
- **owner:** someone
- **status:** `made-up-status`
- **provenance:** PLAN.md D1
"""
        result = df.parse_decisions(text)
        self.assertFalse(result.ok())
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].decision_id, "D1")
        self.assertIn("made-up-status", result.errors[0].reason)
        self.assertNotIn("made-up-status", df.STATUS_VALUES)

    def test_parses_well_formed_entry(self):
        result = df.parse_decisions(_VALID_ENTRY)
        self.assertTrue(result.ok())
        self.assertEqual(len(result.entries), 1)
        entry = result.entries[0]
        self.assertEqual(entry.decision_id, "D1")
        self.assertEqual(entry.statement, "Widgets ship blue by default.")
        self.assertEqual(entry.owner, "platform-team")
        self.assertEqual(entry.status, "ratified")
        self.assertEqual(entry.provenance, "PLAN.md D1")

    def test_malformed_entry_is_reported_not_dropped(self):
        text = """\
### D1

- **statement:** Missing owner and status.
- **provenance:** PLAN.md D1
"""
        result = df.parse_decisions(text)
        self.assertFalse(result.ok())
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].decision_id, "D1")
        self.assertIn("owner", result.errors[0].reason)
        self.assertIn("status", result.errors[0].reason)
        self.assertEqual(result.entries, [])

    def test_overridden_pending_signoff_requires_provenance_fields(self):
        text = """\
### D1

- **statement:** Something happened.
- **owner:** someone
- **status:** `overridden-pending-signoff`
- **provenance:** PLAN.md D1
"""
        result = df.parse_decisions(text)
        self.assertFalse(result.ok())
        self.assertIn("overridden_from", result.errors[0].reason)

    def test_ratified_after_override_is_distinguishable_from_ratified_from_start(self):
        overridden = df.parse_decisions(_OVERRIDDEN_RATIFIED_ENTRY)
        never_overridden = df.parse_decisions(_NEVER_OVERRIDDEN_RATIFIED_ENTRY)
        self.assertTrue(overridden.ok())
        self.assertTrue(never_overridden.ok())

        overridden_entry = overridden.entries[0]
        never_overridden_entry = never_overridden.entries[0]

        self.assertEqual(overridden_entry.status, never_overridden_entry.status)
        self.assertTrue(df.ratified_after_override(overridden_entry))
        self.assertFalse(df.ratified_after_override(never_overridden_entry))
        self.assertTrue(overridden_entry.was_overridden())
        self.assertFalse(never_overridden_entry.was_overridden())


if __name__ == "__main__":
    unittest.main()
