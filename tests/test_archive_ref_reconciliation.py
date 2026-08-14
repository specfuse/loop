#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""auto_archive_feature reconciles the moved section — issues #1169 and #1038.

The archiver moved a detail section into roadmap-archive.md verbatim. Two
consequences, one cause:

  #1169 — cross-references break in BOTH directions. A bare `#feat-…` link
          inside the moved section no longer resolves once the section lives in
          another file, and inbound links in roadmap.md that pointed at the
          moved feature's anchor break when that anchor leaves.

  #1038 — the section's `**Status:`** marker is preserved against a row that
          now says `done`, so lint_roadmap errors on the disagreement. Observed
          three times: FEAT-2026-0056, FEAT-2026-0075, FEAT-2026-0045.

Both are fixed by one reconciliation pass. These tests pin the pass's edges:
a self-reference must stay bare (its anchor travels to the archive), a
reference to an ALREADY-archived feature must stay bare (both ends are in the
archive), and only a reference to a still-inline feature is rewritten.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


_ARCHIVE_EMPTY = textwrap.dedent("""\
    ---
    project: test
    ---

    # Archived feature details

    This file holds the detail sections for features whose status has reached
    `done` or `abandoned`.

    <!-- Archived sections appended below -->
    """)


def _roadmap(section_body: str, *, status: str = "done", extra: str = "") -> str:
    return textwrap.dedent("""\
        ---
        project: test
        ---

        # Roadmap

        | Feature ID | Title | Status | Folder | Detail |
        |------------|-------|--------|--------|--------|
        | FEAT-2026-9999 | Target feature | {status} | — | — |
        | FEAT-2026-8888 | Still inline | planned | — | — |

        ## FEAT-2026-9999 — Target feature

        {body}

        <a id="feat-2026-8888"></a>
        ## FEAT-2026-8888 — Still inline

        An unrelated live feature.
        {extra}
        """).format(status=status, body=section_body, extra=extra)


class _Harness(unittest.TestCase):
    def _run(self, roadmap_text, archive_text=_ARCHIVE_EMPTY, feature="FEAT-2026-9999"):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / ".specfuse").mkdir()
        (root / ".specfuse" / "roadmap.md").write_text(roadmap_text)
        (root / ".specfuse" / "roadmap-archive.md").write_text(archive_text)
        result = loop.auto_archive_feature(feature, root)
        self.addCleanup(self.tmp.cleanup)
        return (
            result,
            (root / ".specfuse" / "roadmap.md").read_text(),
            (root / ".specfuse" / "roadmap-archive.md").read_text(),
        )


class TestOutboundRefs(_Harness):
    """Links INSIDE the moved section (#1169)."""

    def test_ref_to_still_inline_feature_is_rewritten(self):
        result, _roadmap_text, archive = self._run(
            _roadmap("Blocked by [FEAT-2026-8888](#feat-2026-8888) — the reason.")
        )
        self.assertEqual(result, "archived")
        self.assertIn("[FEAT-2026-8888](roadmap.md#feat-2026-8888)", archive)
        self.assertNotIn("[FEAT-2026-8888](#feat-2026-8888)", archive)

    def test_self_reference_stays_bare(self):
        """The feature's own anchor travels to the archive, so it still resolves."""
        _result, _roadmap_text, archive = self._run(
            _roadmap("See [this feature](#feat-2026-9999) above.")
        )
        self.assertIn("[this feature](#feat-2026-9999)", archive)
        self.assertNotIn("roadmap.md#feat-2026-9999", archive)

    def test_ref_to_already_archived_feature_stays_bare(self):
        """Both ends live in the archive, so a bare anchor resolves fine."""
        archive_with_prior = _ARCHIVE_EMPTY + '\n<a id="feat-2026-7777"></a>\n## FEAT-2026-7777 — Older\n\nDone long ago.\n'
        _result, _roadmap_text, archive = self._run(
            _roadmap("Follows [FEAT-2026-7777](#feat-2026-7777)."),
            archive_text=archive_with_prior,
        )
        self.assertIn("[FEAT-2026-7777](#feat-2026-7777)", archive)
        self.assertNotIn("roadmap.md#feat-2026-7777", archive)

    def test_already_qualified_ref_is_left_alone(self):
        """An explicit roadmap.md#… or roadmap-archive.md#… target is not double-prefixed."""
        _result, _roadmap_text, archive = self._run(
            _roadmap("Prior art: [FEAT-2026-7777](roadmap-archive.md#feat-2026-7777).")
        )
        self.assertIn("[FEAT-2026-7777](roadmap-archive.md#feat-2026-7777)", archive)
        self.assertNotIn("roadmap.md#roadmap-archive.md", archive)


