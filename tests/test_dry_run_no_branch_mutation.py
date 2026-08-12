# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`--dry-run` must not move HEAD (#796).

`ensure_feature_branch` runs `git checkout -B <branch>`, which creates the
feature's declared branch and moves the working tree onto it. #796 reported
that happening under `--dry-run`: a flag whose entire contract is "show me
what would happen" left the reporter on a driver-created branch holding an
empty feature folder, with the failure presenting as "my files vanished".

The behaviour is correct on current `main` -- the whole pre-flight block sits
inside `if not dry_run:` -- but nothing pinned it. The guard is a single
enclosing conditional over a dozen statements, so moving one call out of the
block, or adding a new mutating call after it, silently reintroduces the bug.
These tests are the pin: one measures HEAD across a real dry run, one asserts
the branch helper is never called.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop import loop

_FEATURE_ID = "FEAT-2026-9796"
_BRANCH = "feat/FEAT-2026-9796-dry-run-probe"

_PLAN = f"""---
feature_id: {_FEATURE_ID}
title: dry-run probe
branch: {_BRANCH}
roadmap_goal: probe
status: active
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: {_FEATURE_ID}/T01
        file: WU-01.md
        depends_on: []
```
"""


class _Repo:
    """A real git repo carrying one dispatchable feature."""

    def __init__(self, root: Path):
        self.root = root
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "probe@example.com")
        self._git("config", "user.name", "Probe")
        # The host's global signing config must not decide whether this
        # fixture can commit (#296).
        self._git("config", "commit.gpgsign", "false")

        self.feature_dir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-dry-run-probe"
        self.feature_dir.mkdir(parents=True)
        (self.feature_dir / "PLAN.md").write_text(_PLAN)
        (self.feature_dir / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
        (self.feature_dir / "WU-01.md").write_text(
            "---\ntype: implementation\nstatus: pending\n"
            "cost_usd: 0.0\nplanned_cost_usd: 1.0\n---\n\n# T01\n\nbody\n"
        )
        self._git("add", "-A")
        self._git("commit", "-qm", "seed")

    def _git(self, *args) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, text=True, check=False,
        ).stdout.strip()

    def current_branch(self) -> str:
        return self._git("branch", "--show-current")

    def branches(self) -> set:
        out = self._git("branch", "--format=%(refname:short)")
        return {line.strip() for line in out.splitlines() if line.strip()}


class TestDryRunLeavesHeadAlone(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._orig_features_dir = loop.FEATURES_DIR
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))
        os.chdir(self.repo.root)
        loop.FEATURES_DIR = self.repo.feature_dir.parent

    def tearDown(self):
        loop.FEATURES_DIR = self._orig_features_dir
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _dry_run(self) -> int:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            return loop.run(None, dry_run=True)

    def test_head_is_unchanged_by_a_dry_run(self):
        before = self.repo.current_branch()

        self._dry_run()

        self.assertEqual(self.repo.current_branch(), before)

    def test_the_declared_feature_branch_is_not_created(self):
        self._dry_run()

        self.assertNotIn(_BRANCH, self.repo.branches())

    def test_ensure_feature_branch_is_never_called(self):
        """The behavioural assertions above can pass for the wrong reason.

        If a future refactor made `ensure_feature_branch` a no-op on this
        fixture -- an early return on some unrelated condition -- HEAD would
        still be unchanged and the bug would still be back for any repo that
        does not meet that condition. Asserting the call never happens pins
        the guard rather than one of its consequences.
        """
        with patch.object(loop, "ensure_feature_branch") as ensure:
            self._dry_run()

        ensure.assert_not_called()

    def test_a_dry_run_from_an_unrelated_branch_still_succeeds(self):
        """#796's second point: the guard also makes `--dry-run` usable from
        a branch that is not the feature's own, which is the normal state
        when sanity-checking a gate graph before starting work."""
        self.repo._git("checkout", "-q", "-b", "some-other-branch")

        rc = self._dry_run()

        self.assertEqual(rc, 0)
        self.assertEqual(self.repo.current_branch(), "some-other-branch")


if __name__ == "__main__":
    unittest.main()
