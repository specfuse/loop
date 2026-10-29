#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0247/T09 — old IDs resolve through .specfuse/id-aliases.yml."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import gate_eval, gh_features, ids, loop

OLD = "FEAT-2026-0008"
NEW = "FEAT-ACME-2026-0008"
FOLDER = f"{NEW}-health"


def _repo(tmp, alias=True, folder=True, target=NEW):
    root = Path(tmp)
    feats = root / ".specfuse" / "features"
    feats.mkdir(parents=True)
    if folder:
        (feats / FOLDER).mkdir()
        (feats / FOLDER / "PLAN.md").write_text("---\nfeature_id: x\n---\n")
    if alias:
        (root / ".specfuse" / "id-aliases.yml").write_text(f"{OLD}: {target}\n")
    return root


def _issue(title):
    return [{"number": 1, "title": title, "labels": [], "url": "u", "body": ""}]


class ResolveFn(unittest.TestCase):
    def test_alias_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            self.assertEqual(ids.resolve(root, OLD), NEW)
            self.assertEqual(ids.resolve(root, NEW), NEW)

    def test_no_alias_map_is_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, alias=False)
            self.assertEqual(ids.resolve(root, OLD), OLD)

    def test_dangling_alias_reported_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, folder=False)
            err = io.StringIO()
            self.assertEqual(ids.resolve(root, OLD, err=err), OLD)
            self.assertIn("has no feature folder", err.getvalue())


class DriverFeatureArg(unittest.TestCase):
    def _resolve(self, root, arg):
        feats = root / ".specfuse" / "features"
        with mock.patch.object(loop, "FEATURES_DIR", feats), \
                mock.patch.object(loop, "REPO_ROOT", root):
            return loop._resolve_feature_dir(arg)

    def test_old_id_reaches_renamed_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            self.assertEqual(self._resolve(root, OLD).name, FOLDER)

    def test_without_alias_exits_as_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, alias=False)
            with self.assertRaises(SystemExit) as cm:
                self._resolve(root, OLD)
            self.assertIn(f"No feature {OLD}", str(cm.exception))

    def test_dangling_alias_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, folder=False)
            with mock.patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    self._resolve(root, OLD)
            self.assertIn(f"No feature {OLD}", str(cm.exception))


class GateEvalLookup(unittest.TestCase):
    def test_old_id_reaches_renamed_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            self.assertEqual(gate_eval._resolve_feature_dir(OLD, root).name, FOLDER)
            self.assertEqual(gate_eval._resolve_feature_dir("0008", root).name, FOLDER)

    def test_without_alias_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, alias=False)
            self.assertIsNone(gate_eval._resolve_feature_dir(OLD, root))
            self.assertEqual(gate_eval._resolve_feature_dir("0008", root).name, FOLDER)

    def test_dangling_alias_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, folder=False)
            with mock.patch("sys.stderr", io.StringIO()):
                self.assertIsNone(gate_eval._resolve_feature_dir(OLD, root))


class IssueTitleMatch(unittest.TestCase):
    def _ids(self, root, title):
        got = gh_features.list_features("o/r", runner=lambda r: _issue(title), repo_root=root)
        return [c["feature_id"] for c in got]

    def test_old_title_maps_to_renamed_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp)
            self.assertEqual(self._ids(root, f"[{OLD}] Health"), [NEW])

    def test_without_alias_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, alias=False)
            self.assertEqual(self._ids(root, f"[{OLD}] Health"), [OLD])

    def test_dangling_alias_keeps_old_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, folder=False)
            with mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(self._ids(root, f"[{OLD}] Health"), [OLD])


if __name__ == "__main__":
    unittest.main()
