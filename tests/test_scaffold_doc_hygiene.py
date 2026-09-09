#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Issue #140 — vendored scaffold docs/templates must not carry defects that
trip Markdown inspections downstream.

Two genuine defects were observed in a freshly-initialized project:

1. Broken relative links to `methodology.md` from `docs/concepts/*.md`: the
   link uses a same-directory path but `methodology.md` lives one level up in
   `docs/`. Correct target is `../methodology.md`.
2. A "Bad character" parse error on the em-dash (U+2014) leading the inline
   text of the `DRIVER-OWNED FIELDS` paragraph in `WU.template.md`.

These guards run against the CANONICAL sources (`docs/`, `.specfuse/`); the
byte-match drift guard in test_scaffold_data_in_sync.py keeps the vendored
`specfuse/loop/data/` copies in lockstep, so fixing the canonicals + re-vendoring
propagates the fix everywhere.
"""

from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).parent.parent
DOCS = REPO_ROOT / "docs"
WU_TEMPLATE = REPO_ROOT / ".specfuse" / "templates" / "WU.template.md"
RULES = REPO_ROOT / ".specfuse" / "rules"
SKILLS = REPO_ROOT / ".specfuse" / "skills"

# Slash commands the methodology has removed. A retired command may still be
# named in a provenance blockquote — that is history — but never in a live
# instruction. Add a line here when a command is retired (#3241).
RETIRED_COMMANDS = (
    "/accept-hedged-close",   # removed by FEAT-2026-0085, shipped in 0.15.0
)

# Markdown inline link with a relative path target (skips absolute URLs and
# pure-anchor links). Captures the path portion, dropping any `#anchor`.
_LINK_RE = re.compile(r"\]\((?!https?://)([^)#][^)]*?)(?:#[^)]*)?\)")
EM_DASH = "—"


class TestScaffoldDocHygiene(unittest.TestCase):

    def test_docs_relative_md_links_resolve(self):
        """Every relative .md link in docs/ must resolve to an existing file
        from the linking file's own directory (issue #140 defect 1)."""
        broken: list[str] = []
        for md in sorted(DOCS.rglob("*.md")):
            for lineno, line in enumerate(
                md.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for target in _LINK_RE.findall(line):
                    if not target.endswith(".md"):
                        continue
                    resolved = (md.parent / target).resolve()
                    if not resolved.is_file():
                        rel = md.relative_to(REPO_ROOT)
                        broken.append(f"{rel}:{lineno} -> {target}")
        self.assertEqual(
            [], broken,
            "broken relative .md links in docs/ (fix the path):\n"
            + "\n".join(broken),
        )

    def test_wu_template_driver_owned_line_has_no_em_dash(self):
        """The DRIVER-OWNED FIELDS paragraph must not carry the U+2014 em-dash
        that IntelliJ flags as a Bad character (issue #140 defect 2)."""
        matches = [
            line
            for line in WU_TEMPLATE.read_text(encoding="utf-8").splitlines()
            if line.startswith("DRIVER-OWNED FIELDS")
        ]
        self.assertTrue(matches, "DRIVER-OWNED FIELDS line not found in template")
        for line in matches:
            self.assertNotIn(
                EM_DASH, line,
                "DRIVER-OWNED FIELDS line still contains the U+2014 em-dash "
                "that trips the Markdown parser — use ' - ' instead",
            )

    def test_no_live_instruction_cites_a_retired_command(self):
        """A retired slash command may be named in HISTORY, never in an
        instruction an agent is expected to follow (#3241).

        `operator-escalation.md` told the reader that a field recording why a
        human accepted something is "`/accept-hedged-close`'s reason line" —
        for a command FEAT-2026-0085 removed in 0.15.0. An agent following
        that looks for a reason line it can never find. The rule shipped in
        the packaged scaffold, so every consumer read it.

        Provenance blocks are exempt by design: they record what a past
        feature actually did, and rewriting them to erase a command that did
        once exist would be its own defect. The discriminator is the
        blockquote — a `>`-prefixed line is history, anything else is a live
        instruction. Same reasoning `closing_requirements.py` applies to the
        deliberately-unused requirement ID between `close-i` and `close-k`.
        """
        offenders: list[str] = []
        for md in sorted(RULES.rglob("*.md")) + sorted(SKILLS.rglob("SKILL.md")):
            for lineno, line in enumerate(
                    md.read_text(encoding="utf-8").splitlines(), start=1):
                if line.lstrip().startswith(">"):
                    continue                      # provenance, not instruction
                for retired in RETIRED_COMMANDS:
                    if retired in line:
                        rel = md.relative_to(REPO_ROOT)
                        offenders.append(f"{rel}:{lineno}: {retired} — {line.strip()}")
        self.assertEqual(
            [], offenders,
            "these live instructions cite a command that no longer exists;\n"
            "name a surface that still exists, or move the mention into a\n"
            "provenance blockquote if it is recording history:\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
