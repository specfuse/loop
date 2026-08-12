#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`_make_repo` fixtures must not inherit the host's global commit signing
config (#296).

``tests/test_autosync_no_cwd_leak.py``'s ``_make_repo`` pins
``user.email``/``user.name`` (identity) but not ``commit.gpgsign``
(possibility). ``git init`` does not isolate a repo from global config, so
any host with ``commit.gpgsign = true`` and an unreachable signing agent
turns every ``_make_repo`` commit into a hard failure:

    error: Couldn't get agent socket?
    fatal: failed to write commit object

This test simulates that host by pointing ``GIT_CONFIG_GLOBAL`` at a config
file with signing enabled and a nonexistent ``gpg.program``, then asserts
``_make_repo`` still succeeds — which it only does if the fixture pins
``commit.gpgsign = false`` locally, overriding the inherited global setting.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_autosync_no_cwd_leak import _make_repo


class TestMakeRepoIsolatesGpgSign(unittest.TestCase):
    """`_make_repo` must not inherit a host's global commit.gpgsign."""

    def test_make_repo_succeeds_with_global_signing_enabled_and_agent_unreachable(self):
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as config_dir:
            global_config = Path(config_dir) / "gitconfig"
            global_config.write_text(
                "[commit]\n"
                "\tgpgsign = true\n"
                "[gpg]\n"
                "\tprogram = /nonexistent/gpg-agent-stub\n",
                encoding="utf-8",
            )
            previous = os.environ.get("GIT_CONFIG_GLOBAL")
            os.environ["GIT_CONFIG_GLOBAL"] = str(global_config)
            try:
                try:
                    _make_repo(Path(repo_dir))
                except subprocess.CalledProcessError as exc:
                    self.fail(
                        "_make_repo inherited the host's global commit "
                        f"signing config and failed to commit: {exc.stderr}"
                    )
            finally:
                if previous is None:
                    os.environ.pop("GIT_CONFIG_GLOBAL", None)
                else:
                    os.environ["GIT_CONFIG_GLOBAL"] = previous


if __name__ == "__main__":
    unittest.main()
