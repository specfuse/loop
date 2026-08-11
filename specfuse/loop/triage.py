# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Deterministic mechanism for inbound-issue triage (FEAT-2026-0045/T01).

This module owns the closed category vocabulary, the category-to-route map,
the triage marker's render/parse pair, and the scan that finds untriaged
open issues. It does not classify free-text issues -- that judgment call
belongs to the skill (T03). See ``PLAN.md``'s "the seam" section.

The marker is authoritative; the category label (``labels.py``) is a
projection of it for human visibility in the GitHub UI. Precedence is the
marker wins on disagreement -- see ``PLAN.md``'s "how a triaged issue is
marked" section.

Following the convention every other ``gh issue list`` call site in this
package already uses (``monitor/issues.py``, ``monitor/autofix_state.py``):
an injected ``runner``, no ``--search``, client-side filtering.
``list_untriaged`` re-checks the marker itself rather than trusting a label
listing, mirroring ``autofix_state.has_prior_attempt``'s precedent.
"""

from __future__ import annotations

import json
import re
from typing import Callable, Optional

from specfuse.monitor.issues import DEFAULT_LIST_LIMIT, has_finding_marker

# Closed. A sixth category is a scope change, not a code change -- see
# PLAN.md's escalation triggers.
CATEGORIES = ("bug", "feature", "duplicate", "question", "wontfix")

# Closed. No third confidence level.
CONFIDENCES = ("high", "low")

_ROUTES = {
    "bug": "fix-bug",
    "feature": "roadmap-add",
    "duplicate": "link-and-close",
    "question": "needs-human",
    "wontfix": "close",
}

# Labels minted for this feature. `question` deliberately reuses the
# existing `triage-question` label (registered by FEAT-2026-0071, consumer
# `escalation.py`) rather than minting a second one -- see PLAN.md's scope
# boundary on why `wontfix` does mint its own instead of reusing GitHub's
# conventional label.
BUG_LABEL = "triage:bug"
FEATURE_LABEL = "triage:feature"
DUPLICATE_LABEL = "triage:duplicate"
WONTFIX_LABEL = "triage:wontfix"

CATEGORY_LABEL_MAP = {
    "bug": BUG_LABEL,
    "feature": FEATURE_LABEL,
    "duplicate": DUPLICATE_LABEL,
    "question": "triage-question",
    "wontfix": WONTFIX_LABEL,
}

_MARKER_TEMPLATE = "<!-- specfuse:triage category={category} confidence={confidence} -->"
_MARKER_RE = re.compile(
    r"<!-- specfuse:triage category=(?P<category>\S+) confidence=(?P<confidence>\S+) -->"
)


def route_for(category: str) -> str:
    """Return `category`'s route string. Total over `CATEGORIES`.

    Raises `ValueError` on anything not in `CATEGORIES` -- there is no
    fallback route, since an unrouted category is a bug in the caller, not
    a case to paper over.
    """
    if category not in _ROUTES:
        raise ValueError(f"not a triage category: {category!r}")
    return _ROUTES[category]


def label_for(category: str) -> str:
    """Return `category`'s projected label. Total over `CATEGORIES`."""
    if category not in CATEGORY_LABEL_MAP:
        raise ValueError(f"not a triage category: {category!r}")
    return CATEGORY_LABEL_MAP[category]


def render_marker(category: str, confidence: str) -> str:
    """Render the triage marker for `category`/`confidence`.

    Mirrors `monitor/issues.py`'s `_MARKER_TEMPLATE` convention: an
    HTML-comment marker embedded in the issue body, parsed back by
    `parse_marker`.
    """
    return _MARKER_TEMPLATE.format(category=category, confidence=confidence)


def parse_marker(body: str) -> Optional[tuple]:
    """Return the `(category, confidence)` pair carried by `body`'s triage
    marker, or `None` if `body` carries none."""
    match = _MARKER_RE.search(body or "")
    if match is None:
        return None
    return (match.group("category"), match.group("confidence"))


def _list_open_issues(runner: Callable, repo: str, *, limit: int) -> list:
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--state", "open",
            "--limit", str(limit),
            "--json", "number,title,body,labels",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []


