# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3489: a headless analysis session often wraps its one JSON object in a
markdown code fence. `parse_analysis` must read a single surrounding fence as
the object it holds, and stay strict about everything else.
"""

from __future__ import annotations

import json
import unittest

from specfuse.monitor.diagnose_cli import AnalysisParseError, parse_analysis

_PAYLOAD = {
    "root_cause": "The weekly job last ran before heartbeat emission shipped.",
    "evidence": "AppRequests show successful runs; no ScheduleHeartbeat before 2026-10-14.",
    "candidate_fix": "None in the component; wait for the next firing.",
    "confidence": 0.7,
    "fix_scope": "external",
}
_JSON = json.dumps(_PAYLOAD, indent=2)


class TestFencedAnalysisParses(unittest.TestCase):
    def _assert_parses(self, raw):
        diagnosis = parse_analysis(raw)
        self.assertEqual(diagnosis.fix_scope, "external")
        self.assertEqual(diagnosis.confidence, 0.7)
        self.assertEqual(diagnosis.root_cause, _PAYLOAD["root_cause"])

    def test_json_fence_parses(self):
        self._assert_parses(f"```json\n{_JSON}\n```")

    def test_bare_fence_parses(self):
        self._assert_parses(f"```\n{_JSON}\n```")

    def test_fence_with_surrounding_whitespace_parses(self):
        self._assert_parses(f"\n\n```json\n{_JSON}\n```\n")

    def test_unfenced_still_parses(self):
        self._assert_parses(_JSON)


class TestStillStrict(unittest.TestCase):
    def test_prose_before_fence_is_rejected(self):
        with self.assertRaises(AnalysisParseError):
            parse_analysis(f"Here is the diagnosis:\n```json\n{_JSON}\n```")

    def test_prose_after_fence_is_rejected(self):
        with self.assertRaises(AnalysisParseError):
            parse_analysis(f"```json\n{_JSON}\n```\nLet me know if you need more.")

    def test_two_fenced_objects_are_rejected(self):
        with self.assertRaises(AnalysisParseError):
            parse_analysis(f"```json\n{_JSON}\n```\n```json\n{_JSON}\n```")

    def test_unterminated_fence_is_rejected(self):
        with self.assertRaises(AnalysisParseError):
            parse_analysis(f"```json\n{_JSON}\n")

    def test_fenced_payload_missing_field_is_rejected(self):
        partial = {k: v for k, v in _PAYLOAD.items() if k != "fix_scope"}
        with self.assertRaises(AnalysisParseError):
            parse_analysis(f"```json\n{json.dumps(partial)}\n```")


if __name__ == "__main__":
    unittest.main()
