#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Shared loader for the loop driver module under test.

`loop.py` lives at `.specfuse/scripts/loop.py` (it ships in the scaffold a target
repo installs), not as an importable package. The test suite loads it directly via
importlib so tests can call into its functions without any packaging gymnastics.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_module(relpath: str, module_name: str):
    path = REPO_ROOT / relpath
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# The driver code now lives in the `specfuse.loop` package (FEAT-2026-0019); the
# `.specfuse/scripts/*.py` files are thin shims over it. Tests import the package
# directly so they exercise the canonical code and monkeypatching takes effect on
# the same module the driver runs. `load_module` remains for any test that still
# needs to exec a script file by path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_loop():
    import specfuse.loop.loop as m
    return m


def load_lint():
    import specfuse.loop.lint_plan as m
    return m


def load_miniyaml():
    import specfuse.loop._miniyaml as m
    return m
