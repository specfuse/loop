#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/leak_scan.py (FEAT-2026-0020/T15).

Coverage targets:
  - scan_text / scan_staged public API
  - _check_patterns: user-path, email, private-host, denylist, allowlist
  - _check_gitleaks: clean (exit 0), JSON findings, invalid JSON, non-list JSON
  - load_denylist: missing file, entries, comments, blank lines
  - _get_staged_diff: success and git failure
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_mod():
    path = REPO_ROOT / ".specfuse/scripts/leak_scan.py"
    spec = importlib.util.spec_from_file_location("leak_scan", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["leak_scan"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mod()
scan_text = _mod.scan_text
scan_staged = _mod.scan_staged
load_denylist = _mod.load_denylist
DEFAULT_ALLOWLIST = _mod.DEFAULT_ALLOWLIST


# ---------------------------------------------------------------------------
# User-path detection
# ---------------------------------------------------------------------------


class TestUserPath(unittest.TestCase):
    def test_flags_planted_user_path(self):
        hits = scan_text("/Users/testuser/projects/secret.txt", allowlist=frozenset())
        self.assertTrue(any("user-path" in h for h in hits))

    def test_multiple_paths_all_flagged(self):
        text = "/Users/alice/a\n/Users/bob/b"
        hits = scan_text(text, allowlist=frozenset())
        user_hits = [h for h in hits if "user-path" in h]
        self.assertEqual(len(user_hits), 2)

    def test_no_false_positive_relative_path(self):
        text = "src/components/MyComponent.tsx"
        hits = scan_text(text, allowlist=frozenset())
        user_hits = [h for h in hits if "user-path" in h]
        self.assertEqual(user_hits, [])


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


class TestAllowlist(unittest.TestCase):
    def test_allowlist_exempts_init_id(self):
        # INIT-2026-0001 is the canonical orchestrated-ID sample; must never be flagged
        text = "example: INIT-2026-0001/F06/T01"
        hits = scan_text(text, allowlist=DEFAULT_ALLOWLIST)
        structural = [
            h
            for h in hits
            if any(k in h for k in ("user-path", "email", "private-host", "denylist"))
        ]
        self.assertEqual(structural, [])

    def test_custom_token_exempts_line(self):
        text = "/Users/safe-token/projects/"
        hits = scan_text(text, allowlist=frozenset({"safe-token"}))
        self.assertFalse(any("user-path" in h for h in hits))

    def test_empty_allowlist_flags_user_path(self):
        text = "/Users/somebody/projects/"
        hits = scan_text(text, allowlist=frozenset())
        self.assertTrue(any("user-path" in h for h in hits))

    def test_allowlist_token_partial_match_exempts_line(self):
        # If the token appears anywhere on the line, the whole line is exempt
        text = "/Users/testuser/somewhere/ INIT-2026-0001"
        hits = scan_text(text, allowlist=DEFAULT_ALLOWLIST)
        user_hits = [h for h in hits if "user-path" in h]
        self.assertEqual(user_hits, [])

    def test_github_config_address_not_flagged(self):
        # git@github.com is the canonical public git config address, not a
        # secret. It self-poisons via captured leak-scan FINDINGS in
        # events.jsonl (FEAT-2026-0024); the default allowlist must exempt it.
        text = "  line 97: email: 'git@github.com'"
        hits = scan_text(text, allowlist=DEFAULT_ALLOWLIST)
        email_hits = [h for h in hits if "email" in h]
        self.assertEqual(email_hits, [])

    def test_github_config_address_flagged_without_allowlist(self):
        # Confirms the regex still matches it absent the allowlist — the
        # exemption is what makes it pass, not a regex gap.
        hits = scan_text("contact git@github.com", allowlist=frozenset())
        self.assertTrue(any("email" in h for h in hits))


# ---------------------------------------------------------------------------
# Email detection
# ---------------------------------------------------------------------------


class TestEmail(unittest.TestCase):
    def test_flags_email(self):
        hits = scan_text("contact: user@example.com", allowlist=frozenset())
        self.assertTrue(any("email" in h for h in hits))

    def test_no_false_positive_plain_text(self):
        hits = scan_text("no email here at all", allowlist=frozenset())
        self.assertFalse(any("email" in h for h in hits))


# ---------------------------------------------------------------------------
# Private-host detection
# ---------------------------------------------------------------------------


class TestPrivateHost(unittest.TestCase):
    def test_flags_internal(self):
        hits = scan_text("host: build-server.internal", allowlist=frozenset())
        self.assertTrue(any("private-host" in h for h in hits))

    def test_flags_local(self):
        hits = scan_text("server: mybox.local", allowlist=frozenset())
        self.assertTrue(any("private-host" in h for h in hits))

    def test_flags_corp(self):
        hits = scan_text("db: db01.corp", allowlist=frozenset())
        self.assertTrue(any("private-host" in h for h in hits))

    def test_public_tld_not_flagged(self):
        hits = scan_text("url: api.example.com", allowlist=frozenset())
        host_hits = [h for h in hits if "private-host" in h]
        self.assertEqual(host_hits, [])


# ---------------------------------------------------------------------------
# Denylist loading and detection
# ---------------------------------------------------------------------------


class _DenylistBase(unittest.TestCase):
    """Base: patch _mod._DENYLIST_PATH around each test."""

    _original_path = None

    def _set_denylist_file(self, content: str) -> Path:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        f.write(content)
        f.close()
        _mod._DENYLIST_PATH = Path(f.name)
        return Path(f.name)

    def tearDown(self) -> None:
        if self._original_path is not None:
            _mod._DENYLIST_PATH = self._original_path

    def setUp(self) -> None:
        self._original_path = _mod._DENYLIST_PATH


class TestDenylistLoading(_DenylistBase):
    def test_missing_file_returns_empty(self):
        _mod._DENYLIST_PATH = Path("/nonexistent/path/leak_denylist.txt")
        self.assertEqual(load_denylist(), [])

    def test_entries_parsed(self):
        p = self._set_denylist_file("acme-org\nother-entry\n")
        try:
            result = load_denylist()
            self.assertIn("acme-org", result)
            self.assertIn("other-entry", result)
        finally:
            p.unlink(missing_ok=True)

    def test_comments_skipped(self):
        p = self._set_denylist_file("# comment\nreal-entry\n")
        try:
            result = load_denylist()
            self.assertNotIn("# comment", result)
            self.assertIn("real-entry", result)
        finally:
            p.unlink(missing_ok=True)

    def test_blank_lines_skipped(self):
        p = self._set_denylist_file("\n\n  \nentry\n")
        try:
            result = load_denylist()
            self.assertEqual(result, ["entry"])
        finally:
            p.unlink(missing_ok=True)

    def test_whitespace_stripped(self):
        p = self._set_denylist_file("  trimmed-entry  \n")
        try:
            result = load_denylist()
            self.assertIn("trimmed-entry", result)
        finally:
            p.unlink(missing_ok=True)


class TestDenylistDetection(_DenylistBase):
    def test_denylist_entry_flagged(self):
        p = self._set_denylist_file("acme-internal-org\n")
        try:
            hits = scan_text("repo: acme-internal-org/project", allowlist=frozenset())
            self.assertTrue(any("denylist" in h for h in hits))
        finally:
            p.unlink(missing_ok=True)

    def test_denylist_case_insensitive(self):
        p = self._set_denylist_file("SecretOrg\n")
        try:
            hits = scan_text("belongs to SECRETORG", allowlist=frozenset())
            self.assertTrue(any("denylist" in h for h in hits))
        finally:
            p.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Gitleaks integration
# ---------------------------------------------------------------------------


class TestGitleaks(unittest.TestCase):
    def test_clean_text_no_secret_hits(self):
        # Real gitleaks call — verifies it is on PATH and returns exit 0
        hits = scan_text("ordinary config text without secrets", allowlist=DEFAULT_ALLOWLIST)
        secret_hits = [h for h in hits if "secret:" in h or "gitleaks:" in h]
        self.assertEqual(secret_hits, [])

    def test_gitleaks_json_findings_parsed(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = json.dumps(
            [{"RuleID": "fake-rule", "File": "content.txt"}]
        )
        with patch("subprocess.run", return_value=mock_proc):
            hits = _mod._check_gitleaks("irrelevant")
        self.assertIn("secret:fake-rule", hits)

    def test_gitleaks_invalid_json_fallback(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "not json at all"
        with patch("subprocess.run", return_value=mock_proc):
            hits = _mod._check_gitleaks("irrelevant")
        self.assertIn("gitleaks:secrets-detected", hits)

    def test_gitleaks_non_list_json_fallback(self):
        # gitleaks returns exit 1 but body is an object, not a list
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = json.dumps({"error": "unexpected format"})
        with patch("subprocess.run", return_value=mock_proc):
            hits = _mod._check_gitleaks("irrelevant")
        self.assertIn("gitleaks:secrets-detected", hits)

    def test_gitleaks_empty_findings_list(self):
        # exit 1 with empty list (edge case — treat as no named findings)
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = json.dumps([])
        with patch("subprocess.run", return_value=mock_proc):
            hits = _mod._check_gitleaks("irrelevant")
        self.assertEqual(hits, [])

    def test_gitleaks_exit_zero_is_clean(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        with patch("subprocess.run", return_value=mock_proc):
            hits = _mod._check_gitleaks("irrelevant")
        self.assertEqual(hits, [])


# ---------------------------------------------------------------------------
# scan_staged / _get_staged_diff
# ---------------------------------------------------------------------------


class TestScanStaged(unittest.TestCase):
    def test_scan_staged_returns_list(self):
        # In test context staged diff is empty — confirms no crash
        result = scan_staged()
        self.assertIsInstance(result, list)

    def test_scan_staged_delegates_to_scan_text(self):
        with patch.object(_mod, "_get_staged_diff", return_value=""):
            result = scan_staged()
        self.assertIsInstance(result, list)

    def test_get_staged_diff_git_failure_returns_empty(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 128
        mock_proc.stdout = "fatal: not a git repo"
        with patch("subprocess.run", return_value=mock_proc):
            diff = _mod._get_staged_diff()
        self.assertEqual(diff, "")

    def test_get_staged_diff_success_returns_stdout(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "diff --git a/file.py b/file.py\n"
        with patch("subprocess.run", return_value=mock_proc):
            diff = _mod._get_staged_diff()
        self.assertEqual(diff, "diff --git a/file.py b/file.py\n")


# ---------------------------------------------------------------------------
# CI-surface scan (scan_repo) + helpers
# ---------------------------------------------------------------------------


class TestListTrackedFiles(unittest.TestCase):
    def test_success_returns_lines(self):
        mock_proc = MagicMock(returncode=0, stdout="a.py\nb.md\n")
        with patch("subprocess.run", return_value=mock_proc):
            files = _mod._list_tracked_files(Path("."))
        self.assertEqual(files, ["a.py", "b.md"])

    def test_git_failure_returns_empty(self):
        mock_proc = MagicMock(returncode=128, stdout="")
        with patch("subprocess.run", return_value=mock_proc):
            self.assertEqual(_mod._list_tracked_files(Path(".")), [])


class TestCheckGitleaksDir(unittest.TestCase):
    def test_clean_returns_empty(self):
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="[]")):
            self.assertEqual(_mod._check_gitleaks_dir(Path(".")), [])

    def test_findings_parsed(self):
        mock_proc = MagicMock(returncode=1, stdout=json.dumps([{"RuleID": "aws-key"}]))
        with patch("subprocess.run", return_value=mock_proc):
            self.assertEqual(_mod._check_gitleaks_dir(Path(".")), ["secret:aws-key"])

    def test_invalid_json_falls_back(self):
        mock_proc = MagicMock(returncode=1, stdout="not json")
        with patch("subprocess.run", return_value=mock_proc):
            self.assertEqual(
                _mod._check_gitleaks_dir(Path(".")), ["gitleaks:secrets-detected"]
            )


class TestScanRepo(unittest.TestCase):
    def test_denylist_hit_reported_with_path(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "f.txt").write_text("contains ACME-PRIVATE here", encoding="utf-8")
            with patch.object(_mod, "_list_tracked_files", return_value=["f.txt"]), patch.object(
                _mod, "load_denylist", return_value=["ACME-PRIVATE"]
            ), patch.object(_mod, "_check_gitleaks_dir", return_value=[]):
                hits = _mod.scan_repo(d)
        self.assertTrue(any("denylist" in h and "f.txt" in h for h in hits))

    def test_clean_repo_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "f.txt").write_text("nothing here", encoding="utf-8")
            with patch.object(_mod, "_list_tracked_files", return_value=["f.txt"]), patch.object(
                _mod, "load_denylist", return_value=["ACME-PRIVATE"]
            ), patch.object(_mod, "_check_gitleaks_dir", return_value=[]):
                self.assertEqual(_mod.scan_repo(d), [])

    def test_unreadable_file_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(_mod, "_list_tracked_files", return_value=["missing.txt"]), patch.object(
                _mod, "load_denylist", return_value=["X"]
            ), patch.object(_mod, "_check_gitleaks_dir", return_value=[]):
                self.assertEqual(_mod.scan_repo(d), [])

    def test_gitleaks_hits_appended(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "f.txt").write_text("clean", encoding="utf-8")
            with patch.object(_mod, "_list_tracked_files", return_value=["f.txt"]), patch.object(
                _mod, "load_denylist", return_value=[]
            ), patch.object(_mod, "_check_gitleaks_dir", return_value=["secret:aws-key"]):
                self.assertEqual(_mod.scan_repo(d), ["secret:aws-key"])


# ---------------------------------------------------------------------------
# CLI (main)
# ---------------------------------------------------------------------------


class TestMain(unittest.TestCase):
    def test_staged_clean_returns_zero(self):
        with patch.object(_mod, "scan_staged", return_value=[]):
            self.assertEqual(_mod.main(["--staged"]), 0)

    def test_staged_hits_returns_one(self):
        with patch.object(_mod, "scan_staged", return_value=["line 1: email: 'x@y.z'"]):
            self.assertEqual(_mod.main(["--staged"]), 1)

    def test_all_clean_returns_zero(self):
        with patch.object(_mod, "scan_repo", return_value=[]):
            self.assertEqual(_mod.main(["--all"]), 0)

    def test_all_hits_returns_one(self):
        with patch.object(_mod, "scan_repo", return_value=["secret:aws-key"]):
            self.assertEqual(_mod.main(["--all"]), 1)

    def test_no_mode_is_error(self):
        with self.assertRaises(SystemExit):
            _mod.main([])

    def test_both_modes_is_error(self):
        with self.assertRaises(SystemExit):
            _mod.main(["--staged", "--all"])


if __name__ == "__main__":
    unittest.main()
