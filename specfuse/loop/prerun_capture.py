#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Bound T01's captured oracle output and format it for the session prompt.

`run_pre_dispatch` (`specfuse/loop/prerun.py`) returns `oracle_results` — a
list of `{"name", "ok", "report"}` dicts, one per declared oracle, each
carrying that oracle's full captured output. A real oracle (a scenario
matrix, a full generator suite) can emit far more than a session prompt
should be handed, so this module bounds it: `format_oracle_capture` returns a
prompt section whose total size never exceeds `ORACLE_CAPTURE_BUDGET_BYTES`.

The naive way to enforce a byte budget is a positional tail, and that is
precisely the defect FEAT-2026-0068 fixed for gate failure reports:
`select_gate_report_lines` (`loop.py:2715`) pins verdict lines ahead of a
positional tail rather than dropping whatever a raw byte-cap slice happens to
land on. This module calls that selector rather than writing a second
truncation policy.
"""

from __future__ import annotations

from specfuse.loop.loop import select_gate_report_lines

# `truncate_failure_note` (`loop.py:2169`) already injects captured/failure
# text into a work-unit-facing prompt in this codebase, at `max_chars=8000`.
# Reused here rather than picking a fresh number for the same kind of
# injection — this is the established budget for this class of content in
# this repo, not a guess.
ORACLE_CAPTURE_BUDGET_BYTES = 8000

_SECTION_HEADER = "## Captured oracle output (pre-dispatch)\n\n"
_BLOCK_SEP = "\n\n"


def _fit_to_budget(report: str, budget: int) -> tuple[str, int]:
    """Return (fitted_text, dropped_byte_count) for *report* within *budget*.

    Uses `select_gate_report_lines` to choose which lines survive so a
    verdict line pinned ahead of the tail is kept; if the selected lines still
    exceed *budget*, lines are kept front-to-back (preserving pinned verdict
    lines, which `select_gate_report_lines` places first) until the budget is
    spent.
    """
    raw_bytes = report.encode("utf-8")
    if len(raw_bytes) <= budget:
        return report, 0

    lines = select_gate_report_lines(report, window=15)
    fitted = "\n".join(lines)
    fitted_bytes = fitted.encode("utf-8")
    if len(fitted_bytes) <= budget:
        return fitted, len(raw_bytes) - len(fitted_bytes)

    kept_lines = []
    used = 0
    for line in lines:
        line_bytes = len(line.encode("utf-8")) + 1  # +1 for the joining newline
        if used + line_bytes > budget:
            break
        kept_lines.append(line)
        used += line_bytes
    trimmed = "\n".join(kept_lines)
    return trimmed, len(raw_bytes) - len(trimmed.encode("utf-8"))


def format_oracle_capture(results: "list[dict] | None") -> str:
    """Format T01's `oracle_results` into a budget-bounded session-prompt section.

    Returns "" when *results* is empty or None — a work unit with no
    `oracles` declared gets no section and no marker. Otherwise returns a
    section whose total size in bytes is <= `ORACLE_CAPTURE_BUDGET_BYTES`,
    with the budget split evenly across oracles. Any oracle whose report is
    truncated to fit its share gets an explicit marker naming the number of
    bytes dropped — truncation is never silent.
    """
    if not results:
        return ""

    n = len(results)
    header_overhead = len(_SECTION_HEADER.encode("utf-8"))
    sep_overhead = max(n - 1, 0) * len(_BLOCK_SEP.encode("utf-8"))
    available = max(ORACLE_CAPTURE_BUDGET_BYTES - header_overhead - sep_overhead, 0)
    share = available // n

    blocks = []
    for result in results:
        name = result.get("name", "<unknown>")
        verdict = "OK" if result.get("ok") else "FAIL"
        block_header = f"### oracle: {name} ({verdict})\n"
        block_budget = max(share - len(block_header.encode("utf-8")), 0)
        report = result.get("report", "") or ""
        fitted, dropped = _fit_to_budget(report, block_budget)
        block = block_header + fitted
        if dropped > 0:
            block += f"\n... [{dropped} byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES] ...\n"
        blocks.append(block)

    return _SECTION_HEADER + _BLOCK_SEP.join(blocks)