def apply_triage(runner: Callable, repo: str, decisions: list, *, auto: bool = False) -> list:
    """Record each decision in `decisions` against its GitHub issue.

    Each decision is a mapping carrying at least `number`, `body` (the
    issue's current body, for the idempotency check and marker append) and
    `category`, plus optional `confidence` (defaults to `"high"`).

    Marker first, label best-effort -- see `PLAN.md`'s "how a triaged issue
    is marked" section. The marker write is the idempotency key: a decision
    for an issue whose body already carries a marker never rewrites the
    marker. But a marker with no matching label on the issue (the label
    write failed on an earlier pass, e.g. because the label did not exist
    yet) is not fully idempotent -- it is missing its projection, so this
    retries only the label write. `decision["labels"]` (as returned by
    `gh issue list --json ...,labels`, i.e. a list of `{"name": ...}`
    mappings) is what `labels` is checked against; a decision with no
    `labels` key is treated as having none, so a repair is attempted. A
    label write that fails is recorded in the returned report and never
    raised, per `[FEAT-2026-0042/G2/registered-is-not-provisioned]`.

    With `auto=True`, a decision whose confidence is not `"high"` is
    recorded as the `question` category (still marked, still routed to
    `needs-human`) instead of being applied as proposed. With `auto=False`
    every decision is applied as given -- see this WU's flag-scope table.

    Raises `ValueError` if any decision names a category outside
    `CATEGORIES`, before any write for that decision happens.
    """
    results = []
    for decision in decisions:
        category = decision["category"]
        if category not in CATEGORIES:
            raise ValueError(f"not a triage category: {category!r}")

        number = decision["number"]
        body = decision.get("body") or ""
        confidence = decision.get("confidence", "high")

        marker = parse_marker(body)
        if marker is not None:
            marked_category, _marked_confidence = marker
            target_label = label_for(marked_category) if marked_category in CATEGORIES else None
            existing_labels = {
                label.get("name") for label in decision.get("labels") or []
            }
            row = {
                "number": number,
                "skipped": True,
                "marker_written": False,
                "label_written": False,
            }
            if target_label is not None and target_label not in existing_labels:
                try:
                    runner(
                        [
                            "gh", "issue", "edit", str(number),
                            "--repo", repo,
                            "--add-label", target_label,
                        ],
                        check=True,
                    )
                except Exception as exc:  # noqa: BLE001 - label failure never raises
                    row["label_written"] = False
                    row["label_error"] = str(exc)
                else:
                    row["label_written"] = True
            results.append(row)
            continue

        applied_category = category
        if auto and confidence != "high":
            applied_category = "question"

        row = {
            "number": number,
            "category": applied_category,
            "confidence": confidence,
            "route": route_for(applied_category),
            "skipped": False,
        }

        new_body = f"{body}\n\n{render_marker(applied_category, confidence)}" if body else render_marker(applied_category, confidence)
        try:
            runner(
                ["gh", "issue", "edit", str(number), "--repo", repo, "--body", new_body],
                check=True,
            )
        except Exception as exc:  # noqa: BLE001 - recorded, not raised
            row["marker_written"] = False
            row["marker_error"] = str(exc)
            row["label_written"] = False
            results.append(row)
            continue
        row["marker_written"] = True

        try:
            runner(
                [
                    "gh", "issue", "edit", str(number),
                    "--repo", repo,
                    "--add-label", label_for(applied_category),
                ],
                check=True,
            )
        except Exception as exc:  # noqa: BLE001 - label failure never raises
            row["label_written"] = False
            row["label_error"] = str(exc)
        else:
            row["label_written"] = True

        results.append(row)
    return results


def list_untriaged(runner: Callable, repo: str, limit: int = DEFAULT_LIST_LIMIT) -> list:
    """Return open issues whose body carries no triage marker.

    Filters `gh issue list`'s output client-side rather than trusting a
    label listing -- the marker is re-checked here directly, the same
    discipline `autofix_state.has_prior_attempt` uses over
    `find_finding_issue`. An issue that carries a harvester finding marker
    (`has_finding_marker`) is still returned, flagged `already_structured`
    in its row so the caller can skip re-categorising it -- that is a flag,
    not an exclusion.
    """
    issues = _list_open_issues(runner, repo, limit=limit)
    untriaged = []
    for issue in issues:
        body = issue.get("body") or ""
        if parse_marker(body) is not None:
            continue
        row = dict(issue)
        row["already_structured"] = has_finding_marker(body)
        untriaged.append(row)
    return untriaged