class TestInboundRefs(_Harness):
    """Links ELSEWHERE that point at the moved section (#1169)."""

    def test_inbound_ref_in_another_section_is_rewritten(self):
        roadmap_text = _roadmap(
            "Target body.",
            extra="\nBlocked by [FEAT-2026-9999](#feat-2026-9999) — needs it first.\n",
        )
        _result, roadmap_after, _archive = self._run(roadmap_text)
        self.assertIn(
            "[FEAT-2026-9999](roadmap-archive.md#feat-2026-9999)", roadmap_after
        )
        self.assertNotIn("[FEAT-2026-9999](#feat-2026-9999)", roadmap_after)

    def test_inbound_rewrite_does_not_touch_other_features_refs(self):
        roadmap_text = _roadmap(
            "Target body.",
            extra="\nSee [FEAT-2026-8888](#feat-2026-8888) — unrelated.\n",
        )
        _result, roadmap_after, _archive = self._run(roadmap_text)
        self.assertIn("[FEAT-2026-8888](#feat-2026-8888)", roadmap_after)


class TestInboundRefsFromArchive(_Harness):
    """The third inbound direction (#1425).

    #1182 reconciled two directions: outbound links inside the moved section, and
    inbound bare `](#feat-this-one)` links elsewhere in `roadmap.md`. It did not
    cover inbound links held by sections ALREADY in the archive, which use the
    qualified `](roadmap.md#feat-this-one)` form. Those are correct while the
    target is inline and dangle the moment it moves — and the archive is where
    every previously-closed feature's prose lives, so the population only grows.

    Observed five times in one morning archiving FEAT-2026-0044, 0047 and 0048,
    each one hand-fixed after CI went red on a tree nobody edited.
    """

    _ARCHIVE_WITH_INBOUND_REF = textwrap.dedent("""\
        ---
        project: test
        ---

        # Archived feature details

        This file holds the detail sections for features whose status has reached
        `done` or `abandoned`.

        <!-- Archived sections appended below -->

        <a id="feat-2026-7777"></a>
        ## FEAT-2026-7777 — An already-archived feature

        Outbound notification is [FEAT-2026-9999](roadmap.md#feat-2026-9999).
        Unrelated: [FEAT-2026-8888](roadmap.md#feat-2026-8888).
        """)

    def test_qualified_inbound_ref_in_the_archive_is_made_bare(self):
        _result, _roadmap_after, archive = self._run(
            _roadmap("Target body."), archive_text=self._ARCHIVE_WITH_INBOUND_REF
        )
        self.assertIn("[FEAT-2026-9999](#feat-2026-9999)", archive)
        self.assertNotIn("[FEAT-2026-9999](roadmap.md#feat-2026-9999)", archive)

    def test_other_features_qualified_refs_are_untouched(self):
        # Scoped to THIS feature's anchor, mirroring the roadmap-side inbound
        # rewrite. FEAT-2026-8888 is still inline, so its qualified ref is
        # correct and must survive.
        _result, _roadmap_after, archive = self._run(
            _roadmap("Target body."), archive_text=self._ARCHIVE_WITH_INBOUND_REF
        )
        self.assertIn("[FEAT-2026-8888](roadmap.md#feat-2026-8888)", archive)

    def test_the_link_graph_is_clean_after_archiving(self):
        # The end-to-end property the gate actually asserts: no ref anywhere in
        # the archive still points at roadmap.md for an anchor the archive owns.
        _result, _roadmap_after, archive = self._run(
            _roadmap("Target body."), archive_text=self._ARCHIVE_WITH_INBOUND_REF
        )
        owned = {"feat-2026-9999", "feat-2026-7777"}
        for slug in owned:
            with self.subTest(anchor=slug):
                self.assertNotIn(f"](roadmap.md#{slug})", archive)


