#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Binds `docs/methodology.md`'s attempt_outcome contract to the emitter (#270).

Two contracts live in that section and both had drifted:

**The outcome taxonomy.** It is declared "locked at v1" and consumers are told
to treat it as an enum, so a new value is a breaking change. Five values
(`deliverable_missing`, `no_deliverable_files`, `produces_not_in_diff`,
`squash_commit_failed`, `zero_token_skip`) had shipped without that decision,
and two documented values were never emitted at all — `zero_token` had been
renamed `zero_token_skip` without the doc following.

**Where each outcome puts its diagnostic.** The prose lists a "standardized set
of fields" including `failure_class` / `failure_excerpt`, which are *not*
populated on every non-`passed` outcome. `blocked` carries
`agent_blocked_reason`; the guard-refusal outcomes carry `summary`; pre-0.3.23
`files_changed_mismatch` carries only `unchanged_paths`.

That second gap is not hypothetical. A cross-repo audit produced three separate
"the driver records no diagnostic" findings — 45 unrecoverable attempts, then
58, then 30 — every one of them a query against the wrong field. The data was
complete the whole time. Documenting which field to read is the fix; this test
keeps the documentation true.

The emitter is the source of truth. Both checks read `loop.py` and assert the
doc matches, so the code cannot drift away from the contract silently.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LOOP_SRC = _REPO_ROOT / "specfuse" / "loop" / "loop.py"
_DOC = _REPO_ROOT / "docs" / "methodology.md"

# Emitted at a call site the driver reaches; `passed` is emitted through the
# same helper but from the success path.
_EMIT_RE = re.compile(
    r'emit_attempt_outcome\(\s*\n?\s*wu,\s*attempt,\s*"([a-z_]+)"', re.M
)


def _emitted_outcomes() -> set[str]:
    return set(_EMIT_RE.findall(_LOOP_SRC.read_text(encoding="utf-8")))


def _doc_section() -> str:
    text = _DOC.read_text(encoding="utf-8")
    start = text.find("### Per-attempt outcome events")
    assert start >= 0, "methodology.md has no per-attempt outcome section"
    end = text.find("\n### ", start + 1)
    return text[start:end if end > 0 else len(text)]


class TestOutcomeTaxonomyMatchesTheEmitter(unittest.TestCase):
    def test_the_extractor_still_finds_outcomes(self):
        """Vacuity guard: a regex that matches nothing would pass everything."""
        self.assertGreaterEqual(
            len(_emitted_outcomes()), 8,
            "emit_attempt_outcome call sites are no longer shaped the way this "
            "test extracts them; the taxonomy check would pass vacuously",
        )

    def test_every_emitted_outcome_is_documented(self):
        doc = _doc_section()
        for outcome in sorted(_emitted_outcomes()):
            with self.subTest(outcome=outcome):
                self.assertIn(
                    f"`{outcome}`", doc,
                    f"loop.py emits {outcome!r} but methodology.md does not list "
                    f"it. Consumers are told to treat the taxonomy as an enum, so "
                    f"an undocumented value is an unannounced breaking change (#270)",
                )

    def test_no_documented_outcome_is_unreachable(self):
        """A value in the doc that the code never emits is equally misleading.

        `zero_token` sat in the taxonomy after the emitter had renamed it
        `zero_token_skip`, so anyone filtering on the documented name matched
        nothing and saw a clean record.
        """
        doc = _doc_section()
        emitted = _emitted_outcomes()
        documented = set(re.findall(r"^\| `([a-z_]+)` \|", doc, re.M))
        self.assertTrue(documented, "no outcome table found in the doc section")
        self.assertEqual(
            documented - emitted, set(),
            "methodology.md documents outcome values loop.py never emits",
        )


class TestDiagnosticFieldContractIsDocumented(unittest.TestCase):
    """Every field a reader must check to find an outcome's reason.

    Omitting one is what produced three false "missing diagnostic" findings.
    """

    _REQUIRED = [
        ("agent_blocked_reason", "blocked"),
        ("summary", "the guard-refusal outcomes"),
        ("unchanged_paths", "pre-0.3.23 files_changed_mismatch"),
        ("failure_excerpt", "gate failures"),
    ]

    def test_each_diagnostic_field_is_named(self):
        doc = _doc_section()
        for field, why in self._REQUIRED:
            with self.subTest(field=field):
                self.assertIn(
                    field, doc,
                    f"methodology.md does not name {field!r}, which carries the "
                    f"reason for {why}. A consumer that skips it reports a "
                    f"complete record as empty (#270)",
                )

    def test_the_emitter_still_accepts_these_fields(self):
        """Guards the doc against describing parameters that no longer exist."""
        src = _LOOP_SRC.read_text(encoding="utf-8")
        sig_start = src.find("def emit_attempt_outcome(")
        self.assertGreater(sig_start, 0)
        sig = src[sig_start:sig_start + 700]
        for field in ("agent_blocked_reason", "failure_excerpt", "extras"):
            with self.subTest(field=field):
                self.assertIn(field, sig,
                              f"emit_attempt_outcome no longer takes {field!r}")


if __name__ == "__main__":
    unittest.main()
