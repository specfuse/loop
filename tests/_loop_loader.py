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


def load_loop():
    return load_module(".specfuse/scripts/loop.py", "loop_under_test")


def load_lint():
    return load_module(".specfuse/scripts/lint_plan.py", "lint_plan_under_test")


def load_miniyaml():
    return load_module(".specfuse/scripts/_miniyaml.py", "miniyaml_under_test")
