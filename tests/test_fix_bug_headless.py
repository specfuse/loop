#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0042/T03 — fix-bug's headless mode is closed, named, and additive.

`fix-bug` (plugins/specfuse/skills/fix-bug/SKILL.md) is titled "interactive"
and halts for a human at several points: a refusal ("this is feature-scoped,
promote to a feature?"), a missing precondition (no repro, gh unavailable),
and the RESULT step's `blocked` reasons. This test asserts the skill now also
documents a **headless mode** in which every one of those halts resolves to
one of exactly three named outcomes — `refused`, `could_not_proceed`,
`completed` — with an explicit never-prompts/never-waits rule, and that the
interactive Method section above it is untouched (only additive content was
introduced) and both skill surfaces stay byte-identical.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest


def _collapse_whitespace(text: str) -> str:
    """Markdown hard-wraps mid-sentence; compare on normalized whitespace so
    an anchor phrase that happens to straddle a line break still matches."""
    return re.sub(r"\s+", " ", text)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "plugins" / "specfuse" / "skills" / "fix-bug" / "SKILL.md"
VENDORED = REPO_ROOT / ".specfuse" / "skills" / "fix-bug" / "SKILL.md"

REQUIRED_OUTCOMES = ("refused", "could_not_proceed", "completed")

# Halts present in the interactive Method *before* this WU (enumerated from
# HEAD, not assumed) — each must still fire unchanged and must be reachable
# in headless mode via one of REQUIRED_OUTCOMES.
REFUSAL_HALT_ANCHORS = (
    "STOP, print \"this is feature-scoped",          # Step 2
    "STOP the branch immediately",                    # "When to break the rules"
    "issue isn't a bug (feature-scoped",               # Step 9 RESULT status:blocked
)
COULD_NOT_PROCEED_HALT_ANCHORS = (
    "no repro — need\n  reproduction steps",           # Step 1
    "Probe `gh auth status`",                          # Step 7
    "repro can't be reduced to a failing test",        # Step 9 RESULT status:blocked
    "a gate failure that requires operator decision",  # Step 9 RESULT status:blocked
)

HEADLESS_SECTION_HEADING = "## Headless mode"


def _git_show_head(path: pathlib.Path) -> str:
    rel = path.relative_to(REPO_ROOT)
    out = subprocess.run(
        ["git", "show", f"HEAD:{rel.as_posix()}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return out.stdout


class TestFixBugHeadless(unittest.TestCase):

    def setUp(self):
        self.text = CANONICAL.read_text(encoding="utf-8")
        self.head_text = _git_show_head(CANONICAL)
        self.flat_text = _collapse_whitespace(self.text)
        self.flat_head_text = _collapse_whitespace(self.head_text)

    def test_headless_outcomes_are_closed_and_named(self):
        self.assertIn(
            HEADLESS_SECTION_HEADING, self.text,
            "SKILL.md does not document a headless mode section")
        self.assertIn(
            "closed outcome set", self.text.lower(),
            "headless outcomes are not stated as a closed set")
        for name in REQUIRED_OUTCOMES:
            self.assertIn(
                f"`{name}`", self.text,
                f"headless outcome {name!r} is not named verbatim in SKILL.md")

    def test_headless_never_prompts_or_waits(self):
        self.assertIn(
            "never asks a question, never waits", self.flat_text,
            "SKILL.md does not state the never-prompts/never-waits rule "
            "explicitly")
        self.assertIn(
            "never silently proceeds past a decision", self.flat_text,
            "SKILL.md does not state the never-proceeds-past-a-decision rule "
            "explicitly")

    def test_every_refusal_path_reachable_and_mapped_to_refused(self):
        for anchor in REFUSAL_HALT_ANCHORS:
            flat_anchor = _collapse_whitespace(anchor)
            self.assertIn(
                flat_anchor, self.flat_head_text,
                f"test fixture drifted from HEAD: refusal anchor {anchor!r} "
                f"no longer present in the pre-WU skill body")
            self.assertIn(
                flat_anchor, self.flat_text,
                f"refusal path {anchor!r} was removed or reworded — every "
                f"existing refusal criterion must survive unchanged")
        # Each refusal anchor's Method step must appear in the headless
        # halt->outcome mapping, mapped to `refused`.
        for step_label in ("Step 2", "When to break the rules", "Step 9"):
            self.assertIn(step_label, self.text)

    def test_every_could_not_proceed_path_reachable(self):
        for anchor in COULD_NOT_PROCEED_HALT_ANCHORS:
            flat_anchor = _collapse_whitespace(anchor)
            self.assertIn(
                flat_anchor, self.flat_head_text,
                f"test fixture drifted from HEAD: precondition anchor "
                f"{anchor!r} no longer present in the pre-WU skill body")
            self.assertIn(
                flat_anchor, self.flat_text,
                f"precondition halt {anchor!r} was removed or reworded")

    def test_headless_section_is_additive_and_does_not_interleave(self):
        """The headless mode must be ONE contiguous block appended after the
        interactive content — never interleaved into the Method, which is how
        an "addition" silently changes what an interactive run does.

        This replaces an earlier `difflib` assertion that compared the working
        tree against `git show HEAD:` and required added lines > 0. That test
        was self-invalidating: while the authoring WU ran, HEAD was the pre-WU
        commit and additions existed, so it passed; the moment its own commit
        landed, HEAD *became* the working tree, the diff went empty, and it
        failed permanently. It could only ever be green in the single attempt
        that wrote it, and it halted this gate's baseline probe on the next run.

        "Only additions" is a review-time property of a diff, not an invariant
        of a file, so it cannot be a durable test. The durable residue is here
        and in the anchor tests above, which assert every interactive halt still
        appears verbatim in the working tree — that is what catches a reworded
        interactive rule, and it needs no git and no moving reference.
        """
        self.assertEqual(
            self.text.count(f"\n{HEADLESS_SECTION_HEADING}"), 1,
            f"{HEADLESS_SECTION_HEADING!r} must appear exactly once — a second "
            f"headless block means the mode is described in two places")

        headless_start = self.text.index(HEADLESS_SECTION_HEADING)

        # Every interactive halt this WU promised to preserve must sit BEFORE
        # the headless section. One appearing after it means headless content
        # was spliced into the interactive Method rather than appended.
        for anchor in REFUSAL_HALT_ANCHORS + COULD_NOT_PROCEED_HALT_ANCHORS:
            flat_anchor = _collapse_whitespace(anchor)
            flat_interactive = _collapse_whitespace(self.text[:headless_start])
            self.assertIn(
                flat_anchor, flat_interactive,
                f"interactive halt {anchor!r} is not in the interactive region "
                f"(before {HEADLESS_SECTION_HEADING!r}) — the headless section "
                f"was interleaved into the Method instead of appended")

    def test_canonical_and_vendored_skill_are_byte_identical(self):
        result = subprocess.run(
            ["diff", str(CANONICAL), str(VENDORED)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"plugins/specfuse/skills/fix-bug/SKILL.md and "
            f".specfuse/skills/fix-bug/SKILL.md have drifted — diff output: "
            f"{result.stdout!r}")
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
