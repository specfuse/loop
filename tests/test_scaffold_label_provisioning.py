# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests that init()/upgrade_specfuse() call provision_labels without ever
letting it fail the caller, and honor the SPECFUSE_NO_LABELS opt-out.

FEAT-2026-0071/T03.
"""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

from specfuse.loop import labels as labels_module
from specfuse.loop.scaffold import init, init_specfuse, upgrade_specfuse


def _make_target() -> tuple[pathlib.Path, str]:
    tmpdir = tempfile.mkdtemp()
    return pathlib.Path(tmpdir), tmpdir


class TestScaffoldLabelProvisioning(unittest.TestCase):
    def setUp(self):
        # Never let a stray env var from the outer shell change these tests'
        # behaviour underneath them.
        self._env_patch = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        os.environ.pop("SPECFUSE_NO_LABELS", None)
        self.addCleanup(self._env_patch.stop)

    def test_init_calls_provision_labels(self):
        target, tmpdir = _make_target()
        try:
            with mock.patch.object(
                labels_module, "provision_labels", wraps=labels_module.provision_labels
            ) as spy:
                init(target)
            spy.assert_called_once()
        finally:
            shutil.rmtree(tmpdir)

    def test_upgrade_calls_provision_labels(self):
        target, tmpdir = _make_target()
        try:
            init_specfuse(target)
            with mock.patch.object(
                labels_module, "provision_labels", wraps=labels_module.provision_labels
            ) as spy:
                upgrade_specfuse(target)
            spy.assert_called_once()
        finally:
            shutil.rmtree(tmpdir)

    def test_init_survives_provisioning_raising(self):
        target, tmpdir = _make_target()
        try:
            with mock.patch.object(
                labels_module, "provision_labels", side_effect=RuntimeError("boom")
            ):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    written = init(target)
            self.assertIsInstance(written, list)
            self.assertGreater(len(written), 0)
        finally:
            shutil.rmtree(tmpdir)

    def test_upgrade_survives_provisioning_raising(self):
        target, tmpdir = _make_target()
        try:
            init_specfuse(target)
            with mock.patch.object(
                labels_module, "provision_labels", side_effect=RuntimeError("boom")
            ):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    written = upgrade_specfuse(target)
            self.assertIsInstance(written, list)
            self.assertGreater(len(written), 0)
        finally:
            shutil.rmtree(tmpdir)

    def test_no_labels_env_var_skips_init_provisioning(self):
        target, tmpdir = _make_target()
        try:
            with mock.patch.object(labels_module, "provision_labels") as spy:
                with mock.patch.dict(os.environ, {"SPECFUSE_NO_LABELS": "1"}):
                    init(target)
            spy.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_no_labels_env_var_skips_upgrade_provisioning(self):
        target, tmpdir = _make_target()
        try:
            init_specfuse(target)
            with mock.patch.object(labels_module, "provision_labels") as spy:
                with mock.patch.dict(os.environ, {"SPECFUSE_NO_LABELS": "1"}):
                    upgrade_specfuse(target)
            spy.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_no_labels_env_var_does_not_change_written_files(self):
        target_a, tmpdir_a = _make_target()
        target_b, tmpdir_b = _make_target()
        try:
            with mock.patch.object(labels_module, "provision_labels"):
                written_normal = init(target_a)
            with mock.patch.dict(os.environ, {"SPECFUSE_NO_LABELS": "1"}):
                written_no_labels = init(target_b)
            self.assertEqual(written_normal, written_no_labels)
        finally:
            shutil.rmtree(tmpdir_a)
            shutil.rmtree(tmpdir_b)

    def test_no_labels_kwarg_skips_provisioning(self):
        target, tmpdir = _make_target()
        try:
            with mock.patch.object(labels_module, "provision_labels") as spy:
                init(target, no_labels=True)
            spy.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_returned_list_contains_no_label_names(self):
        target, tmpdir = _make_target()
        try:
            with mock.patch.object(labels_module, "provision_labels"):
                written = init(target)
            registry_names = {spec.name for spec in labels_module.LABEL_REGISTRY}
            self.assertTrue(registry_names.isdisjoint(set(written)))
        finally:
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()
