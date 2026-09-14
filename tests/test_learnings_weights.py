# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0111/T02: rank LEARNINGS.md entries by failure-signature
attempt-cost (primary), with citation reach as a tiebreaker only.

`score_learnings_entries` reads a LEARNINGS.md-shaped file plus a
`.specfuse/features/`-shaped tree of `events.jsonl` files and returns each
entry's `cost_usd` (summed from non-`passed` `attempt_outcome` events in its
own feature's `events.jsonl`), `reach` (citations elsewhere, excluding the
entry's own feature folder), and the `failure_signatures` it matched — the
inputs a human at T03's accept step needs to disagree with the ranking, not
just the score.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.loop import (
    LEARNINGS_REACH_TIEBREAK_CAVEAT,
    score_learnings_entries,
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

    def tearDown(self):
        self._tmp.cleanup()

    def _write_learnings(self, bullets: list[str]) -> Path:
        path = self.root / "LEARNINGS.md"
        body = "\n\n".join(f"- [{tag}] {text}" for tag, text in
                            (b if isinstance(b, tuple) else (b, "text") for b in bullets))
        path.write_text(_LEARNINGS_HEADER + body + "\n", encoding="utf-8")
        return path

    def _feature_dir(self, feat_id: str, slug: str) -> Path:
        d = self.features_dir / f"{feat_id}-{slug}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_events(self, feature_dir: Path, lines: list[str]) -> None:
        (feature_dir / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _score(self, learnings_path: Path) -> dict:
        return score_learnings_entries(
            learnings_path=learnings_path, features_dir=self.features_dir
        )


class TestCostIsThePrimarySignal(_Harness):
    def test_higher_attempt_cost_ranks_first_even_with_less_reach(self):
        learnings = self._write_learnings([
            ("FEAT-2026-0001/G1", "expensive lesson"),
            ("FEAT-2026-0002/G1", "cheap but widely cited lesson"),
        ])
        expensive_dir = self._feature_dir("FEAT-2026-0001", "expensive")
        self._write_events(expensive_dir, [
            _event("FEAT-2026-0001/T01", "gate_fail", cost_usd=12.0,
                   failure_signature="boom"),
        ])
        cheap_dir = self._feature_dir("FEAT-2026-0002", "cheap")
        self._write_events(cheap_dir, [
            _event("FEAT-2026-0002/T01", "gate_fail", cost_usd=0.50,
                   failure_signature="tiny"),
        ])
        other_dir = self._feature_dir("FEAT-2026-0003", "citer")
        (other_dir / "PLAN.md").write_text(
            "cites FEAT-2026-0002/G1 five times: "
            "FEAT-2026-0002/G1 FEAT-2026-0002/G1 FEAT-2026-0002/G1 FEAT-2026-0002/G1",
            encoding="utf-8",
        )

        result = self._score(learnings)
        tags = [e["tag"] for e in result["entries"]]
        self.assertEqual(tags[0], "FEAT-2026-0001/G1")
        self.assertEqual(tags[1], "FEAT-2026-0002/G1")
        self.assertGreater(
            [e for e in result["entries"] if e["tag"] == "FEAT-2026-0002/G1"][0]["reach"],
            [e for e in result["entries"] if e["tag"] == "FEAT-2026-0001/G1"][0]["reach"],
        )

    def test_only_non_passed_attempts_are_costed(self):
        learnings = self._write_learnings([("FEAT-2026-0004/G1", "text")])
        d = self._feature_dir("FEAT-2026-0004", "slug")
        self._write_events(d, [
            _event("FEAT-2026-0004/T01", "passed", cost_usd=99.0),
            _event("FEAT-2026-0004/T01", "gate_fail", cost_usd=3.0,
                   failure_signature="sig"),
        ])
        result = self._score(learnings)
        self.assertEqual(result["entries"][0]["cost_usd"], 3.0)

    def test_events_outside_the_entrys_feature_are_not_costed(self):
        learnings = self._write_learnings([("FEAT-2026-0005/G1", "text")])
        self._feature_dir("FEAT-2026-0005", "slug")
        other = self._feature_dir("FEAT-2026-0006", "other")
        self._write_events(other, [
            _event("FEAT-2026-0006/T01", "gate_fail", cost_usd=500.0,
                   failure_signature="unrelated"),
        ])
        result = self._score(learnings)
        self.assertEqual(result["entries"][0]["cost_usd"], 0.0)
        self.assertEqual(result["entries"][0]["failure_signatures"], [])


class TestReachExcludesSelfCitation(_Harness):
    def test_citation_from_the_owning_feature_does_not_count(self):
        """The whole signal per the WU: a naive substring scan over
        `.specfuse/features/**` counts self-citations; excluding the owning
        feature's own files must reduce the count."""
        learnings = self._write_learnings([("FEAT-2026-0007/G1", "text")])
        own_dir = self._feature_dir("FEAT-2026-0007", "slug")
        (own_dir / "RETROSPECTIVE.md").write_text(
            "as recorded in FEAT-2026-0007/G1, twice: FEAT-2026-0007/G1",
            encoding="utf-8",
        )

        naive_hits = sum(
            1 for p in own_dir.rglob("*") if p.is_file()
            and "FEAT-2026-0007/G1" in p.read_text(encoding="utf-8")
        )
        self.assertGreater(naive_hits, 0, "fixture must actually self-cite")

        result = self._score(learnings)
        self.assertEqual(result["entries"][0]["reach"], 0)

    def test_citation_from_another_feature_does_count(self):
        learnings = self._write_learnings([("FEAT-2026-0008/G1", "text")])
        self._feature_dir("FEAT-2026-0008", "slug")
        citer = self._feature_dir("FEAT-2026-0009", "citer")
        (citer / "PLAN.md").write_text("per FEAT-2026-0008/G1", encoding="utf-8")

        result = self._score(learnings)
        self.assertEqual(result["entries"][0]["reach"], 1)

    def test_meta_tag_has_no_owning_folder_to_exclude(self):
        learnings = self._write_learnings([("meta/some-lesson", "text")])
        citer = self._feature_dir("FEAT-2026-0010", "citer")
        (citer / "PLAN.md").write_text("see meta/some-lesson", encoding="utf-8")

        result = self._score(learnings)
        entry = result["entries"][0]
        self.assertEqual(entry["cost_usd"], 0.0)
        self.assertEqual(entry["reach"], 1)


class TestScoredEntryCarriesItsInputs(_Harness):
    def test_every_entry_exposes_cost_reach_and_signature(self):
        learnings = self._write_learnings([("FEAT-2026-0011/G1", "text")])
        d = self._feature_dir("FEAT-2026-0011", "slug")
        self._write_events(d, [
            _event("FEAT-2026-0011/T01", "gate_fail", cost_usd=2.5,
                   failure_signature="assert_foo_failed"),
        ])
        entry = self._score(learnings)["entries"][0]
        for key in ("tag", "text", "cost_usd", "reach", "failure_signatures",
                    "feature_ids"):
            self.assertIn(key, entry)
        self.assertEqual(entry["cost_usd"], 2.5)
        self.assertEqual(entry["failure_signatures"], ["assert_foo_failed"])
        self.assertEqual(entry["feature_ids"], ["FEAT-2026-0011"])


class TestOutputStatesTheTiebreakBias(_Harness):
    def test_reach_caveat_is_present_and_names_tiebreak_and_age(self):
        learnings = self._write_learnings([("FEAT-2026-0012/G1", "text")])
        result = self._score(learnings)
        self.assertIn("reach_caveat", result)
        caveat = result["reach_caveat"].lower()
        self.assertIn("tiebreak", caveat)
        self.assertIn("older", caveat)
        self.assertEqual(result["reach_caveat"], LEARNINGS_REACH_TIEBREAK_CAVEAT)


class TestMultiFeatureTag(_Harness):
    def test_costs_and_exclusions_apply_across_every_named_feature(self):
        learnings = self._write_learnings([
            ("FEAT-2026-0013/G1-CLOSE; FEAT-2026-0014/G2-CLOSE", "shared lesson"),
        ])
        d13 = self._feature_dir("FEAT-2026-0013", "a")
        self._write_events(d13, [
            _event("FEAT-2026-0013/T01", "gate_fail", cost_usd=1.0,
                   failure_signature="sig-a"),
        ])
        d14 = self._feature_dir("FEAT-2026-0014", "b")
        self._write_events(d14, [
            _event("FEAT-2026-0014/T01", "gate_fail", cost_usd=4.0,
                   failure_signature="sig-b"),
        ])
        (d13 / "PLAN.md").write_text("FEAT-2026-0013/G1-CLOSE", encoding="utf-8")
        (d14 / "PLAN.md").write_text("FEAT-2026-0014/G2-CLOSE", encoding="utf-8")

        entry = self._score(learnings)["entries"][0]
        self.assertEqual(entry["cost_usd"], 5.0)
        self.assertEqual(entry["reach"], 0)
        self.assertEqual(entry["failure_signatures"], ["sig-a", "sig-b"])
        self.assertEqual(entry["feature_ids"],
                          ["FEAT-2026-0013", "FEAT-2026-0014"])


class TestLiveRepoSmoke(unittest.TestCase):
    """`failure_signature` must map onto a meaningful share of this repo's
    actual corpus (§ Escalation triggers), not just the isolated fixtures
    above."""

    def test_runs_clean_against_this_repos_real_learnings_and_events(self):
        result = score_learnings_entries()
        self.assertGreater(len(result["entries"]), 100)
        with_signature = sum(
            1 for e in result["entries"] if e["failure_signatures"]
        )
        self.assertGreater(
            with_signature / len(result["entries"]), 0.25,
            "failure_signature should resolve for a meaningful share of entries",
        )


if __name__ == "__main__":
    unittest.main()
