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
