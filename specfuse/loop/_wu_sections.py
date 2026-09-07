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

_ANY_HEADING_RE = re.compile(r"(?m)^(?:\*\*|#{1,6}\s)")


def slice_wu_section(body: str, section_name: str) -> str:
    """Return content between a named section heading and the next heading
    of the same or shallower level.

    Handles both section-heading shapes a WU body uses: the canonical
    bold-preamble form (`**Section name.** content starting on the same
    line`, what `.specfuse/templates/WU.template.md` prescribes and what
    327/327 real WU bodies in this repo use) and the ATX form (`## Section
    name`, content starting on the next line). For the bold form, content
    immediately following the closing `**` — on the label line itself — is
    part of the section; discarding it (as a next-line-only slice would)
    silently drops whatever a WU author wrote inline after the label.

    A `###` (or deeper) subheading nested inside the opened section is part
    of that section's content, not the end of it — only a heading at the
    opened section's own ATX level or shallower, or a bold-preamble heading,
    closes it. Bold-preamble sections have no nesting concept of their own,
    so they keep ending at the next heading of any kind.
    """
    escaped = re.escape(section_name)
    heading_re = re.compile(
        rf"(?mi)^#{{1,6}}\s*{escaped}\b|^\*\*{escaped}[^\n*]*\*\*\.?"
    )
    m = heading_re.search(body)
    if not m:
        return ""
    if m.group(0).startswith("#"):
        level = len(m.group(0)) - len(m.group(0).lstrip("#"))
        end_re = re.compile(rf"(?m)^(?:\*\*|#{{1,{level}}}\s)")
        nl = body.find("\n", m.end())
        after = body[nl + 1:] if nl != -1 else ""
    else:
        end_re = _ANY_HEADING_RE
        after = body[m.end():]
    em = end_re.search(after)
    return after[:em.start()] if em else after


def slice_acceptance_criteria(body: str) -> str:
    """Return the text of the Acceptance criteria section only (bold-preamble or ATX)."""
    return slice_wu_section(body, "Acceptance criteria")
