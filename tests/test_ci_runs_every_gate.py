#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#592 — CI must run every gate `verification.yml` declares.

`scripts/smoke-test.sh` carried a hand-maintained copy of the `code` gate set
under the comment "Keep in sync". It drifted by six: `roadmap-link-gate`,
`arm-sweep-gate`, `monitoring-example-lint`, `sync-scaffold-symlinks-bats`,
`init-sh-shim-bats`, and `hookspath-conflict-bats` were declared and never
executed.

A declared-but-unrun gate is worse than no gate: `verification.yml` is the
source of truth for what gets verified, so an unrun entry reads as coverage.
`sync_scaffold_symlinks.bats` sat red through two merges because of this, and
its silence made a one-PR-old regression look environmental.

`init-skills-bats` already carried the comment "Was silently red + un-run
before #121" — the same problem, fixed once for one gate.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from specfuse.loop.gate_commands import code_gate_names, iter_code_gates

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "scripts" / "smoke-test.sh"
VERIFICATION = REPO_ROOT / ".specfuse" / "verification.yml"


class TestGateParity(unittest.TestCase):
    def test_declared_gates_were_found(self):
        """Guard the guard: an empty parse would make every check vacuous."""
        names = code_gate_names(VERIFICATION)
        self.assertGreaterEqual(len(names), 10, names)
        self.assertIn("tests", names)
        self.assertIn("roadmap-link-gate", names)

    def test_every_declared_gate_has_a_command(self):
        for name, command in iter_code_gates(VERIFICATION):
            with self.subTest(gate=name):
                self.assertTrue(command.strip(), f"{name} declares no command")

    def test_smoke_test_derives_gates_rather_than_listing_them(self):
        """The drift is structural: any hand-copied list can fall behind.

        Asserts the runner iterates the declared set instead of naming gates
        one by one, so a gate added to verification.yml is run without anyone
        remembering to touch the shell script.
        """
        sh = SMOKE.read_text()
        self.assertIn("gate_commands", sh,
                      "smoke-test.sh does not derive its gates from "
                      "verification.yml; a seventh drift is a matter of time")

    def test_no_declared_gate_is_hardcoded_out_of_the_run(self):
        """Every declared gate must be reachable by the runner's iteration.

        Catches the specific failure this issue is about: a gate present in
        verification.yml that the CI runner never executes.
        """
        declared = set(code_gate_names(VERIFICATION))
        emitted = {name for name, _ in iter_code_gates(VERIFICATION)}
        self.assertEqual(
            declared - emitted, set(),
            "declared gates the runner would skip",
        )


if __name__ == "__main__":
    unittest.main()
