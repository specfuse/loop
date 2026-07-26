#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests binding .specfuse/monitoring.yml.example to the validator and doc."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

from specfuse.loop import _miniyaml
from specfuse.loop.lint_monitoring import (
    CHECK_TYPES,
    _CREDENTIAL_KEY_RE,
    _ENV_VAR_NAME_RE,
    validate_monitoring,
)
from tests.test_monitoring_fenced_blocks import _extract_blocks

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLE_PATH = _REPO_ROOT / ".specfuse" / "monitoring.yml.example"
_DOC_PATH = _REPO_ROOT / "docs" / "concepts" / "monitoring-schema.md"

# Explicit scope for the tree-wide no-targetless-dlq assertion below: the six
# paths named in this WU's `produces:` frontmatter (minus this test file
# itself, which is not a check surface) plus the one synced-copy surface the
# frontmatter doesn't list separately. Not a glob, on purpose — a new surface
# must be added to this tuple consciously, per T02's escalation.
_ALL_DLQ_SURFACES = (
    _REPO_ROOT / ".specfuse" / "monitoring.yml.example",
    _REPO_ROOT / "specfuse" / "loop" / "data" / "monitoring.yml.example",
    _REPO_ROOT / ".specfuse" / "monitoring.overrides.yml.example",
    _REPO_ROOT / "specfuse" / "loop" / "data" / "monitoring.overrides.yml.example",
    _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring" / "SKILL.md",
    _REPO_ROOT / ".specfuse" / "skills" / "derive-monitoring" / "SKILL.md",
)

# Both credential regexes are IMPORTED, not redeclared. They used to be copied
# here, which made this module assert a stricter rule than the validator itself
# the moment the validator widened — the exact drift #246 exposed and
# `[FEAT-2026-0015/G1]` in LEARNINGS warns about. One fact, one home.


def _parsed_example() -> dict:
    return _miniyaml.parse(_EXAMPLE_PATH.read_text())


def _iter_credential_values(node: object):
    if isinstance(node, dict):
        for key, value in node.items():
            if _CREDENTIAL_KEY_RE.search(str(key)) and isinstance(value, str):
                yield key, value
            yield from _iter_credential_values(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_credential_values(item)


class MonitoringExampleTests(unittest.TestCase):
    def test_shipped_example_validates_clean(self):
        self.assertTrue(
            _EXAMPLE_PATH.is_file(),
            f"{_EXAMPLE_PATH} does not exist",
        )
        findings = validate_monitoring(_EXAMPLE_PATH)
        self.assertEqual(findings, [])

    def test_example_exercises_every_check_type(self):
        parsed = _parsed_example()
        seen_types = set()
        for component in parsed["components"]:
            for check in component["checks"]:
                seen_types.add(check["type"])
        self.assertEqual(seen_types, set(CHECK_TYPES))

    def test_example_declares_two_differently_typed_components(self):
        parsed = _parsed_example()
        component_types = {c["type"] for c in parsed["components"]}
        self.assertGreaterEqual(len(parsed["components"]), 2)
        self.assertGreaterEqual(len(component_types), 2)

    def test_example_credentials_are_env_var_names(self):
        parsed = _parsed_example()
        credentials = list(_iter_credential_values(parsed))
        self.assertGreater(len(credentials), 0)
        for key, value in credentials:
            self.assertRegex(
                value, _ENV_VAR_NAME_RE,
                f"credential '{key}' is not an environment-variable name: {value!r}",
            )

    def test_leak_scan_passes_on_repo(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / ".specfuse" / "scripts" / "leak_scan.py"), "--all"],
            capture_output=True, text=True, check=False, cwd=_REPO_ROOT,
        )
        self.assertEqual(
            result.returncode, 0,
            f"leak_scan.py --all failed:\nstdout={result.stdout}\nstderr={result.stderr}",
        )

    def test_doc_and_validator_agree(self):
        doc_text = _DOC_PATH.read_text()
        table_match = re.search(
            r"## Check types\n.*?\n\n(\| Type.*?)\n\n", doc_text, re.DOTALL
        )
        self.assertIsNotNone(table_match, "could not find check-types table in doc")
        documented_types = set(re.findall(r"^\| `([a-z0-9-]+)` \|", table_match.group(1), re.MULTILINE))
        self.assertEqual(documented_types, set(CHECK_TYPES))


class TestTargetsAreExercised(unittest.TestCase):
    def test_example_has_a_multi_target_dlq_check(self):
        parsed = _parsed_example()
        found = False
        for component in parsed["components"]:
            for check in component["checks"]:
                if check["type"] != "dlq":
                    continue
                targets = check.get("targets") or []
                if len(targets) >= 2:
                    found = True
                    for target in targets:
                        self.assertTrue(target.get("subscription"))
                        self.assertTrue(target.get("function"))
        self.assertTrue(found, "no 'dlq' check with 2+ targets found in the shipped example")

    def test_example_has_a_multi_target_heartbeat_check(self):
        parsed = _parsed_example()
        found = False
        for component in parsed["components"]:
            for check in component["checks"]:
                if check["type"] != "heartbeat":
                    continue
                targets = check.get("targets") or []
                if len(targets) >= 2:
                    crons = {t.get("cron") for t in targets}
                    self.assertEqual(
                        len(crons), len(targets),
                        "multi-target heartbeat check has duplicate cron values",
                    )
                    found = True
        self.assertTrue(found, "no 'heartbeat' check with 2+ distinct-cron targets found in the shipped example")


def _dlq_checks_in_parsed(parsed: dict):
    for component in parsed.get("components", []):
        for check in component.get("checks", []):
            if check.get("type") == "dlq":
                yield component["name"], check


def _dlq_checks_in_yaml_surface(path: Path):
    parsed = _miniyaml.parse(path.read_text())
    return list(_dlq_checks_in_parsed(parsed))


def _dlq_checks_in_prose_surface(path: Path):
    found = []
    for block in _extract_blocks(path.read_text(), path):
        if block.is_fragment:
            continue
        parsed = _miniyaml.parse(block.body)
        for name, check in _dlq_checks_in_parsed(parsed):
            found.append((f"{block.where()} ({name})", check))
    return found


class TestNoTargetlessDlqRemains(unittest.TestCase):
    def test_no_shipped_surface_has_a_targetless_dlq(self):
        offenders = []
        for path in _ALL_DLQ_SURFACES:
            self.assertTrue(path.is_file(), f"declared surface missing: {path}")
            if path.suffix == ".md":
                dlq_checks = _dlq_checks_in_prose_surface(path)
            else:
                dlq_checks = _dlq_checks_in_yaml_surface(path)
            for where, check in dlq_checks:
                targets = check.get("targets") or []
                if not targets:
                    offenders.append(f"{path}: {where}: 'dlq' check has no targets")
                    continue
                for target in targets:
                    if not target.get("subscription") or not target.get("function"):
                        offenders.append(
                            f"{path}: {where}: 'dlq' target missing "
                            f"'subscription' and/or 'function': {target!r}"
                        )
        self.assertEqual(
            offenders,
            [],
            "target-less or incomplete 'dlq' check(s) found:\n" + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
