#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The judge must not be asked to grade state its own verdict gates (#3307).

`fire_terminal_flips` runs *after* the judge returns and only when the verdict
is `met`, so at the moment a judge evaluates, `PLAN.md` reads `active`, the
roadmap row reads `active` and `GATE-NN.md` reads `open` — on every terminal
close of every feature, necessarily.

`.specfuse/templates/GATE.template.md` puts "Documentation and roadmap status
reflect what was actually built." into every gate's definition of done. A judge
that reads that bullet literally and checks those surfaces lowers the verdict,
which guarantees they stay as found: the re-close runs a fresh judge against
identical evidence and reaches the identical verdict. FEAT-2026-0104 deadlocked
there for one full close.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop import judge


GATE_WITH_BOILERPLATE = """\
---
gate: 2
status: open
---

# Gate 2 — the thing

## Definition of done

The user-visible thing works end to end.

Also required, as for every gate:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Documentation and roadmap status reflect what was actually built.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## Reflection notes

nothing yet
"""


class DriverOwnedStatusIsNotJudgeableEvidence(unittest.TestCase):

    def _bundle(self, gate_text: str = GATE_WITH_BOILERPLATE):
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "GATE-02.md").write_text(gate_text, encoding="utf-8")
            (d / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Measurements\n\nnothing\n", encoding="utf-8")
            return judge.build_judge_bundle(d, 2, diff_text="(diff)")

    def test_the_roadmap_status_bullet_is_stripped_from_the_definition_of_done(self):
        dod = self._bundle().definition_of_done
        self.assertNotIn("Documentation and roadmap status", dod)
        # The rest of the definition of done survives: this strips one
        # unsatisfiable criterion, it does not trim the section.
        self.assertIn("The user-visible thing works end to end.", dod)
        self.assertIn("A retrospective exists", dod)
        self.assertIn("Per-criterion state", dod)

    def test_the_stripped_bullet_does_not_reach_the_rendered_prompt(self):
        prompt = judge.render_judge_prompt(self._bundle())
        self.assertNotIn("Documentation and roadmap status", prompt)

    def test_the_prompt_says_why_those_surfaces_are_not_evidence(self):
        # Stripping the bullet is not enough on its own: the diff still shows
        # PLAN.md at `active`, and a judge can go read the roadmap itself. It
        # has to be told the coupling, not merely not-reminded of it.
        prompt = judge.render_judge_prompt(self._bundle())
        self.assertIn("PLAN.md", prompt)
        # \s+ not " ": the prompt is wrapped prose and the clause can straddle a
        # line break. Asserting on a single space tests the line width.
        self.assertRegex(prompt, r"(after|once) you\s+(return|answer|decide)")

    def test_a_gate_without_the_bullet_is_unchanged(self):
        plain = GATE_WITH_BOILERPLATE.replace(
            "- Documentation and roadmap status reflect what was actually built.\n", "")
        dod = self._bundle(plain).definition_of_done
        self.assertIn("The user-visible thing works end to end.", dod)
        self.assertIn("Per-criterion state", dod)


if __name__ == "__main__":
    unittest.main()
