#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#3554 — post-rename validation lints feature folders only, not every directory."""

import tempfile
import unittest

from tests.test_ids_migrate_all import _git, _make, _run


class ValidateSkipsNonFeatureDirs(unittest.TestCase):
    def test_empty_untracked_dot_directory_is_not_linted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            (root / ".specfuse" / "features" / ".claude").mkdir()
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertNotIn(".claude", out)
            self.assertIn("validated", out)

    def test_directory_without_a_feature_id_name_is_not_linted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            notes = root / ".specfuse" / "features" / "notes"
            notes.mkdir()
            (notes / "README.md").write_text("scratch\n")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "notes")
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertNotIn("ERROR: notes", out)


if __name__ == "__main__":
    unittest.main()
