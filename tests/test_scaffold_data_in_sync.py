# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Drift guard: every file in specfuse/loop/data/ must byte-match its canonical
# .specfuse/ counterpart. Fails CI if the two trees diverge.
# Run scripts/sync-scaffold.sh to restore parity.

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).parent.parent
CANONICAL = REPO_ROOT / ".specfuse"
CANONICAL_DOCS = REPO_ROOT / "docs"
PACKAGE_DATA = REPO_ROOT / "specfuse" / "loop" / "data"

# Explicit manifest — every file the sync script manages (canonical: .specfuse/).
TRACKED = {
    "VERSION",
    "gitignore.snippet",
    "verification.yml.example",
    "roadmap.template.md",
    "LEARNINGS.template.md",
    "templates/GATE.template.md",
    "templates/PLAN.template.md",
    "templates/WU.template.md",
    "rules/correlation-ids.md",
    "rules/never-touch.md",
    "rules/planning-discipline.md",
    "rules-local/README.md",
    "rules/result-contract.md",
    "rules/security-boundaries.md",
    "rules/verification-discipline.md",
    "schemas/event.schema.json",
    "schemas/events/initiative_created.schema.json",
    "schemas/events/spec_validated.schema.json",
    "schemas/events/spec_issue_resolved.schema.json",
    "schemas/events/spec_issue_routed.schema.json",
}

# Docs manifest — canonical source is repo docs/, not .specfuse/.
DOCS_TRACKED = {
    "docs/getting-started.md",
    "docs/methodology.md",
    "docs/skills.md",
    "docs/concepts/ralph-lineage.md",
    "docs/concepts/architecture-addendum-gates-and-iterative-planning.md",
}


class TestScaffoldDataInSync(unittest.TestCase):
    def test_package_data_matches_canonical(self):
        """Each tracked file in specfuse/loop/data/ must byte-match .specfuse/."""
        mismatches = []
        for rel in sorted(TRACKED):
            canonical_path = CANONICAL / rel
            package_path = PACKAGE_DATA / rel
            if not canonical_path.exists():
                mismatches.append(f"canonical missing: {rel}")
                continue
            if not package_path.exists():
                mismatches.append(f"package copy missing: {rel}")
                continue
            if canonical_path.read_bytes() != package_path.read_bytes():
                mismatches.append(f"content differs: {rel}")
        if mismatches:
            self.fail(
                "Scaffold data out of sync with canonical sources.\n"
                "Run: scripts/sync-scaffold.sh\n\n"
                "Diffs:\n" + "\n".join(f"  {m}" for m in mismatches)
            )

    def test_package_docs_match_canonical(self):
        """Each tracked doc in specfuse/loop/data/docs/ must byte-match repo docs/."""
        mismatches = []
        for rel in sorted(DOCS_TRACKED):
            # rel is e.g. "docs/getting-started.md"; canonical lives at docs/<rest>
            rest = rel[len("docs/"):]
            canonical_path = CANONICAL_DOCS / rest
            package_path = PACKAGE_DATA / rel
            if not canonical_path.exists():
                mismatches.append(f"canonical missing: {rel}")
                continue
            if not package_path.exists():
                mismatches.append(f"package copy missing: {rel}")
                continue
            if canonical_path.read_bytes() != package_path.read_bytes():
                mismatches.append(f"content differs: {rel}")
        if mismatches:
            self.fail(
                "Docs seed out of sync with canonical docs/.\n"
                "Run: scripts/sync-scaffold.sh\n\n"
                "Diffs:\n" + "\n".join(f"  {m}" for m in mismatches)
            )

    def test_no_orphan_files_in_package_data(self):
        """No files in specfuse/loop/data/ that are absent from the sync manifest."""
        actual = {
            str(p.relative_to(PACKAGE_DATA))
            for p in PACKAGE_DATA.rglob("*")
            if p.is_file()
        }
        orphans = actual - TRACKED - DOCS_TRACKED
        if orphans:
            self.fail(
                "Unexpected files in specfuse/loop/data/ not in sync manifest.\n"
                "Add them to scripts/sync-scaffold.sh and the TRACKED set here:\n"
                + "\n".join(f"  {p}" for p in sorted(orphans))
            )


if __name__ == "__main__":
    unittest.main()
