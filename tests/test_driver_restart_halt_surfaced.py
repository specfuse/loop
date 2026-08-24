# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Drift guard: /attention and gate-status document the driver-restart halt (#1042).

The halt deliberately marks nothing -- it flips no WU status and leaves the
gate `open`, so a fresh process sees exactly the state `ready()` would have
handed the dead one. That is why it shipped with zero consumer migration, and
also why a halted feature is indistinguishable on disk from one nobody has
run. `events.jsonl` is the only place it is recorded, so a reader that does
not consult the event log reports a stopped run as an idle gate.

These skills are prose, so the testable contract is that the prose names the
event, the flag, and the payload keys an implementation must read -- imported
from `loop.py` where they are constants, never hardcoded here. Following
`test_triage_skill_contract.py`'s precedent: this is a drift guard on the
vocabulary, NOT proof that an agent following the prose reports a halt
correctly.

The payload shape is asserted against a synthesized event rather than a
recorded one, because as of #1042's filing `driver_staleness_detected` had
never fired in this repository -- so there is no real event to read, and a
test that waited for one would never run.
"""

from __future__ import annotations

import pathlib
import unittest

from specfuse.loop.loop import HALT_REASON_DRIVER_RESTART, build_event

REPO_ROOT = pathlib.Path(__file__).parent.parent
_SKILLS = REPO_ROOT / "plugins" / "specfuse" / "skills"
ATTENTION_MD = _SKILLS / "attention" / "SKILL.md"
GATE_STATUS_MD = _SKILLS / "gate-status" / "SKILL.md"

#: The scaffold copies the canonical skills sync into. Both must carry the
#: prose or a consumer project reads a version that predates the fix.
_VENDORED = REPO_ROOT / ".specfuse" / "skills"

EVENT_TYPE = "driver_staleness_detected"


def _synthesized_halt_event() -> dict:
    """The event the driver emits, built through `build_event` itself.

    Constructed rather than fixtured so a change to the envelope shape fails
    here instead of silently making the prose describe a payload that no
    longer exists.
    """
    return build_event(
        EVENT_TYPE,
        "FEAT-2026-0001",
        {
            "gate": 1,
            "wu_id": "FEAT-2026-0001/T03",
            "driver_paths": ["specfuse/loop/loop.py"],
            "halted": True,
            "reason": HALT_REASON_DRIVER_RESTART,
            "remaining_wu_ids": ["FEAT-2026-0001/T04"],
            "resume_command": "python3 -m specfuse.loop.loop --feature FEAT-2026-0001",
        },
    )


class TestBothSkillsNameTheHalt(unittest.TestCase):
    def test_attention_documents_the_detection(self):
        text = ATTENTION_MD.read_text()

        self.assertIn(EVENT_TYPE, text)
        self.assertIn("halted", text)
        self.assertIn("resume_command", text)

    def test_gate_status_documents_the_detection(self):
        text = GATE_STATUS_MD.read_text()

        self.assertIn(EVENT_TYPE, text)
        self.assertIn("halted", text)
        self.assertIn("resume_command", text)

    def test_both_forbid_reconstructing_the_resume_command(self):
        """#2642 in reverse: a reader can reintroduce it just as easily.

        The stamped command resumes the build the halt came from. A skill
        that rebuilds `specfuse run --feature <id>` instead can send the
        operator at the installed build, which is a different one in any
        checkout carrying its own source.
        """
        for path in (ATTENTION_MD, GATE_STATUS_MD):
            with self.subTest(skill=path.parent.name):
                text = path.read_text()
                self.assertIn("verbatim", text)
                self.assertIn("2642", text)


class TestThePayloadKeysTheProseNamesExist(unittest.TestCase):
    """The prose is only useful if it names keys the driver actually emits."""

    def test_synthesized_event_carries_every_documented_key(self):
        event = _synthesized_halt_event()
        payload = event["payload"]

        for key in ("wu_id", "driver_paths", "remaining_wu_ids",
                    "resume_command", "halted"):
            with self.subTest(key=key):
                self.assertIn(key, payload)

    def test_the_halt_flag_and_reason_are_what_the_skills_look_for(self):
        payload = _synthesized_halt_event()["payload"]

        self.assertIs(payload["halted"], True)
        self.assertEqual(payload["reason"], HALT_REASON_DRIVER_RESTART)

    def test_the_event_type_is_the_one_the_prose_names(self):
        self.assertEqual(_synthesized_halt_event()["event_type"], EVENT_TYPE)


class TestTheVendoredCopiesCarryIt(unittest.TestCase):
    """`scripts/sync-scaffold.sh` must have run: consumers read the vendored
    copy, so prose that lands only in `plugins/` reaches nobody."""

    def test_vendored_skills_match_the_canonical_ones(self):
        for name in ("attention", "gate-status"):
            with self.subTest(skill=name):
                canonical = (_SKILLS / name / "SKILL.md").read_text()
                vendored = (_VENDORED / name / "SKILL.md").read_text()
                self.assertEqual(
                    canonical, vendored,
                    f"{name}: run scripts/sync-scaffold.sh",
                )
                self.assertIn(EVENT_TYPE, vendored)


if __name__ == "__main__":
    unittest.main()
