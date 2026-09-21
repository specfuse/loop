#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Published prose cross-references this project only (#3378).

Two surfaces are published content: everything under ``plugins/``, which ships
in a ``specfuse-loop`` release, is mirrored into the umbrella marketplace repo
and lands in every consumer's checkout when they install the plugin; and
``CHANGELOG.md``, which ships in the pip package. Both are a far wider surface
than the commit bodies, PR bodies, roadmap prose and ``events.jsonl`` notes the
leak-scan discipline already guards.

The failure this guards against is #3378: ``fix-bug/SKILL.md`` cited a real
downstream consumer's ``org/repo#issue`` while explaining the ``Closes #<n>``
rule, and the 0.22.1 changelog entry describing that same fix cited it again.
Both shipped before anyone noticed.

`leak_scan` could not catch it and still cannot. A bare ``org/repo#n`` token is
indistinguishable from the many legitimate ``specfuse/loop#NNNN``
cross-references the same prose uses, and the denylist is the wrong instrument
here for a sharper reason: the consumer's name legitimately appears in
``.specfuse/agent-policy.yml`` (it is the repo the bug lane is pointed at) and
in this repo's own tests. A denylist entry cannot tell published prose from
local configuration, so adding one would red the whole repository rather than
the one file that was actually wrong.

So the invariant is scoped to the published surfaces instead, and stated
positively: prose under ``plugins/`` and in ``CHANGELOG.md`` may cross-reference
this project's own repositories and nothing else. Any other ``org/repo#n`` is someone else's
identity riding out in our release.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# `owner/repo#123`. Deliberately broad on the owner/repo halves: the point is to
# catch an owner we have never seen, so the pattern cannot enumerate them.
CROSS_REF_RE = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9._-]*)/([A-Za-z0-9._-]+)#\d+")

# The only owner published prose may name. This project's own repositories are
# the ones a reader of a shipped skill can be expected to follow.
ALLOWED_OWNERS = frozenset({"specfuse"})


class PluginProseCrossRefs(unittest.TestCase):

    def test_published_prose_references_only_this_project(self):
        offenders = []
        published = sorted(PLUGINS_DIR.rglob("*.md")) + [CHANGELOG]
        for path in published:
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for owner, repo in CROSS_REF_RE.findall(line):
                    if owner not in ALLOWED_OWNERS:
                        rel = path.relative_to(REPO_ROOT)
                        offenders.append(f"{rel}:{lineno}: {owner}/{repo}#…")

        self.assertEqual(
            offenders,
            [],
            "published plugin prose names a repository outside "
            f"{sorted(ALLOWED_OWNERS)}. This content ships to every consumer, "
            "so another party's org/repo must not ride along in it — describe "
            "the repo instead ('a downstream consumer repo') and keep the "
            "traceable reference on this project's own issue. Offenders:\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
