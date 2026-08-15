#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# #1414: `specfuse run` launched from a sandboxed shell whose deny-list covers
# ~/.claude/session-env dispatched anyway. Every `claude -p` session it spawned
# then failed to create its own session directory, so the session's Bash tool was
# dead for the whole attempt:
#
#   EPERM: operation not permitted, mkdir '~/.claude/session-env/<session-id>'
#
# Cost $7.85 across two attempts. The second attempt's agent diagnosed it
# correctly and reported `blocked` rather than claiming complete -- good conduct,
# and $7.20 to produce a diagnosis a probe could have made for free.
#
# The failure is invisible from the launching side: the PARENT shell works, only
# the children don't, and attempt 1's files_touched was non-empty because Write
# still functions. So it reads as ordinary work-unit trouble and the blame lands
# on the WU.

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop

loop = load_loop()


class TestSessionEnvPreflight(unittest.TestCase):
    """`require_session_env_writable` must refuse before spending anything."""

    def test_helper_exists(self):
        self.assertTrue(
            hasattr(loop, "require_session_env_writable"),
            "the preflight must be a named guard alongside "
            "require_feature_folder_committed / _unmodified, not inline in run()",
        )

    def test_writable_root_passes_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop.require_session_env_writable(Path(tmp))  # must not raise or exit

    def test_unwritable_root_exits_rather_than_dispatching(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "session-env"
            root.mkdir()
            root.chmod(0o500)  # readable, not writable — the sandbox's shape
            try:
                with self.assertRaises(SystemExit) as caught:
                    loop.require_session_env_writable(root)
            finally:
                # Restore INSIDE the context: addCleanup runs after
                # TemporaryDirectory has already removed the tree.
                root.chmod(0o700)
            self.assertNotEqual(caught.exception.code, 0)

    def test_absent_root_is_created_when_possible(self):
        # A first-ever run has no session-env dir. That is not a failure — the
        # guard must distinguish "cannot create" from "does not exist yet",
        # or it refuses every clean machine.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "never-existed"
            loop.require_session_env_writable(root)
            self.assertTrue(root.is_dir())

    def test_probe_leaves_nothing_behind(self):
        # The probe creates and removes a directory. Leaving debris in the user's
        # session-env root would be its own small bug.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = set(os.listdir(root))
            loop.require_session_env_writable(root)
            self.assertEqual(set(os.listdir(root)), before)

    def test_refusal_names_the_path_and_the_cause(self):
        # The whole point is that the operator learns what to fix. A bare
        # "permission denied" reproduces the invisibility this guard exists to
        # remove.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "session-env"
            root.mkdir()
            root.chmod(0o500)
            try:
                with self.assertRaises(SystemExit) as caught:
                    loop.require_session_env_writable(root)
            finally:
                root.chmod(0o700)
            message = str(caught.exception)
            self.assertIn(str(root), message)
            self.assertIn("sandbox", message.lower())

    def test_default_root_is_the_claude_session_env_dir(self):
        # Called with no argument the guard must probe the real location a
        # dispatched session uses, not a guess.
        with mock.patch.object(loop, "_session_env_root") as probe:
            probe.return_value = Path(tempfile.gettempdir()) / "specfuse-probe-root"
            loop.require_session_env_writable()
            probe.assert_called_once()

    def test_concurrent_calls_do_not_exit(self):
        # #1951: the probe used a fixed name, so two overlapping calls raced —
        # the loser's mkdir(exist_ok=True) re-checked is_dir() after the winner's
        # finally-block rmdir() already removed it, and it re-raised FileExistsError
        # as though the root itself were unwritable.
        import threading

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            errors = []
            barrier = threading.Barrier(8)

            def worker():
                barrier.wait()
                try:
                    loop.require_session_env_writable(root)
                except SystemExit as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(errors, [])

    def test_run_invokes_the_guard_before_dispatch(self):
        # A guard nothing calls is the defect unfixed. Assert it is wired into
        # the same preflight block as the other two.
        import inspect

        src = inspect.getsource(loop.run)
        self.assertIn("require_session_env_writable", src)


if __name__ == "__main__":
    unittest.main()
