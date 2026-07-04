#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the events.jsonl home-path redaction chokepoint (FEAT-2026-0030/T01).

Fixture home paths are built by concatenation, never as a contiguous
"/Users/" + "<seg>/" literal, so this file's own staged diff does not re-trip
the repo's structural leak-scan (which this test itself exercises in AC4).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from specfuse.loop.loop import _redact_home_paths, _HOME_PATH_RE, build_event, flush_events

# Concatenated so no contiguous "/Users/" + "<seg>/" literal appears in source.
MAC_HOME = "/Users/" + "alice/checkout/repo"
LINUX_HOME = "/home/" + "bob/checkout/repo"


class RedactHomePathsTests(unittest.TestCase):
    def test_home_path_redacted_before_flush(self):
        """Red on HEAD: flush_events must strip a macOS home path from payload."""
        events_path = Path(self._tmp_events_path())
        evt = build_event(
            "attempt_outcome",
            "FEAT-2026-0030/T01",
            {"agent_blocked_reason": f"grepped {MAC_HOME}/events.jsonl for context"},
        )
        flush_events(events_path, [evt])
        written = events_path.read_text()
        self.assertIsNone(_HOME_PATH_RE.search(written))

    def _tmp_events_path(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        import os
        os.close(fd)
        os.remove(path)
        return path

    def test_linux_home_path_redacted(self):
        out = _redact_home_paths(f"note: {LINUX_HOME}/x.py")
        self.assertIsNone(_HOME_PATH_RE.search(out))

    def test_nested_dict_redacted_at_depth(self):
        payload = {"outer": {"inner": f"path {MAC_HOME}/x.py"}}
        out = _redact_home_paths(payload)
        self.assertIsNone(_HOME_PATH_RE.search(json.dumps(out)))

    def test_list_of_strings_redacted_elementwise(self):
        payload = [f"a {MAC_HOME}/one.py", "clean text", f"b {LINUX_HOME}/two.py"]
        out = _redact_home_paths(payload)
        self.assertIsNone(_HOME_PATH_RE.search(json.dumps(out)))

    def test_no_home_path_unchanged(self):
        payload = {"correlation_id": "FEAT-2026-0030/T01", "notes": "no path here at all"}
        out = _redact_home_paths(payload)
        self.assertEqual(out, payload)

    def test_audit_fields_survive_unchanged(self):
        evt = build_event(
            "attempt_outcome",
            "FEAT-2026-0030/T01",
            {"failure_class": "tests", "notes": f"see {MAC_HOME}/log.txt"},
        )
        out = _redact_home_paths(evt)
        self.assertEqual(out["correlation_id"], "FEAT-2026-0030/T01")
        self.assertEqual(out["event_type"], "attempt_outcome")
        self.assertEqual(out["source"], "driver")
        self.assertEqual(out["payload"]["failure_class"], "tests")

    def test_idempotent(self):
        once = _redact_home_paths(f"path {MAC_HOME}/x.py")
        twice = _redact_home_paths(once)
        self.assertEqual(once, twice)

    def test_dogfood_leak_scan_clean(self):
        """Redacted output would pass this repo's structural leak-scan (user-path)."""
        sys.path.insert(
            0, str(Path(__file__).resolve().parent.parent / ".specfuse" / "scripts")
        )
        from leak_scan import scan_text  # noqa: E402  (repo-internal, test-only)

        events_path = Path(self._tmp_events_path())
        evt = build_event(
            "attempt_outcome",
            "FEAT-2026-0030/T01",
            {"agent_blocked_reason": f"grepped {MAC_HOME}/events.jsonl for context"},
        )
        flush_events(events_path, [evt])
        written = events_path.read_text()
        findings = [f for f in scan_text(written) if f.startswith("user-path")]
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
