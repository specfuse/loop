# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The bug-lane merge-eligibility predicate (FEAT-2026-0048/T02): may this
bug-lane PR auto-merge?

Mirrors `specfuse/monitor/autofix.py`'s shape: module-level `REASON_*`
constants, a frozen decision dataclass, an injected state-reader `Protocol`
so the predicate performs no I/O. Its docstring promise carries over
unchanged: any failure to evaluate an input returns "do not merge".

Fail closed. This is the whole design. A guardrail that raises on malformed
input is a guardrail that malformed input walks straight through. Every
unreadable, missing, wrong-typed, or ambiguous input yields `eligible=False`
with a reason -- never an exception, never a default-permit.

Six guardrails, all required, all and-ed: test-first evidence (structural
only -- this module does not judge whether a test is a *good* test, per
FEAT-2026-0053's rule that model-authored signals may only veto, never
approve); CI green; a diff-size cap; no `arm_eval.JUDGE_PATHS` touched;
traced to a triaged issue or diagnosed finding; and a rolling-24h merge cap
whose storage T03 owns.

This module performs no merge. Execution is T04's, deliberately kept out of
this predicate's reach.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from specfuse.loop.arm_eval import JUDGE_PATHS

REASON_NO_TEST_EVIDENCE = "no_test_evidence"
REASON_CI_NOT_GREEN = "ci_not_green"
REASON_DIFF_TOO_LARGE = "diff_too_large"
REASON_JUDGE_PATH_TOUCHED = "judge_path_touched"
REASON_UNTRACEABLE = "untraceable_provenance"
REASON_DAILY_CAP_REACHED = "daily_cap_reached"
REASON_ELIGIBLE = "eligible"
REASON_UNREADABLE_INPUT = "unreadable_input"

# Public label names for the declining reasons (#1420). The REASON_* values above
# are internal identifiers and must not double as labels: they are snake_case
# where the registry is kebab/prefixed, and — the defect this fixes — nothing
# created them, so `gh pr edit --add-label <reason>` failed on every declining
# path in every repository. Every name here has a LABEL_SPEC in
# `loop/labels.py`, so `provision_labels` creates it on init/upgrade;
# `tests/test_bug_lane_labels_registered.py` asserts that both ways.
#
# REASON_ELIGIBLE is deliberately absent: it is not a decline and is never
# labelled.
DECLINE_LABELS = {
    REASON_NO_TEST_EVIDENCE: "bug-lane:no-test-evidence",
    REASON_CI_NOT_GREEN: "bug-lane:ci-not-green",
    REASON_DIFF_TOO_LARGE: "bug-lane:diff-too-large",
    REASON_JUDGE_PATH_TOUCHED: "bug-lane:judge-path-touched",
    REASON_UNTRACEABLE: "bug-lane:untraceable-provenance",
    REASON_DAILY_CAP_REACHED: "bug-lane:daily-cap-reached",
    REASON_UNREADABLE_INPUT: "bug-lane:unreadable-input",
}

PROVENANCE_KINDS = ("triaged_issue", "diagnosed_finding")

# Retained as the fallback only; the accepted paths now arrive as a parameter
# (#1418) so a consumer project can declare its own layout. Kept module-level
# so the historical default has one name.
_TESTS_PREFIX = "tests/"


class MergeCapStateReader(Protocol):
    """Read-only view over rolling-24h merge-cap state (T03 owns where it
    lives). Injected so this module stays testable with no disk and no
    network."""

    def merges_last_24h(self) -> int: ...


@dataclass(frozen=True)
class MergeDecision:
    """The predicate's output: eligibility plus the guardrail that produced
    the verdict."""

    eligible: bool
    reason: str


def _decline(reason: str) -> MergeDecision:
    return MergeDecision(eligible=False, reason=reason)


def evaluate_pr_shape_guardrails(
    *,
    changed_files: Any,
    diff_lines: Any,
    max_diff_lines: Any,
    provenance: Any,
    test_paths: Any = (_TESTS_PREFIX,),
) -> MergeDecision:
    """The guardrails decidable from the PR's shape alone -- no CI, no cap.

    Extracted so a caller can learn that a PR can never merge *before* paying
    for something expensive. `run_bug_lane` waits up to ten minutes for CI to
    settle; a PR touching a judge path is unmergeable whatever CI says, so
    that wait buys nothing. Observed live: two of eight items in one run
    declined `judge_path_touched` after the full CI wait.

    Returns `eligible=True` only in the sense that no shape guardrail
    objected -- CI and the rolling merge cap are still unevaluated, so this
    is never on its own an authorisation to merge. `evaluate_merge_guardrails`
    remains the single predicate the merge decision reads.
    """
    changed = _validate_changed_files(changed_files)
    if changed is None:
        return _decline(REASON_UNREADABLE_INPUT)

    if not _has_test_evidence(changed, test_paths):
        return _decline(REASON_NO_TEST_EVIDENCE)

    max_diff = _validate_positive_int(max_diff_lines)
    if max_diff is None:
        return _decline(REASON_UNREADABLE_INPUT)
    diff_count = _validate_nonnegative_int(diff_lines)
    if diff_count is None:
        return _decline(REASON_UNREADABLE_INPUT)
    if diff_count > max_diff:
        return _decline(REASON_DIFF_TOO_LARGE)

    if judge_paths_touched(changed):
        return _decline(REASON_JUDGE_PATH_TOUCHED)

    if not _is_traceable(provenance):
        return _decline(REASON_UNTRACEABLE)

    return MergeDecision(eligible=True, reason=REASON_ELIGIBLE)


