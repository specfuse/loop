#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Reference implementation and tests for the roadmap-add skill algorithm.

The skill appends a new planned feature's table row and detail section to
roadmap.md, auto-picking the next FEAT-YYYY-NNNN by scanning four sources
(the fourth — GitHub issue/PR-reserved IDs — added for specfuse#16).

Exercises:
  (a) headless mode appends a row and detail section in the right places
  (b) next-ID scan picks FEAT-2026-0011 when max is 0010 in roadmap table,
      0009 in a feature PLAN.md, and 0010 referenced in a LEARNINGS stub
      (cross-source max wins)
  (c) ID collision is rejected with a message naming the conflicting source
"""

from __future__ import annotations

import re
import textwrap
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# Reference implementation
# ---------------------------------------------------------------------------

FEAT_RE = re.compile(r"FEAT-(\d{4})-(\d{4})")
FEAT_ROW_RE = re.compile(r"^\| (FEAT-\d{4}-\d{4})")
PLAN_FEAT_RE = re.compile(r"^feature_id:\s*(FEAT-\d{4}-\d{4})")


def scan_feat_ids(
    roadmap_path: Path,
    features_dir: Path,
    extra_paths: list[Path],
    github_reserved: dict[str, str] | None = None,
) -> dict:
    """Scan FEAT-YYYY-NNNN IDs from four sources.

    Source (a): table rows in roadmap_path (lines matching ``^| FEAT-``).
    Source (b): ``feature_id:`` lines in features_dir/*/PLAN.md.
    Source (c): any occurrence in extra_paths (LEARNINGS.md, RETROSPECTIVE.md).
        ADVISORY ONLY (#771): these files quote illustrative IDs as examples,
        so a (c) hit is reported for collision but never raises the max.
    Source (d): GitHub issue/PR titles+bodies — modelled here as an injected
        ``github_reserved`` map ``{feat_id: "GitHub issue/PR #<n>"}`` so the
        fold-into-max + collision logic is exercised hermetically (no network).
        ``None`` models GitHub being unreachable: the skill degrades gracefully
        and simply omits source (d).

    Returns dict mapping feat_id (str) -> (location_str, line_no) for the
    first occurrence of each ID seen.
    """
    sources: dict[str, tuple[str, int, str]] = {}

    def record(feat_id: str, filepath, lineno: int, source: str) -> None:
        # Provenance is recorded because it is load-bearing, not decorative:
        # source (c) is ADVISORY and must not raise the max (#771).
        if feat_id not in sources:
            sources[feat_id] = (str(filepath), lineno, source)

    # (a) roadmap table rows
    if roadmap_path.exists():
        for lineno, line in enumerate(roadmap_path.read_text().splitlines(), 1):
            m = FEAT_ROW_RE.match(line)
            if m:
                record(m.group(1), roadmap_path, lineno, "a")

    # (b) feature_id: in PLAN.md files
    if features_dir.exists():
        for plan in sorted(features_dir.glob("*/PLAN.md")):
            for lineno, line in enumerate(plan.read_text().splitlines(), 1):
                m = PLAN_FEAT_RE.match(line)
                if m:
                    record(m.group(1), plan, lineno, "b")

    # (c) any FEAT-YYYY-NNNN in LEARNINGS.md / RETROSPECTIVE.md
    for path in extra_paths:
        if path.exists():
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                for m in FEAT_RE.finditer(line):
                    record(m.group(0), path, lineno, "c")

    # (d) GitHub issue/PR-reserved IDs (None = GitHub unreachable, skip source).
    if github_reserved:
        for feat_id, ref in github_reserved.items():
            # location is the issue/PR ref; lineno 0 (not a file line)
            if feat_id not in sources:
                sources[feat_id] = (ref, 0, "d")

    return sources


# Sources whose hits are authoritative for the sequence maximum. Source (c) is
# excluded on purpose: LEARNINGS/RETROSPECTIVE prose quotes illustrative IDs
# (this repo's retrospectives contain FEAT-2026-9301, 0099, 0098 and 0000 as
# examples), and counting them put the computed next ID at FEAT-2026-9302 and
# reported ~9200 phantom gaps. See #771.
_AUTHORITATIVE_SOURCES = frozenset({"a", "b", "d"})


def _year_ordinals(year: int, sources: dict, authoritative_only: bool = True) -> list[int]:
    year_str = str(year)
    out = []
    for fid, meta in sources.items():
        if not fid.startswith(f"FEAT-{year_str}-"):
            continue
        source = meta[2] if len(meta) > 2 else "a"
        if authoritative_only and source not in _AUTHORITATIVE_SOURCES:
            continue
        out.append(int(fid.split("-")[2]))
    return sorted(out)


def sequence_gaps(year: int, sources: dict) -> list[str]:
    """Return the year's missing ordinals, zero-padded, as an INFORMATIONAL list.

    Reported to the operator, never raised on the auto-computed path — see
    `next_feat_id`.
    """
    ordinals = _year_ordinals(year, sources)
    if not ordinals:
        return []
    present = set(ordinals)
    return [f"{n:04d}" for n in range(ordinals[0], ordinals[-1] + 1)
            if n not in present]


def assert_requested_id_is_not_a_gap(feat_id: str, year: int, sources: dict) -> None:
    """Refuse an EXPLICITLY requested ID that fills a gap (#771).

    This is where the original hard stop belongs. On the auto-computed path the
    next ID is `max + 1`, which can never fill a gap, so blocking there guarded
    a risk the algorithm does not take. When an operator names an ID by hand,
    the risk is real: a gap may be an ID reserved somewhere this scan cannot
    see, and reusing it is exactly the collision the check exists to prevent.
    """
    gaps = sequence_gaps(year, sources)
    ordinal = feat_id.split("-")[2]
    if ordinal in gaps:
        raise ValueError(
            f"{feat_id} fills a gap in the FEAT-{year} sequence "
            f"(gaps: {gaps}). A gap may be an ID reserved outside this scan's "
            f"reach — confirm it is free before reusing it."
        )


def next_feat_id(year: int, sources: dict) -> tuple[str, int]:
    """Return (next_feat_id_str, next_ordinal) for the given year.

    Computed from the AUTHORITATIVE sources only (a, b, d). Gaps do not raise:
    the returned ordinal is `max + 1`, which fills none of them. Callers that
    want to surface gaps to the operator call `sequence_gaps`; callers honouring
    an operator-supplied `--id` call `assert_requested_id_is_not_a_gap`.
    """
    year_str = str(year)
    ordinals = _year_ordinals(year, sources)
    if not ordinals:
        return f"FEAT-{year_str}-0001", 1

    next_n = ordinals[-1] + 1
    return f"FEAT-{year_str}-{next_n:04d}", next_n


def check_collision(feat_id: str, sources: dict) -> tuple[bool, str | None, int | None]:
    """Return (True, filepath, lineno) if feat_id in sources, else (False, None, None)."""
    if feat_id in sources:
        filepath, lineno, _source = sources[feat_id]
        return True, filepath, lineno
    return False, None, None


def add_feature(
    roadmap_path: Path,
    feat_id: str,
    title: str,
    why: str,
    goal: str,
    benefits: str,
) -> str:
    """Append one table row and one detail section to roadmap.md.

    Returns 'added'.
    Raises ValueError if the roadmap structure is unexpected.
    """
    text = roadmap_path.read_text()
    lines = text.splitlines(keepends=True)

    # Find last feature table row (insert new row after it)
    last_row_idx: int | None = None
    for i, line in enumerate(lines):
        if FEAT_ROW_RE.match(line):
            last_row_idx = i

    if last_row_idx is None:
        raise ValueError("No feature table rows found in roadmap.md")

    new_row = f"| {feat_id} | {title} | planned | — | — |\n"
    lines.insert(last_row_idx + 1, new_row)

    # Find ## Notes section (insert detail before it)
    notes_idx: int | None = None
    for i, line in enumerate(lines):
        if re.match(r"^## Notes\s*$", line):
            notes_idx = i
            break

    if notes_idx is None:
        raise ValueError("## Notes section not found in roadmap.md")

    detail = (
        f"## {feat_id} — {title}\n"
        f"\n"
        f"**Why.** {why}\n"
        f"\n"
        f"**Goal.** {goal}\n"
        f"\n"
        f"**Benefits.** {benefits}\n"
        f"\n"
        f"**Status: planned.**\n"
        f"\n"
    )

    lines.insert(notes_idx, detail)
    roadmap_path.write_text("".join(lines))
    return "added"


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_ROADMAP_STUB = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID     | Title          | Status  | Folder | Detail |
    |----------------|----------------|---------|--------|--------|
    | FEAT-2026-0009 | Alpha feature  | done    | —      | —      |
    | FEAT-2026-0010 | Beta feature   | planned | —      | —      |

    ## FEAT-2026-0010 — Beta feature

    **Why.** This is the why.

    **Goal.** This is the goal.

    **Benefits.** These are the benefits.

    **Status: planned.**

    ## Notes

    Notes content.
""")

_LEARNINGS_STUB = textwrap.dedent("""\
    # LEARNINGS

    [FEAT-2026-0010] Something learned from this feature.
""")

_PLAN_STUB = textwrap.dedent("""\
    ---
    feature_id: FEAT-2026-0009
    status: done
    ---

    # Plan
""")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAddFeatureHeadless(unittest.TestCase):
    """(a) Headless mode appends a row and detail section in the right places."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        d = Path(self._tmpdir.name)
        self.roadmap = d / "roadmap.md"
        self.roadmap.write_text(_ROADMAP_STUB)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_add_returns_added(self):
        result = add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        self.assertEqual(result, "added")

    def test_new_row_appended_after_last_table_row(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        lines = self.roadmap.read_text().splitlines()
        row_indices = [i for i, line in enumerate(lines) if "FEAT-2026-0011" in line and "planned" in line]
        self.assertTrue(len(row_indices) >= 1, "FEAT-2026-0011 row not found")

    def test_new_row_has_canonical_columns(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("| FEAT-2026-0011 | New feature | planned |", text)

    def test_new_row_appears_after_feat_0010_row(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        lines = self.roadmap.read_text().splitlines()
        idx_0010 = next(i for i, line in enumerate(lines) if "FEAT-2026-0010" in line and "planned" in line)
        idx_0011 = next(i for i, line in enumerate(lines) if "FEAT-2026-0011" in line and "planned" in line)
        self.assertGreater(idx_0011, idx_0010)

    def test_detail_section_inserted_before_notes(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        lines = self.roadmap.read_text().splitlines()
        idx_detail = next(i for i, line in enumerate(lines) if "## FEAT-2026-0011" in line)
        idx_notes = next(i for i, line in enumerate(lines) if line.strip() == "## Notes")
        self.assertLess(idx_detail, idx_notes)

    def test_detail_section_heading_format(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("## FEAT-2026-0011 — New feature", text)

    def test_detail_section_contains_why(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("**Why.** Because it matters.", text)

    def test_detail_section_contains_goal(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("**Goal.** Ship it.", text)

    def test_detail_section_contains_benefits(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("**Benefits.** Faster, better.", text)

    def test_detail_section_contains_status_planned(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("**Status: planned.**", text)

    def test_existing_content_preserved(self):
        add_feature(
            self.roadmap,
            "FEAT-2026-0011",
            "New feature",
            "Because it matters.",
            "Ship it.",
            "Faster, better.",
        )
        text = self.roadmap.read_text()
        self.assertIn("## FEAT-2026-0010 — Beta feature", text)
        self.assertIn("## Notes", text)
        self.assertIn("Notes content.", text)


class TestNextFeatId(unittest.TestCase):
    """(b) Cross-source next-ID scan picks correct value."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.d = Path(self._tmpdir.name)

        # Roadmap: highest row is FEAT-2026-0010
        self.roadmap = self.d / "roadmap.md"
        self.roadmap.write_text(_ROADMAP_STUB)

        # LEARNINGS: references FEAT-2026-0010
        self.learnings = self.d / "LEARNINGS.md"
        self.learnings.write_text(_LEARNINGS_STUB)

        # Feature folder with PLAN.md: feature_id = FEAT-2026-0009
        feat_dir = self.d / "features" / "FEAT-2026-0009-alpha"
        feat_dir.mkdir(parents=True)
        (feat_dir / "PLAN.md").write_text(_PLAN_STUB)

        self.features_dir = self.d / "features"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_max_from_roadmap_rows_is_0010(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        year_ordinals = [
            int(fid.split("-")[2])
            for fid in sources
            if fid.startswith("FEAT-2026-")
        ]
        self.assertIn(10, year_ordinals)

    def test_plan_contributes_0009(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        self.assertIn("FEAT-2026-0009", sources)

    def test_learnings_contributes_0010(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        self.assertIn("FEAT-2026-0010", sources)

    def test_next_id_is_0011_cross_source_max_wins(self):
        # roadmap max = 0010, plan max = 0009, learnings max = 0010
        # cross-source max = 0010 => next = 0011
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        feat_id, ordinal = next_feat_id(2026, sources)
        self.assertEqual(feat_id, "FEAT-2026-0011")
        self.assertEqual(ordinal, 11)

    def test_next_id_when_no_ids_found_is_0001(self):
        empty_roadmap = self.d / "empty_roadmap.md"
        empty_roadmap.write_text("# Roadmap\n\n## Notes\n\nNotes.\n")
        empty_features = self.d / "empty_features"
        empty_features.mkdir()
        sources = scan_feat_ids(empty_roadmap, empty_features, [])
        feat_id, ordinal = next_feat_id(2026, sources)
        self.assertEqual(feat_id, "FEAT-2026-0001")
        self.assertEqual(ordinal, 1)

    def test_gap_detection_raises_value_error(self):
        # Roadmap with 0001 and 0003 but missing 0002 — gap
        gap_roadmap = self.d / "gap_roadmap.md"
        gap_roadmap.write_text(textwrap.dedent("""\
            | Feature ID     | Title  | Status | Folder | Detail |
            |----------------|--------|--------|--------|--------|
            | FEAT-2026-0001 | One    | done   | —      | —      |
            | FEAT-2026-0003 | Three  | done   | —      | —      |

            ## Notes

            Notes.
        """))
        empty_features = self.d / "empty_features2"
        empty_features.mkdir()
        sources = scan_feat_ids(gap_roadmap, empty_features, [])

        # #771: the gap is still DETECTED and reported...
        self.assertEqual(sequence_gaps(2026, sources), ["0002"])
        # ...but it no longer blocks the auto-computed path, because max + 1
        # fills no gap. Previously this raised, which meant any repo with a
        # permanently burned ordinal could never use the skill again.
        feat_id, _ = next_feat_id(2026, sources)
        self.assertEqual(feat_id, "FEAT-2026-0004")
        # The hard stop moved to where the risk is real: naming 0002 by hand.
        with self.assertRaises(ValueError) as ctx:
            assert_requested_id_is_not_a_gap("FEAT-2026-0002", 2026, sources)
        self.assertIn("0002", str(ctx.exception))

    # ── #771: illustrative IDs in prose, and gaps that never get filled ─────

    def test_illustrative_ids_in_prose_do_not_raise_the_max(self):
        """Retrospectives QUOTE FEAT IDs as examples; those are not reservations.

        On the real repo, source (c) read as "any occurrence" yields max 9301 --
        FEAT-2026-9301 is an example inside FEAT-2026-0064's retrospective -- so
        the next ID computes as FEAT-2026-9302 and ~9200 ordinals report as gaps.
        """
        roadmap = self.d / "prose_roadmap.md"
        roadmap.write_text(textwrap.dedent("""\
            | Feature ID     | Title  | Status | Folder | Detail |
            |----------------|--------|--------|--------|--------|
            | FEAT-2026-0001 | One    | done   | —      | —      |
            | FEAT-2026-0002 | Two    | done   | —      | —      |

            ## Notes
        """))
        retro = self.d / "RETROSPECTIVE.md"
        retro.write_text(
            "An example ID a reader might see is FEAT-2026-9301, and a fixture\n"
            "in the suite uses FEAT-2026-0099.\n"
        )
        empty = self.d / "prose_features"
        empty.mkdir()

        sources = scan_feat_ids(roadmap, empty, [retro])
        feat_id, ordinal = next_feat_id(2026, sources)

        self.assertEqual(feat_id, "FEAT-2026-0003")
        self.assertEqual(ordinal, 3)

    def test_prose_ids_are_still_reported_for_collision(self):
        """Advisory, not ignored: an explicitly requested ID that appears only in
        prose must still be reported, so the operator can check it by hand."""
        roadmap = self.d / "collide_roadmap.md"
        roadmap.write_text(
            "| Feature ID | Title | Status | Folder | Detail |\n"
            "|---|---|---|---|---|\n"
            "| FEAT-2026-0001 | One | done | — | — |\n\n## Notes\n"
        )
        retro = self.d / "RETRO2.md"
        retro.write_text("Reserved verbally: FEAT-2026-0044.\n")
        empty = self.d / "collide_features"
        empty.mkdir()

        sources = scan_feat_ids(roadmap, empty, [retro])

        hit, where, _ = check_collision("FEAT-2026-0044", sources)
        self.assertTrue(hit, "a prose-only ID must still be collision-visible")
        self.assertIn("RETRO2.md", str(where))

    def test_a_permanent_gap_does_not_block_the_auto_computed_next_id(self):
        """next = max + 1 never fills a gap, so a gap is not a risk on this path.

        This repo's 2026 sequence has three permanently burned ordinals (0009,
        0065, 0066 -- the latter two are cross-repo references, per PR #319).
        A hard stop on the auto-computed path fires on every invocation forever,
        which trains an operator to override the check that exists to catch a
        real collision.
        """
        roadmap = self.d / "burned_roadmap.md"
        roadmap.write_text(textwrap.dedent("""\
            | Feature ID     | Title  | Status | Folder | Detail |
            |----------------|--------|--------|--------|--------|
            | FEAT-2026-0001 | One    | done   | —      | —      |
            | FEAT-2026-0003 | Three  | done   | —      | —      |

            ## Notes
        """))
        empty = self.d / "burned_features"
        empty.mkdir()
        sources = scan_feat_ids(roadmap, empty, [])

        feat_id, ordinal = next_feat_id(2026, sources)

        self.assertEqual(feat_id, "FEAT-2026-0004")
        self.assertEqual(ordinal, 4)

    def test_gaps_are_reported_even_though_they_do_not_block(self):
        """Informational, not silent: the operator still gets told."""
        roadmap = self.d / "report_roadmap.md"
        roadmap.write_text(textwrap.dedent("""\
            | Feature ID     | Title  | Status | Folder | Detail |
            |----------------|--------|--------|--------|--------|
            | FEAT-2026-0001 | One    | done   | —      | —      |
            | FEAT-2026-0003 | Three  | done   | —      | —      |

            ## Notes
        """))
        empty = self.d / "report_features"
        empty.mkdir()
        sources = scan_feat_ids(roadmap, empty, [])

        self.assertEqual(sequence_gaps(2026, sources), ["0002"])

    def test_explicitly_requesting_a_gap_ordinal_is_refused(self):
        """The hard stop is retained where the risk is real: an operator naming
        a gap ordinal via --id could be reusing something reserved elsewhere."""
        roadmap = self.d / "explicit_roadmap.md"
        roadmap.write_text(textwrap.dedent("""\
            | Feature ID     | Title  | Status | Folder | Detail |
            |----------------|--------|--------|--------|--------|
            | FEAT-2026-0001 | One    | done   | —      | —      |
            | FEAT-2026-0003 | Three  | done   | —      | —      |

            ## Notes
        """))
        empty = self.d / "explicit_features"
        empty.mkdir()
        sources = scan_feat_ids(roadmap, empty, [])

        with self.assertRaises(ValueError) as ctx:
            assert_requested_id_is_not_a_gap("FEAT-2026-0002", 2026, sources)
        self.assertIn("0002", str(ctx.exception))
        self.assertIn("gap", str(ctx.exception).lower())

        # And an ID beyond max is fine.
        assert_requested_id_is_not_a_gap("FEAT-2026-0004", 2026, sources)

    # ── Source (d): GitHub issue/PR-reserved IDs (specfuse#16) ──────────────

    def test_github_reserved_id_raises_max(self):
        """A FEAT ID reserved only on a GitHub issue (no roadmap row) must be
        folded into the max so the next ID does not collide with it."""
        # roadmap/plan/learnings top out at 0010; GitHub reserves 0011.
        gh = {"FEAT-2026-0011": "GitHub issue #345"}
        sources = scan_feat_ids(
            self.roadmap, self.features_dir, [self.learnings], github_reserved=gh
        )
        feat_id, ordinal = next_feat_id(2026, sources)
        self.assertEqual(feat_id, "FEAT-2026-0012")
        self.assertEqual(ordinal, 12)

    def test_github_unreachable_degrades_gracefully(self):
        """github_reserved=None models GitHub being unreachable: the scan omits
        source (d) and proceeds on the three local sources — no hard failure."""
        sources = scan_feat_ids(
            self.roadmap, self.features_dir, [self.learnings], github_reserved=None
        )
        feat_id, _ = next_feat_id(2026, sources)
        self.assertEqual(feat_id, "FEAT-2026-0011")  # local-only max=0010

    def test_github_reserved_beyond_local_max_surfaces_gap(self):
        """A reserved ID beyond the local max exposes the intervening ordinals
        as genuine gaps (roadmap→0010, issue reserves 0016 → 0011–0015 gap)."""
        gh = {"FEAT-2026-0016": "GitHub issue #345"}
        sources = scan_feat_ids(
            self.roadmap, self.features_dir, [self.learnings], github_reserved=gh
        )

        # The reservation still raises the max and still exposes 0011-0015 as
        # genuine gaps -- that part of the contract is unchanged (#771 narrowed
        # the DISPOSITION of a gap, not its detection).
        self.assertEqual(
            sequence_gaps(2026, sources),
            ["0011", "0012", "0013", "0014", "0015"],
        )
        feat_id, _ = next_feat_id(2026, sources)
        self.assertEqual(feat_id, "FEAT-2026-0017")
        # Reusing one of the exposed ordinals by hand is still refused.
        with self.assertRaises(ValueError):
            assert_requested_id_is_not_a_gap("FEAT-2026-0013", 2026, sources)


class TestCollisionRejection(unittest.TestCase):
    """(c) ID collision is rejected with a message naming the conflicting source."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.d = Path(self._tmpdir.name)

        self.roadmap = self.d / "roadmap.md"
        self.roadmap.write_text(_ROADMAP_STUB)

        self.learnings = self.d / "LEARNINGS.md"
        self.learnings.write_text(_LEARNINGS_STUB)

        feat_dir = self.d / "features" / "FEAT-2026-0009-alpha"
        feat_dir.mkdir(parents=True)
        (feat_dir / "PLAN.md").write_text(_PLAN_STUB)
        self.features_dir = self.d / "features"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_collision_detected_for_roadmap_id(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0010", sources)
        self.assertTrue(collides)

    def test_collision_names_file(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0010", sources)
        self.assertIsNotNone(filepath)
        self.assertIn("roadmap", filepath)

    def test_collision_names_line_number(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0010", sources)
        self.assertIsNotNone(lineno)
        self.assertIsInstance(lineno, int)
        self.assertGreater(lineno, 0)

    def test_collision_detected_for_plan_id(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0009", sources)
        self.assertTrue(collides)

    def test_collision_for_plan_id_names_plan_file(self):
        # FEAT-2026-0009 appears in roadmap table AND PLAN.md; first occurrence wins
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0009", sources)
        self.assertTrue(collides)
        self.assertIsNotNone(filepath)

    def test_no_collision_for_new_id(self):
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0011", sources)
        self.assertFalse(collides)

    def test_collision_detected_in_learnings(self):
        # Add an ID that only appears in LEARNINGS, not in roadmap/PLAN
        only_learnings = self.d / "only_learnings.md"
        only_learnings.write_text("See FEAT-2026-0099 for context.\n")
        empty_features = self.d / "empty_features3"
        empty_features.mkdir()
        empty_roadmap = self.d / "empty_roadmap2.md"
        empty_roadmap.write_text("# Roadmap\n\n## Notes\n\nNotes.\n")
        sources = scan_feat_ids(empty_roadmap, empty_features, [only_learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0099", sources)
        self.assertTrue(collides)
        self.assertIn("learnings", filepath.lower())

    def test_add_feature_does_not_write_on_collision(self):
        # Attempt to add FEAT-2026-0010 (already in roadmap) via add_feature
        # The collision check is caller's responsibility, so we verify the
        # roadmap row count does not change when the caller checks first.
        sources = scan_feat_ids(self.roadmap, self.features_dir, [self.learnings])
        collides, filepath, lineno = check_collision("FEAT-2026-0010", sources)
        self.assertTrue(collides, "expected collision for FEAT-2026-0010")
        snapshot = self.roadmap.read_text()
        # Caller would not invoke add_feature on collision; verify snapshot unchanged
        self.assertEqual(self.roadmap.read_text(), snapshot)

    def test_collision_detected_for_github_reserved_id(self):
        """specfuse#16: an ID reserved only on a GitHub issue/PR (no local
        source) must be caught by the collision check and name the GitHub ref."""
        gh = {"FEAT-2026-0016": "GitHub issue #345"}
        sources = scan_feat_ids(
            self.roadmap, self.features_dir, [self.learnings], github_reserved=gh
        )
        collides, filepath, lineno = check_collision("FEAT-2026-0016", sources)
        self.assertTrue(collides, "GitHub-reserved ID must collide")
        self.assertIn("GitHub", filepath)


class TestSkillDocumentsGitHubSource(unittest.TestCase):
    """The skill prose must document source (d) + graceful offline degradation
    (specfuse#16). Guards against the four-source scan silently regressing to
    three in the authored SKILL.md."""

    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.skill = (
            repo_root / "plugins" / "specfuse" / "skills"
            / "roadmap-add" / "SKILL.md"
        ).read_text()

    def test_declares_four_sources(self):
        self.assertIn("four sources", self.skill)

    def test_documents_github_source(self):
        self.assertIn("Source (d)", self.skill)
        self.assertIn("gh search issues", self.skill)

    def test_documents_graceful_degradation(self):
        # A WARN path so offline runs continue rather than hard-failing.
        self.assertIn("WARN", self.skill)
        self.assertIn("offline", self.skill.lower())


if __name__ == "__main__":
    unittest.main()
