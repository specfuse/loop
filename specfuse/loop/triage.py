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

from specfuse.loop.agent_policy import (
    SEVERITY_LABEL_PREFIX,
    SEVERITY_VALUES,
    read_severity_label,
)
from specfuse.loop.escalation import CATEGORY_LABELS, NEEDS_HUMAN_LABEL
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
_MARKER_TEMPLATE_WITH_SEVERITY = (
    "<!-- specfuse:triage category={category} confidence={confidence} "
    "severity={severity} -->"
)
_MARKER_RE = re.compile(r"<!-- specfuse:triage (?P<fields>.*?) -->")
_MARKER_FIELD_RE = re.compile(r"(\S+)=(\S+)")


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


def labels_for(category: str) -> tuple:
    """Return every label `category` projects onto its issue, category
    label first. Total over `CATEGORIES`.

    `question` projects two (#2705). Its route is `needs-human`, and
    `NEEDS_HUMAN_LABEL` is what puts an issue in the queue `/attention`
    reads -- the category label alone is a classification nobody sweeps.
    `escalation.py` has always applied both for the issues it files; this
    is the same pairing on the triage write path.

    Every other category projects exactly one. A triaged bug is a routing
    decision, not a halt, and labelling it `needs-human` would drown the
    queue this exists to keep readable.
    """
    label = label_for(category)
    if category == "question":
        return (label, NEEDS_HUMAN_LABEL)
    return (label,)


def render_marker(category: str, confidence: str, severity: Optional[str] = None) -> str:
    """Render the triage marker for `category`/`confidence`, plus `severity`
    as a third field when given.

    Mirrors `monitor/issues.py`'s `_MARKER_TEMPLATE` convention: an
    HTML-comment marker embedded in the issue body, parsed back by
    `parse_marker`/`parse_marker_fields`. The two-field form is
    byte-identical to what this rendered before `severity` existed -- every
    marker already written in the wild is read against that exact string.
    """
    if severity is None:
        return _MARKER_TEMPLATE.format(category=category, confidence=confidence)
    return _MARKER_TEMPLATE_WITH_SEVERITY.format(
        category=category, confidence=confidence, severity=severity
    )


def severity_label_for(value: str) -> str:
    """Return `value`'s projected `severity:<value>` label."""
    return f"{SEVERITY_LABEL_PREFIX}{value}"


def parse_marker_fields(body: str) -> Optional[dict]:
    """Return every `key=value` field carried by `body`'s triage marker as a
    dict, or `None` if `body` carries none.

    Scans the fields as `key=value` pairs rather than a fixed sequence, so
    field order and field count don't decide whether a marker is seen at
    all -- a marker carrying an extra field (e.g. `severity=`) still parses.
    """
    match = _MARKER_RE.search(body or "")
    if match is None:
        return None
    return dict(_MARKER_FIELD_RE.findall(match.group("fields")))


