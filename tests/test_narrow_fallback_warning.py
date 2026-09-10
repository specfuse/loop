"""Issue #3292 — a declared `narrow_command` whose selection is empty must say so.

`resolve_narrow_command` falls back to the gate's full `command` when the
per-attempt selection resolves to nothing. That fallback is correct, but it
was silent: a project could carry a `narrow_command:` line indefinitely
believing narrowing fires, while every attempt paid the full suite. The
observed case is a Maven project whose `produces:` names
`src/test/java/...` while `narrow_selection.test_roots` stays at its
`tests/` default.

`verify()` now names the fallback, both on the driver's stderr (the live
log) and inside the report it returns (the attempt note), so the no-op is
visible where the operator looks.
"""
from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def make_wu(produces):
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=Path("/tmp/does-not-matter.md"),
        depends_on=[],
        type="implementation",
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title="test fixture",
        body="(body unused)",
        produces=list(produces),
    )


class TestNarrowFallbackWarning(unittest.TestCase):

    def setUp(self):
        self._orig = loop._run_gate_set
        self.calls = []

        def recording(gate_set, feature_dir, _capture_returncodes=None):
            self.calls.append(list(gate_set))
            return [{"name": g["name"], "ok": True, "report": f"### {g['name']}: PASS"}
                    for g in gate_set]

        loop._run_gate_set = recording
        self._orig_changed = loop.attempt_changed_source_lines
        loop.attempt_changed_source_lines = lambda: {}

    def tearDown(self):
        loop._run_gate_set = self._orig
        loop.attempt_changed_source_lines = self._orig_changed

    def _cfg(self):
        return {"code": [{
            "name": "tests",
            "command": "FULLCMD",
            "narrow_command": "mvn -q test -Dtest={selected_test_modules}",
        }]}

    def test_empty_selection_names_the_fallback(self):
        wu = make_wu(["src/test/java/com/acme/FooTest.java"])
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=self._cfg())
        self.assertTrue(ok)
        self.assertEqual(self.calls[0][0]["command"], "FULLCMD",
                         "the fallback itself is unchanged")
        for surface, text in (("stderr", err.getvalue()), ("report", msg)):
            self.assertIn("narrow_command", text, surface)
            self.assertIn("'tests'", text, surface)
            self.assertIn("tests/", text,
                          f"{surface} names the test_roots the selection used")
            self.assertIn("src/test/java/com/acme/FooTest.java", text,
                          f"{surface} names what produces: offered")
        self.assertNotRegex(msg, loop._FAILURE_KEYWORD_RE,
                            "the note must not read as a failure signature")

    def test_a_firing_selection_says_nothing(self):
        wu = make_wu(["tests/test_foo.py"])
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=self._cfg())
        self.assertTrue(ok)
        self.assertEqual(self.calls[0][0]["command"],
                         "mvn -q test -Dtest=tests.test_foo")
        self.assertNotIn("narrow_command", err.getvalue())
        self.assertNotIn("narrow_command", msg)

    def test_no_narrow_command_says_nothing(self):
        wu = make_wu(["src/foo.py"])
        cfg = {"code": [{"name": "tests", "command": "FULLCMD"}]}
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertTrue(ok)
        self.assertNotIn("narrow_command", err.getvalue())
        self.assertNotIn("narrow_command", msg)


if __name__ == "__main__":
    unittest.main()
