#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Review an existing `.specfuse/agent-policy.yml` against its shipped baseline
(FEAT-2026-0076/T04).

Gate 1 bootstrapped a policy file from nothing; gate 2 reviews one that
already exists. `GATE-02-REVIEW.md` `The provenance question` decides how:
compare the file's current value against the *shipped baseline* --
`agent_policy.DEFAULT_*` where a constant exists, and
`.specfuse/agent-policy.yml.example`'s literal value where one does not -- and
record which source answered each key. The comparison is explicitly a hint,
not a claim: an operator who deliberately chose a value equal to the baseline
is indistinguishable from one who never chose, and `matches_baseline` entries
carry a caveat saying so in the returned data rather than leaving that
disclaimer to prose a downstream reader might not read.

Composes `policy_proposals.propose_policy_defaults` (FEAT-2026-0076/T01) for
the evidence-backed proposal half of each entry; does not reimplement it and
does not extend `agent_policy`'s schema (`PLAN.md` "Scope boundary"). `queue`
is out of scope entirely and is never read or returned. Returns a per-key
readout only -- never a whole-file document -- so clobbering the live file is
structurally impossible here, not merely discouraged in prose.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from . import _miniyaml, agent_policy
from .policy_proposals import propose_policy_defaults

__all__ = ("review_agent_policy",)

_CAVEAT = (
    "This value matches the shipped baseline, which means it may never have "
    "been deliberately chosen -- or an operator chose it and it happens to "
    "equal the baseline. The two are indistinguishable from this comparison "
    "alone."
)

# Dotted in-scope key -> (path into the parsed policy mapping, baseline
# source). "constant" baselines read agent_policy.DEFAULT_TEST_PATHS directly
# and never need the example file; "example" baselines are read from
# `.specfuse/agent-policy.yml.example` at the same dotted path.
_IN_SCOPE_KEYS = (
    ("budgets.max_tokens_per_run", ("budgets", "max_tokens_per_run"), "example", "converted"),
    ("budgets.max_items_per_day", ("budgets", "max_items_per_day"), "example", "converted"),
    ("budgets.max_open_prs", ("budgets", "max_open_prs"), "example", "converted"),
    ("rules.bugs.test_paths", ("rules", "bugs", "test_paths"), "constant", "measured"),
)

# Dotted in-scope key -> key propose_policy_defaults uses for it. That
# function's keys are unprefixed (it proposes one flat namespace across
# budgets and rules.bugs); this module's keys are dotted for readability.
_PROPOSAL_KEYS = {
    "budgets.max_tokens_per_run": "max_tokens_per_run",
    "budgets.max_items_per_day": "max_items_per_day",
    "budgets.max_open_prs": "max_open_prs",
    "rules.bugs.test_paths": "test_paths",
}

_EXAMPLE_PATH = Path(".specfuse") / "agent-policy.yml.example"
_POLICY_PATH = Path(".specfuse") / "agent-policy.yml"


def review_agent_policy(repo_root: "str | Path | None" = None, *, runner: Optional[Callable] = None) -> dict:
    """Review *repo_root*'s `.specfuse/agent-policy.yml` against the shipped
    baseline for the four in-scope keys.

    Returns `{dotted_key: entry}`. Each entry carries `current` (the value
    read from the live file, or absence), `proposal` (what
    `propose_policy_defaults` returns for it, or absence, plus `kind`:
    `measured` or `converted`), `baseline` (the shipped value and which
    source answered it, or unavailable), and `classification`: one of
    `matches_baseline`, `differs_from_baseline`, `absent_from_file`, or
    `baseline_unavailable`. A `matches_baseline` entry always carries a
    caveat string; no other classification does.
    """
    root = (Path(repo_root) if repo_root is not None else Path.cwd()).resolve()

    current_policy = _load_current_policy(root)
    example_policy, example_ok = _load_example_policy(root)
    proposals = propose_policy_defaults(root, runner=runner)

    readout: dict = {}
    for dotted_key, path, baseline_source, kind in _IN_SCOPE_KEYS:
        readout[dotted_key] = _build_entry(
            dotted_key, path, baseline_source, kind,
            current_policy, example_policy, example_ok, proposals,
        )
    return readout


def _build_entry(
    dotted_key: str,
    path: tuple,
    baseline_source: str,
    kind: str,
    current_policy: Optional[dict],
    example_policy: Optional[dict],
    example_ok: bool,
    proposals: dict,
) -> dict:
    current = _lookup(current_policy, path)
    baseline = _baseline_for(path, baseline_source, example_policy, example_ok)

    proposal_key = _PROPOSAL_KEYS[dotted_key]
    proposal_entry = proposals.get(proposal_key)
    if proposal_entry is None:
        proposal = {"available": False}
    else:
        proposal = {
            "available": True,
            "value": proposal_entry["value"],
            "evidence": proposal_entry["evidence"],
            "kind": kind,
        }

    classification = _classify(current, baseline)
    caveat = _CAVEAT if classification == "matches_baseline" else None

    return {
        "current": current,
        "proposal": proposal,
        "baseline": baseline,
        "classification": classification,
        "caveat": caveat,
    }


def _classify(current: dict, baseline: dict) -> str:
    if not baseline["available"]:
        return "baseline_unavailable"
    if not current["present"]:
        return "absent_from_file"
    if current["value"] == baseline["value"]:
        return "matches_baseline"
    return "differs_from_baseline"


def _lookup(policy: Optional[dict], path: tuple) -> dict:
    node = policy
    for segment in path:
        if not isinstance(node, dict) or segment not in node:
            return {"present": False, "value": None}
        node = node[segment]
    return {"present": True, "value": node}


def _baseline_for(
    path: tuple, source: str, example_policy: Optional[dict], example_ok: bool
) -> dict:
    if source == "constant":
        return {
            "available": True,
            "value": list(agent_policy.DEFAULT_TEST_PATHS),
            "source": "agent_policy.DEFAULT_TEST_PATHS",
        }

    if not example_ok:
        return {"available": False, "source": "agent-policy.yml.example"}

    found = _lookup(example_policy, path)
    if not found["present"]:
        return {"available": False, "source": "agent-policy.yml.example"}
    return {
        "available": True,
        "value": found["value"],
        "source": "agent-policy.yml.example",
    }


def _load_current_policy(root: Path) -> Optional[dict]:
    policy_path = root / _POLICY_PATH
    try:
        return agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return None
    except _miniyaml.MiniYAMLError:
        return None


def _load_example_policy(root: Path) -> "tuple[Optional[dict], bool]":
    example_path = root / _EXAMPLE_PATH
    if not example_path.is_file():
        return None, False
    try:
        parsed = _miniyaml.parse(example_path.read_text())
    except _miniyaml.MiniYAMLError:
        return None, False
    if not isinstance(parsed, dict):
        return None, False
    return parsed, True
