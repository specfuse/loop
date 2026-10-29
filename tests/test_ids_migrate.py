#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for `ids migrate --planned-only` (FEAT-2026-0247/T05)."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import ids, lint_roadmap

ROADMAP = """# Roadmap

| Feature ID | Title | Status | Folder | Detail |
|---|---|---|---|---|
| FEAT-2026-0001 | Old | done | — | x |
| FEAT-2026-0002 | Busy | planned | — | [→ detail](#feat-2026-0002) |
| FEAT-2026-0003 | Live | active | — | [→ detail](#feat-2026-0003) |
| FEAT-2026-0004 | Free | planned | — | [→ detail](#feat-2026-0004) |
| FEAT-ACME-2026-0005 | Keyed | planned | — | [→ detail](#feat-acme-2026-0005) |

<a id="feat-2026-0002"></a>
## FEAT-2026-0002 — Busy

Body.

<a id="feat-2026-0003"></a>
## FEAT-2026-0003 — Live

Body.

<a id="feat-2026-0004"></a>
## FEAT-2026-0004 — Free

Depends on [Live](#feat-2026-0003) and itself `#feat-2026-0004`.

<a id="feat-acme-2026-0005"></a>
## FEAT-ACME-2026-0005 — Keyed

See [Free](#feat-2026-0004) and [Free](roadmap.md#feat-2026-0004).
"""


def _repo(tmp, key="ACME", archive=None):
    root = Path(tmp)
    spec = root / ".specfuse"
    (spec / "features" / "FEAT-2026-0002-busy").mkdir(parents=True)
    (spec / "roadmap.md").write_text(ROADMAP)
    if archive:
        (spec / "roadmap-archive.md").write_text(archive)
    if key:
        (spec / "layout.yml").write_text(f"ids:\n  key: {key}\n")
    return root


def _run(root, *args):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ids.main(["--repo", str(root), "migrate", "--planned-only", *args])
    return code, out.getvalue(), err.getvalue()


class Migrate(unittest.TestCase):
    def test_dry_run_writes_nothing_and_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            code, out, _ = _run(root)
            self.assertEqual(code, 0)
            self.assertEqual((root / ".specfuse" / "roadmap.md").read_text(), ROADMAP)
            self.assertIn("FEAT-2026-0004 -> FEAT-ACME-2026-0004", out)
            self.assertIn("FEAT-2026-0002: has a feature folder", out)
            self.assertIn("FEAT-2026-0003: status is active", out)
            self.assertIn("FEAT-ACME-2026-0005: already keyed", out)

    def test_apply_rekeys_with_cross_section_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            code, _, _ = _run(root, "--apply")
            self.assertEqual(code, 0)
            text = (root / ".specfuse" / "roadmap.md").read_text()
            self.assertIn("| FEAT-ACME-2026-0004 | Free |", text)
            self.assertIn('<a id="feat-acme-2026-0004"></a>\n## FEAT-ACME-2026-0004 — Free', text)
            self.assertIn("[Free](#feat-acme-2026-0004)", text)
            self.assertIn("(roadmap.md#feat-acme-2026-0004)", text)
            self.assertIn("`#feat-2026-0004`", text)  # code span left alone
            for untouched in ("| FEAT-2026-0002 |", "| FEAT-2026-0003 |", "| FEAT-ACME-2026-0005 |"):
                self.assertIn(untouched, text)
            errors = [f for f in lint_roadmap.lint_roadmap(root) if f.severity == lint_roadmap.SEVERITY_ERROR]
            self.assertEqual(errors, [])

    def test_code_span_ref_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _, out, _ = _run(root)
            self.assertIn("unplaced ref to FEAT-2026-0004", out)

    def test_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            _run(root, "--apply")
            first = (root / ".specfuse" / "roadmap.md").read_text()
            code, out, _ = _run(root, "--apply")
            self.assertEqual(code, 0)
            self.assertIn("no candidates", out)
            self.assertEqual((root / ".specfuse" / "roadmap.md").read_text(), first)

    def test_archive_rewritten_and_features_untouched(self):
        archive = (
            "| Feature ID | Title | Status | Folder | Detail |\n|---|---|---|---|---|\n"
            "| FEAT-2026-0009 | Arch | planned | — | [→](#feat-2026-0009) |\n\n"
            '<a id="feat-2026-0009"></a>\n## FEAT-2026-0009 — Arch\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, archive=archive)
            marker = root / ".specfuse" / "features" / "FEAT-2026-0002-busy" / "events.jsonl"
            marker.write_text("{}\n")
            _run(root, "--apply")
            text = (root / ".specfuse" / "roadmap-archive.md").read_text()
            self.assertIn("| FEAT-ACME-2026-0009 |", text)
            self.assertIn('<a id="feat-acme-2026-0009">', text)
            self.assertEqual(marker.read_text(), "{}\n")
            self.assertTrue((root / ".specfuse" / "features" / "FEAT-2026-0002-busy").is_dir())

    def test_no_key_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, key=None)
            code, _, err = _run(root, "--apply")
            self.assertNotEqual(code, 0)
            self.assertIn("ids.key", err)
            self.assertIn(".specfuse/layout.yml", err)
            self.assertEqual((root / ".specfuse" / "roadmap.md").read_text(), ROADMAP)


if __name__ == "__main__":
    unittest.main()
