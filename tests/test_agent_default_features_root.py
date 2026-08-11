#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`specfuse-agent run` survives a bare invocation — issue #1746.

`--features-root` is optional, so the default invocation passes `None`, and
`FeatureProvider` fell back to the string literal `".specfuse/features"` while
`state.read_feature_summaries` called `.is_dir()` on it. The result was an
`AttributeError` raised from inside `_select_next`, which is not wrapped in a
per-provider guard — so one provider's type error ended the whole run,
including the bug, triage and findings providers that were working fine.

Every existing test injects a `Path` fixture, so the string fallback was never
exercised. These tests exercise the **default** rather than a supplied value;
that is the whole point, and a fixture-injecting variant would re-hide the bug.
"""

from __future__ import annotations

import os
import subprocess
import unittest

from tests._workspace import integration_workspace

from specfuse.agent import run as agent_run
from specfuse.agent import state as agent_state
from specfuse.agent.providers.feature import FeatureProvider


def _runner(args, check=False):
    return subprocess.run(args, capture_output=True, text=True, check=check)


class _RestoresCwd(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)


class TestReadFeatureSummariesAcceptsStr(_RestoresCwd):
    """The boundary itself: the reader must not require a `Path`."""

    def test_accepts_a_string_path(self):
        with integration_workspace() as root:
            target = root / ".specfuse" / "features"
            target.mkdir(parents=True, exist_ok=True)
            features, errors = agent_state.read_feature_summaries(str(target))
            self.assertEqual(features, ())
            self.assertEqual(errors, {})

    def test_accepts_a_path(self):
        with integration_workspace() as root:
            target = root / ".specfuse" / "features"
            target.mkdir(parents=True, exist_ok=True)
            features, errors = agent_state.read_feature_summaries(target)
            self.assertEqual(features, ())
            self.assertEqual(errors, {})

    def test_absent_root_is_empty_not_an_error(self):
        with integration_workspace() as root:
            features, errors = agent_state.read_feature_summaries(
                str(root / "nope" / "features"),
            )
            self.assertEqual(features, ())
            self.assertEqual(errors, {})


class TestFeatureProviderDefaultRoot(_RestoresCwd):
    """The shipped default path — no `features_root` supplied anywhere."""

    def test_advertise_does_not_raise_with_no_features_root(self):
        """The bug: `FeatureProvider(features_root=None)` fell back to a str."""
        with integration_workspace() as root:
            (root / ".specfuse" / "features").mkdir(parents=True, exist_ok=True)
            os.chdir(root)
            snapshot = agent_state.gather_snapshot(_runner, repo="acme/widget")
            provider = FeatureProvider(runner=_runner, repo="acme/widget")
            items = list(provider.advertise(snapshot))  # must not raise
            self.assertIsInstance(items, list)

    def test_default_providers_advertise_without_features_root(self):
        """`default_providers()` with no features_root — what `main()` builds
        when the flag is omitted — must advertise across every provider."""
        with integration_workspace() as root:
            (root / ".specfuse" / "features").mkdir(parents=True, exist_ok=True)
            os.chdir(root)
            snapshot = agent_state.gather_snapshot(_runner, repo="acme/widget")
            providers = agent_run.default_providers(
                repo="acme/widget", runner=_runner,
            )
            self.assertTrue(providers)
            for provider in providers:
                with self.subTest(provider=type(provider).__name__):
                    list(provider.advertise(snapshot))  # must not raise

    def test_selector_completes_with_no_features_root(self):
        """`_select_next` iterates every provider's `advertise` un-guarded, so
        one raising ends the run. Assert the selector itself survives."""
        with integration_workspace() as root:
            (root / ".specfuse" / "features").mkdir(parents=True, exist_ok=True)
            os.chdir(root)
            snapshot = agent_state.gather_snapshot(_runner, repo="acme/widget")
            providers = agent_run.default_providers(
                repo="acme/widget", runner=_runner,
            )
            decision = agent_run._select_next(
                providers, snapshot, bugs_preempt=True, handled_ids=set(),
            )
            self.assertIsNotNone(decision)


class TestSuppliedRootStillWorks(_RestoresCwd):
    """Not weakened: an explicitly supplied root behaves as before."""

    def test_explicit_path_is_honoured(self):
        with integration_workspace() as root:
            target = root / ".specfuse" / "features"
            target.mkdir(parents=True, exist_ok=True)
            snapshot = agent_state.gather_snapshot(_runner, repo="acme/widget")
            provider = FeatureProvider(
                runner=_runner, repo="acme/widget", features_root=target,
            )
            self.assertIsInstance(list(provider.advertise(snapshot)), list)

    def test_explicit_str_is_honoured(self):
        with integration_workspace() as root:
            target = root / ".specfuse" / "features"
            target.mkdir(parents=True, exist_ok=True)
            snapshot = agent_state.gather_snapshot(_runner, repo="acme/widget")
            provider = FeatureProvider(
                runner=_runner, repo="acme/widget", features_root=str(target),
            )
            self.assertIsInstance(list(provider.advertise(snapshot)), list)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
