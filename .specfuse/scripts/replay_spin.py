#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Shim — re-exports specfuse.loop.replay_spin. Canonical code lives in the package.

This file ships for dogfood (`python3 .specfuse/scripts/replay_spin.py <feature-dir>`).
It path-inserts the repo root so `specfuse.loop` resolves from SOURCE even when the
package is pip-installed in the running interpreter — which is the whole point for
this tool: replaying against an installed build while believing you replayed against
the checkout is its own recorded defect (#2642).
"""
import sys as _sys
from pathlib import Path as _Path

_root = _Path(__file__).resolve().parents[2]
if str(_root) not in _sys.path:
    _sys.path.insert(0, str(_root))

from specfuse.loop import replay_spin as _m  # noqa: E402

main = _m.main
replay = _m.replay
read_recorded_attempts = _m.read_recorded_attempts
read_attempt_note = _m.read_attempt_note
format_report = _m.format_report

if __name__ == "__main__":
    raise SystemExit(main(_sys.argv[1:]))