def parse_marker(body: str) -> Optional[tuple]:
    """Return the `(category, confidence)` pair carried by `body`'s triage
    marker, or `None` if `body` carries none."""
    fields = parse_marker_fields(body)
    if fields is None:
        return None
    category = fields.get("category")
    confidence = fields.get("confidence")
    if not category or not confidence:
        return None
    return (category, confidence)


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
            marked_severity = (parse_marker_fields(body) or {}).get("severity")
            target_labels = labels_for(marked_category) if marked_category in CATEGORIES else ()
            if marked_severity:
                target_labels = tuple(target_labels) + (severity_label_for(marked_severity),)
            existing_labels = {
                label.get("name") for label in decision.get("labels") or []
            }
            missing = [label for label in target_labels if label not in existing_labels]
            row = {
                "number": number,
                "skipped": True,
                "marker_written": False,
                "label_written": False,
            }
            if missing:
                try:
                    runner(
                        [
                            "gh", "issue", "edit", str(number),
                            "--repo", repo,
                            "--add-label", ",".join(missing),
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

        severity = decision.get("severity")

        row = {
            "number": number,
            "category": applied_category,
            "confidence": confidence,
            "route": route_for(applied_category),
            "skipped": False,
        }
        if severity:
            row["severity"] = severity

        marker = render_marker(applied_category, confidence, severity)
        new_body = f"{body}\n\n{marker}" if body else marker
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

        labels_to_add = list(labels_for(applied_category))
        if severity:
            labels_to_add.append(severity_label_for(severity))

        try:
            runner(
                [
                    "gh", "issue", "edit", str(number),
                    "--repo", repo,
                    "--add-label", ",".join(labels_to_add),
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
    """Return open issues with no triage marker, plus marked issues whose
    projected label is missing.

    Filters `gh issue list`'s output client-side rather than trusting a
    label listing -- the marker is re-checked here directly, the same
    discipline `autofix_state.has_prior_attempt` uses over
    `find_finding_issue`. An issue that carries a harvester finding marker
    (`has_finding_marker`) is still returned, flagged `already_structured`
    in its row so the caller can skip re-categorising it -- that is a flag,
    not an exclusion.

    A marked issue is normally excluded -- marked means done, per
    `PLAN.md`'s scope boundary. But `apply_triage`'s repair path
    (`[FEAT-2026-0045/T01/marker-label-desync]`) can only fire on rows this
    function hands it, so a marked issue whose projected label is missing
    from its `labels` is still returned here, flagged `needs_repair` with
    the marker's own `category`/`confidence` copied onto the row -- the
    caller applies those straight to `apply_triage` without a
    classification round, since the category is already decided.
    """
    issues = _list_open_issues(runner, repo, limit=limit)
    untriaged = []
    for issue in issues:
        body = issue.get("body") or ""
        marker = parse_marker(body)
        if marker is not None:
            marked_category, marked_confidence = marker
            target_labels = labels_for(marked_category) if marked_category in CATEGORIES else ()
            existing_labels = {label.get("name") for label in issue.get("labels") or []}
            if not target_labels or all(label in existing_labels for label in target_labels):
                continue
            row = dict(issue)
            row["needs_repair"] = True
            row["category"] = marked_category
            row["confidence"] = marked_confidence
            row["already_structured"] = has_finding_marker(body)
            untriaged.append(row)
            continue
        row = dict(issue)
        row["needs_repair"] = False
        row["already_structured"] = has_finding_marker(body)
        untriaged.append(row)
    return untriaged


#: The `gh issue list` window size a backfill page grows by. Deliberately
#: not `limit` itself -- criterion 2 of
#: `[FEAT-2026-0113/T08H/limit-bounds-candidates]`: a small `limit` must not
#: shrink the listing window, since candidates cluster in the oldest issues
#: and a stranded backlog is old by construction.
_BACKFILL_PAGE_SIZE = DEFAULT_LIST_LIMIT


#: What a backfill run should do with one candidate's severity (#3360).
SEVERITY_CLASSIFY = "classify"
SEVERITY_RECONCILE = "reconcile"
SEVERITY_SKIP = "skip"


def _severity_label_names(labels) -> list:
    """The `severity:*` label names on an issue, however `labels` is shaped.

    `gh issue list --json ...,labels` yields `{"name": ...}` mappings; callers
    holding bare strings are accepted too so the decision below stays testable
    without a fixture shape.
    """
    names = []
    for label in labels or ():
        name = label.get("name") if isinstance(label, dict) else label
        text = str(name or "").strip().lower()
        if text.startswith(SEVERITY_LABEL_PREFIX):
            names.append(text)
    return names


def severity_decision(labels, aliases: Optional[dict] = None) -> tuple:
    """`(action, severity, reason)` for one backfill candidate (#3360).

    A candidate is selected on its MARKER -- already triaged, no `severity=`
    field. That predicate never looked at the issue's labels, so an issue a
    person had already labelled `severity:minor` was still a candidate: it got
    a fresh classification, and the write path added a second severity label
    beside the human's. `read_severity_label` then returns whichever it
    recognises first, which is the agent silently overriding a person at the
    `min_severity` floor.

    So the label is consulted first, and when it states a severity the marker is
    written FROM it:

    * `SEVERITY_RECONCILE` -- the labels agree on one value. The issue stops
      being stranded *and* the person's judgement is what gets recorded. No
      classification session is spent, and no label is written, because the
      label is already there and is the source.
    * `SEVERITY_CLASSIFY` -- no `severity:*` label at all. The original path.
    * `SEVERITY_SKIP` -- the labels resolve to more than one value (the
      operator's own ambiguity), or a `severity:*` label is present that
      nothing can read. Classifying either would put a second, readable label
      beside one a human chose, which is the collision in a different spelling.

    This was latent when FEAT-2026-0113 closed: the measured repository's
    `critical`/`major`/`minor` scheme yielded a one-entry rubric, so the
    classifier failed closed on exactly the issues that would have collided.
    Shipping the default alias table (#3355) made that scheme readable, which
    removed the mask rather than the hazard.
    """
    names = _severity_label_names(labels)
    if not names:
        return (SEVERITY_CLASSIFY, None, None)

    resolved = set()
    unreadable = []
    for name in names:
        value, _aliased_from = read_severity_label([name], aliases)
        if value in SEVERITY_VALUES:
            resolved.add(value)
        else:
            unreadable.append(name)

    if len(resolved) > 1:
        return (
            SEVERITY_SKIP,
            None,
            f"labels resolve to more than one severity ({', '.join(sorted(resolved))}) "
            f"— the marker is left alone rather than picking one",
        )
    if not resolved:
        return (
            SEVERITY_SKIP,
            None,
            f"carries {', '.join(sorted(unreadable))}, which no vocabulary value "
            f"or alias reads — a person's judgement this run cannot interpret",
        )
    return (SEVERITY_RECONCILE, resolved.pop(), None)


def _is_backfill_candidate(issue: dict) -> bool:
    body = issue.get("body") or ""
    fields = parse_marker_fields(body)
    if fields is None:
        return False
    if fields.get("severity"):
        return False
    category = fields.get("category")
    if category not in CATEGORIES:
        return False
    if has_finding_marker(body):
        return False
    existing_labels = {label.get("name") for label in issue.get("labels") or []}
    if existing_labels & CATEGORY_LABELS:
        return False
    return True


def list_severity_backfill_candidates(
    runner: Callable, repo: str, limit: int = DEFAULT_LIST_LIMIT
) -> list:
    """Return up to `limit` already-marked, severity-less open issues a
    backfill run may amend.

    The inverse of `list_untriaged`'s exclusion: a marked issue is normally
    done and skipped, but one whose marker carries no `severity=` field is
    exactly what a backfill exists to touch. Reuses the exclusions the normal
    triage path already applies rather than re-deriving them -- a harvester
    finding (`has_finding_marker`) and an agent-authored escalation (any
    label in `escalation.CATEGORY_LABELS`) are both left alone. An issue
    whose marker names a category outside `CATEGORIES`, carries no marker at
    all, or already carries `severity=` is not a candidate.

    `limit` bounds how many *candidates* are returned, not how many open
    issues are listed -- `[FEAT-2026-0113/T08H/limit-bounds-candidates]`.
    The underlying `gh issue list` window grows in `_BACKFILL_PAGE_SIZE`
    steps, each page re-listing from the start (`gh`'s own listing has no
    cursor), until `limit` candidates are found or the repository's open
    issues are exhausted (a page shorter than the window it asked for).
    """
    candidates: list = []
    window = _BACKFILL_PAGE_SIZE
    scanned = 0
    while True:
        issues = _list_open_issues(runner, repo, limit=window)
        for issue in issues[scanned:]:
            if _is_backfill_candidate(issue):
                candidates.append(issue)
                if len(candidates) >= limit:
                    return candidates
        scanned = len(issues)
        if len(issues) < window:
            return candidates
        window += _BACKFILL_PAGE_SIZE


def amend_marker_severity(body: str, severity: str) -> str:
    """Replace `body`'s existing triage marker in place with one that also
    carries `severity`, keeping `category=`/`confidence=` unchanged.

    Returns `body` unchanged, by string equality, when it carries no marker
    or its marker already carries a `severity=` field -- there is nothing to
    amend in either case. Rendered through `render_marker` rather than a
    fourth marker literal, so the two template strings stay the only place a
    marker's shape is spelled out.
    """
    fields = parse_marker_fields(body)
    if fields is None or fields.get("severity"):
        return body
    match = _MARKER_RE.search(body)
    new_marker = render_marker(fields.get("category"), fields.get("confidence"), severity)
    return body[: match.start()] + new_marker + body[match.end() :]
