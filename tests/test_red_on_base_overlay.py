# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The red-on-base probe runs the PR's own tests against the base (#3417).

The probe's worktree sits at the merge base, so it held the *base's* copy of
every changed test path. Only a brand-new test file was measured -- absent at
base, the command failed. A test added to an existing class ran the base's
class, which passes; an updated golden was compared by the base's own golden,
which matches. Both read "not red on base" and declined
`test_not_red_on_base` whatever the fix (clabonte/generator#2154).

The probe now overlays the PR head's version of each selected test path onto
the base worktree: the PR's tests, the base's production code -- which is what
"red on base" means. Pinned for all three shapes over a real repository.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop.red_on_base import probe_red_on_base

# The operator's command: run every test script; `{tests}` names the changed
# test paths, as a real command would use them to select.
_COMMAND = 'for t in tests/test_*.sh; do sh "$t" || exit 1; done; : {tests}'


def _git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _real_runner(argv, check=False, cwd=None, **_kwargs):
    return subprocess.run(argv, check=check, capture_output=True, text=True, cwd=cwd)


class TestThePrsTestsRunAgainstTheBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        (self.repo / "tests").mkdir(parents=True)
        _git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "prod.txt").write_text("bug\n")
        (self.repo / "tests" / "test_existing.sh").write_text("true\n")
        (self.repo / "tests" / "expected.txt").write_text("bug\n")
        (self.repo / "tests" / "test_golden.sh").write_text("cmp -s prod.txt tests/expected.txt\n")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base = _git(self.repo, "rev-parse", "HEAD")
        self._cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _head(self, name, edits):
        """Commit the fix plus *edits* on a branch off base; return its SHA."""
        _git(self.repo, "checkout", "-q", "-b", name, self.base)
        (self.repo / "prod.txt").write_text("fixed\n")
        for path, text in edits.items():
            (self.repo / path).write_text(text)
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", name)
        sha = _git(self.repo, "rev-parse", "HEAD")
        _git(self.repo, "checkout", "-q", "main")
        return sha

    def _probe(self, head, test_files):
        return probe_red_on_base(
            _real_runner,
            base_sha=self.base,
            head_sha=head,
            test_files=test_files,
            command_template=_COMMAND,
            worktree_root=self._tmp.name,
        )

    def test_a_new_test_file_reads_red(self):
        head = self._head("new-file", {"tests/test_new.sh": "grep -q fixed prod.txt\n"})

        probe = self._probe(head, ["tests/test_new.sh"])

        self.assertIs(probe.verdict, True, probe.reason)

    def test_a_test_added_to_an_existing_file_reads_red(self):
        head = self._head(
            "added-test", {"tests/test_existing.sh": "true\ngrep -q fixed prod.txt\n"},
        )

        probe = self._probe(head, ["tests/test_existing.sh"])

        self.assertIs(probe.verdict, True, probe.reason)

    def test_an_updated_golden_reads_red(self):
        head = self._head("golden", {"tests/expected.txt": "fixed\n"})

        probe = self._probe(head, ["tests/expected.txt"])

        self.assertIs(probe.verdict, True, probe.reason)

    def test_a_test_that_passes_without_the_fix_still_reads_not_red(self):
        head = self._head("adjacent", {"tests/test_existing.sh": "true\ntrue\n"})

        probe = self._probe(head, ["tests/test_existing.sh"])

        self.assertIs(probe.verdict, False, probe.reason)

    def test_the_live_checkout_is_untouched(self):
        head = self._head(
            "added-test", {"tests/test_existing.sh": "true\ngrep -q fixed prod.txt\n"},
        )

        self._probe(head, ["tests/test_existing.sh"])

        self.assertEqual((self.repo / "tests" / "test_existing.sh").read_text(), "true\n")
        self.assertEqual(_git(self.repo, "status", "--porcelain"), "")


class TestOverlayFailuresAreUnverified(unittest.TestCase):
    def _run(self, runner, head="def456"):
        return probe_red_on_base(
            runner, base_sha="abc123", head_sha=head,
            test_files=["tests/test_a.py"], command_template="pytest {tests}",
            worktree_root=tempfile.gettempdir(),
        )

    def test_unknown_head_is_unverified(self):
        probe = self._run(lambda argv, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""), head="")

        self.assertIsNone(probe.verdict)
        self.assertEqual(probe.reason, "head_sha_lookup_failed")

    def test_overlay_failure_is_unverified_with_gits_error(self):
        def runner(argv, **_kwargs):
            if "checkout" in argv:
                return SimpleNamespace(
                    returncode=1, stdout="",
                    stderr="error: pathspec 'tests/test_a.py' did not match",
                )
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        probe = self._run(runner)

        self.assertIsNone(probe.verdict)
        self.assertTrue(probe.reason.startswith("overlay_failed"), probe.reason)
        self.assertIn("did not match", probe.reason)


if __name__ == "__main__":
    unittest.main()
