#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for Windows home-path redaction (FEAT-2026-0032/T03).

Fixture home paths are built by concatenation, never as a contiguous
"/Users/" + "<seg>/" or "\\Users\\" + "<seg>\\" literal, so this file's own
staged diff does not re-trip the repo's structural leak-scan.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from specfuse.loop.loop import _redact_home_paths, _HOME_PATH_RE, _WIN_HOME_PATH_RE

MAC_HOME = "/Users/" + "alice/checkout/repo"
LINUX_HOME = "/home/" + "bob/checkout/repo"
WIN_HOME = "C:" + "\\Users\\" + "alice" + "\\checkout\\repo"
WIN_HOME_MIXED = "C:" + "\\Users\\" + "alice" + "/checkout/repo"
WIN_HOME_LOWER_DRIVE = "c:" + "\\Users\\" + "alice" + "\\checkout"


class WindowsHomeRedactionTests(unittest.TestCase):
    def test_windows_userprofile_path_redacted(self):
        """Red on HEAD: POSIX-only regex leaves C:\\Users\\<name>\\ intact."""
        out = _redact_home_paths(f"grepped {WIN_HOME}\\secret.txt for context")
        self.assertIsNone(_WIN_HOME_PATH_RE.search(out))
        self.assertNotIn("alice", out)

    def test_windows_mixed_separator_redacted(self):
        out = _redact_home_paths(f"path {WIN_HOME_MIXED}/secret.txt")
        self.assertNotIn("alice", out)

    def test_windows_lowercase_drive_letter_redacted(self):
        out = _redact_home_paths(f"path {WIN_HOME_LOWER_DRIVE}\\x.py")
        self.assertNotIn("alice", out)

    def test_posix_home_redaction_unchanged(self):
        mac_out = _redact_home_paths(f"note: {MAC_HOME}/x.py")
        linux_out = _redact_home_paths(f"note: {LINUX_HOME}/x.py")
        self.assertIsNone(_HOME_PATH_RE.search(mac_out))
        self.assertIsNone(_HOME_PATH_RE.search(linux_out))
        self.assertNotIn("alice", mac_out)
        self.assertNotIn("bob", linux_out)


if __name__ == "__main__":
    unittest.main()
