#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Propose `agent-policy.yml` values from repository evidence (FEAT-2026-0076/T01).

`.specfuse/agent-policy.yml` shipped full of values an agent chose and never
explained. `propose_policy_defaults` proposes only what a repository's own
history and structure can answer, and every proposal carries the evidence it
came from -- a number with no evidence is the same opaque default again.

Proposing nothing is a first-class outcome: a repository with no
`events.jsonl` gets no budget proposal, not a plausible-looking guess dressed
as one. See PLAN.md "The oracle problem" and `[FEAT-2026-0039]`, the prior
failure this posture exists to avoid.

Consumes `events_stats.collect`, `gate_commands.iter_code_gates`, and
`agent_policy`'s constants/validator -- it does not re-implement any of them
and does not extend the schema (PLAN.md "Scope boundary"). `queue:` is out of
scope entirely; `/groom-backlog` owns it.

No network call happens except through an injected `runner` (same convention
as `triage.py` / `bug_lane_state.py`: `runner(args, check=...)` returning an
object with `.returncode` / `.stdout`), and no file outside `repo_root` is
ever opened -- `events_stats.collect` walks arbitrary sibling repositories
under a workspace root by design, so this module hands it a throwaway
directory holding a single symlink into `repo_root` rather than `repo_root`'s
real parent, which this process does not control and may hold unrelated
repositories.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Callable, Optional

from . import events_stats, gate_commands

__all__ = ("propose_policy_defaults",)

# events_stats.collect() aggregates `payload.cost_usd`, not raw token counts --
# `attempt_outcome`'s `input_tokens` / `output_tokens` fields are written by
# loop.py but are not among the fields collect() extracts. Converting the
# spend it does expose into a token-shaped budget therefore requires a
# disclosed conversion assumption; a blended per-token rate that is generous
# enough not to under-budget a token-heavy run.
_ASSUMED_TOKENS_PER_USD = 200_000
_TOKEN_BUDGET_HEADROOM = 1.5

_ITEMS_PER_DAY_HEADROOM = 0.1

_TEST_DIR_CANDIDATES = ("tests", "spec")


def propose_policy_defaults(
    repo_root: "str | Path | None" = None, *, runner: Optional[Callable] = None
) -> dict:
    """Propose derivable `agent-policy.yml` values, each as `{value, evidence}`.

    Only `budgets.max_tokens_per_run`, `budgets.max_items_per_day`,
    `budgets.max_open_prs`, and `rules.bugs.test_paths` are in scope -- see
    the WU. A key is absent from the result entirely when the repository
    carries no evidence to answer it; this function never fills a gap with
    the shipped default dressed as a proposal.
    """
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    proposals: dict = {}

    stats = _collect_local_events(root)
    if stats is not None and stats["totals"]["work_units"] > 0:
        tokens = _propose_max_tokens_per_run(stats)
        if tokens is not None:
            proposals["max_tokens_per_run"] = tokens
        items = _propose_max_items_per_day(stats)
        if items is not None:
            proposals["max_items_per_day"] = items

    test_paths = _propose_test_paths(root)
    if test_paths is not None:
        proposals["test_paths"] = test_paths

    open_prs = _propose_max_open_prs(runner)
    if open_prs is not None:
        proposals["max_open_prs"] = open_prs

    return proposals


def _collect_local_events(repo_root: Path) -> Optional[dict]:
    """Run `events_stats.collect` scoped to *repo_root* alone.

    `collect` globs `<root>/*/.specfuse/features/*/events.jsonl` -- it is
    built to walk a workspace of several repositories. Pointing it at
    `repo_root.parent` would hand it siblings this process has no business
    reading. Instead this hands it a fresh, empty directory holding one
    symlink named after `repo_root`, so the glob's `*` resolves to exactly
    one repository: this one.
    """
    features_dir = repo_root / ".specfuse" / "features"
    if not features_dir.is_dir():
        return None

    with tempfile.TemporaryDirectory() as scratch:
        link = Path(scratch) / (repo_root.name or "repo")
        try:
            link.symlink_to(repo_root, target_is_directory=True)
        except OSError:
            return None
        stats = events_stats.collect([Path(scratch)])

    if stats["totals"]["work_units"] == 0:
        return None
    return stats


