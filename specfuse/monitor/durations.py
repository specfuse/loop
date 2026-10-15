#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The `<integer><unit>` duration grammar, one home for adapter and linter.

Imports nothing from any provider SDK: `specfuse.loop` (the linter) imports
this module, and the linter must stay SDK-free.
"""

from __future__ import annotations

import re
from typing import Mapping

DURATION_GRAMMAR = "<integer><unit> with unit in s/m/h/d, e.g. '15m'"

_DURATION_RE = re.compile(r"^(\d+)([smhd])$")
_DURATION_MULTIPLIERS: Mapping[str, int] = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def parse_duration_seconds(value: str, field: str = "stall_after") -> int:
    """Parse `<integer><unit>` (unit in s/m/h/d) into seconds.

    Refuses rather than guesses: anything outside the grammar — no unit, an
    unsupported unit, whitespace, a negative sign — raises `ValueError`
    naming the offending value. No coercion, no silent zero.
    """
    match = _DURATION_RE.match(value) if isinstance(value, str) else None
    if not match:
        raise ValueError(
            f"invalid {field} value {value!r} — expected {DURATION_GRAMMAR}"
        )
    magnitude, unit = match.groups()
    return int(magnitude) * _DURATION_MULTIPLIERS[unit]