class TestStatusMarker(_Harness):
    """The stale **Status:** marker (#1038)."""

    def test_status_marker_is_rewritten_to_match_the_row(self):
        _result, _roadmap_text, archive = self._run(
            _roadmap("Body prose.\n\n**Status: active.**")
        )
        self.assertIn("**Status: done.**", archive)
        self.assertNotIn("**Status: active.**", archive)

    def test_prose_after_the_marker_is_preserved(self):
        """lint_roadmap's own message specifies keeping any prose after the marker."""
        _result, _roadmap_text, archive = self._run(
            _roadmap("**Status: active — hedged, awaiting acceptance.** More detail here.")
        )
        self.assertIn("**Status: done.**", archive)
        self.assertIn("More detail here.", archive)

    def test_section_without_a_status_marker_is_untouched(self):
        _result, _roadmap_text, archive = self._run(_roadmap("Just body prose."))
        self.assertIn("Just body prose.", archive)
        self.assertNotIn("**Status:", archive)

    def test_a_prose_mention_of_the_marker_is_not_the_marker(self):
        """#2345: the pattern was unanchored, so `count=1` rewrote whichever
        `**Status:...**` came first — including one quoted mid-sentence. A
        section discussing the roadmap format is exactly where that happens.

        Observed on FEAT-2026-0079, whose own detail prose quotes the marker
        by name: the sentence became `its **Status: done.** marker` while the
        real trailing marker kept saying `planned` against a `done` row, and
        three `lint_roadmap` tests went red against the real tree."""
        _result, _roadmap_text, archive = self._run(
            _roadmap(
                "**Why.** #1169 taught the driver to reconcile its "
                "`**Status:**` marker.\n\n**Status: active.**"
            )
        )
        # The quoted mention is prose about the format, not a status claim.
        self.assertIn("its `**Status:**` marker", archive)
        # The real marker — anchored at the start of its own line — is the one
        # that had to move.
        self.assertIn("\n**Status: done.**", archive)
        self.assertNotIn("**Status: active.**", archive)

    def test_only_the_first_standalone_marker_is_rewritten(self):
        """`count=1` is still right once the pattern is anchored: a section
        carries one status marker, and a second standalone one would be a
        different defect than this pass owns."""
        _result, _roadmap_text, archive = self._run(
            _roadmap("**Status: active.**\n\nBody.\n\n**Status: active.**")
        )
        self.assertIn("**Status: done.**", archive)

    def test_abandoned_row_status_is_honoured_not_hardcoded_done(self):
        _result, _roadmap_text, archive = self._run(
            _roadmap("Body.\n\n**Status: active.**", status="abandoned")
        )
        self.assertIn("**Status: abandoned.**", archive)


class TestNoRegression(_Harness):
    """The existing contract must survive the reconciliation pass."""

    def test_anchor_and_back_link_still_written(self):
        result, roadmap_after, archive = self._run(_roadmap("Body."))
        self.assertEqual(result, "archived")
        self.assertIn('<a id="feat-2026-9999"></a>', archive)
        self.assertIn("[→ archive](roadmap-archive.md#feat-2026-9999)", roadmap_after)

    def test_section_removed_from_roadmap(self):
        _result, roadmap_after, _archive = self._run(_roadmap("Body."))
        self.assertNotIn("## FEAT-2026-9999 — Target feature", roadmap_after)


if __name__ == "__main__":
    unittest.main()