def _propose_max_tokens_per_run(stats: dict) -> Optional[dict]:
    bucket = stats.get("by_type", {}).get("implementation")
    if not bucket or not bucket.get("passing_costs"):
        return None

    p90_cost = bucket["p90"]
    n = len(bucket["passing_costs"])
    tokens = round(p90_cost * _ASSUMED_TOKENS_PER_USD * _TOKEN_BUDGET_HEADROOM)
    tokens = max(tokens, 1)
    return {
        "value": tokens,
        "evidence": (
            f"events_stats.collect over {_repr_wu_count(n)} passing "
            f"implementation attempts reports a p90 cost of ${p90_cost:.2f}; "
            "events.jsonl carries no raw token count through collect(), so "
            f"this converts cost at an assumed {_ASSUMED_TOKENS_PER_USD:,} "
            f"tokens/$ blended rate with {_TOKEN_BUDGET_HEADROOM}x headroom "
            f"-> {tokens:,} tokens"
        ),
    }


def _repr_wu_count(n: int) -> str:
    return f"{n} run" if n == 1 else f"{n} runs"


def _propose_max_items_per_day(stats: dict) -> Optional[dict]:
    total = stats["totals"]["work_units"]
    if total <= 0:
        return None
    value = max(1, round(total * _ITEMS_PER_DAY_HEADROOM))
    return {
        "value": value,
        "evidence": (
            f"events_stats.collect reports {total} completed work units across "
            f"{stats['totals']['repos']} repositor{'y' if stats['totals']['repos'] == 1 else 'ies'} "
            "in this history; events.jsonl carries no per-day date breakdown "
            f"through collect(), so this proposes {int(_ITEMS_PER_DAY_HEADROOM * 100)}% "
            f"of that total volume as a daily cap -> {value}"
        ),
    }


def _propose_test_paths(repo_root: Path) -> Optional[dict]:
    tree = _tree_test_paths(repo_root)
    gate = _gate_command_test_paths(repo_root)
    if not tree and not gate:
        return None

    union = sorted(tree | gate)
    if tree == gate:
        note = f"directory tree and verification.yml's code gate commands agree: {union}"
    elif not gate:
        note = f"directory tree only ({sorted(tree)}); no matching evidence in verification.yml's gate commands"
    elif not tree:
        note = f"verification.yml's gate commands only ({sorted(gate)}); directory not found in the tree"
    else:
        note = (
            f"directory tree ({sorted(tree)}) and verification.yml's gate commands "
            f"({sorted(gate)}) disagree; proposing the union"
        )

    return {"value": union, "evidence": f"rules.bugs.test_paths from {note}"}


def _tree_test_paths(repo_root: Path) -> set:
    found = set()
    for name in _TEST_DIR_CANDIDATES:
        if (repo_root / name).is_dir():
            found.add(f"{name}/")
    return found


def _path_mentions(command: str, name: str) -> bool:
    return re.search(rf"(?<![\w.-]){re.escape(name)}(?:/|\b)", command) is not None


def _gate_command_test_paths(repo_root: Path) -> set:
    verification_yml = repo_root / ".specfuse" / "verification.yml"
    if not verification_yml.is_file():
        return set()
    try:
        gates = gate_commands.iter_code_gates(verification_yml)
    except OSError:
        return set()

    found = set()
    for _name, command in gates:
        for candidate in _TEST_DIR_CANDIDATES:
            if _path_mentions(command, candidate):
                found.add(f"{candidate}/")
    return found


def _propose_max_open_prs(runner: Optional[Callable]) -> Optional[dict]:
    if runner is None:
        return None
    try:
        result = runner(
            ["gh", "pr", "list", "--state", "open", "--json", "number"],
            check=False,
        )
    except Exception:  # noqa: BLE001 - a failing runner yields no proposal
        return None

    if result is None or getattr(result, "returncode", 1) != 0:
        return None

    stdout = getattr(result, "stdout", None)
    if not stdout:
        return None
    try:
        data = json.loads(stdout)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, list):
        return None

    count = len(data)
    value = max(count + 2, 3)
    return {
        "value": value,
        "evidence": (
            f"gh pr list --state open reports {count} open PR(s) right now; "
            f"proposing headroom of {value}"
        ),
    }
