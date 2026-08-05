#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Pre-dispatch runner for a work unit's `prep` and `oracles` frontmatter sets.

Everything that runs a declared command in this repo runs at work-unit *exit*
(`verify()`, `loop.py:2855`, "the exit oracle"). Captured output therefore
reaches an agent only as failure feedback on a retry, and a fail-fast
environment-prep step has no representation at all. This module adds the
pre-dispatch half: `run_pre_dispatch` resolves a WU's `prep` and `oracles`
names against a `verification.yml`-shaped cfg dict and runs them **before**
the session is dispatched — `prep` fail-fast, `oracles` capture-all.

It calls `_run_gate_set` (`loop.py:2753`) rather than reimplementing gate
execution, and mirrors `verify()`'s CONFIGURATION ERROR shape for an unknown
set name (`loop.py:2875-2891`) rather than inventing a second error
vocabulary. `verify()`, `_run_gate_set`, and `extra_gates` handling are out of
scope for this module — it only calls them.
"""

from __future__ import annotations

from pathlib import Path

from specfuse.loop.loop import _run_gate_set

# Halt class carried by a pre-dispatch outcome when a `prep` entry fails, or
# when a `prep`/`oracles` name cannot be resolved against cfg. Distinct from
# any exit-time verification failure class — a prep failure is a setup
# problem, not a verdict on the WU's work.
PREP_HALT_CLASS = "prep_halt"


def _wu_id(wu) -> str:
    return getattr(wu, "wu_id", None) or "<unknown>"


def resolve_prerun_sets(wu, cfg: dict):
    """Resolve wu.prep / wu.oracles set names against cfg.

    Returns (prep_gates, oracle_gates, error_message). On success
    error_message is None and prep_gates/oracle_gates are flattened,
    dedup-by-name gate lists (each entry a {"name", "command"} dict), one list
    per declared name in declared order. On a name absent from cfg,
    prep_gates and oracle_gates are both None and error_message is a named
    CONFIGURATION ERROR naming the missing set and the work unit — never a
    silent pass. A field with no declared names resolves to an empty list.
    """
    prep_names = list(getattr(wu, "prep", None) or [])
    oracle_names = list(getattr(wu, "oracles", None) or [])

    def _resolve(names, field_name):
        gates = []
        seen = set()
        for name in names:
            named_set = cfg.get(name)
            if not named_set:
                return None, (
                    f"CONFIGURATION ERROR: work unit {_wu_id(wu)} declares "
                    f"`{field_name}: [{name}]` but no '{name}' gates are "
                    f"configured in .specfuse/verification.yml. This is not "
                    f"a work-unit failure — fix verification.yml (or the "
                    f"WU's {field_name}) and re-run."
                )
            for gate in named_set:
                if gate["name"] in seen:
                    continue
                seen.add(gate["name"])
                gates.append(gate)
        return gates, None

    prep_gates, err = _resolve(prep_names, "prep")
    if err:
        return None, None, err
    oracle_gates, err = _resolve(oracle_names, "oracles")
    if err:
        return None, None, err
    return prep_gates, oracle_gates, None


def run_pre_dispatch(wu, feature_dir: Path, cfg: dict) -> dict:
    """Run wu's `prep` set fail-fast, then its `oracles` set capture-all.

    Returns a dict outcome:
      {"halted": bool, "halt_class": str | None, "message": str | None,
       "prep_results": list[dict], "oracle_results": list[dict]}
    Each result dict is the {"name", "ok", "report"} shape `_run_gate_set`
    produces.

    A work unit declaring neither `prep` nor `oracles` returns the empty
    outcome ({"halted": False, ..., "prep_results": [], "oracle_results":
    []}) without invoking `_run_gate_set` at all — no pre-dispatch work, no
    behavior change.

    `prep` entries run in declared order and stop at the first non-zero
    exit: a later prep entry never runs once an earlier one has failed. The
    halted outcome carries `PREP_HALT_CLASS`. A `prep`/`oracles` name absent
    from cfg halts the same way, before any command runs.

    On prep success, every `oracles` entry runs regardless of any individual
    failure — captured output for all of them is returned so a session can
    read it as input, not just failure feedback.
    """
    if not getattr(wu, "prep", None) and not getattr(wu, "oracles", None):
        return {
            "halted": False, "halt_class": None, "message": None,
            "prep_results": [], "oracle_results": [],
        }

    prep_gates, oracle_gates, err = resolve_prerun_sets(wu, cfg)
    if err:
        return {
            "halted": True, "halt_class": PREP_HALT_CLASS, "message": err,
            "prep_results": [], "oracle_results": [],
        }

    prep_results = []
    for gate in prep_gates:
        result = _run_gate_set([gate], feature_dir)[0]
        prep_results.append(result)
        if not result["ok"]:
            return {
                "halted": True, "halt_class": PREP_HALT_CLASS,
                "message": (
                    f"PREP HALT: '{result['name']}' failed for "
                    f"{_wu_id(wu)} — halting before dispatch."
                ),
                "prep_results": prep_results, "oracle_results": [],
            }

    oracle_results = _run_gate_set(oracle_gates, feature_dir) if oracle_gates else []
    return {
        "halted": False, "halt_class": None, "message": None,
        "prep_results": prep_results, "oracle_results": oracle_results,
    }