def evaluate_merge_guardrails(
    *,
    changed_files: Any,
    ci_conclusion: Any,
    diff_lines: Any,
    max_diff_lines: Any,
    provenance: Any,
    max_merges_per_day: Any,
    # Defaults to the historical `tests/` so an omitting caller behaves exactly
    # as before #1418. An explicitly malformed value still fails closed —
    # omission means "use the default", not "skip the guardrail".
    test_paths: Any = (_TESTS_PREFIX,),
    state_reader: MergeCapStateReader,
) -> MergeDecision:
    """Decide whether a bug-lane PR may auto-merge.

    `changed_files` is the PR's changed-file path list; `ci_conclusion` is
    the CI run's terminal conclusion string; `diff_lines` is the PR's total
    changed-line count; `max_diff_lines` / `max_merges_per_day` come from
    `agent_policy.bug_lane_limits()` (resolved by the caller -- this module
    reads no config file); `provenance` names the triaging source; and
    `state_reader` answers the rolling-24h merge-count question T03 owns the
    storage for. Any failure to evaluate an input returns
    `eligible=False`.
    """
    # The two checks that precede the CI read keep their own inline form, so
    # the CI check stays exactly where it was in the sequence and no declining
    # reason's precedence changes. Everything after CI is the shape predicate,
    # which re-runs these two harmlessly.
    changed = _validate_changed_files(changed_files)
    if changed is None:
        return _decline(REASON_UNREADABLE_INPUT)

    if not _has_test_evidence(changed, test_paths):
        return _decline(REASON_NO_TEST_EVIDENCE)

    if ci_conclusion != "success":
        return _decline(REASON_CI_NOT_GREEN)

    shape = evaluate_pr_shape_guardrails(
        changed_files=changed_files,
        diff_lines=diff_lines,
        max_diff_lines=max_diff_lines,
        provenance=provenance,
        test_paths=test_paths,
    )
    if not shape.eligible:
        return shape

    max_merges = _validate_positive_int(max_merges_per_day)
    if max_merges is None:
        return _decline(REASON_UNREADABLE_INPUT)

    try:
        merge_count = state_reader.merges_last_24h()
    except Exception:  # noqa: BLE001
        return _decline(REASON_UNREADABLE_INPUT)
    if not isinstance(merge_count, int) or isinstance(merge_count, bool):
        return _decline(REASON_UNREADABLE_INPUT)
    if merge_count >= max_merges:
        return _decline(REASON_DAILY_CAP_REACHED)

    return MergeDecision(eligible=True, reason=REASON_ELIGIBLE)


def _validate_changed_files(changed_files: Any) -> list[str] | None:
    if changed_files is None or isinstance(changed_files, (str, bytes)):
        return None
    if not isinstance(changed_files, Sequence):
        return None
    result: list[str] = []
    for entry in changed_files:
        if not isinstance(entry, str):
            return None
        result.append(entry)
    return result


def _has_test_evidence(changed: list[str], test_paths: Any) -> bool:
    """True when the diff touches a declared test path.

    Structural only — it never judges whether the test is a *good* test. A
    semantic judgement here would be a model-authored approval, and
    FEAT-2026-0053's principle permits models to veto, never to approve.

    Fails closed: an unreadable, empty, or non-list `test_paths` returns False,
    so a malformed declaration refuses the merge rather than waving it through.
    An empty list is deliberately not read as "no evidence needed".
    """
    if not isinstance(test_paths, (list, tuple)) or not test_paths:
        return False
    prefixes = [p for p in test_paths if isinstance(p, str) and p]
    if not prefixes:
        return False
    return any(
        path.startswith(prefix)
        for path in changed
        for prefix in prefixes
    )


def judge_paths_touched(changed: Sequence[str]) -> list[str]:
    """Return the changed paths that fall under `JUDGE_PATHS`, in order.

    Public and path-naming rather than boolean (it used to be
    `_touches_judge_path`) so an escalation can tell the reader *which* path
    tripped the guardrail. `judge_path_touched` on its own sends the human
    back to the diff to work out what the agent already knew.
    """
    hits: list[str] = []
    for path in changed:
        for judge_path in JUDGE_PATHS:
            if judge_path.endswith("/"):
                if path.startswith(judge_path):
                    hits.append(path)
                    break
            elif path == judge_path:
                hits.append(path)
                break
    return hits


def _is_traceable(provenance: Any) -> bool:
    if not isinstance(provenance, Mapping):
        return False
    kind = provenance.get("kind")
    ref = provenance.get("ref")
    if kind not in PROVENANCE_KINDS:
        return False
    if not isinstance(ref, str) or not ref.strip():
        return False
    return True


def _validate_positive_int(value: Any) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    if value <= 0:
        return None
    return value


def _validate_nonnegative_int(value: Any) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    if value < 0:
        return None
    return value
