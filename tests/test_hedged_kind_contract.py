#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The `kind:` contract on hedged-verdict follow-up entries — FEAT-2026-0059/T01.

Reproduces the trap PLAN.md names explicitly: a lint that swept every
feature's RETROSPECTIVE.md would be red on arrival, because two closed
features (FEAT-2026-0041, FEAT-2026-0042) hedged before `kind:` existed. The
check must be scoped to the close WU currently under lint. Criterion 6 below
holds that guarantee as a test.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

from specfuse.loop import closing_requirements as creq  # noqa: E402
from specfuse.loop import lint_closing as lc  # noqa: E402

PLAN_HEADER = (
    "---\nfeature_id: FEAT-9999\ntitle: Test\nbranch: feat/test\n"
    "roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n"
)

VALID_HEDGED_RECORD = """# Retrospective

## Hedged-verdict follow-up record (close-discipline §2)

`verdict: met_locally`. One entry.

### D1 — Human acknowledgment of the contract-change list — OPEN

- **The criterion, verbatim:** "some criterion text"
- **Why it is unverifiable in this environment:** needs a human.
- **The exact re-run condition that would upgrade the verdict to `met`:** an
  operator acknowledges and runs /accept-hedged-close.
- **kind:** `acceptance-discharged`
"""

UNCLASSIFIED_HEDGED_RECORD = """# Retrospective

## Hedged-verdict follow-up record (close-discipline §2)

`verdict: met_locally`. One entry.

### D1 — Human acknowledgment of the contract-change list — OPEN

- **The criterion, verbatim:** "some criterion text"
- **Why it is unverifiable in this environment:** needs a human.
- **The exact re-run condition that would upgrade the verdict to `met`:** an
  operator acknowledges and runs /accept-hedged-close.
"""

BAD_KIND_HEDGED_RECORD = """# Retrospective

## Hedged-verdict follow-up record (close-discipline §2)

`verdict: met_locally`. One entry.

### D1 — Human acknowledgment of the contract-change list — OPEN

- **The criterion, verbatim:** "some criterion text"
- **Why it is unverifiable in this environment:** needs a human.
- **The exact re-run condition that would upgrade the verdict to `met`:** an
  operator acknowledges and runs /accept-hedged-close.
- **kind:** `not-a-real-kind`
"""


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                    capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / ".specfuse").mkdir(parents=True, exist_ok=True)
    (root / ".specfuse" / "LEARNINGS.md").write_text("# Learnings\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")


def _write_plan(feature_dir: Path, gates_yaml: str) -> None:
    (feature_dir / "PLAN.md").write_text(
        PLAN_HEADER + "```yaml\ngates:\n" + gates_yaml + "```\n"
    )


def _write_wu(path: Path, wu_id: str, wu_type: str, status: str, extra_fm: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {wu_id}\ntype: {wu_type}\nstatus: {status}\nattempts: 0\n{extra_fm}---\n\n"
        f"# {wu_type} WU\n\n"
        "**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )


def _make_close_feature(
    tmp: str, feature_id: str = "FEAT-9999", verdict: str = "met_locally",
) -> Path:
    root = Path(tmp)
    _init_repo(root)
    fdir = root / ".specfuse" / "features" / f"{feature_id}-test"
    fdir.mkdir(parents=True)
    _write_plan(fdir, (
        "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        f"      - id: {feature_id}/G1-CLOSE\n        file: WU-close.md\n"
        "        depends_on: []\n"
    ))
    extra_fm = f"verdict: {verdict}\n" if verdict else ""
    _write_wu(fdir / "WU-close.md", f"{feature_id}/G1-CLOSE", "close", "pending",
              extra_fm=extra_fm)
    return fdir


def _satisfy_other_close_requirements(fdir: Path) -> None:
    (fdir.parents[2] / ".specfuse" / "LEARNINGS.md").write_text(
        "# Learnings\n\n- new lesson\n"
    )
    docs = fdir.parents[2] / "docs"
    if not docs.exists():
        docs.mkdir()
    (docs / "closing.md").write_text("doc\n")


class TestHedgedKindContract(unittest.TestCase):

    def test_hedged_close_without_kind_fails_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _make_close_feature(tmp, verdict="met_locally")
            (fdir / "RETROSPECTIVE.md").write_text(UNCLASSIFIED_HEDGED_RECORD)
            _satisfy_other_close_requirements(fdir)

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_hedged_followup_kinds_classified", joined)
            self.assertIn("kind", joined)

    def test_hedged_close_with_valid_kinds_lints_clean_on_this_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _make_close_feature(tmp, verdict="met_locally")
            (fdir / "RETROSPECTIVE.md").write_text(VALID_HEDGED_RECORD)
            _satisfy_other_close_requirements(fdir)

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("assert_hedged_followup_kinds_classified", joined)

    def test_unrecognised_kind_value_fails_naming_legal_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _make_close_feature(tmp, verdict="partially_met")
            (fdir / "RETROSPECTIVE.md").write_text(BAD_KIND_HEDGED_RECORD)
            _satisfy_other_close_requirements(fdir)

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertIn("assert_hedged_followup_kinds_classified", joined)
            for kind in creq.FOLLOW_UP_KINDS:
                self.assertIn(kind, joined)

    def test_met_verdict_close_is_unaffected_no_record_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _make_close_feature(tmp, verdict="met")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n"
            )
            _satisfy_other_close_requirements(fdir)

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("assert_hedged_followup_kinds_classified", joined)

    def test_check_scoped_to_close_under_lint_ignores_other_features(self):
        """A malformed §2 record in a *different* feature produces no finding.

        This is the satisfiability guarantee PLAN.md names: FEAT-2026-0041
        and FEAT-2026-0042 hedged before `kind:` existed, and a corpus sweep
        would be permanently red. The check must read only the feature dir
        it was called with.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)

            other_fdir = root / ".specfuse" / "features" / "FEAT-0041-other"
            other_fdir.mkdir(parents=True)
            (other_fdir / "RETROSPECTIVE.md").write_text(UNCLASSIFIED_HEDGED_RECORD)

            fdir = root / ".specfuse" / "features" / "FEAT-9999-test"
            fdir.mkdir(parents=True)
            _write_plan(fdir, (
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-CLOSE\n        file: WU-close.md\n"
                "        depends_on: []\n"
            ))
            _write_wu(fdir / "WU-close.md", "FEAT-9999/G1-CLOSE", "close", "pending",
                      extra_fm="verdict: met\n")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Cost analysis\n\nAll cheap.\n"
            )
            _satisfy_other_close_requirements(fdir)

            findings, _ = lc.lint_closing(fdir)
            joined = "\n".join(findings)
            self.assertNotIn("assert_hedged_followup_kinds_classified", joined)
            self.assertEqual(findings, [])


class TestVerdictCeilingForKinds(unittest.TestCase):

    def test_externally_verifiable_later_present_means_rework_exists(self):
        result = creq.verdict_ceiling_for_kinds(
            {"acceptance-discharged", "externally-verifiable-later"}
        )
        self.assertEqual(result, creq.REWORK_EXISTS)

    def test_no_externally_verifiable_later_means_no_in_repo_rework(self):
        result = creq.verdict_ceiling_for_kinds(
            {"acceptance-discharged", "routed-finding", "inherent"}
        )
        self.assertEqual(result, creq.NO_IN_REPO_REWORK)

    def test_empty_kind_set_means_no_in_repo_rework(self):
        result = creq.verdict_ceiling_for_kinds(set())
        self.assertEqual(result, creq.NO_IN_REPO_REWORK)


if __name__ == "__main__":
    unittest.main()
