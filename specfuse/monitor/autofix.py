# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The autofix predicate (FEAT-2026-0042/T01): should a diagnosed finding be
handed to an automated fix?

This module decides. It does not invoke `fix-bug`, create a branch, open a
pull request, call `gh`, or touch the network — gate 1 ships a decision
layer that cannot act; that is the gate's whole safety property. It also
reads no config file: the caller passes an already-parsed monitoring config
and the component name, and `CONFIDENCE_THRESHOLD` below is a hardcoded
module constant, not a config value — a safety threshold that lives in a
config file can be tuned into uselessness by the person it is meant to stop
(FEAT-2026-0053's precedent for arm-predicate stop classes).

Decision vocabulary — a closed set of three, not a boolean, because the
caller must be able to tell *declined* from *routed to a human* and the
reason must survive into the label and issue comment gate 2 writes:

    FIRE            -- hand the finding to an automated fix run.
    ROUTE_TO_HUMAN  -- out of an automated run's competence or confidence;
                       needs a human, but is not a failure.
    DECLINE         -- automation stays off: dial is off, this fingerprint
                       already ran, the daily cap is reached, or the input
                       could not be evaluated at all.

Reason vocabulary names which rule fired (`REASON_*` below), so a decision
is always traceable to the rule that produced it.

Fail closed: any input this predicate cannot evaluate -- a diagnosis body
that will not parse, a component absent from the config, a malformed dial
value, a state reader that raises -- returns DECLINE, never FIRE. A
predicate that guesses "probably fine" on unreadable input is worse than no
predicate, because it reads as a guardrail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from specfuse.monitor.diagnosis import Diagnosis, DiagnosisParseError, parse

FIRE = "fire"
ROUTE_TO_HUMAN = "route_to_human"
DECLINE = "decline"

DECISIONS = (FIRE, ROUTE_TO_HUMAN, DECLINE)

# Deliberately hardcoded, not read from monitoring.yml. See module docstring.
CONFIDENCE_THRESHOLD = 0.8

REASON_DIAL_OFF = "dial_off"
REASON_FIX_SCOPE_OUT_OF_COMPETENCE = "fix_scope_out_of_competence"
REASON_LOW_CONFIDENCE = "confidence_below_threshold"
REASON_ALREADY_ATTEMPTED = "fingerprint_already_attempted"
REASON_DAILY_CAP_REACHED = "daily_cap_reached"
REASON_ELIGIBLE = "eligible"
REASON_UNREADABLE_INPUT = "unreadable_input"

_ROUTE_SCOPES = ("large", "external")


class RateLimitStateReader(Protocol):
    """Read-only view over autofix rate-limit state (T02 owns where it
    lives). Injected so this module stays testable with no GitHub and no
    network."""

    def has_prior_attempt(self, fingerprint: str) -> bool: ...

    def daily_cap_reached(self) -> bool: ...


@dataclass(frozen=True)
class AutofixDecision:
    """The predicate's output: a decision plus the rule that produced it."""

    decision: str
    reason: str


def _decline(reason: str) -> AutofixDecision:
    return AutofixDecision(decision=DECLINE, reason=reason)


def decide(
    *,
    diagnosis_body: str,
    monitoring_config: Mapping[str, Any],
    component: str,
    fingerprint: str,
    state_reader: RateLimitStateReader,
) -> AutofixDecision:
    """Decide whether a diagnosed finding should fire an automated fix.

    `diagnosis_body` is a rendered diagnosis comment body (see
    `specfuse.monitor.diagnosis`); `monitoring_config` is an already-parsed
    mapping of component name to that component's config (this module reads
    no file); `state_reader` answers the rate-limit questions T02 owns the
    storage for. Any failure to evaluate an input returns DECLINE.
    """
    try:
        diagnosis = parse(diagnosis_body)
    except DiagnosisParseError:
        return _decline(REASON_UNREADABLE_INPUT)
    if diagnosis is None:
        return _decline(REASON_UNREADABLE_INPUT)

    dial = _read_dial(monitoring_config, component)
    if dial is None:
        return _decline(REASON_UNREADABLE_INPUT)

    return _decide_for_diagnosis(diagnosis, dial, fingerprint, state_reader)


def _read_dial(monitoring_config: Mapping[str, Any], component: str) -> str | None:
    try:
        component_config = monitoring_config[component]
        dial = component_config["autofix"]
    except (KeyError, TypeError):
        return None
    if dial not in ("on", "off"):
        return None
    return dial


def _decide_for_diagnosis(
    diagnosis: Diagnosis,
    dial: str,
    fingerprint: str,
    state_reader: RateLimitStateReader,
) -> AutofixDecision:
    if dial != "on":
        return _decline(REASON_DIAL_OFF)

    if diagnosis.fix_scope in _ROUTE_SCOPES:
        return AutofixDecision(
            decision=ROUTE_TO_HUMAN, reason=REASON_FIX_SCOPE_OUT_OF_COMPETENCE
        )

    if diagnosis.confidence < CONFIDENCE_THRESHOLD:
        return AutofixDecision(decision=ROUTE_TO_HUMAN, reason=REASON_LOW_CONFIDENCE)

    # An injected reader's failure mode is unknown to this module; any raise
    # is unreadable state, per the fail-closed contract (module docstring).
    try:
        already_attempted = state_reader.has_prior_attempt(fingerprint)
    except Exception:  # noqa: BLE001
        return _decline(REASON_UNREADABLE_INPUT)
    if already_attempted:
        return _decline(REASON_ALREADY_ATTEMPTED)

    try:
        cap_reached = state_reader.daily_cap_reached()
    except Exception:  # noqa: BLE001
        return _decline(REASON_UNREADABLE_INPUT)
    if cap_reached:
        return _decline(REASON_DAILY_CAP_REACHED)

    return AutofixDecision(decision=FIRE, reason=REASON_ELIGIBLE)
