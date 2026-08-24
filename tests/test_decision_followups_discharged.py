#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Discharges two of FEAT-2026-0058's hedged-close follow-ups.

**Follow-up 3 — one unsigned override reported as seven errors.** An entry
with incomplete override provenance is refused by the parser and drops out of
`.entries`, so `valid_ids` loses its ID and every artifact citing that ID is
*additionally* reported as a dangling citation. Observed: 7 ERRORs for one
fault, six advising "Add the decision to the registry" for a decision that is
in the registry. `DecisionParseError` already carries `decision_id`, so the
ID is recoverable without a shape change.

**Follow-up 1 — the non-restatement check was inert on most files.** The
legitimate-quotation exemption was scoped per whole artifact: if a decision's
ID appeared anywhere in a document, a near-verbatim restatement anywhere else
in that same document was exempt. Worse than per-file in practice, because
`_DECISION_CITATION_RE` is `\\bD\\d+\\b` — the exemption triggered on the bare
token `D3` in unrelated prose, not on anything resembling a citation. Measured
on this feature's own artifacts the check was live on 3 of 24 (artifact,
decision) pairs, and `PLAN.md` — which restated D1 and D3 — was fully exempt.

The exemption is now scoped to the quotation: a restatement is legitimate
when the decision's ID appears near the restating passage, which is what
"quoting a decision while citing it" actually looks like. Quoting it in one
place and mentioning the ID a thousand words away is not.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

from tests.test_decision_citation_lint import _build_feature  # noqa: E402

_D4_UNSIGNED = """\
### D4

- **statement:** Close ceremony contract-change enumeration stays out of
  scope for this gate and is not re-derived from the registry.
- **owner:** platform-team
- **status:** `overridden-pending-signoff`
- **provenance:** PLAN.md D4
"""


class TestOneUnsignedOverrideReportsOnce(unittest.TestCase):
    """Follow-up 3's re-run condition, verbatim: the injection yields exactly
    one ERROR, the override one."""

    def _errors_for_injection(self) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_D4_UNSIGNED,
                # Three artifacts each citing D4 — without the fix, each adds
                # its own spurious dangling-citation ERROR on top of the real
                # override finding.
                plan_body_extra="This gate's scope follows D4.",
                wu_body_extra="Per D4, the enumeration is out of scope.",
            )
            (feat / "GATE-01.md").write_text(
                "---\nstatus: open\n---\n\n# Gate 1\n\nScope per D4.\n"
            )
            return lint_plan.lint(feat)

    def test_the_citation_to_a_refused_entry_is_not_reported_as_dangling(self):
        errs = self._errors_for_injection()

        dangling = [e for e in errs if "not in DECISIONS.md" in e]
        self.assertEqual(
            dangling, [],
            f"a present-but-unparseable ID must stay known to the citation "
            f"check; errs={errs}")

    def test_exactly_one_error_and_it_names_the_override(self):
        # Scoped to the decision machinery's own findings, which are the ones
        # prefixed `ERROR:`. The minimal fixture also trips unrelated
        # structural checks (missing WU sections, closing sequence); those are
        # another check's business and counting them would make this assert
        # something it does not mean.
        errs = [e for e in self._errors_for_injection() if e.startswith("ERROR:")]

        self.assertEqual(len(errs), 1, f"expected exactly one ERROR; errs={errs}")
        self.assertIn("D4", errs[0])


class TestTheExemptionIsScopedToTheQuotation(unittest.TestCase):
    """Follow-up 1: citing an ID somewhere must not exempt the whole file."""

    _RESTATEMENT = (
        "The API returns 404 for a missing widget, 410 for a deleted one, "
        "403 for one the caller cannot see, and 401 when unauthenticated."
    )

    def test_a_bare_id_token_elsewhere_does_not_exempt_a_restatement(self):
        # The regression itself. `D2` appears far from the restatement, in
        # prose that is not a citation of it in any meaningful sense.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra=(
                    "Scheduling note: this unit runs after D2 is ratified.\n\n"
                    + ("Filler sentence to separate the passages. " * 40)
                    + "\n\n" + self._RESTATEMENT
                ),
            )
            errs = lint_plan.lint(feat)

        self.assertTrue(
            [e for e in errs if "reproduces decision" in e and "D2" in e],
            f"a distant ID mention must not exempt a restatement; errs={errs}")

    def test_a_quotation_that_cites_alongside_it_stays_legitimate(self):
        # The behaviour the exemption exists for, preserved.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra="Per D2: " + self._RESTATEMENT,
            )
            errs = lint_plan.lint(feat)

        self.assertFalse(
            [e for e in errs if "reproduces decision" in e],
            f"a cited quotation must stay legitimate; errs={errs}")

    def test_a_trailing_citation_is_also_legitimate(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra=self._RESTATEMENT + " (D2)",
            )
            errs = lint_plan.lint(feat)

        self.assertFalse(
            [e for e in errs if "reproduces decision" in e],
            f"a trailing citation must stay legitimate; errs={errs}")


#: The feature that authored the DECISIONS.md format. A sweep whose only
#: in-scope member is this folder has never seen producer output from a
#: session other than the one that wrote the checker.
AUTHORING_FEATURE = "FEAT-2026-0058-decision-registry"


