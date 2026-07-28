# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Neutral cron-schedule evaluator (FEAT-2026-0040/T07).

Answers one question — "given this expression, under this declared dialect,
in this timezone, what is the most recent time it was expected to fire at or
before this reference instant?" — with no provider type reachable from this
module and no read of the wall clock: the reference instant is always an
argument — this module never reads the wall clock itself — so every computation here is reproducible
at the exact boundary a test wants to pin down (a DST transition, a month
end, the minute after a fire).

The dialect is read from the caller, never inferred from the expression's own
field count: `CRON_DIALECTS`, imported from `specfuse.loop.lint_monitoring`
(T04's schema-side enum), is the single source of truth for which dialects
exist and how many fields each requires. This module adds the one thing that
enum does not carry — field *order* per dialect — and refuses outright, never
guesses, when a given expression's field count disagrees with its declared
dialect's arity.

Supported field syntax, in every field of both arities: `*`, `*/n`, comma
lists, `a-b` ranges, and literal values. Anything else — `L`, `W`, `#`, named
months or weekdays — is out of scope and raises naming the unsupported token,
rather than silently mis-parsing it.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

from specfuse.loop.lint_monitoring import CRON_DIALECTS

__all__ = ("most_recent_firing",)

_FIELD_BOUNDS: Mapping[str, tuple[int, int]] = {
    "second": (0, 59),
    "minute": (0, 59),
    "hour": (0, 23),
    "dom": (1, 31),
    "month": (1, 12),
    "dow": (0, 6),
}

# The field order each dialect's whitespace-separated expression carries.
# `CRON_DIALECTS` (T04's enum) supplies the *arity*; this supplies the
# *order*, which the enum has no reason to carry.
_FIELD_ORDER: Mapping[str, tuple[str, ...]] = {
    "standard-5": ("minute", "hour", "dom", "month", "dow"),
    "seconds-first-6": ("second", "minute", "hour", "dom", "month", "dow"),
}

# Generous bound on how many days to search backward for a matching
# month/day-of-month/day-of-week combination before concluding the
# expression can never fire (e.g. a Feb-29-only schedule needs up to a few
# years). Ordinary schedules match within the first day or two.
_MAX_DAY_LOOKBACK = 8 * 366


def _parse_field(
    token: str, field_name: str, expression: str, low: int, high: int
) -> tuple[frozenset, bool]:
    """Parse one whitespace-delimited cron field into its allowed values.

    Returns ``(allowed_values, is_wildcard)`` — the wildcard flag matters
    only for `dom`/`dow`, where cron's day-of-month/day-of-week combination
    rule (AND when either is unrestricted, OR when both are restricted)
    needs to know whether a field was actually `*` rather than a range that
    happens to span the full domain.
    """
    is_wildcard = token.strip() == "*"
    values: set[int] = set()
    for part in token.split(","):
        part = part.strip()
        if part == "*":
            values.update(range(low, high + 1))
            continue
        if part.startswith("*/"):
            step_str = part[2:]
            if not step_str.isdigit() or int(step_str) <= 0:
                raise ValueError(
                    f"unsupported cron token {part!r} in field {field_name!r} "
                    f"of expression {expression!r}"
                )
            values.update(range(low, high + 1, int(step_str)))
            continue
        if "-" in part:
            lo_s, _, hi_s = part.partition("-")
            if not (lo_s.isdigit() and hi_s.isdigit()):
                raise ValueError(
                    f"unsupported cron token {part!r} in field {field_name!r} "
                    f"of expression {expression!r}"
                )
            lo, hi = int(lo_s), int(hi_s)
            if lo > hi or lo < low or hi > high:
                raise ValueError(
                    f"cron range {part!r} out of bounds for field "
                    f"{field_name!r} ({low}-{high}) in expression "
                    f"{expression!r}"
                )
            values.update(range(lo, hi + 1))
            continue
        if part.isdigit():
            value = int(part)
            if not (low <= value <= high):
                raise ValueError(
                    f"cron value {part!r} out of bounds for field "
                    f"{field_name!r} ({low}-{high}) in expression "
                    f"{expression!r}"
                )
            values.add(value)
            continue
        raise ValueError(
            f"unsupported cron token {part!r} in field {field_name!r} of "
            f"expression {expression!r}"
        )
    return frozenset(values), is_wildcard


def _date_matches(
    day: date,
    month_values: frozenset,
    dom_values: frozenset,
    dom_wildcard: bool,
    dow_values: frozenset,
    dow_wildcard: bool,
) -> bool:
    if day.month not in month_values:
        return False
    dom_ok = day.day in dom_values
    dow_ok = (day.isoweekday() % 7) in dow_values  # cron: Sunday=0 .. Saturday=6
    if dom_wildcard and dow_wildcard:
        return True
    if dom_wildcard:
        return dow_ok
    if dow_wildcard:
        return dom_ok
    return dom_ok or dow_ok


def _search_time_fields(
    fields: Sequence[Sequence[int]],
    thresholds: Sequence[int],
    index: int,
    bounded: bool,
) -> Optional[tuple[int, ...]]:
    """Find the largest tuple of (hour[, minute[, second]]) at or before
    *thresholds*, each component drawn from the matching entry in *fields*
    (each pre-sorted ascending). Returns ``None`` if no combination fits."""
    if index == len(fields):
        return ()
    values = fields[index]
    if not bounded:
        if not values:
            return None
        rest = _search_time_fields(fields, thresholds, index + 1, False)
        if rest is None:
            return None
        return (values[-1],) + rest
    threshold = thresholds[index]
    for value in reversed(values):
        if value > threshold:
            continue
        rest = _search_time_fields(
            fields, thresholds, index + 1, value == threshold
        )
        if rest is not None:
            return (value,) + rest
    return None


def most_recent_firing(
    expression: str,
    dialect: str,
    timezone: str,
    reference: datetime,
) -> datetime:
    """Return the most recent time *expression* (under *dialect*, in
    *timezone*) was expected to fire at or before *reference*.

    Raises ``ValueError`` if *dialect* is not one of T04's declared cron
    dialects, if *expression*'s field count disagrees with that dialect's
    declared arity, if any field uses syntax outside the supported subset,
    or if no firing time could be found within an 8-year lookback (the
    expression is effectively unsatisfiable, e.g. Feb 30).
    """
    if dialect not in CRON_DIALECTS:
        raise ValueError(
            f"unknown cron dialect {dialect!r} — must be one of "
            f"{sorted(CRON_DIALECTS)}"
        )
    if reference.tzinfo is None:
        raise ValueError("reference must be a timezone-aware datetime")

    raw_fields = expression.split()
    expected_arity = CRON_DIALECTS[dialect]
    if len(raw_fields) != expected_arity:
        raise ValueError(
            f"cron expression {expression!r} has {len(raw_fields)} field(s) "
            f"but declared dialect {dialect!r} requires {expected_arity}"
        )

    field_order = _FIELD_ORDER[dialect]
    parsed = {
        name: _parse_field(value, name, expression, *_FIELD_BOUNDS[name])
        for name, value in zip(field_order, raw_fields, strict=True)
    }

    zone = ZoneInfo(timezone)
    reference_local = reference.astimezone(zone)

    month_values, _ = parsed["month"]
    dom_values, dom_wildcard = parsed["dom"]
    dow_values, dow_wildcard = parsed["dow"]
    hour_values, _ = parsed["hour"]
    minute_values, _ = parsed["minute"]
    has_seconds = "second" in parsed

    time_fields = [sorted(hour_values), sorted(minute_values)]
    if has_seconds:
        second_values, _ = parsed["second"]
        time_fields.append(sorted(second_values))

    candidate_date = reference_local.date()
    first_day = True
    for _ in range(_MAX_DAY_LOOKBACK):
        if _date_matches(
            candidate_date,
            month_values,
            dom_values,
            dom_wildcard,
            dow_values,
            dow_wildcard,
        ):
            if first_day:
                threshold = (
                    reference_local.hour,
                    reference_local.minute,
                    reference_local.second,
                )
            else:
                threshold = (23, 59, 59)
            thresholds = threshold[: len(time_fields)]
            found = _search_time_fields(time_fields, thresholds, 0, True)
            if found is not None:
                hour, minute, *rest = found
                second = rest[0] if has_seconds else 0
                return datetime(
                    candidate_date.year,
                    candidate_date.month,
                    candidate_date.day,
                    hour,
                    minute,
                    second,
                    tzinfo=zone,
                )
        first_day = False
        candidate_date = candidate_date - timedelta(days=1)

    raise ValueError(
        f"no expected firing time found for {expression!r} within "
        f"{_MAX_DAY_LOOKBACK} days before {reference.isoformat()} — the "
        f"expression may be unsatisfiable"
    )
