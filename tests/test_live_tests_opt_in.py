#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#3223: live round-trip tests run only on explicit opt-in, against a named repo.

`tests/test_autofix_live.py` and `tests/test_diagnosis_roundtrip_live.py`
ran whenever `gh auth status` succeeded and created real issues in this
repository — two per CI run, about 200 in two days. `tests/_live.py` now
owns the decision: `SPECFUSE_LIVE_TESTS=1` opts in, `SPECFUSE_LIVE_REPO`
names the scratch repository, and an authenticated `gh` alone is never
enough.
"""

from __future__ import annotations

import unittest

from tests._live import live_target


def _gh_ok() -> tuple[bool, str]:
    return True, ""


class TestLiveTestsOptIn(unittest.TestCase):
    def test_authenticated_gh_alone_does_not_opt_in(self):
        ready, reason, repo = live_target(env={}, gh_ready=_gh_ok)
        self.assertFalse(ready)
        self.assertIn("SPECFUSE_LIVE_TESTS", reason)
        self.assertIsNone(repo)

    def test_opt_in_without_a_repo_is_refused(self):
        ready, reason, repo = live_target(env={"SPECFUSE_LIVE_TESTS": "1"}, gh_ready=_gh_ok)
        self.assertFalse(ready)
        self.assertIn("SPECFUSE_LIVE_REPO", reason)
        self.assertIsNone(repo)

    def test_opt_in_with_repo_and_gh_is_ready(self):
        env = {"SPECFUSE_LIVE_TESTS": "1", "SPECFUSE_LIVE_REPO": "acme/scratch"}
        ready, reason, repo = live_target(env=env, gh_ready=_gh_ok)
        self.assertTrue(ready, reason)
        self.assertEqual(repo, "acme/scratch")

    def test_opt_in_with_unauthenticated_gh_is_not_ready(self):
        env = {"SPECFUSE_LIVE_TESTS": "1", "SPECFUSE_LIVE_REPO": "acme/scratch"}
        ready, reason, _ = live_target(env=env, gh_ready=lambda: (False, "gh unauthenticated"))
        self.assertFalse(ready)
        self.assertIn("gh unauthenticated", reason)

    def test_live_test_modules_no_longer_hardcode_this_repository(self):
        import pathlib
        root = pathlib.Path(__file__).parent
        for name in ("test_autofix_live.py", "test_diagnosis_roundtrip_live.py"):
            text = (root / name).read_text(encoding="utf-8")
            self.assertNotIn('REPO = "specfuse/loop"', text, name)
            self.assertIn("live_target", text, name)


if __name__ == "__main__":
    unittest.main()
