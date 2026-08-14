# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The conductor dispatches the source it is standing in (#2186).

`specfuse-agent` dispatched the driver as `specfuse run`, which resolves to
whatever `specfuse` is on PATH. In a dogfooding checkout that is the
installed build -- observed 2026-08-14 roughly twenty merged PRs behind the
tree, both reporting the same version string. FEAT-2026-0080's close then
failed three times, at $40.27 across 99 minutes, against a bug fixed on main
two days earlier.

`build_provenance` cannot catch this from inside the dispatched process: a
build old enough to be the problem is old enough to lack the check. The
dispatcher is newer than what it dispatches, so the decision belongs here.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.agent.driver_command import (
    INSTALLED_COMMAND,
    describe_command,
    resolve_driver_command,
)


def _make_checkout(root: Path) -> Path:
    """A directory that looks like a driver source checkout to
    `build_provenance.source_tree_package_dir`."""
    package = root / "specfuse" / "loop"
    package.mkdir(parents=True)
    (package / "loop.py").write_text("# stand-in for the driver\n")
    return root


class ResolveDriverCommandTests(unittest.TestCase):
    def test_a_source_checkout_dispatches_its_own_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_checkout(Path(tmp))
            command = resolve_driver_command(start=root)

        self.assertEqual(command[0], sys.executable)
        self.assertEqual(command[1], "-m")
        # `-m` puts the working directory first on sys.path, so this resolves
        # the checkout's source even when the interpreter is a pipx venv's.
        self.assertTrue(command[2].startswith("specfuse.loop"))

    def test_a_plain_project_still_dispatches_the_installed_cli(self):
        """Silent for downstream by construction: a project that installed
        Specfuse has no source tree of its own, and `specfuse run` is the
        correct thing to run there."""
        with tempfile.TemporaryDirectory() as tmp:
            command = resolve_driver_command(start=Path(tmp))

        self.assertEqual(tuple(command), INSTALLED_COMMAND)

    def test_an_explicit_override_is_never_second_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_checkout(Path(tmp))
            command = resolve_driver_command(
                start=root, override=("my-specfuse", "run")
            )

        self.assertEqual(tuple(command), ("my-specfuse", "run"))

    def test_the_description_names_which_build_is_being_dispatched(self):
        """The operator watches the conductor's stdout; the driver's own
        output is teed to a file nobody reads during a run (#2186)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_checkout(Path(tmp))
            in_tree = describe_command(resolve_driver_command(start=root))
            installed = describe_command(INSTALLED_COMMAND)

        self.assertIn("source", in_tree)
        self.assertIn("installed", installed)
        self.assertNotEqual(in_tree, installed)


class DispatchedArgvTests(unittest.TestCase):
    """The resolved command must accept the same flags `specfuse run` does --
    `build_invocation` appends `--feature <id>` to whatever it is given."""

    def test_the_in_tree_module_accepts_the_feature_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "specfuse.loop.loop", "--help"],
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).resolve().parent.parent,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--feature", result.stdout)


class ProviderWiringTests(unittest.TestCase):
    def test_the_feature_provider_passes_its_command_to_the_driver(self):
        from specfuse.agent import driver_invoke
        from specfuse.agent.providers.feature import FeatureProvider
        from specfuse.agent.queue_read import DISPOSITION_WORKABLE
        from specfuse.agent.run import ActionItem, KIND_FEATURE

        seen = {}

        def _fake_advance(runner, feature_id, *, features_root, command=None, **kwargs):
            seen["command"] = command
            return driver_invoke.HaltResult(
                halt_class=driver_invoke.HALT_FEATURE_DONE, detail=None, argv=[]
            )

        real = driver_invoke.advance_feature
        driver_invoke.advance_feature = _fake_advance
        try:
            provider = FeatureProvider(
                repo="acme-widget/example",
                features_root="/nonexistent",
                driver_command=("my-specfuse", "run"),
            )
            item_id = "feature-FEAT-2026-0001-g1"
            provider._rows = {
                item_id: {
                    "disposition": DISPOSITION_WORKABLE,
                    "feature_id": "FEAT-2026-0001",
                }
            }
            provider.execute(
                ActionItem(item_id=item_id, kind=KIND_FEATURE, summary="advance")
            )
        finally:
            driver_invoke.advance_feature = real

        self.assertEqual(tuple(seen["command"]), ("my-specfuse", "run"))


if __name__ == "__main__":
    unittest.main()
