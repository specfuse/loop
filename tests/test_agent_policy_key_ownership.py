# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0076/T03: the disjoint-key-ownership boundary must be written
# down in both `derive-agent-policy` and `/groom-backlog`, and must stay
# testable — this is the test that fails if either skill widens into the
# other's key blocks, or if a future top-level key ships unowned.

import pathlib
import re
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_DERIVE_AGENT_POLICY = (
    _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-agent-policy" / "SKILL.md"
)
_GROOM_BACKLOG = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "groom-backlog" / "SKILL.md"

# The file's non-`version` top-level keys, read from the schema this
# feature does not touch (specfuse/loop/agent_policy.py). Kept here as a
# literal, not imported, because this WU must not edit agent_policy.py.
_ALL_KEY_BLOCKS = {"queue", "rules", "budgets", "escalation"}

_OWNS = {
    "derive-agent-policy": {"rules", "budgets", "escalation"},
    "groom-backlog": {"queue"},
}
_FORBIDDEN = {
    "derive-agent-policy": {"queue"},
    "groom-backlog": {"rules", "budgets", "escalation"},
}


def _frontmatter_and_body(text: str):
    assert text.startswith("---\n"), "SKILL.md must open with YAML frontmatter"
    _, _, rest = text.partition("---\n")
    fm_text, _, body = rest.partition("\n---\n")
    return yaml.safe_load(fm_text), body


def _body(path: pathlib.Path) -> str:
    _, body = _frontmatter_and_body(path.read_text())
    return body


class TestKeyOwnership(unittest.TestCase):
    def test_groom_backlog_disclaims_the_other_blocks(self):
        body = _body(_GROOM_BACKLOG)
        self.assertTrue(
            re.search(r"must never\s+write", body, re.IGNORECASE),
            "expected a 'must never write' disclaimer",
        )
        self.assertIn("derive-agent-policy", body)
        for key in ("rules", "budgets", "escalation"):
            self.assertIn(f"`{key}`", body)

    def test_derive_agent_policy_disclaims_queue(self):
        body = _body(_DERIVE_AGENT_POLICY)
        self.assertTrue(
            re.search(r"must never\s+write", body, re.IGNORECASE),
            "expected a 'must never write' disclaimer",
        )
        self.assertIn("/groom-backlog", body)
        self.assertIn("`queue`", body)

    def test_each_skill_names_every_key_block_it_owns(self):
        for path, name in ((_DERIVE_AGENT_POLICY, "derive-agent-policy"), (_GROOM_BACKLOG, "groom-backlog")):
            body = _body(path)
            for key in _OWNS[name]:
                self.assertIn(
                    f"`{key}`",
                    body,
                    f"{name} SKILL.md must name the key block it owns: {key}",
                )

    def test_each_skill_names_every_key_block_it_must_not_write(self):
        for path, name in ((_DERIVE_AGENT_POLICY, "derive-agent-policy"), (_GROOM_BACKLOG, "groom-backlog")):
            body = _body(path)
            for key in _FORBIDDEN[name]:
                self.assertIn(
                    f"`{key}`",
                    body,
                    f"{name} SKILL.md must name the key block it must never write: {key}",
                )

    def test_ownership_sets_are_disjoint_and_exhaustive(self):
        derive_owns = _OWNS["derive-agent-policy"]
        groom_owns = _OWNS["groom-backlog"]
        self.assertEqual(
            derive_owns & groom_owns,
            set(),
            "derive-agent-policy and groom-backlog must not claim the same key block",
        )
        union = derive_owns | groom_owns
        self.assertEqual(
            union,
            _ALL_KEY_BLOCKS,
            f"declared ownership {union} does not cover the file's non-version "
            f"top-level keys {_ALL_KEY_BLOCKS} — an unowned key is a real gap",
        )

    def test_both_skills_state_the_one_writer_per_key_block_invariant(self):
        for path in (_DERIVE_AGENT_POLICY, _GROOM_BACKLOG):
            body = _body(path)
            self.assertTrue(
                re.search(r"one writer per key block", body, re.IGNORECASE),
                f"{path} must state the invariant as 'one writer per key block', "
                "not the superseded per-file phrasing",
            )


if __name__ == "__main__":
    unittest.main()
