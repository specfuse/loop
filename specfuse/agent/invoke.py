# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Shared headless-`claude` invoker (FEAT-2026-0108/T01).

One call site builds the argv, appends `--output-format json`, and parses
the CLI's JSON envelope -- mirroring `specfuse.loop.loop.parse_claude_json_output`'s
field list (`loop.py:3572-3598`) without importing from it, since the driver
module is off limits to this WU. Every headless invoke site
(`agent/diagnose_invoke.py`, `agent/drafting_invoke.py`, `agent/triage_invoke.py`,
`monitor/autofix_invoke.py`) builds its argv through `build_claude_argv`, and
every provider that dispatches a session runs it through `run_claude` and
reports the returned usage as `ActionOutcome.spend` (via `usage_spend`).

A CLI that returns non-JSON output -- an older CLI, or `cost_tracking: false`
-- never raises here: `run_claude` falls back to treating the raw stdout as
the session's text, with `usage=None`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

__all__ = ("InvokeResult", "build_claude_argv", "run_claude", "usage_spend")


@dataclass(frozen=True)
class InvokeResult:
    """One headless session's result text, usage block, and process return
    code. `usage` is `None` whenever the CLI's output could not be read as
    the JSON envelope."""

    text: str
    usage: Optional[dict]
    returncode: int


def build_claude_argv(model: str = "sonnet", effort: str = "medium") -> list:
    """The one place an invoke site's argv starts: `claude -p --model
    <model> --effort <effort>`. `run_claude` appends `--output-format json`
    and the prompt itself at dispatch time, never here -- so a caller that
    only wants the argv (to inspect it, or to build a different dispatch
    shape) never sees those two."""
    return ["claude", "-p", "--model", model, "--effort", effort]


def _parse_envelope(raw: str) -> tuple:
    """Parse Claude CLI's `--output-format=json` envelope. Mirrors
    `specfuse.loop.loop.parse_claude_json_output`'s field list exactly --
    `total_cost_usd` and the four `usage` sub-fields -- without importing
    from the driver module. Any shape drift returns `(raw, None)` so a
    caller falls back to reading `raw` as ordinary text."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw, None
    if not isinstance(data, dict) or "result" not in data:
        # A session asked to answer in JSON (the finding-diagnose and
        # triage-classification prompts both do) can return a JSON object
        # on stdout that is not the CLI's envelope at all -- it has no
        # `result` key, since it never went through a real `claude
        # --output-format json` dispatch in these tests. Treating any
        # parseable dict as the envelope would silently replace that JSON
        # object with `data.get("result", "")`'s empty-string default,
        # corrupting the very output the caller asked for.
        return raw, None
    result_text = data.get("result", "")
    if not isinstance(result_text, str):
        result_text = raw
    usage: dict = {}
    cost = data.get("total_cost_usd")
    if isinstance(cost, (int, float)):
        usage["cost_usd"] = float(cost)
    u = data.get("usage")
    if isinstance(u, dict):
        for key in (
            "input_tokens",
            "output_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
        ):
            if isinstance(u.get(key), int):
                usage[key] = u[key]
    return result_text, (usage if usage else None)


def usage_spend(usage: Optional[dict]) -> int:
    """`spend` for `ActionOutcome`: input + output tokens, cache reads
    excluded -- matching the driver's own cost line (`loop.py:7300-7302`).
    Zero for a `None` usage, never a `KeyError`."""
    if not usage:
        return 0
    return int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))


def run_claude(
    argv: Sequence[str],
    prompt: str,
    *,
    runner: Callable,
    timeout: Optional[float] = None,
) -> InvokeResult:
    """Run one headless `claude` session and return its usage envelope.

    Appends `--output-format json` to *argv*, then the prompt itself, and
    calls *runner* the same way every invoke site already did directly --
    `runner(full_argv, check=False)` -- so an injected runner across the
    codebase needs no new keyword to keep working. *timeout*, when given, is
    forwarded to *runner* as a keyword; omitted entirely otherwise, so
    existing test doubles that accept only `(argv, check=False)` are
    unaffected.
    """
    full_argv = list(argv) + ["--output-format", "json", prompt]
    kwargs = {"check": False}
    if timeout is not None:
        kwargs["timeout"] = timeout
    result = runner(full_argv, **kwargs)
    raw = getattr(result, "stdout", "") or ""
    returncode = getattr(result, "returncode", 0)
    text, usage = _parse_envelope(raw)
    return InvokeResult(text=text, usage=usage, returncode=returncode)
