# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0046/T04: the /attention skill claims to be read-only. This guard
# holds that claim to a falsifiable check — a grep over the skill text for
# write-verb instructions, expecting zero hits — plus a positive control that
# proves the pattern is capable of firing at all. Without the control, a zero
# result is indistinguishable from a pattern that can never match anything.
# [FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "attention" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "attention" / "SKILL.md"

# Write-verb instruction pattern. Matches an imperative write verb governing
# one of the three protected targets (a work unit's status, a gate's status,
# a GitHub issue).
_WRITE_VERB_PATTERN = re.compile(
    r"\b(?:edit|set|update|change|flip)\b"
    r"[^.]{0,40}\b(?:work unit'?s?|gate'?s?)\s+status\b"
    r"|\b(?:close|comment on)\b[^.]{0,40}\bgithub issue\b",
    re.IGNORECASE,
)

# Negation that, read backward from a match's start, cancels it: the skill's
# "Hard rules" prose legitimately says "does not flip a work unit's status"
# and "does not close or comment on a GitHub issue" to describe what it
# refrains from doing. A match is a real violation only if no negation word
# appears between the start of its clause (the preceding sentence-ending
# punctuation) and the match itself.
_NEGATION_PATTERN = re.compile(r"\b(?:not|never|n't)\b", re.IGNORECASE)

# Purpose-built violating instruction, in-memory only — never written to disk.
_VIOLATING_INSTRUCTION = (
    "When the queue is empty, flip the work unit's status to done, flip the "
    "gate's status to passed, and close the GitHub issue automatically."
)


def _normalized_body(path: pathlib.Path) -> str:
    text = path.read_text()
    _, _, rest = text.partition("---\n")
    _, _, body = rest.partition("\n---\n")
    return re.sub(r"\s+", " ", body)


def _unnegated_matches(text: str):
    results = []
    for match in _WRITE_VERB_PATTERN.finditer(text):
        clause_start = text.rfind(".", 0, match.start()) + 1
        preceding_clause = text[clause_start:match.start()]
        if not _NEGATION_PATTERN.search(preceding_clause):
            results.append(match.group(0))
    return results


class TestAttentionNonWritingGuard(unittest.TestCase):
    def test_canonical_skill_has_no_write_verbs(self):
        body = _normalized_body(_CANONICAL)
        matches = _unnegated_matches(body)
        self.assertEqual(matches, [], f"write-verb instruction found in {_CANONICAL}: {matches}")

    def test_vendored_skill_has_no_write_verbs(self):
        body = _normalized_body(_VENDORED)
        matches = _unnegated_matches(body)
        self.assertEqual(matches, [], f"write-verb instruction found in {_VENDORED}: {matches}")

    def test_violating_instruction_is_detected(self):
        normalized = re.sub(r"\s+", " ", _VIOLATING_INSTRUCTION)
        matches = _unnegated_matches(normalized)
        self.assertGreaterEqual(
            len(matches),
            1,
            "positive control did not fire — pattern cannot detect a real violation",
        )


if __name__ == "__main__":
    unittest.main()
