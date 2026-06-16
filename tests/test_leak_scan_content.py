#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the content-scan runner (FEAT-2026-0024/T03) leak_scan_content.py.

The runner scans a single GitHub event payload (issue/PR title+body+comment)
for leaks, reusing gate 1's leak_scan as a library. These tests build the hashed
denylist and the event payload in a tmp dir from the ``acme-widget`` placeholder
family — never a real private org name — so this committed test file does not
itself carry a denylisted string (which would trip the ``leak-scan --all`` gate;
see FEAT-2026-0024 PLAN.md and Escalation trigger 3).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".specfuse/scripts"


def _load(name: str):
    """Load a script module by name from .specfuse/scripts on sys.path."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# leak_scan must be importable first — the runner does ``import leak_scan``.
leak_scan = _load("leak_scan")
content = _load("leak_scan_content")

# Placeholder "private literal" — acme-widget normalizes to acmewidget (10).
_PLACEHOLDER = "acme-widget"


def _write_hashes(tmpdir: str, literals) -> Path:
    """Build a leak_denylist.hashes via gate 1's generator, in tmpdir only."""
    path = Path(tmpdir) / "leak_denylist.hashes"
    path.write_text(leak_scan.generate_hashed_denylist(list(literals)), encoding="utf-8")
    return path


def _write_event(tmpdir: str, payload: dict) -> Path:
    path = Path(tmpdir) / "event.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class ContentScanRunnerTests(unittest.TestCase):
    def test_runner_exits_nonzero_on_planted_denylist_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            hashes = _write_hashes(tmp, [_PLACEHOLDER])
            event = _write_event(
                tmp,
                {"issue": {"title": "Deploy request",
                           "body": f"Please deploy {_PLACEHOLDER} to prod."}},
            )
            # scan_event names the offending field.
            payload = json.loads(event.read_text(encoding="utf-8"))
            findings = content.scan_event(payload, hashes_path=hashes)
            self.assertTrue(findings, "expected a finding on the planted hit")
            self.assertTrue(
                any(f.startswith("issue.body:") for f in findings),
                f"expected a finding naming issue.body, got {findings!r}",
            )
            # main exits non-zero.
            rc = content.main(
                ["--event-path", str(event), "--hashes-path", str(hashes)]
            )
            self.assertEqual(rc, 1)

    def test_runner_exits_zero_on_clean_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            hashes = _write_hashes(tmp, [_PLACEHOLDER])
            event = _write_event(
                tmp,
                {"issue": {"title": "Button alignment",
                           "body": "Fix the login button alignment on mobile."}},
            )
            payload = json.loads(event.read_text(encoding="utf-8"))
            self.assertEqual(content.scan_event(payload, hashes_path=hashes), [])
            rc = content.main(
                ["--event-path", str(event), "--hashes-path", str(hashes)]
            )
            self.assertEqual(rc, 0)

    def test_main_missing_event_path_fails_closed(self):
        saved = os.environ.pop("GITHUB_EVENT_PATH", None)
        try:
            # No --event-path and no env var -> fail closed (non-zero).
            self.assertNotEqual(content.main([]), 0)
            # A path that does not exist -> fail closed (non-zero), not a pass.
            with tempfile.TemporaryDirectory() as tmp:
                missing = Path(tmp) / "nope.json"
                self.assertNotEqual(
                    content.main(["--event-path", str(missing)]), 0
                )
        finally:
            if saved is not None:
                os.environ["GITHUB_EVENT_PATH"] = saved

    def test_scan_event_no_hashes_file_no_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.hashes"
            payload = {"issue": {"title": "Hi", "body": "ordinary issue text"}}
            # Absent .hashes contributes nothing — no crash, clean -> [].
            self.assertEqual(content.scan_event(payload, hashes_path=missing), [])

    def test_scan_event_skips_missing_fields(self):
        # A pull_request event payload carries no issue/comment fields.
        with tempfile.TemporaryDirectory() as tmp:
            hashes = _write_hashes(tmp, [_PLACEHOLDER])
            payload = {"pull_request": {"title": "Add feature",
                                        "body": f"introduces {_PLACEHOLDER}"}}
            findings = content.scan_event(payload, hashes_path=hashes)
            self.assertTrue(
                any(f.startswith("pull_request.body:") for f in findings),
                f"expected a pull_request.body finding, got {findings!r}",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
