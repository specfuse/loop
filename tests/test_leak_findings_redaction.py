#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression tests for #76 — events.jsonl leak-scan self-poison.

When a squash commit is rejected by the leak-scan pre-commit hook, git's stderr
embeds the hook's FINDINGS block, which QUOTES the offending match. That text is
captured as the attempt-failure note and flushed into events.jsonl; the next
bookkeeping commit re-scans the log and re-trips on the quoted token — a
cascading self-poison the per-token allowlist only band-aided one instance of.

`loop.redact_leak_findings` redacts the quoted match before capture, keeping the
audit signal (which check, which line, a stable hash) while removing the live
trigger. These tests prove the redacted note no longer trips the scanner.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_leak_scan():
    path = REPO_ROOT / ".specfuse/scripts/leak_scan.py"
    spec = importlib.util.spec_from_file_location("leak_scan", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["leak_scan"] = mod
    spec.loader.exec_module(mod)
    return mod


leak_scan = _load_leak_scan()

# A FINDINGS block as captured from a rejected squash commit's stderr. The
# email is NOT allowlisted (corp.internal is not an RFC-2606 doc domain), so it
# re-trips the structural scan when quoted into events.jsonl.
_FINDINGS = (
    "leak-scan: FINDINGS\n"
    "  line 5: email: 'secret@corp.internal'\n"
    "  line 5: user-path: '/Users/alice/secret'\n"
)


class TestRedactLeakFindings(unittest.TestCase):

    def test_quoted_email_match_is_redacted(self):
        out = loop.redact_leak_findings(_FINDINGS)
        self.assertNotIn("secret@corp.internal", out)
        self.assertIn("email: '<redacted:", out)

    def test_quoted_user_path_match_is_redacted(self):
        out = loop.redact_leak_findings(_FINDINGS)
        self.assertNotIn("/Users/alice/secret", out)
        self.assertIn("user-path: '<redacted:", out)

    def test_audit_signal_preserved(self):
        """Which check failed and on which line must survive redaction."""
        out = loop.redact_leak_findings(_FINDINGS)
        self.assertIn("leak-scan: FINDINGS", out)
        self.assertIn("line 5", out)
        self.assertIn("email:", out)
        self.assertIn("user-path:", out)

    def test_non_leak_text_unchanged(self):
        """Ordinary failure notes (no FINDINGS marker) pass through untouched."""
        note = "verify failed: AssertionError at test_x.py line 5: email: 'a@b.com'"
        self.assertEqual(loop.redact_leak_findings(note), note)

    def test_redaction_is_stable_per_token(self):
        """Same token → same hash (so audit can correlate occurrences)."""
        a = loop.redact_leak_findings("leak-scan: x email: 'dup@corp.internal'")
        b = loop.redact_leak_findings("leak-scan: y email: 'dup@corp.internal'")
        digest_a = a.split("<redacted:")[1].split(">")[0]
        digest_b = b.split("<redacted:")[1].split(">")[0]
        self.assertEqual(digest_a, digest_b)

    def test_self_poison_defused_scanner_no_longer_trips(self):
        """The core acceptance: the captured FINDINGS text trips the structural
        scan (the self-poison), but the redacted copy is clean — so the next
        bookkeeping commit re-scanning events.jsonl will not re-trip."""
        empty_denylist: list[str] = []
        original_hits = leak_scan._check_patterns(
            _FINDINGS, leak_scan.DEFAULT_ALLOWLIST, empty_denylist,
        )
        self.assertTrue(
            original_hits,
            "fixture must trip the scanner unredacted (else it proves nothing)",
        )
        redacted = loop.redact_leak_findings(_FINDINGS)
        redacted_hits = leak_scan._check_patterns(
            redacted, leak_scan.DEFAULT_ALLOWLIST, empty_denylist,
        )
        self.assertEqual(
            redacted_hits, [],
            f"redacted note must not re-trip the scan; got {redacted_hits}",
        )


if __name__ == "__main__":
    unittest.main()