class TestTheSweepCorpusIsPinned(unittest.TestCase):
    """Follow-up 2's other half: the in-scope count asserted, not assumed.

    `test_check_runs_clean_over_this_repository` sweeps every feature folder
    carrying a `DECISIONS.md` and asserts zero findings. With exactly one
    such folder — the feature that wrote it — a green sweep proves nothing:
    the check has never been observed firing on producer output from a
    session that was not this one.

    This does NOT discharge follow-up 2, which needs a genuine second live
    adopter. It converts a silently-unfalsifiable green into a **tripwire**:
    the count is pinned, so the moment a second feature adopts a registry
    this test fails and forces someone to confirm the sweep still passes
    against a corpus that can actually falsify it — at which point
    follow-up 2 is dischargeable and this assertion should be raised.

    **The corpus is now empty, and the pin only ever anticipated growth.**
    It was first measured at 1 — the feature that wrote the format, which was
    live at the time. Closing that feature flipped its PLAN to `done`, and
    `_in_scope` skips `done` as sealed history, so the one member removed
    itself and the count fell to 0. The sweep does not merely fail to
    falsify now; it runs over nothing and passes vacuously. That makes
    follow-up 2 sharper rather than resolved: what it needs is unchanged —
    a second live adopter — but the state it is measured against is 0, not 1.

    The lesson is the pin's own: a corpus assertion whose single member is
    the feature that authored it decays the moment that feature closes.
    Pin the count, and expect it to move in both directions.
    """

    #: Live (non-`done`, non-`abandoned`) features carrying a DECISIONS.md.
    #: Measured 2026-08-22 at 1 (the authoring feature); fell to 0 on
    #: 2026-08-23 when that feature closed and became sealed history.
    #: Raise this when a feature adopts a registry — see the class docstring.
    EXPECTED_IN_SCOPE = 0

    def _in_scope(self) -> list:
        from tests._loop_loader import REPO_ROOT

        root = REPO_ROOT / ".specfuse" / "features"
        found = []
        for feat in sorted(p for p in root.iterdir() if p.is_dir()):
            plan = feat / "PLAN.md"
            if not plan.is_file() or not (feat / "DECISIONS.md").is_file():
                continue
            fm, _ = lint_plan.read_frontmatter(plan)
            if fm.get("status") in ("done", "abandoned"):
                continue  # sealed history, exempt from the check
            found.append(feat.name)
        return found

    def test_the_in_scope_corpus_is_the_size_we_think_it_is(self):
        found = self._in_scope()

        self.assertEqual(
            len(found), self.EXPECTED_IN_SCOPE,
            f"in-scope corpus changed: {found}. If it GREW, FEAT-2026-0058's "
            f"hedged follow-up 2 may now be dischargeable — confirm "
            f"test_check_runs_clean_over_this_repository still passes with a "
            f"corpus that can falsify it, then raise EXPECTED_IN_SCOPE. If it "
            f"SHRANK, a feature carrying a DECISIONS.md reached `done` or "
            f"`abandoned` and is now exempt as sealed history; lower "
            f"EXPECTED_IN_SCOPE and say so in the follow-up record, because a "
            f"smaller corpus means the sweep proves correspondingly less.")

    def test_no_third_party_folder_has_entered_the_corpus(self):
        # Records WHY the pin exists, so a future reader does not raise the
        # number without understanding what it was guarding. Follow-up 2 is
        # not about the count for its own sake — it is about whether the
        # sweep has ever run over a registry written by a session other than
        # the one that authored the format. So the claim under test is
        # membership, not size: every in-scope folder is still the authoring
        # feature. The moment that stops holding, the sweep can falsify and
        # follow-up 2 is dischargeable.
        found = self._in_scope()
        if len(found) >= 2:
            self.skipTest("corpus grew; follow-up 2 is dischargeable")
        self.assertEqual(
            [f for f in found if f != AUTHORING_FEATURE], [],
            f"corpus is {found} — a folder other than the authoring feature "
            f"is in scope, so the sweep now runs over producer output it did "
            f"not write. Confirm test_check_runs_clean_over_this_repository "
            f"still passes, then discharge follow-up 2 and raise "
            f"EXPECTED_IN_SCOPE.")


class TestTheDogfoodIsActuallyCovered(unittest.TestCase):
    """The measurement follow-up 1 reports: coverage over the real feature."""

    def test_this_features_own_artifacts_carry_no_restatement(self):
        # Re-run condition (a): zero restatements across the feature's own
        # graph artifacts once PLAN.md's decision prose cites rather than
        # restates. Runs the real check over the real folder, not a fixture.
        from tests._loop_loader import REPO_ROOT

        feat = REPO_ROOT / ".specfuse/features/FEAT-2026-0058-decision-registry"
        errs = lint_plan.lint(feat)

        restatements = [e for e in errs if "reproduces decision" in e]
        self.assertEqual(
            restatements, [],
            f"this feature's own artifacts must cite, not restate; "
            f"errs={restatements}")


if __name__ == "__main__":
    unittest.main()
