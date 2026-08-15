#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0047/T04 criterion 9: structural oracle for the /attention skill's
# heartbeat-silence section.
#
# [FEAT-2026-0003/G2-LESSONS] — a prose artifact (SKILL.md) passes automated code
# gates trivially, so only a test like this can falsify it. Filed as hedge D2 on
# that feature's close: the section shipped and its guard did not, which is the
# same shape as #284 (CLAUDE.md declared a symlink contract nothing enforced, and
# four skills sat invisible for seven weeks).

import pathlib
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "attention" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "attention" / "SKILL.md"

# The load-bearing literal. If heartbeat's entry point is ever renamed, this
# test fails and the skill prose gets corrected with it — which is the whole
# point of asserting on an exact-match literal rather than a paraphrase.
_ENTRY_POINT = "specfuse.loop.heartbeat.silence_check"


class TestAttentionSilenceSection(unittest.TestCase):
    def test_canonical_skill_exists(self):
        self.assertTrue(_CANONICAL.is_file(), f"missing canonical skill: {_CANONICAL}")

    def test_names_silence_check_entry_point_verbatim(self):
        self.assertIn(
            _ENTRY_POINT,
            _CANONICAL.read_text(),
            f"/attention must name {_ENTRY_POINT} as an exact-match literal",
        )

    def test_declares_a_silence_section(self):
        body = _CANONICAL.read_text().lower()
        self.assertIn("silence", body, "/attention must carry a silence-check section")

    def test_states_the_no_webhook_rule(self):
        # The scheduled path fires the webhook; /attention deliberately does not,
        # because a human is already reading the output. If this instruction is
        # lost, an operator opening the inbox pings the channel every time.
        body = _CANONICAL.read_text()
        self.assertIn("webhook", body)
        self.assertRegex(
            body,
            r"[Dd]o \*\*not\*\* fire the webhook|do not fire the webhook",
            "/attention must state that it does not fire the webhook",
        )

    def test_vendored_copy_is_byte_identical(self):
        # plugins/ is canonical; .specfuse/skills/ is vendored by
        # scripts/sync-scaffold.sh. Editing one copy only is the drift this guards.
        self.assertTrue(_VENDORED.is_file(), f"missing vendored skill: {_VENDORED}")
        self.assertEqual(
            _CANONICAL.read_bytes(),
            _VENDORED.read_bytes(),
            "vendored .specfuse/skills/attention/SKILL.md has drifted from "
            "plugins/specfuse/skills/attention/SKILL.md — run scripts/sync-scaffold.sh",
        )


if __name__ == "__main__":
    unittest.main()
