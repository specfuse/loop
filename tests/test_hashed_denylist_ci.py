#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""CI-surface hashed-denylist tests (FEAT-2026-0024/T02).

Covers the T02 wiring: the `--hash-denylist` generator, the `scan_repo` hashed
path, and the round-trip through T01's load/match primitives. All org-name
literals here are the `acme-*` placeholders — never real private names (the
plaintext denylist is gitignored and is not referenced by these tests).
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_mod():
    path = REPO_ROOT / ".specfuse/scripts/leak_scan.py"
    spec = importlib.util.spec_from_file_location("leak_scan", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["leak_scan"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mod()


# ---------------------------------------------------------------------------
# AC1 — the red→green proof: scan_repo flags an org name using ONLY the hashed
# file, with the plaintext denylist absent (the CI condition) and gitleaks mute.
# ---------------------------------------------------------------------------


class TestScanRepoHashedOnly(unittest.TestCase):
    def test_scan_repo_flags_org_name_via_hashed_file_only(self):
        org = "Acme-Private-Org"
        with tempfile.TemporaryDirectory() as d:
            hashes_text = _mod.generate_hashed_denylist([org])
            hashes_path = Path(d) / "leak_denylist.hashes"
            hashes_path.write_text(hashes_text, encoding="utf-8")
            tup = _mod.load_hashed_denylist(hashes_path)
            (Path(d) / "leaked.md").write_text(
                "internal note\nwe deploy on Acme-Private-Org infra\n",
                encoding="utf-8",
            )
            with patch.object(_mod, "load_denylist", return_value=[]), patch.object(
                _mod, "_check_gitleaks_dir", return_value=[]
            ), patch.object(
                _mod, "load_hashed_denylist", return_value=tup
            ), patch.object(
                _mod, "_list_tracked_files", return_value=["leaked.md"]
            ):
                hits = _mod.scan_repo(d)
        self.assertTrue(
            any("leaked.md:2" in h and "denylist-hash" in h for h in hits),
            f"expected a denylist-hash hit on leaked.md line 2, got {hits!r}",
        )

    def test_scan_repo_flags_org_name_embedded_substring(self):
        # Mid-token substring fidelity: the committed literal `acmewidget`
        # (10 chars normalized) must still match inside `acmewidgetapp`.
        with tempfile.TemporaryDirectory() as d:
            hashes_text = _mod.generate_hashed_denylist(["acme-widget"])
            hashes_path = Path(d) / "leak_denylist.hashes"
            hashes_path.write_text(hashes_text, encoding="utf-8")
            tup = _mod.load_hashed_denylist(hashes_path)
            (Path(d) / "f.txt").write_text("uses acmewidgetapp here\n", encoding="utf-8")
            with patch.object(_mod, "load_denylist", return_value=[]), patch.object(
                _mod, "_check_gitleaks_dir", return_value=[]
            ), patch.object(
                _mod, "load_hashed_denylist", return_value=tup
            ), patch.object(
                _mod, "_list_tracked_files", return_value=["f.txt"]
            ):
                hits = _mod.scan_repo(d)
        self.assertTrue(any("denylist-hash" in h for h in hits))


# ---------------------------------------------------------------------------
# AC3 — additive behavior: clean tree, and missing .hashes file.
# ---------------------------------------------------------------------------


class TestScanRepoHashedAdditive(unittest.TestCase):
    def test_scan_repo_clean_with_hashed_file(self):
        with tempfile.TemporaryDirectory() as d:
            hashes_text = _mod.generate_hashed_denylist(["Acme-Private-Org"])
            tup = _mod.load_hashed_denylist(
                _write(Path(d) / "leak_denylist.hashes", hashes_text)
            )
            (Path(d) / "clean.txt").write_text("nothing sensitive here\n", encoding="utf-8")
            with patch.object(_mod, "load_denylist", return_value=[]), patch.object(
                _mod, "_check_gitleaks_dir", return_value=[]
            ), patch.object(
                _mod, "load_hashed_denylist", return_value=tup
            ), patch.object(
                _mod, "_list_tracked_files", return_value=["clean.txt"]
            ):
                self.assertEqual(_mod.scan_repo(d), [])

    def test_scan_repo_missing_hashes_file_no_crash(self):
        # Absent .hashes -> load_hashed_denylist returns the empty tuple ->
        # hashed path contributes nothing; behaves as gitleaks/plaintext only.
        empty = ("", frozenset(), frozenset())
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "f.txt").write_text("Acme-Private-Org\n", encoding="utf-8")
            with patch.object(_mod, "load_denylist", return_value=[]), patch.object(
                _mod, "_check_gitleaks_dir", return_value=[]
            ), patch.object(
                _mod, "load_hashed_denylist", return_value=empty
            ), patch.object(
                _mod, "_list_tracked_files", return_value=["f.txt"]
            ):
                self.assertEqual(_mod.scan_repo(d), [])


# ---------------------------------------------------------------------------
# AC2 — the generator: --hash-denylist and write_hashed_denylist round-trip.
# ---------------------------------------------------------------------------


class TestGenerator(unittest.TestCase):
    def test_write_hashed_denylist_format_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            plaintext = Path(d) / "leak_denylist.txt"
            plaintext.write_text(
                "# a comment\nAcme-Private-Org\nacme-widget\n\n",
                encoding="utf-8",
            )
            out = Path(d) / "leak_denylist.hashes"
            count = _mod.write_hashed_denylist(plaintext_path=plaintext, out_path=out)
            self.assertEqual(count, 2)

            text = out.read_text(encoding="utf-8")
            lines = text.splitlines()
            self.assertTrue(any(line.startswith("# salt:") for line in lines))
            lengths_line = next(line for line in lines if line.startswith("# lengths:"))
            # "Acme-Private-Org" -> acmeprivateorg (14); "acme-widget" -> acmewidget (10)
            self.assertIn("10", lengths_line)
            self.assertIn("14", lengths_line)

            salt, lengths, hashes = _mod.load_hashed_denylist(out)
            self.assertEqual(salt, _mod._DEFAULT_DENYLIST_SALT)
            self.assertEqual(lengths, frozenset({10, 14}))
            self.assertEqual(len(hashes), 2)
            # Each plaintext entry round-trips through the matcher.
            self.assertTrue(
                _mod.hashed_denylist_hits("Acme-Private-Org", salt, lengths, hashes)
            )
            self.assertTrue(
                _mod.hashed_denylist_hits("acme-widget", salt, lengths, hashes)
            )
            self.assertFalse(
                _mod.hashed_denylist_hits("totally fine text", salt, lengths, hashes)
            )

    def test_write_hashed_denylist_missing_plaintext_writes_empty_set(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "leak_denylist.hashes"
            count = _mod.write_hashed_denylist(
                plaintext_path=Path(d) / "absent.txt", out_path=out
            )
            self.assertEqual(count, 0)
            salt, lengths, hashes = _mod.load_hashed_denylist(out)
            self.assertEqual(hashes, frozenset())

    def test_header_carries_obfuscation_caveat(self):
        text = _mod.generate_hashed_denylist(["acme-widget"])
        self.assertIn("Obfuscation, not secrecy", text)

    def test_main_hash_denylist_mode_writes_default_file(self):
        # main(["--hash-denylist"]) reaches write_hashed_denylist and returns 0.
        with patch.object(_mod, "write_hashed_denylist", return_value=3) as mock_w:
            rc = _mod.main(["--hash-denylist"])
        self.assertEqual(rc, 0)
        mock_w.assert_called_once_with()


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
