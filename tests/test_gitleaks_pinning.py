#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the gitleaks pinning + error-classification fixes (issue #250).

Three defects are covered:

  1. The gate's verdict depended on an UNPINNED external binary. CI preferred
     `apt-get install gitleaks` and only fell back to a pinned release, so a
     runner whose apt carries gitleaks silently got Ubuntu's build while a
     developer had whatever their package manager shipped. Pass/fail could
     change with no change to the repo. Every workflow must now install exactly
     the pinned version, and the pin must agree with the module constant.

  2. `_check_gitleaks*` conflated "secrets found" with "gitleaks broke": any
     non-zero exit with unparseable stdout became the finding string
     `gitleaks:secrets-detected`, regardless of cause.

  3. A missing gitleaks binary raised FileNotFoundError — `check=False` does not
     suppress it — so a contributor without gitleaks got a traceback instead of
     an actionable message.
"""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCANNER = _REPO_ROOT / ".specfuse" / "scripts" / "leak_scan.py"

_spec = importlib.util.spec_from_file_location("_leak_scan_pinning", _SCANNER)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Every workflow that installs gitleaks. Enumerated explicitly rather than
# globbed: a new workflow that installs gitleaks must be added here consciously,
# and the "declared surfaces all exist" test below fails if one is renamed.
_WORKFLOWS_INSTALLING_GITLEAKS = (
    _REPO_ROOT / ".github" / "workflows" / "ci.yml",
    _REPO_ROOT / ".github" / "workflows" / "release.yml",
    _REPO_ROOT / ".github" / "workflows" / "leak-scan-content.yml",
)


class TestPinnedVersionIsSingleSourced(unittest.TestCase):
    def test_declared_workflow_surfaces_all_exist(self):
        for wf in _WORKFLOWS_INSTALLING_GITLEAKS:
            with self.subTest(workflow=wf.name):
                self.assertTrue(wf.is_file(), f"{wf} is missing")

    def test_module_exposes_a_pinned_version(self):
        self.assertRegex(_mod.GITLEAKS_PINNED_VERSION, r"^\d+\.\d+\.\d+$")

    def test_every_workflow_pins_the_module_version(self):
        """The pin in each workflow must equal GITLEAKS_PINNED_VERSION.

        This is the drift guard. Bumping the constant without bumping the
        workflows (or vice versa) reintroduces exactly the cross-machine
        divergence #250 reports.
        """
        pinned = _mod.GITLEAKS_PINNED_VERSION
        for wf in _WORKFLOWS_INSTALLING_GITLEAKS:
            text = wf.read_text(encoding="utf-8")
            found = set(re.findall(r"gitleaks[/_-]v?(\d+\.\d+\.\d+)", text))
            with self.subTest(workflow=wf.name):
                self.assertTrue(found, f"{wf.name} names no gitleaks version")
                self.assertEqual(
                    found, {pinned},
                    f"{wf.name} pins {sorted(found)}, module pins {pinned}",
                )

    def test_no_workflow_prefers_apt_gitleaks(self):
        """`apt-get install ... gitleaks` must be gone.

        Preferring apt is what made the version environment-dependent: on a
        runner where apt has gitleaks the pinned release was never fetched.
        Installing bats from apt is still fine — only gitleaks is the oracle.
        """
        for wf in _WORKFLOWS_INSTALLING_GITLEAKS:
            text = wf.read_text(encoding="utf-8")
            for line in text.splitlines():
                if "apt-get install" in line:
                    with self.subTest(workflow=wf.name, line=line.strip()):
                        self.assertNotIn(
                            "gitleaks", line,
                            f"{wf.name} still installs gitleaks via apt",
                        )


class TestGitleaksVersionReporting(unittest.TestCase):
    def test_version_reported_when_available(self):
        # Real `gitleaks version` prints a BARE `8.30.1` on the pinned build.
        proc = MagicMock(returncode=0, stdout="8.30.1\n", stderr="")
        with patch.object(_mod.subprocess, "run", return_value=proc):
            self.assertEqual(_mod.gitleaks_version(), "8.30.1")

    def test_missing_binary_reports_not_installed(self):
        with patch.object(_mod.subprocess, "run", side_effect=FileNotFoundError):
            self.assertEqual(_mod.gitleaks_version(), "not-installed")

    def test_nonzero_exit_reports_unknown(self):
        proc = MagicMock(returncode=2, stdout="", stderr="")
        with patch.object(_mod.subprocess, "run", return_value=proc):
            self.assertEqual(_mod.gitleaks_version(), "unknown")

    def test_main_prints_the_version_line(self):
        """The verdict must carry the build that produced it."""
        import contextlib
        import io

        for reported in (_mod.GITLEAKS_PINNED_VERSION,
                         f"v{_mod.GITLEAKS_PINNED_VERSION}"):
            with self.subTest(reported=reported):
                buf = io.StringIO()
                with patch.object(_mod, "scan_repo", return_value=[]), \
                        patch.object(_mod, "gitleaks_version", return_value=reported), \
                        contextlib.redirect_stdout(buf):
                    rc = _mod.main(["--all"])
                out = buf.getvalue()
                self.assertEqual(rc, 0)
                self.assertIn(f"gitleaks {reported}", out)
                # Both spellings are the pinned build: neither may be flagged.
                self.assertNotIn("expected v", out)

    def test_main_flags_an_unexpected_version(self):
        import contextlib
        import io

        buf = io.StringIO()
        with patch.object(_mod, "scan_repo", return_value=[]), \
                patch.object(_mod, "gitleaks_version", return_value="v8.18.2"), \
                contextlib.redirect_stdout(buf):
            _mod.main(["--all"])
        out = buf.getvalue()
        self.assertIn("v8.18.2", out)
        self.assertIn(f"expected v{_mod.GITLEAKS_PINNED_VERSION}", out)


class TestScanFailureIsNotASecretFinding(unittest.TestCase):
    """Defect 2: 'gitleaks broke' must not be reported as 'a secret exists'."""

    def test_unparseable_output_reports_scan_failed_not_secrets(self):
        proc = MagicMock(
            returncode=1,
            stdout="not json at all",
            stderr="Error: unknown flag: --report-path",
        )
        with patch.object(_mod.subprocess, "run", return_value=proc):
            hits = _mod._run_gitleaks("/tmp/whatever")
        self.assertEqual(len(hits), 1)
        self.assertIn("gitleaks:scan-failed", hits[0])
        self.assertNotIn("secret:", hits[0])
        self.assertNotIn("secrets-detected", hits[0])

    def test_scan_failure_carries_stderr_for_diagnosis(self):
        proc = MagicMock(returncode=1, stdout="", stderr="Error: config is malformed")
        with patch.object(_mod.subprocess, "run", return_value=proc):
            hits = _mod._run_gitleaks("/tmp/whatever")
        self.assertIn("config is malformed", hits[0])

    def test_non_list_json_is_scan_failure_not_secrets(self):
        proc = MagicMock(
            returncode=1,
            stdout=json.dumps({"error": "unexpected format"}),
            stderr="boom",
        )
        with patch.object(_mod.subprocess, "run", return_value=proc):
            hits = _mod._run_gitleaks("/tmp/whatever")
        self.assertIn("gitleaks:scan-failed", hits[0])

    def test_real_findings_name_the_rule_and_file(self):
        """A real finding must be diagnosable: rule id AND file.

        The old fallback discarded both, which is why the #250 incident needed a
        version-archaeology dig instead of reading a rule name.
        """
        proc = MagicMock(
            returncode=1,
            stdout=json.dumps([
                {"RuleID": "aws-access-token", "File": "tests/fixture.py"},
                {"RuleID": "generic-api-key", "File": "docs/example.md"},
            ]),
            stderr="",
        )
        with patch.object(_mod.subprocess, "run", return_value=proc):
            hits = _mod._run_gitleaks("/tmp/whatever")
        self.assertEqual(len(hits), 2)
        self.assertIn("secret:aws-access-token", hits[0])
        self.assertIn("tests/fixture.py", hits[0])
        self.assertIn("secret:generic-api-key", hits[1])

    def test_clean_exit_is_clean(self):
        proc = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(_mod.subprocess, "run", return_value=proc):
            self.assertEqual(_mod._run_gitleaks("/tmp/whatever"), [])

    def test_both_call_sites_share_one_implementation(self):
        """Defect 2 existed in duplicate; the fix must not be half-applied.

        `_check_gitleaks` (text) and `_check_gitleaks_dir` (directory) each had
        their own copy of the conflation. Both must now route through
        `_run_gitleaks`, or a future fix to one silently misses the other —
        the `[FEAT-2026-0015/G1]` enumeration rule.
        """
        proc = MagicMock(returncode=1, stdout="garbage", stderr="tool exploded")
        with patch.object(_mod.subprocess, "run", return_value=proc):
            from_text = _mod._check_gitleaks("irrelevant")
            from_dir = _mod._check_gitleaks_dir(Path("/tmp/whatever"))
        for hits in (from_text, from_dir):
            self.assertEqual(len(hits), 1)
            self.assertIn("gitleaks:scan-failed", hits[0])
            self.assertIn("tool exploded", hits[0])


class TestMissingBinaryFailsCleanly(unittest.TestCase):
    """Defect 3: FileNotFoundError must not escape as a traceback."""

    def test_missing_binary_returns_actionable_finding(self):
        with patch.object(_mod.subprocess, "run", side_effect=FileNotFoundError):
            hits = _mod._run_gitleaks("/tmp/whatever")
        self.assertEqual(len(hits), 1)
        self.assertIn("gitleaks:not-installed", hits[0])

    def test_missing_binary_hint_names_how_to_install(self):
        with patch.object(_mod.subprocess, "run", side_effect=FileNotFoundError):
            hits = _mod._run_gitleaks("/tmp/whatever")
        self.assertIn("PATH", hits[0])
        self.assertIn("github.com/gitleaks/gitleaks/releases", hits[0])
        self.assertIn(_mod.GITLEAKS_PINNED_VERSION, hits[0])

    def test_missing_binary_does_not_raise_from_either_call_site(self):
        with patch.object(_mod.subprocess, "run", side_effect=FileNotFoundError):
            _mod._check_gitleaks("irrelevant")          # must not raise
            _mod._check_gitleaks_dir(Path("/tmp/x"))    # must not raise

    def test_missing_binary_still_fails_the_gate(self):
        """Not-installed is a finding, so the gate fails — silence would be worse."""
        import contextlib
        import io

        buf = io.StringIO()
        with patch.object(_mod, "scan_repo", return_value=[_mod._GITLEAKS_MISSING_HINT]), \
                patch.object(_mod, "gitleaks_version", return_value="not-installed"), \
                contextlib.redirect_stdout(buf):
            rc = _mod.main(["--all"])
        self.assertEqual(rc, 1)
        self.assertIn("not-installed", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
