# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Caps and the kill switch (FEAT-2026-0049/T03).

Three caps bound a conductor run — `--max-minutes`, `--max-tokens`,
`--max-items` — plus a PAUSE marker file. All four are checked only at item
boundaries (PLAN.md D3): a running item is never interrupted, so a cap can
overshoot and that is accepted, not a bug. `run.py` (T04) is the only caller
that starts an item; it must call `record_item_started()` / `record_tokens()`
after an item completes and consult `may_start_next_item()` /
`pause_requested()` before starting the next one — never mid-item.

Time is injected via a `clock` callable (seconds, monotonic-shaped) rather
than read from `time` directly, so tests control elapsed time without
sleeping.

The PAUSE marker's path, `.specfuse/.agent.pause`, follows the naming
convention T01 established for this same package's own lock file,
`.specfuse/.agent.lock` (`specfuse/loop/_filelock.py`): a hidden
`.agent.<thing>` marker under `.specfuse/`, distinct from the driver's own
`.specfuse/.loop.lock`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

DEFAULT_PAUSE_MARKER = Path(".specfuse/.agent.pause")

# Machine-readable stop reasons. A run must end with exactly one of these —
# never silence, never a reason inferred after the fact from other state.
STOP_DRAINED = "drained"
STOP_CAP = "cap"
STOP_PAUSE = "pause"
STOP_ERROR = "error"


class RunBudget:
    """The three caps plus the PAUSE-marker check, evaluated at item boundaries.

    Absent caps (`None`) are unbounded — a `RunBudget` with all three unset
    never blocks on caps. `max_items=0` is not "unset": it is a real cap of
    zero, so `may_start_next_item()` is `False` from the first call.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float],
        max_minutes: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_items: Optional[int] = None,
        pause_marker: Path = DEFAULT_PAUSE_MARKER,
    ) -> None:
        self.clock = clock
        self.max_minutes = max_minutes
        self.max_tokens = max_tokens
        self.max_items = max_items
        self.pause_marker = Path(pause_marker)

        self._start = clock()
        self._items_started = 0
        self._tokens_spent = 0

    @property
    def elapsed_minutes(self) -> float:
        """Actual elapsed minutes since construction — never the cap itself.

        The run summary reports this value even when a cap fired, so an
        overshoot past `max_minutes` is visible rather than hidden behind
        the configured limit.
        """
        return (self.clock() - self._start) / 60.0

    @property
    def items_started(self) -> int:
        return self._items_started

    @property
    def tokens_spent(self) -> int:
        return self._tokens_spent

    def record_item_started(self) -> None:
        """Call once an item has actually started — never speculatively."""
        self._items_started += 1

    def record_tokens(self, count: int) -> None:
        """Add to the running token total, observed after an item completes."""
        self._tokens_spent += count

    def may_start_next_item(self) -> bool:
        """The single predicate: is another item allowed to start?

        Pure query — evaluating it never disturbs an item already in
        flight, and it says nothing about the PAUSE marker (see
        `pause_requested`); callers check both before starting the next item.
        """
        if self.max_items is not None and self._items_started >= self.max_items:
            return False
        if self.max_tokens is not None and self._tokens_spent >= self.max_tokens:
            return False
        if self.max_minutes is not None and self.elapsed_minutes >= self.max_minutes:
            return False
        return True

    def pause_requested(self) -> bool:
        """Whether the PAUSE marker is present. Checked once per iteration,
        before selecting the next item — never mid-item, same as the caps."""
        return self.pause_marker.is_file()
