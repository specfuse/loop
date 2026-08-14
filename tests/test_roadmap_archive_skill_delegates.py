#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The roadmap-archive skill delegates archiving mechanics to T01's CLI.

Steps 2-5 of the skill used to restate the archiving algorithm in prose —
move a section, rewrite a Detail cell, append to the archive, delete the
inline section by hand. That prose predated #1169's reconciliation fix and
reproduced the pre-fix behaviour when an operator followed it literally.

This unit replaces the prose with a call to `specfuse.loop.roadmap_archive`
(auto_archive_feature's CLI wrapper). Step 1's row validation and the
`--auto` selection/confirmation prose stay — those are human-facing
judgement, not file-editing mechanics.

Exercises:
  (a) the skill body contains the literal CLI invocation
  (b) the skill body does not reintroduce file-editing mechanics prose
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "plugins" / "specfuse" / "skills" / "roadmap-archive" / "SKILL.md"
VENDORED_SKILL_PATH = REPO_ROOT / ".specfuse" / "skills" / "roadmap-archive" / "SKILL.md"

# File-editing verbs, not a keyword allowlist tied to current wording: any
# paragraph pairing one of these verbs with one of these targets is an
# instruction to perform the edit directly, mechanics prose regardless of
# how it is phrased around the verb — UNLESS the same paragraph names the
# CLI as the actor (a sentence naming the owner is permitted; see WU
# acceptance criterion 4) or is describing what the skill will NOT do, or
# quotes example user phrasing.
_MECHANICS_VERB_RE = re.compile(
    r"\b(take|extract|insert|remove|replace|append|delete|strip|write)\b", re.IGNORECASE
)
_MECHANICS_OBJECT_RE = re.compile(
    r"\b(section|cell|archive|roadmap\.md|marker line)\b", re.IGNORECASE
)
_CLI_OWNER_MARKERS = ("CLI", "auto_archive_feature")


def _mechanics_paragraphs(body: str) -> list[str]:
    hits = []
    for para in re.split(r"\n\s*\n", body):
        if any(marker in para for marker in _CLI_OWNER_MARKERS):
            continue
        if "Does not" in para or '"' in para:
            continue
        if "table row" in para:
            # Step 1 (row read/validate) is retained prose, not a file edit.
            continue
        if _MECHANICS_VERB_RE.search(para) and _MECHANICS_OBJECT_RE.search(para):
            hits.append(para)
    return hits


class SkillDelegatesToCliTests(unittest.TestCase):
    def test_skill_invokes_the_cli(self) -> None:
        body = SKILL_PATH.read_text(encoding="utf-8")
        self.assertTrue(
            "python3 -m specfuse.loop.roadmap_archive" in body
            or ".specfuse/scripts/roadmap_archive.py" in body,
            "SKILL.md must invoke T01's CLI rather than restate the archiving mechanics",
        )

    def test_skill_carries_no_mechanics_prose(self) -> None:
        body = SKILL_PATH.read_text(encoding="utf-8")
        hits = _mechanics_paragraphs(body)
        self.assertEqual(
            hits,
            [],
            "SKILL.md restates file-editing mechanics instead of delegating to the CLI:\n"
            + "\n---\n".join(hits),
        )

    def test_skill_surfaces_refused_outcome(self) -> None:
        body = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("refused", body)
        self.assertIn("already archived", body)
        self.assertIn("archived", body)

    def test_vendored_copy_matches_canonical(self) -> None:
        self.assertEqual(
            SKILL_PATH.read_text(encoding="utf-8"),
            VENDORED_SKILL_PATH.read_text(encoding="utf-8"),
            ".specfuse/skills/roadmap-archive/SKILL.md must be byte-identical to the "
            "canonical plugins/specfuse/skills/roadmap-archive/SKILL.md after "
            "scripts/sync-scaffold.sh",
        )


if __name__ == "__main__":
    unittest.main()
