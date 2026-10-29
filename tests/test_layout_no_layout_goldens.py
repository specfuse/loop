#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""No-layout goldens for FEAT-2026-0224/T04.

Fixtures and expected outputs are module-level constants. The goldens were
recorded once against HEAD's `lint_roadmap` and `layout` before any consumer
edit; nothing in this module regenerates them.
"""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.lint_roadmap import lint_roadmap

ROOT = Path(__file__).resolve().parent.parent

_HEADER = (
    "---\nproject: test\n---\n\n# Roadmap\n\n"
    "| Feature ID | Title | Status | Folder | Detail |\n"
    "|---|---|---|---|---|\n"
)
_ARCHIVE = (
    "---\nproject: test\n---\n\n# Archived feature details\n\n"
    "<!-- Archived sections appended below -->\n"
)

FIXTURES = {
    "clean": {
        ".specfuse/roadmap.md": _HEADER
        + "| FEAT-2026-0001 | Alpha | active | — | [→ detail](#feat-2026-0001) |\n"
        + '\n<a id="feat-2026-0001"></a>\n'
        + "## FEAT-2026-0001 — Alpha\n\nBody.\n",
        ".specfuse/roadmap-archive.md": _ARCHIVE,
    },
    "blocked_resolves": {
        ".specfuse/roadmap.md": _HEADER
        + "| FEAT-2026-0002 | Beta | blocked | — | [→ detail](#feat-2026-0002) |\n"
        + '\n<a id="feat-2026-0002"></a>\n'
        + "## FEAT-2026-0002 — Beta\n\n"
        + "**Blocked by.** [ADR-0001](../docs/adr/0001-real.md) — pending.\n",
        ".specfuse/roadmap-archive.md": _ARCHIVE,
        "docs/adr/0001-real.md": "# ADR 0001\n",
    },
    "blocked_dangling": {
        ".specfuse/roadmap.md": _HEADER
        + "| FEAT-2026-0003 | Gamma | blocked | — | [→ detail](#feat-2026-0003) |\n"
        + "| FEAT-2026-0004 | Orphan | active | — | — |\n"
        + '\n<a id="feat-2026-0003"></a>\n'
        + "## FEAT-2026-0003 — Gamma\n\n"
        + "**Blocked by.** [ADR-0099](../docs/adr/0099-missing.md) — pending.\n"
        + '\n<a id="feat-2026-0004"></a>\n'
        + "## FEAT-2026-0004 — Orphan\n\nNo row points here.\n",
        ".specfuse/roadmap-archive.md": _ARCHIVE,
    },
}

GOLDEN_GET = {
    "decisions.style": "adr\n",
    "decisions.location": "docs/adr\n",
    "decisions.link": "{path}\n",
}
GOLDEN_LINK = "[ADR-0001](../docs/adr/0001-real.md)\n"
GOLDEN_LINT = {
    "clean": [],
    "blocked_resolves": [],
    "blocked_dangling": [
        "error roadmap.md:15 FEAT-2026-0003's Blocked-by link "
        "'../docs/adr/0099-missing.md' does not resolve to a file on disk and is "
        "not a well-formed URL \u2014 fix the path",
        "warn roadmap.md:10 FEAT-2026-0004's Detail cell is '\u2014' but a detail "
        "section already exists in roadmap.md \u2014 link it, e.g. "
        "'[\u2192 detail](#feat-2026-0004)' or "
        "'[\u2192 archive](roadmap-archive.md#feat-2026-0004)'",
    ],
}

GET_KEYS = ("decisions.style", "decisions.location", "decisions.link")
LINK_ARGS = (
    "link", "--from", ".specfuse", "--target", "docs/adr/0001-real.md",
    "--label", "ADR-0001",
)


def write_fixture(root, name):
    for rel, text in FIXTURES[name].items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def run_layout(repo, *args):
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "specfuse.loop.layout", *args],
        cwd=repo, capture_output=True, text=True, env=env, check=False,
    )


def render_lint(repo):
    return [
        f"{f.severity} {f.file}:{f.line} {f.message}" for f in lint_roadmap(Path(repo))
    ]


class NoLayoutGoldens(unittest.TestCase):
    def test_get_every_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            for key in GET_KEYS:
                r = run_layout(tmp, "get", key)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, GOLDEN_GET[key], key)

    def test_link_block_feature_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_layout(tmp, *LINK_ARGS)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, GOLDEN_LINK)

    def test_lint_every_fixture(self):
        for name in FIXTURES:
            with self.subTest(fixture=name), tempfile.TemporaryDirectory() as tmp:
                write_fixture(tmp, name)
                self.assertEqual(render_lint(tmp), GOLDEN_LINT[name])

    def test_lint_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_fixture(tmp, "blocked_dangling")
            self.assertEqual(render_lint(tmp), render_lint(tmp))

    def test_no_temp_path_in_golden(self):
        for lines in GOLDEN_LINT.values():
            for line in lines:
                self.assertNotIn("/tmp", line)
                self.assertNotIn("/var/", line)

    def test_positive_control(self):
        lines = GOLDEN_LINT["blocked_dangling"]
        self.assertTrue(any(x.startswith("error ") for x in lines), lines)
        self.assertTrue(any(x.startswith("warn ") for x in lines), lines)

    def test_fixtures_carry_no_fragment_links(self):
        for name, files in FIXTURES.items():
            for rel, text in files.items():
                self.assertIsNone(
                    re.search(r"\]\([^)]*\.md#", text), f"{name}:{rel}"
                )


# sha256 of HEAD's roadmap.template.md (before the layout region markers).
# Re-recorded for FEAT-2026-0247/T06, which intentionally changed the template's Notes.
GOLDEN_TEMPLATE_SHA256 = "1a0deeb13ed6411c3594487909e5d89b7ecb6029695f0009869d916d33807f67"


class NoLayoutTemplateGoldens(unittest.TestCase):
    def test_render_equals_head_template(self):
        import hashlib

        from specfuse.loop import layout

        text = (ROOT / "specfuse/loop/data/roadmap.template.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            out = layout.render_roadmap_template(text, layout.load(tmp))
        self.assertNotIn("layout:decisions-example", out)
        self.assertEqual(hashlib.sha256(out.encode("utf-8")).hexdigest(), GOLDEN_TEMPLATE_SHA256)

    def test_fresh_seed_equals_head_seed(self):
        import hashlib

        from specfuse.loop.scaffold import init_specfuse

        with tempfile.TemporaryDirectory() as tmp:
            init_specfuse(tmp)
            seed = (Path(tmp) / ".specfuse" / "roadmap.md").read_bytes()
        self.assertEqual(hashlib.sha256(seed).hexdigest(), GOLDEN_TEMPLATE_SHA256)


if __name__ == "__main__":
    unittest.main()
