#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0040/T04: the cron dialect is declared, never inferred.

Two classes:

  * ``TestCronDialect`` — the four validator rules on `lint_monitoring.py`,
    each proven by a purpose-built negative observation (per
    `verification-discipline.md` §3, a positive case alone does not verify a
    validation rule), plus the two positive "stays valid" cases the schema
    still owes: a conforming target, and a cron-less heartbeat target.

  * ``TestShippedSurfacesDeclareDialect`` — the tree-wide sweep. It walks the
    git-tracked tree (excluding `.specfuse/features/`, in-flight WU scratch)
    over `*.yml`/`*.yaml`/`*.yml.example`/`*.yaml.example` files, every
    fenced ```yaml block in `*.md` files, and every `*.py` file, collecting
    **every** mapping that carries a `cron` key — the schema-agnostic shape
    a heartbeat target takes whether it is a shipped `monitoring.yml`, a
    discovery-fixture schedule entry, or a test assertion — and asserts zero
    of them lack a `dialect` or carry one whose arity disagrees with the
    expression. The file list is discovered by walking (`git ls-files`),
    never a hand-written tuple — see `[FEAT-2026-0039/T04]`.
"""

from __future__ import annotations

import ast
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import _miniyaml
from specfuse.loop.lint_monitoring import CRON_DIALECTS, validate_monitoring

_REPO_ROOT = Path(__file__).resolve().parent.parent

_YAML_FENCE_RE = re.compile(r"```yaml\n(.*?)```", re.DOTALL)

_VALID_CONFIG_HEAD = """\
environments:
  staging:
    telemetry:
      provider: acme-telemetry
    broker:
      provider: acme-broker
      credentials:
        api_key: BROKER_API_KEY
components:
  - name: svc
    type: service
    runner: local
    diagnose: manual
    autofix: "off"
    checks:
"""


def _write_heartbeat_target(tmp_dir: str, target_yaml: str) -> Path:
    text = _VALID_CONFIG_HEAD + "      - type: heartbeat\n        targets:\n" + target_yaml
    p = Path(tmp_dir) / "monitoring.yml"
    p.write_text(text)
    return p


class TestCronDialect(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def test_cron_dialects_enum_membership(self):
        self.assertEqual(set(CRON_DIALECTS), {"standard-5", "seconds-first-6"})
        self.assertEqual(CRON_DIALECTS["standard-5"], 5)
        self.assertEqual(CRON_DIALECTS["seconds-first-6"], 6)

    def test_conforming_target_validates_clean(self):
        p = _write_heartbeat_target(
            self._tmpdir.name,
            "          - name: nightly\n"
            "            cron: \"0 2 * * *\"\n"
            "            dialect: standard-5\n"
            "            timezone: Etc/UTC\n",
        )
        self.assertEqual(validate_monitoring(p), [])

    def test_conforming_six_field_target_validates_clean(self):
        p = _write_heartbeat_target(
            self._tmpdir.name,
            "          - name: nightly\n"
            "            cron: \"0 0 2 * * *\"\n"
            "            dialect: seconds-first-6\n",
        )
        self.assertEqual(validate_monitoring(p), [])

    def test_cron_less_heartbeat_target_needs_no_dialect(self):
        p = _write_heartbeat_target(self._tmpdir.name, "          - name: nightly\n")
        self.assertEqual(validate_monitoring(p), [])

    # --- the four rules, each a negative observation -----------------------

    def test_cron_without_dialect_is_a_finding(self):
        p = _write_heartbeat_target(
            self._tmpdir.name,
            "          - name: nightly\n"
            "            cron: \"0 2 * * *\"\n",
        )
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("dialect", findings[0])

    def test_out_of_enum_dialect_is_a_finding(self):
        p = _write_heartbeat_target(
            self._tmpdir.name,
            "          - name: nightly\n"
            "            cron: \"0 2 * * *\"\n"
            "            dialect: fortnightly-9\n",
        )
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("dialect", findings[0])
        self.assertIn("fortnightly-9", findings[0])

    def test_dialect_arity_mismatch_is_a_finding(self):
        # A 5-field expression declared `seconds-first-6` (arity 6).
        p = _write_heartbeat_target(
            self._tmpdir.name,
            "          - name: nightly\n"
            "            cron: \"0 2 * * *\"\n"
            "            dialect: seconds-first-6\n",
        )
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("field(s)", findings[0])
        self.assertIn("6", findings[0])

    def test_dialect_without_cron_is_a_finding(self):
        p = _write_heartbeat_target(
            self._tmpdir.name,
            "          - name: nightly\n"
            "            dialect: standard-5\n",
        )
        findings = validate_monitoring(p)
        self.assertEqual(len(findings), 1, findings)
        self.assertIn("dialect", findings[0])
        self.assertIn("cron", findings[0])


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


def _tracked_files(root: Path) -> list[str]:
    proc = subprocess.run(  # nosec B603 - list args, no shell
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {proc.stderr}")
    return proc.stdout.splitlines()


def _walk_cron_carrying_dicts(node: object):
    """Recurse a parsed structure, yielding every mapping carrying a string
    `cron` key — the schema-agnostic notion of "a heartbeat target" this
    sweep needs: the same shape appears as a monitoring target, a
    discovery-fixture schedule entry, and a rendered test assertion."""
    if isinstance(node, dict):
        if isinstance(node.get("cron"), str):
            yield node
        for value in node.values():
            yield from _walk_cron_carrying_dicts(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_cron_carrying_dicts(item)


def _cron_dicts_in_yaml_text(text: str) -> list[dict]:
    try:
        parsed = _miniyaml.parse(text)
    except _miniyaml.MiniYAMLError:
        return []
    return list(_walk_cron_carrying_dicts(parsed))


_UNKNOWN = object()


def _cron_dicts_in_python(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        pairs: dict = {}
        skip = False
        for key_node, value_node in zip(node.keys, node.values, strict=True):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                skip = True
                break
            pairs[key_node.value] = (
                value_node.value if isinstance(value_node, ast.Constant) else _UNKNOWN
            )
        if skip:
            continue
        if isinstance(pairs.get("cron"), str):
            found.append(pairs)
    return found


def _collect_cron_carrying_targets() -> list[tuple]:
    found: list[tuple] = []
    for relpath in _tracked_files(_REPO_ROOT):
        if relpath.startswith(".specfuse/features/"):
            continue
        path = _REPO_ROOT / relpath
        if not path.is_file():
            continue
        if relpath.endswith((".yml", ".yaml", ".yml.example", ".yaml.example")):
            for target in _cron_dicts_in_yaml_text(path.read_text()):
                found.append((relpath, target))
        elif relpath.endswith(".md"):
            text = path.read_text()
            for match in _YAML_FENCE_RE.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                for target in _cron_dicts_in_yaml_text(match.group(1)):
                    found.append((f"{relpath}:{line_no}", target))
        elif relpath.endswith(".py"):
            for target in _cron_dicts_in_python(path):
                found.append((relpath, target))
    return found


class TestShippedSurfacesDeclareDialect(unittest.TestCase):
    def test_no_cron_without_a_conforming_dialect_anywhere(self):
        found = _collect_cron_carrying_targets()

        # AC5: the sweep cannot pass vacuously.
        self.assertGreaterEqual(
            len(found), 4,
            f"expected at least 4 cron-carrying targets tree-wide, found "
            f"{len(found)}: {[w for w, _ in found]}",
        )
        discovered_files = {where.split(":")[0] for where, _ in found}
        self.assertIn(".specfuse/monitoring.yml.example", discovered_files)
        self.assertIn("specfuse/loop/data/monitoring.yml.example", discovered_files)

        offenders = []
        for where, target in found:
            cron = target["cron"]
            dialect = target.get("dialect")
            if not isinstance(dialect, str) or dialect not in CRON_DIALECTS:
                offenders.append(
                    f"{where}: cron {cron!r} has no conforming dialect "
                    f"(got {dialect!r})"
                )
                continue
            arity = CRON_DIALECTS[dialect]
            field_count = len(cron.split())
            if field_count != arity:
                offenders.append(
                    f"{where}: cron {cron!r} has {field_count} field(s), "
                    f"declared dialect {dialect!r} requires {arity}"
                )
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
