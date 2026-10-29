#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0247/T02 — every code site that parses a feature ID accepts the keyed form.

Each site is driven with a keyed ID and with the legacy ID through the same
code path; the keyed case fails on a site still carrying its own literal.
"""

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import (
    agent_policy,
    ids,
    changelog,
    gate_eval,
    gh_features,
    loop,
    promotion,
    upgrade_merge_gate,
)

KEYED = "FEAT-ACME-2026-0008"
LEGACY = "FEAT-2026-0008"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _agent_policy_queue(fid):
    return agent_policy._check_queue([fid]) == []


def _agent_policy_override(fid):
    return agent_policy._check_feature_overrides({fid: "human"}) == []


def _changelog_trace(fid):
    text = f"## [Unreleased]\n\n### Added\n\n- Something new ({fid}/T01)\n"
    return changelog.parse_changelog(text).ok


def _gh_title(fid):
    issues = [{"number": 1, "title": f"[{fid}] Thing", "labels": []}]
    got = gh_features.list_features("o/r", runner=lambda repo: issues)
    # list_features resolves an old ID through the cwd repo's alias map.
    return [c["feature_id"] for c in got] == [ids.resolve(".", fid)]


def _promotion(fid):
    return bool(promotion.FEATURE_ID_RE.match(fid))


def _merge_gate_dir(fid):
    return upgrade_merge_gate._is_feature_dir(Path(f"{fid}-slug"))


def _learnings(fid):
    m = loop._LEARNINGS_FEAT_ID_RE.match(f"{fid}/T01 something")
    return bool(m) and m.group(1) == fid


def _feature_arg(fid):
    return bool(loop._FEATURE_ID_RE.match(fid))


def _anchor_ref(fid):
    anchor = fid.lower()
    other = "feat-acme-2026-0009" if fid == KEYED else "feat-2026-0009"
    roadmap = f'<a id="{other}"></a>\n## x\n'
    text = f"See [x](#{other}).\n"
    out = loop._reconcile_moved_section(
        text, feat_id_lower=anchor, row_status="", roadmap_text=roadmap
    )
    return out == f"See [x](roadmap.md#{other}).\n"


def _resolve(fid):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".specfuse" / "features" / f"{fid}-x").mkdir(parents=True)
        got = gate_eval._resolve_feature_dir(fid, root)
        return got is not None and got.name == f"{fid}-x"


class CallSiteCases(unittest.TestCase):
    SITES = {
        "agent_policy queue": _agent_policy_queue,
        "agent_policy override": _agent_policy_override,
        "changelog trace": _changelog_trace,
        "gh_features title": _gh_title,
        "promotion": _promotion,
        "upgrade_merge_gate": _merge_gate_dir,
        "loop learnings": _learnings,
        "loop --feature": _feature_arg,
        "loop anchor ref": _anchor_ref,
        "gate_eval full id": _resolve,
    }

    def test_keyed_and_legacy_through_each_site(self):
        for name, check in self.SITES.items():
            with self.subTest(site=name, form="keyed"):
                self.assertTrue(check(KEYED))
            with self.subTest(site=name, form="legacy"):
                self.assertTrue(check(LEGACY))


class PartialLookup(unittest.TestCase):
    def _fixture(self, tmp, folder):
        root = Path(tmp)
        (root / ".specfuse" / "features" / folder).mkdir(parents=True)
        (root / ".specfuse" / "features" / "FEAT-2026-0001-other").mkdir()
        return root

    def test_ordinal_and_slug_resolve_keyed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp, "FEAT-ACME-2026-0008-x")
            for arg in ("0008", "x"):
                got = gate_eval._resolve_feature_dir(arg, root)
                self.assertEqual(got.name, "FEAT-ACME-2026-0008-x", arg)

    def test_ordinal_and_slug_resolve_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp, "FEAT-2026-0008-x")
            for arg in ("0008", "x"):
                got = gate_eval._resolve_feature_dir(arg, root)
                self.assertEqual(got.name, "FEAT-2026-0008-x", arg)

    def test_real_corpus_by_ordinal_matches_head(self):
        features = REPO_ROOT / ".specfuse" / "features"
        for d in sorted(p for p in features.iterdir() if p.is_dir()):
            parsed = ids.parse(d.name)
            if parsed is None:
                continue
            ordinal = f"{parsed.ordinal:04d}"
            expected = [
                c for c in sorted(features.iterdir())
                if c.is_dir() and ids.parse(c.name) is not None
                and ids.parse(c.name).ordinal == parsed.ordinal
            ]
            if len(expected) == 1:
                got = gate_eval._resolve_feature_dir(ordinal, REPO_ROOT)
                self.assertEqual(got, expected[0], ordinal)
            else:
                with self.assertRaises(ValueError):
                    gate_eval._resolve_feature_dir(ordinal, REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
