#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every `.specfuse/skills/` directory must have a live `.claude/skills/` link (#284).

CLAUDE.md states the contract: skills under `.claude/skills/` are symlinks into
`.specfuse/skills/` so Claude Code's discovery picks them up. Nothing enforced
it, and four skills sat invisible for seven weeks before anyone noticed. PR #285
restored the missing links; this test is the enforcement that stops it from
happening silently again.

The check is deliberately asymmetric. `.claude/skills/` also holds entries like
`cavecrew` and `caveman` that point at `../../.agents/skills/` — local operator
tooling, untracked, unrelated to specfuse skill discovery. A symmetric
`set(.specfuse/skills/*) == set(.claude/skills/*)` assertion would report
non-zero on a correct tree (those operator entries have no `.specfuse/skills/`
counterpart and never will), which is unsatisfiable. So the forward direction
(every `.specfuse/skills/` dir has a `.claude/skills/` link) is checked in full,
but the reverse direction (every `.claude/skills/` entry resolves to something
live) is filtered to only the entries whose target resolves inside
`.specfuse/skills/` — the ones this repo's own sync step is responsible for.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPECFUSE_SKILLS = REPO_ROOT / ".specfuse" / "skills"
CLAUDE_SKILLS = REPO_ROOT / ".claude" / "skills"

# Skill name -> why it is deliberately not linked. Empty by design: as of this
# WU every .specfuse/skills/ directory has a .claude/skills/ entry. An entry
# here is a recorded decision, not a backlog item.
_INTENTIONALLY_UNLINKED: dict[str, str] = {}


def _specfuse_skill_dirs() -> set[str]:
    """Top-level, non-hidden directories only — `.specfuse/skills/.claude/`
    is stray tooling state (a `.cc-writes` cache dir), not a skill."""
    return {
        p.name for p in SPECFUSE_SKILLS.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }


def _claude_skill_entries() -> dict[str, Path]:
    """Map .claude/skills/ entry name -> its resolved (real) target path."""
    return {p.name: p.resolve() for p in CLAUDE_SKILLS.iterdir()}


def _resolves_inside_specfuse_skills(target: Path) -> bool:
    specfuse_skills_real = SPECFUSE_SKILLS.resolve()
    try:
        target.relative_to(specfuse_skills_real)
        return True
    except ValueError:
        return False


class TestSkillDiscoveryLinks(unittest.TestCase):

    def test_every_skill_has_a_discovery_link(self):
        """Forward, complete: every .specfuse/skills/ dir needs a live symlink
        in .claude/skills/ resolving back to it, else discovery misses it."""
        specfuse_dirs = _specfuse_skill_dirs() - set(_INTENTIONALLY_UNLINKED)
        entries = _claude_skill_entries()
        specfuse_skills_real = SPECFUSE_SKILLS.resolve()

        missing = []
        wrong_target = []
        not_symlink = []
        for name in sorted(specfuse_dirs):
            claude_path = CLAUDE_SKILLS / name
            if name not in entries:
                missing.append(name)
                continue
            if not claude_path.is_symlink():
                not_symlink.append(name)
                continue
            if entries[name] != specfuse_skills_real / name:
                wrong_target.append(name)

        self.assertEqual(
            missing, [],
            f".specfuse/skills/ director(ies) with no .claude/skills/ "
            f"discovery link: {missing}. Claude Code's skill discovery will "
            f"not see them.")
        self.assertEqual(
            not_symlink, [],
            f".claude/skills/ entr(ies) that are not symlinks: {not_symlink}. "
            f"A copied directory drifts from .specfuse/skills/ silently; it "
            f"must be a symlink.")
        self.assertEqual(
            wrong_target, [],
            f".claude/skills/ entr(ies) that are symlinks but do not resolve "
            f"to the matching .specfuse/skills/ directory: {wrong_target}.")

    def test_no_dangling_specfuse_skill_link(self):
        """Reverse, filtered: only .claude/skills/ entries whose target
        resolves inside .specfuse/skills/ are checked for a live target.
        Entries like `cavecrew`/`caveman` resolve into ../../.agents/skills/ —
        local operator tooling with no .specfuse/skills/ counterpart — and are
        ignored here; a symmetric check over them would be unsatisfiable."""
        dangling = []
        for name, resolved in _claude_skill_entries().items():
            if not _resolves_inside_specfuse_skills(resolved):
                continue
            if not resolved.exists():
                dangling.append(name)

        self.assertEqual(
            dangling, [],
            f".claude/skills/ entr(ies) pointing into .specfuse/skills/ whose "
            f"target does not exist: {sorted(dangling)}.")

    def test_intentionally_unlinked_entries_carry_a_reason(self):
        """An opt-out is only a decision if it says why."""
        for name, reason in _INTENTIONALLY_UNLINKED.items():
            self.assertTrue(
                reason and reason.strip(),
                f"_INTENTIONALLY_UNLINKED[{name!r}] must carry a non-empty "
                f"reason explaining why the skill is not linked")

    def test_intentionally_unlinked_entries_exist_on_disk(self):
        """A stale opt-out for a removed skill is drift of its own."""
        stale = set(_INTENTIONALLY_UNLINKED) - _specfuse_skill_dirs()
        self.assertEqual(
            stale, set(),
            f"_INTENTIONALLY_UNLINKED names skill(s) not present in "
            f".specfuse/skills/: {sorted(stale)}. Remove the entry.")


if __name__ == "__main__":
    unittest.main()
