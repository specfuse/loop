# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0111/T03: rank T02's scores into a proposal cut at the word
budget, and land nothing in `.specfuse/rules-local/learnings-distilled.md`
without an explicit per-entry human accept.

`propose_distilled_learnings` is read-only: it ranks and cuts. Only
`apply_distilled_decisions` writes, and only for entries whose decision is
`accept` or `edit` -- a `reject`, or an empty acceptance, must leave the file
untouched.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.loop import (
    LEARNINGS_GUARD_REVIEW_PROMPT,
    apply_distilled_decisions,
    propose_distilled_learnings,
)

_LEARNINGS_HEADER = """# LEARNINGS

## Entries

<!-- lessons work units append below this line -->

"""


def _event(correlation_id: str, outcome: str, *, cost_usd=None, failure_signature=None) -> str:
    return json.dumps({
        "event_type": "attempt_outcome",
        "correlation_id": correlation_id,
        "payload": {
            "outcome": outcome,
            "cost_usd": cost_usd,
            "failure_signature": failure_signature,
        },
    })


class _Harness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.features_dir = self.root / "features"
        self.features_dir.mkdir()
        self.distilled_path = self.root / "learnings-distilled.md"

    def tearDown(self):
        self._tmp.cleanup()

    def _write_learnings(self, bullets: list[tuple[str, str]]) -> Path:
        path = self.root / "LEARNINGS.md"
        body = "\n\n".join(f"- [{tag}] {text}" for tag, text in bullets)
        path.write_text(_LEARNINGS_HEADER + body + "\n", encoding="utf-8")
        return path

    def _feature_dir(self, feat_id: str, slug: str) -> Path:
        d = self.features_dir / f"{feat_id}-{slug}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_events(self, feature_dir: Path, lines: list[str]) -> None:
        (feature_dir / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _propose(self, learnings_path: Path, **kwargs) -> dict:
        return propose_distilled_learnings(
            learnings_path=learnings_path, features_dir=self.features_dir, **kwargs
        )


class TestProposalIsRankedAndEvidenced(_Harness):
    def test_higher_cost_entry_is_proposed_first(self):
        learnings = self._write_learnings([
            ("FEAT-2026-0001/G1", "expensive lesson"),
            ("FEAT-2026-0002/G1", "cheap lesson"),
        ])
        self._write_events(self._feature_dir("FEAT-2026-0001", "a"), [
            _event("FEAT-2026-0001/T01", "gate_fail", cost_usd=12.0, failure_signature="boom"),
        ])
        self._write_events(self._feature_dir("FEAT-2026-0002", "b"), [
            _event("FEAT-2026-0002/T01", "gate_fail", cost_usd=0.5, failure_signature="tiny"),
        ])

        result = self._propose(learnings)
        tags = [e["tag"] for e in result["proposed"]]
        self.assertEqual(tags, ["FEAT-2026-0001/G1", "FEAT-2026-0002/G1"])

    def test_each_proposed_entry_carries_its_evidence_and_review_prompt(self):
        learnings = self._write_learnings([("FEAT-2026-0003/G1", "text")])
        self._write_events(self._feature_dir("FEAT-2026-0003", "a"), [
            _event("FEAT-2026-0003/T01", "gate_fail", cost_usd=3.0, failure_signature="sig-x"),
        ])

        entry = self._propose(learnings)["proposed"][0]
        for key in ("tag", "text", "cost_usd", "reach", "failure_signatures", "word_count"):
            self.assertIn(key, entry)
        self.assertEqual(entry["cost_usd"], 3.0)
        self.assertEqual(entry["failure_signatures"], ["sig-x"])
        self.assertEqual(entry["guard_review_prompt"], LEARNINGS_GUARD_REVIEW_PROMPT)
        self.assertIn("guard or lint", entry["guard_review_prompt"])


class TestCutIsByWordBudgetNotEntryCount(_Harness):
    def test_entries_past_the_word_cap_are_cut_not_the_nth_entry(self):
        learnings = self._write_learnings([
            ("FEAT-2026-0004/G1", "one two three four five"),
            ("FEAT-2026-0005/G1", "six seven eight nine ten"),
            ("FEAT-2026-0006/G1", "eleven twelve thirteen"),
        ])
        self._write_events(self._feature_dir("FEAT-2026-0004", "a"), [
            _event("FEAT-2026-0004/T01", "gate_fail", cost_usd=9.0, failure_signature="s1"),
        ])
        self._write_events(self._feature_dir("FEAT-2026-0005", "b"), [
            _event("FEAT-2026-0005/T01", "gate_fail", cost_usd=5.0, failure_signature="s2"),
        ])
        self._write_events(self._feature_dir("FEAT-2026-0006", "c"), [
            _event("FEAT-2026-0006/T01", "gate_fail", cost_usd=1.0, failure_signature="s3"),
        ])

        result = self._propose(learnings, word_cap=7)
        proposed_tags = [e["tag"] for e in result["proposed"]]
        cut_tags = [e["tag"] for e in result["cut"]]
        self.assertEqual(proposed_tags, ["FEAT-2026-0004/G1"])
        self.assertEqual(cut_tags, ["FEAT-2026-0005/G1", "FEAT-2026-0006/G1"])
        self.assertEqual(result["word_cap"], 7)
        total_words = sum(e["word_count"] for e in result["proposed"])
        self.assertLessEqual(total_words, 7)


class TestNothingWritesWithoutExplicitAccept(_Harness):
    def test_declining_leaves_the_file_byte_identical(self):
        self.distilled_path.write_text("# stub\n", encoding="utf-8")
        before = self.distilled_path.read_bytes()

        result = apply_distilled_decisions(
            [{"tag": "FEAT-2026-0007/G1", "action": "reject", "text": "text"}],
            rules_local_path=self.distilled_path,
        )

        after = self.distilled_path.read_bytes()
        self.assertEqual(before, after)
        self.assertEqual(result["written"], [])
        self.assertNotIn("@", after.decode("utf-8"))

    def test_empty_decisions_leaves_the_file_byte_identical(self):
        self.distilled_path.write_text("# stub\n", encoding="utf-8")
        before = self.distilled_path.read_bytes()

        result = apply_distilled_decisions([], rules_local_path=self.distilled_path)

        self.assertEqual(before, self.distilled_path.read_bytes())
        self.assertEqual(result["written"], [])

    def test_accept_appends_only_the_accepted_entry(self):
        self.distilled_path.write_text("# stub\n", encoding="utf-8")

        result = apply_distilled_decisions(
            [
                {"tag": "FEAT-2026-0008/G1", "action": "accept", "text": "keep this"},
                {"tag": "FEAT-2026-0009/G1", "action": "reject", "text": "drop this"},
            ],
            rules_local_path=self.distilled_path,
        )

        text = self.distilled_path.read_text(encoding="utf-8")
        self.assertIn("FEAT-2026-0008/G1", text)
        self.assertIn("keep this", text)
        self.assertNotIn("FEAT-2026-0009/G1", text)
        self.assertNotIn("drop this", text)
        self.assertEqual(result["written"], ["FEAT-2026-0008/G1"])

    def test_edit_writes_the_humans_replacement_text_not_the_original(self):
        self.distilled_path.write_text("# stub\n", encoding="utf-8")

        apply_distilled_decisions(
            [{"tag": "FEAT-2026-0010/G1", "action": "edit", "text": "rewritten wording"}],
            rules_local_path=self.distilled_path,
        )

        text = self.distilled_path.read_text(encoding="utf-8")
        self.assertIn("rewritten wording", text)


if __name__ == "__main__":
    unittest.main()
