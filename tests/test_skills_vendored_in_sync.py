# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Drift guard: .specfuse/skills/ is a byte-for-byte vendored copy of the loop's
# canonical, marketplace-published plugin at plugins/specfuse/skills/. The loop
# operates on .specfuse/skills/ (via .claude/skills forward symlinks); the plugin
# is the single source of truth. Fails CI if the two trees diverge.
# Run scripts/sync-scaffold.sh to restore parity.

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).parent.parent
CANONICAL = REPO_ROOT / "plugins" / "specfuse" / "skills"
VENDORED = REPO_ROOT / ".specfuse" / "skills"


def _tree(root: pathlib.Path) -> set[str]:
    """Relative paths of every regular file under *root*."""
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
    }


class TestSkillsVendoredInSync(unittest.TestCase):
    def test_canonical_and_vendored_exist(self):
        self.assertTrue(CANONICAL.is_dir(), f"canonical plugin skills missing: {CANONICAL}")
        self.assertTrue(VENDORED.is_dir(), f"vendored skills missing: {VENDORED}")

    def test_same_file_set(self):
        canon, vend = _tree(CANONICAL), _tree(VENDORED)
        only_canon = sorted(canon - vend)
        only_vend = sorted(vend - canon)
        msg = []
        if only_canon:
            msg.append("in plugins/ but not .specfuse/: " + ", ".join(only_canon))
        if only_vend:
            msg.append("in .specfuse/ but not plugins/: " + ", ".join(only_vend))
        if msg:
            self.fail(
                "Skills tree out of sync.\nRun: scripts/sync-scaffold.sh\n\n"
                + "\n".join(msg)
            )

    def test_byte_identical(self):
        mismatches = []
        for rel in sorted(_tree(CANONICAL)):
            c = (CANONICAL / rel).read_bytes()
            v = (VENDORED / rel).read_bytes()
            if c != v:
                mismatches.append(rel)
        if mismatches:
            self.fail(
                "Vendored skills differ from canonical plugin.\n"
                "Run: scripts/sync-scaffold.sh\n\n"
                "Differing files:\n" + "\n".join(f"  {m}" for m in mismatches)
            )

    def test_no_symlinks_in_either_tree(self):
        """Both trees must hold real files — the #56 dangling-symlink failure mode.
        (.claude/skills holds the forward discovery symlinks; these trees do not.)"""
        for root in (CANONICAL, VENDORED):
            links = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_symlink()]
            self.assertEqual(links, [], f"unexpected symlinks under {root}: {links}")


if __name__ == "__main__":
    unittest.main()
