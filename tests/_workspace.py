#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Shared integration-workspace fixture.

Single source of truth for integration_workspace() — guards against
gc.auto background detach and ensures all fd/handle flushes complete
before TemporaryDirectory cleanup fires.
"""

from __future__ import annotations

import functools
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD_SRC = REPO_ROOT / ".specfuse"


def write_stub_deliverable(wu) -> Path:
    """Write the file a real agent would have produced. Returns its path.

    Dispatch stubs that touch nothing leave a squash diff naming only the WU's
    own markdown and events.jsonl — which the deliverable-presence gate
    (FEAT-2026-0022) correctly rejects as a hollow pass. Such stubs used to
    survive by accident: `squash_commit`'s `git add -A` committed the driver's
    untracked `.specfuse/.loop.lock`, and the guard counted that as the WU's
    output. Issue #150 stopped `add -A` from absorbing pre-existing untracked
    files, so a stub must now model an agent that actually writes code.

    Call this from any dispatch stub whose test expects the WU to PASS. Do NOT
    call it from stubs whose test asserts the guard FIRES — those must keep
    writing nothing, which is the condition under test.
    """
    path = Path("src") / f"{wu.wu_id.split('/')[-1].lower().replace('-', '_')}_impl.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# deliverable for {wu.wu_id}\n")
    return path


def with_deliverable(dispatch_stub):
    """Wrap a dispatch stub so it writes a deliverable, like a real agent would.

    Apply in a test class's `_patch` when `name == "dispatch"`. See
    `write_stub_deliverable` for why stubs that write nothing now fail, and for
    when NOT to use this (tests that assert the deliverable guard fires).
    """
    @functools.wraps(dispatch_stub)
    def _wrapped(wu, *args, **kwargs):
        write_stub_deliverable(wu)
        return dispatch_stub(wu, *args, **kwargs)
    return _wrapped


@contextmanager
def integration_workspace():
    """Build a temp git repo with a minimal .specfuse/ scaffold and yield its path."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email",
                        "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"],
                       check=True)
        subprocess.run(["git", "-C", str(root), "config", "gc.auto", "0"],
                       check=True)
        subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign", "false"],
                       check=True)
        (root / "README.md").write_text("# fixture\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"],
                       check=True)
        shutil.copytree(SCAFFOLD_SRC / "scripts", root / ".specfuse/scripts")
        shutil.copytree(SCAFFOLD_SRC / "templates", root / ".specfuse/templates")
        shutil.copytree(SCAFFOLD_SRC / "rules", root / ".specfuse/rules")
        (root / ".specfuse/verification.yml").write_text(
            "code:\n  - name: noop\n    command: \"true\"\n"
            "doc:\n  - name: noop\n    command: \"true\"\n"
            "plannext:\n  - name: noop\n    command: \"true\"\n"
        )
        (root / ".specfuse/features").mkdir(parents=True)
        try:
            yield root
        finally:
            subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True, capture_output=True,
            )
