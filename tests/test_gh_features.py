#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""T02 — gh_features.py: list specfuse:feature issues as loop-feature candidates.

Drives list_features() with a stub runner. No live gh call is made.
Covers: orchestrated issue (INIT title + initiative/type/autonomy labels),
component-local issue (FEAT title, no initiative, no autonomy → defaults),
untagged title (skipped with warning), and CLI main() output format.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_gh_features():
    path = REPO_ROOT / ".specfuse/scripts/gh_features.py"
    spec = importlib.util.spec_from_file_location("gh_features_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gh_features_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


gh_features = _load_gh_features()

# ---------------------------------------------------------------------------
# Canned fixture data — matches the issue title/label contract (handoff §2)
# ---------------------------------------------------------------------------

_ORCHESTRATED = {
    "number": 42,
    "title": "[example-feature] Conform exampleEndpoint to validated spec",
    "labels": [
        {"name": "specfuse:feature"},
        {"name": "initiative:example-init"},
        {"name": "type:implementation"},
        {"name": "autonomy:review"},
    ],
    "url": "https://github.com/example/repo/issues/42",
    "body": "Five-section WU body.",
}

_COMPONENT_LOCAL = {
    "number": 7,
    "title": "[FEAT-2026-0003] Add GitHub feature pick",
    "labels": [
        {"name": "specfuse:feature"},
        {"name": "type:implementation"},
    ],
    "url": "https://github.com/example/repo/issues/7",
    "body": "",
}

_UNTAGGED = {
    "number": 99,
    "title": "A random issue with no bracket id tag",
    "labels": [{"name": "specfuse:feature"}],
    "url": "https://github.com/example/repo/issues/99",
    "body": "",
}

_CANNED = [_ORCHESTRATED, _COMPONENT_LOCAL, _UNTAGGED]


def _stub(repo: str) -> list:
    return list(_CANNED)


# ---------------------------------------------------------------------------
# Orchestrated issue — INIT-YYYY-NNNN/FNN title + all labels present
# ---------------------------------------------------------------------------

class TestOrchestratedIssue(unittest.TestCase):
    def setUp(self):
        candidates = gh_features.list_features("example/repo", runner=_stub)
        self.candidate = next(c for c in candidates if c["number"] == 42)

    def test_feature_id(self):
        self.assertEqual(self.candidate["feature_id"], "example-feature")

    def test_title_is_summary_without_bracket_tag(self):
        self.assertEqual(
            self.candidate["title"], "Conform exampleEndpoint to validated spec"
        )

    def test_initiative_extracted(self):
        self.assertEqual(self.candidate["initiative"], "example-init")

    def test_task_type_extracted(self):
        self.assertEqual(self.candidate["task_type"], "implementation")

    def test_autonomy_extracted(self):
        self.assertEqual(self.candidate["autonomy"], "review")

    def test_url_preserved(self):
        self.assertEqual(
            self.candidate["url"], "https://github.com/example/repo/issues/42"
        )

    def test_number_preserved(self):
        self.assertEqual(self.candidate["number"], 42)

    def test_body_preserved(self):
        self.assertEqual(self.candidate["body"], "Five-section WU body.")


# ---------------------------------------------------------------------------
# Component-local issue — FEAT-YYYY-NNNN title, no initiative, no autonomy
# ---------------------------------------------------------------------------

class TestComponentLocalIssue(unittest.TestCase):
    def setUp(self):
        candidates = gh_features.list_features("example/repo", runner=_stub)
        self.candidate = next(c for c in candidates if c["number"] == 7)

    def test_feature_id(self):
        self.assertEqual(self.candidate["feature_id"], "FEAT-2026-0003")

    def test_initiative_is_none(self):
        self.assertIsNone(self.candidate["initiative"])

    def test_autonomy_defaults_to_review(self):
        self.assertEqual(self.candidate["autonomy"], "review")

    def test_task_type_extracted(self):
        self.assertEqual(self.candidate["task_type"], "implementation")


# ---------------------------------------------------------------------------
# Untagged issue — must be skipped; warning to stderr; no crash
# ---------------------------------------------------------------------------

class TestUntaggedIssueSkipped(unittest.TestCase):
    def test_untagged_absent_from_results(self):
        candidates = gh_features.list_features("example/repo", runner=_stub)
        self.assertNotIn(99, [c["number"] for c in candidates])

    def test_two_valid_candidates_returned(self):
        candidates = gh_features.list_features("example/repo", runner=_stub)
        self.assertEqual(len(candidates), 2)

    def test_warning_written_to_stderr_with_issue_number(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            gh_features.list_features("example/repo", runner=_stub)
        output = buf.getvalue()
        self.assertIn("99", output)
        self.assertIn("WARNING", output)

    def test_no_crash_on_all_untagged(self):
        def only_bad(repo):
            return [_UNTAGGED]

        buf = io.StringIO()
        with redirect_stderr(buf):
            result = gh_features.list_features("example/repo", runner=only_bad)
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# No live gh call — stub is the only runner invoked
# ---------------------------------------------------------------------------

class TestNoLiveGhCall(unittest.TestCase):
    def test_stub_runner_is_called_not_subprocess(self):
        calls = []

        def recording_stub(repo):
            calls.append(repo)
            return []

        gh_features.list_features("some/repo", runner=recording_stub)
        self.assertEqual(calls, ["some/repo"])


# ---------------------------------------------------------------------------
# CLI entrypoint — main() with injected runner, argv patched
# ---------------------------------------------------------------------------

class TestCLIMain(unittest.TestCase):
    def _run_main(self, argv_repo, runner):
        out = io.StringIO()
        saved = sys.argv[:]
        sys.argv = ["gh_features.py", argv_repo]
        try:
            with redirect_stdout(out):
                gh_features.main(_runner=runner)
        finally:
            sys.argv = saved
        return out.getvalue()

    def test_main_prints_one_line_per_candidate(self):
        output = self._run_main("example/repo", _stub)
        lines = [line for line in output.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)

    def test_main_output_format_tab_separated_four_fields(self):
        output = self._run_main("example/repo", _stub)
        first = output.splitlines()[0]
        parts = first.split("\t")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "example-feature")
        self.assertEqual(parts[1], "implementation")
        self.assertEqual(parts[2], "review")
        self.assertIn("issues/42", parts[3])

    def test_main_no_args_exits_nonzero(self):
        saved = sys.argv[:]
        sys.argv = ["gh_features.py"]
        try:
            with self.assertRaises(SystemExit) as ctx:
                buf = io.StringIO()
                with redirect_stderr(buf):
                    gh_features.main()
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            sys.argv = saved


if __name__ == "__main__":
    unittest.main()
