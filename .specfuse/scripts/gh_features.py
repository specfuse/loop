#\!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Shim — re-exports specfuse.loop.gh_features. Canonical code lives in the package.

This file ships in the scaffold for dogfood (`python .specfuse/scripts/gh_features.py`)
and back-compat imports. It path-inserts the repo root so `specfuse.loop` resolves
from source even when the package is not pip-installed in the running interpreter.
"""
import sys as _sys
from pathlib import Path as _Path

_root = _Path(__file__).resolve().parents[2]
if str(_root) not in _sys.path:
    _sys.path.insert(0, str(_root))

from specfuse.loop import gh_features as _m  # noqa: E402

# Mirror the package module's public namespace so importlib-loaded shims and
# `from gh_features import X` back-compat both resolve every symbol.
globals().update({k: v for k, v in vars(_m).items() if not k.startswith("__")})

if __name__ == "__main__":  # pragma: no cover
    _sys.exit(_m.main() if hasattr(_m, "main") else 0)
