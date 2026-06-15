#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Test package init.

Isolates the test process from any inherited git environment so that
subprocess `git` calls inside tests target their own temp repos and never
the host repository.

Why this is here: when the suite runs from a git hook (e.g. the pre-push
hook invoking scripts/smoke-test.sh), git exports GIT_DIR, GIT_WORK_TREE,
GIT_INDEX_FILE, etc. into the environment. A child `git` process honors those
variables over its working directory, so a test that `git init`-s a temp dir
would instead read and write the HOST repo. Incident 2026-06-15: this wrote
core.bare=true into the real .git/config and created ~20 fixture branches in
the real ref store when a push triggered the hook.

Scrub the leaky variables once, at import — before any test runs. unittest's
discovery imports this package first, so every test (helper-based or
self-rolled) inherits the cleaned environment for its subprocesses.
"""

from __future__ import annotations

import os

# Variables that pin git to a specific repo/index/config regardless of cwd.
# Removing them makes `git -C <tmp>` (and a bare `git` run with cwd inside the
# temp repo) resolve to that temp repo, which is what every test assumes.
_LEAKY_GIT_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
)


def scrub_git_env(environ=None):
    """Remove inherited git-location env vars so subprocess git targets cwd.

    Operates on ``os.environ`` by default (mutating the live process env), or
    on a supplied mapping. Also sets ``GIT_CONFIG_NOSYSTEM=1`` so a host
    ``/etc/gitconfig`` cannot perturb test repos. Returns the list of leaky
    vars actually removed. Idempotent: a clean env yields ``[]``.
    """
    env = os.environ if environ is None else environ
    removed = [v for v in _LEAKY_GIT_VARS if v in env]
    for v in removed:
        del env[v]
    env.setdefault("GIT_CONFIG_NOSYSTEM", "1")
    return removed


# Run at import — before any test module loads.
scrub_git_env()
