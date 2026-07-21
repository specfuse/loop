#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#176: warn when an implementation WU's Verification omits a declared code gate.

The driver enforces the full `code` gate set regardless of what a WU's
Verification names, so the two can silently disagree — the authoring-side
trigger of #175. This lint catches it before dispatch at zero model cost.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

# Only `format` opts in via wu_must_reference; tests/lint are NOT checked.
_VERIFICATION = """\
code:
  - name: tests
    command: "python3 -m unittest discover -s tests -v"
  - name: lint
    command: "ruff check specfuse tests"
  - name: format
    command: "./mvnw spotless:check"
    wu_must_reference: true
"""


class TestMustReferenceGateSignatureHelpers(unittest.TestCase):

    def _feature_with_verification(self, tmp: str, yml: str | None) -> Path:
        root = Path(tmp)
        fdir = root / ".specfuse" / "features" / "FEAT-2026-9401-x"
        fdir.mkdir(parents=True)
        if yml is not None:
            (root / ".specfuse" / "verification.yml").write_text(yml)
        return fdir

    def test_only_flagged_gate_is_included(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._feature_with_verification(tmp, _VERIFICATION)
            sigs = dict(lint_plan._must_reference_gate_signatures(fdir))
            # tests/lint are NOT flagged → excluded; only format opts in.
            self.assertEqual(set(sigs), {"format"})
            self.assertIn("spotless:check", sigs["format"])
            self.assertIn("format", sigs["format"])  # gate name is a token

    def test_no_flag_anywhere_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = ("code:\n  - name: tests\n"
                     "    command: \"pytest -q\"\n")
            fdir = self._feature_with_verification(tmp, plain)
            self.assertEqual(lint_plan._must_reference_gate_signatures(fdir), [])

    def test_no_verification_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._feature_with_verification(tmp, None)
            self.assertEqual(lint_plan._must_reference_gate_signatures(fdir), [])

    def test_unparseable_verification_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._feature_with_verification(tmp, "code: {bad: flow}\n")
            self.assertEqual(lint_plan._must_reference_gate_signatures(fdir), [])

    def test_unreferenced_detects_omitted_gate(self):
        sigs = [("tests", {"tests", "unittest"}),
                ("format", {"format", "spotless:check"})]
        # Names tests but not the formatter → only 'format' is unreferenced.
        text = "Run the unittest suite; all tests pass."
        self.assertEqual(lint_plan._unreferenced_code_gates(text, sigs),
                         ["format"])

    def test_umbrella_phrase_short_circuits(self):
        sigs = [("format", {"format", "spotless:check"})]
        for phrase in ("all declared gates pass", "every gate is green",
                       "the full gate set runs clean"):
            self.assertEqual(
                lint_plan._unreferenced_code_gates(phrase, sigs), [],
                f"{phrase!r} should short-circuit")

    def test_all_referenced_is_empty(self):
        sigs = [("tests", {"tests"}), ("format", {"spotless:check"})]
        text = "tests pass; ran spotless:check clean."
        self.assertEqual(lint_plan._unreferenced_code_gates(text, sigs), [])


class TestVerificationReferenceLintWarn(unittest.TestCase):

    def _make_feature(self, tmp: str, verification_body: str,
                      yml: str | None = _VERIFICATION) -> Path:
        root = Path(tmp)
        fdir = root / ".specfuse" / "features" / "FEAT-2026-9401-x"
        fdir.mkdir(parents=True)
        if yml is not None:
            (root / ".specfuse" / "verification.yml").write_text(yml)
        (fdir / "PLAN.md").write_text(
            "---\n"
            "feature_id: FEAT-2026-9401\n"
            "title: verification-reference lint\n"
            "branch: feat/vref\n"
            "roadmap_goal: Check the Verification-reference WARN.\n"
            "status: active\n"
            "---\n\n# Plan\n\n```yaml\n"
            "gates:\n"
            "  - gate: 1\n"
            "    file: GATE-01.md\n"
            "    work_units:\n"
            "      - id: FEAT-2026-9401/T01\n"
            "        file: WU-01-impl.md\n"
            "        depends_on: []\n"
            "      - id: FEAT-2026-9401/G1-CLOSE\n"
            "        file: WU-90-close.md\n"
            "        depends_on: [FEAT-2026-9401/T01]\n"
            "```\n"
        )
        (fdir / "WU-01-impl.md").write_text(
            "---\nid: FEAT-2026-9401/T01\ntype: implementation\n"
            "status: done\nattempts: 1\nproduces: [src/x.py]\n---\n\n"
            "# Title\n\n**Context.**\nAdd a file.\n\n"
            "**Acceptance criteria.**\nThe code works.\n\n"
            "**Do not touch.**\nNothing.\n\n"
            f"**Verification.**\n{verification_body}\n\n"
            "**Escalation triggers.**\nEmit blocked if wrong.\n"
        )
        (fdir / "WU-90-close.md").write_text(
            "---\nid: FEAT-2026-9401/G1-CLOSE\ntype: close\n"
            "status: done\nattempts: 1\n---\n\n# Close\n"
        )
        (fdir / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
        return fdir

    def _lint(self, fdir: Path) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            lint_plan.lint(fdir)
        return buf.getvalue()

    def test_warns_when_formatter_gate_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(
                tmp, "Run the unittest suite and ruff; all pass.")
            out = self._lint(fdir)
            self.assertIn("WARN", out)
            # Only the omitted formatter gate is named; the referenced
            # tests/lint gates are not listed as unreferenced.
            listed = out.split("gate(s):", 1)[1].split("\n", 1)[0]
            self.assertIn("format", listed)
            self.assertNotIn("tests", listed)
            self.assertNotIn("lint", listed)

    def test_silent_when_all_gates_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(
                tmp, "unittest suite passes; ruff clean; spotless:check clean.")
            self.assertNotIn("references none", self._lint(fdir))

    def test_silent_on_umbrella_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(tmp, "All declared code gates pass.")
            self.assertNotIn("references none", self._lint(fdir))

    def test_silent_when_no_verification_yml(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(tmp, "anything at all", yml=None)
            self.assertNotIn("references none", self._lint(fdir))


if __name__ == "__main__":
    unittest.main()
