# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0039/T06: local-runner bootstrap artifacts.
#
# Covers AC1-AC7 of the work unit: the overrides example validates clean
# against gate 1's validator, both artifacts seed without a rename, the live
# overrides file is gitignored, the chosen filename carries no `.local.`
# segment, the secrets checklist names variables and no values, and both
# headers point merge/execution semantics at FEAT-2026-0040.

import pathlib
import re
import tempfile
import unittest

from specfuse.loop.lint_monitoring import _ENV_VAR_NAME_RE, validate_monitoring
from specfuse.loop.scaffold import init

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_OVERRIDES_EXAMPLE = _REPO_ROOT / ".specfuse" / "monitoring.overrides.yml.example"
_SECRETS_CHECKLIST = _REPO_ROOT / ".specfuse" / "monitoring-secrets-checklist.md"
_GITIGNORE_SNIPPET = _REPO_ROOT / ".specfuse" / "gitignore.snippet"
_PACKAGED_GITIGNORE_SNIPPET = (
    _REPO_ROOT / "specfuse" / "loop" / "data" / "gitignore.snippet"
)

# Same pattern .specfuse/scripts/leak_scan.py uses to flag private-host tokens.
_DOT_LOCAL_RE = re.compile(
    r"\b[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.(?:local|internal|corp|lan|intranet|localdomain)\b"
)

# A credential-shaped literal: a connection-string scheme, or a long
# base64/hex-ish run — the same shape `lint_monitoring` rejects inline, used
# here to confirm the secrets checklist contains no value, only names.
_SUSPICIOUS_LITERAL_RE = re.compile(r"://\S+|[A-Za-z0-9+/]{24,}")


class TestOverridesExampleValidatesClean(unittest.TestCase):
    def test_overrides_example_validates_clean(self):
        self.assertTrue(_OVERRIDES_EXAMPLE.is_file())
        findings = validate_monitoring(_OVERRIDES_EXAMPLE)
        self.assertEqual(findings, [])


class TestBothArtifactsAreSeededWithoutRename(unittest.TestCase):
    def test_both_artifacts_are_seeded_without_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            written = init(target)
            self.assertIn("monitoring.overrides.yml.example", written)
            self.assertIn("monitoring-secrets-checklist.md", written)

            sf = target / ".specfuse"
            self.assertTrue((sf / "monitoring.overrides.yml.example").is_file())
            self.assertTrue((sf / "monitoring-secrets-checklist.md").is_file())

            # Opt-in: no live file auto-created by a rename.
            self.assertNotIn("monitoring.overrides.yml", written)
            self.assertFalse((sf / "monitoring.overrides.yml").exists())
            self.assertNotIn("monitoring-secrets-checklist", written)


class TestLiveOverridesFileIsGitignored(unittest.TestCase):
    def test_live_overrides_file_is_gitignored(self):
        snippet = _GITIGNORE_SNIPPET.read_text(encoding="utf-8")
        self.assertIn(".specfuse/monitoring.overrides.yml", snippet)
        self.assertEqual(
            _GITIGNORE_SNIPPET.read_bytes(),
            _PACKAGED_GITIGNORE_SNIPPET.read_bytes(),
        )


class TestChosenFilenameHasNoDotLocalSegment(unittest.TestCase):
    def test_chosen_filename_has_no_dot_local_segment(self):
        paths = [
            _OVERRIDES_EXAMPLE,
            _SECRETS_CHECKLIST,
            _REPO_ROOT / "specfuse" / "loop" / "data" / "monitoring.overrides.yml.example",
            _REPO_ROOT / "specfuse" / "loop" / "data" / "monitoring-secrets-checklist.md",
        ]
        for path in paths:
            self.assertIsNone(
                _DOT_LOCAL_RE.search(str(path.name)),
                f"{path.name} matches leak-scan's private-host pattern",
            )
            self.assertIsNone(
                _DOT_LOCAL_RE.search(path.read_text(encoding="utf-8")),
                f"{path.name} contents match leak-scan's private-host pattern",
            )
        self.assertIsNone(_DOT_LOCAL_RE.search(_GITIGNORE_SNIPPET.read_text(encoding="utf-8")))


class TestSecretsChecklistNamesNoValues(unittest.TestCase):
    def test_secrets_checklist_names_no_values(self):
        text = _SECRETS_CHECKLIST.read_text(encoding="utf-8")

        tokens = re.findall(r"`([A-Z][A-Z0-9_]*)`", text)
        self.assertGreater(len(tokens), 0, "expected at least one credential name")
        for token in tokens:
            self.assertRegex(token, _ENV_VAR_NAME_RE)

        self.assertIsNone(
            _SUSPICIOUS_LITERAL_RE.search(text),
            "secrets checklist appears to contain a literal credential value",
        )

    def test_suspicious_literal_regex_fires_on_a_real_literal(self):
        # Negative case: prove the same detector rejects a literal it should.
        literal = "postgres://user:hunter2@db.example.com:5432/orders"
        self.assertIsNotNone(_SUSPICIOUS_LITERAL_RE.search(literal))
        key_shaped = "AKIA" + "Q" * 30
        self.assertIsNotNone(_SUSPICIOUS_LITERAL_RE.search(key_shaped))


class TestHeadersNameFeat20260040(unittest.TestCase):
    def test_headers_name_feat_2026_0040(self):
        self.assertIn("FEAT-2026-0040", _OVERRIDES_EXAMPLE.read_text(encoding="utf-8"))
        self.assertIn("FEAT-2026-0040", _SECRETS_CHECKLIST.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
