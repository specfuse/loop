#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Dependency-free slicers for work-unit body sections.

Shared by `loop.py` and `lint_plan.py`, which cannot import each other
(`lint_plan.py` imports `VERDICT_VALUES` from `loop.py`, so the reverse
import would be a cycle). This module imports nothing from either.
"""

from __future__ import annotations

import re

_AC_START_RE = re.compile(
    r"(?mi)^\*\*Acceptance criteria[^\n*]*\*\*\.?|^#{1,6}\s+Acceptance criteria"
)
_AC_END_RE = re.compile(r"(?m)^(?:\*\*|#{1,6}\s)")


def slice_acceptance_criteria(body: str) -> str:
    """Return the text of the Acceptance criteria section only (bold-preamble or ATX)."""
    m = _AC_START_RE.search(body)
    if not m:
        return ""
    nl = body.find("\n", m.end())
    after = body[nl + 1:] if nl != -1 else ""
    em = _AC_END_RE.search(after)
    return after[:em.start()] if em else after


def slice_wu_section(body: str, section_name: str) -> str:
    """Return content between a named section heading and the next heading."""
    start_re = re.compile(rf"(?mi)^(?:#+\s*|\**){re.escape(section_name)}")
    m = start_re.search(body)
    if not m:
        return ""
    nl = body.find("\n", m.end())
    after = body[nl + 1:] if nl != -1 else ""
    em = _AC_END_RE.search(after)
    return after[:em.start()] if em else after
