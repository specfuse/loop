#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0057/T03 — the `oracles` set in verification.yml must be real.

Adoption proof for the pre-dispatch `oracles` frontmatter key (FEAT-2026-0057/T01):
a WU cannot declare `oracles: [oracles]` unless this repo has actually declared a
non-empty, well-formed `oracles` set in `.specfuse/verification.yml`. A
declared-but-malformed set (missing entries, an entry without a `name` or
`command` key) should fail here on the first run rather than drift silently
until a work unit tries to resolve it mid-dispatch.

Parses with `_miniyaml` rather than `gate_commands.iter_code_gates`: that
module's regex splits entries on the `- name:` line itself, so an entry that
has *lost* its `name` key silently disappears from the parsed list instead of
surfacing as a missing key — the wrong failure mode for this test. `_miniyaml`
returns real dicts, so a key that is missing on one entry stays visible as a
missing key on that entry, which is what "falsifiable" requires here.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from specfuse.loop import _miniyaml

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_YML = REPO_ROOT / ".specfuse" / "verification.yml"


def _load_oracles() -> list:
    parsed = _miniyaml.parse(VERIFICATION_YML.read_text(encoding="utf-8"))
    return parsed.get("oracles") or []


class TestOracleSetDeclared(unittest.TestCase):

    def test_oracles_set_is_non_empty(self):
        oracles = _load_oracles()
        self.assertTrue(
            oracles,
            "`.specfuse/verification.yml` declares no 'oracles' set (or it is "
            "empty) — a WU cannot honestly declare `oracles: [oracles]` "
            "against nothing.")

    def test_every_oracle_entry_has_a_name_and_a_command(self):
        oracles = _load_oracles()
        for entry in oracles:
            self.assertIn(
                "name", entry,
                f"oracles entry {entry!r} is missing the `name` key")
            self.assertIn(
                "command", entry,
                f"oracles entry {entry!r} is missing the `command` key")
            self.assertTrue(
                str(entry.get("name", "")).strip(),
                f"oracles entry {entry!r} has an empty `name`")
            self.assertTrue(
                str(entry.get("command", "")).strip(),
                f"oracles entry {entry!r} has an empty `command`")


if __name__ == "__main__":
    unittest.main()
