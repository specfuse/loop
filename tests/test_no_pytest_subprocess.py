# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""No test may shell out to `python3 -m pytest`.

pytest is a dependency of NOTHING in this repository — it appears in no
`pyproject.toml` extra and in no CI workflow. The entire suite runs under
`python3 -m unittest discover -s tests`, declared in `.specfuse/verification.yml`.

A test that shells out to pytest therefore has the worst available failure
shape: green on any developer machine whose virtualenv happens to have pytest
installed, red only on the runner, and red for a reason unrelated to what it
asserts. The failure reads `No module named pytest`, which points at the
environment rather than at the test.

This guard exists because that defect shipped THREE times before anyone stopped
patching instances and wrote a check:

  1. FEAT-2026-0042/T02 — `test_label_registry_covers_consumers_suite_passes`
  2. FEAT-2026-0059/T02 — two suite-passes tests
  3. FEAT-2026-0059/T03 — two more

All five came from the same authoring shape: a work-unit acceptance criterion
saying "run suite X by name and quote the result", which invites reaching for a
runner rather than loading the suite in-process. The durable fix is this check,
not a fourth patch.

The in-process replacement is `unittest.defaultTestLoader.loadTestsFromName`
plus a `TextTestRunner` writing to a `StringIO` — no subprocess, no dependency,
and a `countTestCases() > 0` assertion so a renamed target module fails loudly
instead of passing vacuously on an empty suite.
"""

from __future__ import annotations

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

def _pytest_invocations(path):
    """Return `lineno: source` for every real pytest INVOCATION in *path*.

    AST-based, not regex-based, and deliberately so: a regex cannot tell an
    invocation from a mention, and the first cut of this guard fired on its own
    docstring for saying "NOT a `python3 -m pytest` subprocess". Prose about
    pytest is fine and this file is full of it; only a call is a defect.

    Matches a list/tuple literal containing consecutive "-m" and "pytest"
    elements — the argv form — and any string literal containing "-m pytest",
    the shell-command form.
    """
    import ast
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines = src.splitlines()
    hits = []

    # Docstrings are Constant nodes too, so prose describing this very defect
    # would flag. Collect them and skip. Comments never reach the AST.
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef,
                             ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                docstrings.add(id(body[0].value))

    class V(ast.NodeVisitor):
        def visit_Constant(self, node):
            if (id(node) not in docstrings
                    and isinstance(node.value, str)
                    and "-m pytest" in node.value):
                hits.append(node.lineno)
            self.generic_visit(node)

        def _seq(self, node):
            vals = [e.value for e in node.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            for a, b in zip(vals, vals[1:], strict=False):
                if a == "-m" and b == "pytest":
                    hits.append(node.lineno)
            self.generic_visit(node)

        visit_List = _seq
        visit_Tuple = _seq

    V().visit(tree)
    return [f"{path.name}:{n}: {lines[n - 1].strip()}" for n in sorted(set(hits))]


# Files legitimately containing the literal string: this guard itself, and any
# test asserting on a CONFIG VALUE a target project may set (the scaffold lets a
# consumer declare their own ci_check command, which may well be pytest — that is
# their choice about their repo, not this repo running pytest).
_ALLOWED = {
    "test_no_pytest_subprocess.py",
    "test_scaffold_wiring.py",
}


class TestNoPytestSubprocess(unittest.TestCase):

    def test_no_test_file_invokes_pytest(self):
        offenders = []
        for path in sorted(TESTS_DIR.glob("test_*.py")):
            if path.name in _ALLOWED:
                continue
            offenders.extend(_pytest_invocations(path))

        self.assertEqual(
            offenders, [],
            "these tests shell out to pytest, which is not a dependency of this "
            "repository and is absent from CI — they pass locally and fail on the "
            "runner with `No module named pytest`. Load the suite in-process with "
            "unittest.defaultTestLoader.loadTestsFromName instead, asserting "
            "countTestCases() > 0 so a renamed module fails loudly:\n  "
            + "\n  ".join(offenders))

    def test_the_guard_is_falsifiable(self):
        """A planted invocation must be caught, and prose must not be."""
        import tempfile
        cases = [
            ('subprocess.run([sys.executable, "-m", "pytest", "-q", "x.py"])', True),
            ('run("python3 -m pytest tests/")', True),
            ('"""NOT a `python3 -m pytest` subprocess — prose only."""', False),
            ('# pytest is not a dependency of this repository', False),
            ('MSG = "use unittest, never pytest"', False),
        ]
        with tempfile.TemporaryDirectory() as td:
            for i, (src, should_hit) in enumerate(cases):
                f = pathlib.Path(td) / f"probe_{i}.py"
                f.write_text(src + "\n")
                hits = _pytest_invocations(f)
                self.assertEqual(
                    bool(hits), should_hit,
                    f"case {i!r} expected hit={should_hit}, got {hits}")

    def test_allowlist_entries_still_exist(self):
        """A stale allowlist silently widens the guard's blind spot."""
        for name in _ALLOWED:
            self.assertTrue(
                (TESTS_DIR / name).is_file(),
                f"{name} is allowlisted but no longer exists — drop it from _ALLOWED")


if __name__ == "__main__":
    unittest.main()
