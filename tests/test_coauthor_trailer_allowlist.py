#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the Co-authored-by trailer exemption in leak_scan (issue #1171).

`gh pr create --fill` copies a single commit's message into the PR body verbatim,
trailers included. `leak_scan_content.py` scans `pull_request.body`, `_EMAIL_RE`
matched the trailer's address, and every single-commit PR opened that way failed
the `leak-scan-content` check on a clean diff.

The exemption is deliberately narrow, and these tests pin every edge of it:
  - the email rule is skipped ONLY on a line that starts with the trailer key
  - a bare address elsewhere in the same body still fails
  - the other rules (user-path, private-host, denylist) still fire on a trailer
    line, so the exemption cannot be used to smuggle anything past them
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_mod():
    path = REPO_ROOT / ".specfuse/scripts/leak_scan.py"
    spec = importlib.util.spec_from_file_location("leak_scan_1171", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


leak_scan = _load_mod()


def _patterns(text, denylist=None):
    """Run only the pattern checks — no gitleaks subprocess."""
    return leak_scan._check_patterns(text, leak_scan.DEFAULT_ALLOWLIST, denylist or [])


class TestCoauthorTrailerExemption(unittest.TestCase):
    """The regression this issue is about: a trailer must not fail the scan."""

    def test_coauthor_trailer_line_does_not_trip_the_email_rule(self):
        """The exact shape `gh pr create --fill` produces must scan clean."""
        body = (
            "fix(scope): a one-line summary\n"
            "\n"
            "Closes #1171. Some root-cause prose.\n"
            "\n"
            "Co-Authored-By: A Contributor <contributor@vendor.example>\n"
        )
        self.assertEqual(_patterns(body), [])

    def test_trailer_key_is_case_insensitive(self):
        """Git trailer keys are case-insensitive; the exemption must match that."""
        for key in ("Co-Authored-By", "Co-authored-by", "co-authored-by", "CO-AUTHORED-BY"):
            with self.subTest(key=key):
                line = f"{key}: A Contributor <contributor@vendor.example>\n"
                self.assertEqual(_patterns(line), [])

    def test_leading_whitespace_before_the_trailer_is_tolerated(self):
        line = "   Co-authored-by: A Contributor <contributor@vendor.example>\n"
        self.assertEqual(_patterns(line), [])


class TestExemptionIsNarrow(unittest.TestCase):
    """Everything the exemption must NOT let through."""

    def test_bare_address_elsewhere_in_the_body_still_fails(self):
        """A trailer in the body does not license an address on another line."""
        body = (
            "Some prose naming someone@vendor.example directly.\n"
            "\n"
            "Co-authored-by: A Contributor <contributor@vendor.example>\n"
        )
        hits = _patterns(body)
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("line 1", hits[0])
        self.assertIn("email", hits[0])

    def test_address_mid_line_after_the_trailer_key_still_fails(self):
        """The key must START the line — not merely appear on it."""
        line = "see the Co-authored-by: convention, e.g. someone@vendor.example\n"
        hits = _patterns(line)
        self.assertTrue(any("email" in h for h in hits), hits)

    def test_user_path_on_a_trailer_line_still_fails(self):
        """Only the email rule is exempted, not the whole line."""
        line = "Co-authored-by: X <x@vendor.example> /Users/someone/secret\n"
        hits = _patterns(line)
        self.assertTrue(any("user-path" in h for h in hits), hits)
        self.assertFalse(any("email" in h for h in hits), hits)

    def test_private_host_on_a_trailer_line_still_fails(self):
        line = "Co-authored-by: X <x@vendor.example> build.corp\n"
        hits = _patterns(line)
        self.assertTrue(any("private-host" in h for h in hits), hits)

    def test_denylist_entry_on_a_trailer_line_still_fails(self):
        """A private org name must never ride in on a trailer."""
        line = "Co-authored-by: X <x@acme-widget.example>\n"
        hits = _patterns(line, denylist=["acme-widget"])
        self.assertTrue(any("denylist" in h for h in hits), hits)


class TestScanTextIntegration(unittest.TestCase):
    """The exemption must hold through the public entry point, not just the helper."""

    def test_scan_text_is_clean_on_a_fill_generated_body(self):
        body = (
            "chore(roadmap): a one-line summary\n"
            "\n"
            "Closes #1171.\n"
            "\n"
            "Co-Authored-By: A Contributor <contributor@vendor.example>\n"
        )
        with patch.object(leak_scan, "_check_gitleaks", return_value=[]):
            self.assertEqual(leak_scan.scan_text(body), [])


if __name__ == "__main__":
    unittest.main()
