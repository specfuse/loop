#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Discovery: list a repo's open specfuse:feature GitHub issues as loop-feature candidates."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any, Optional

# Matches [INIT-YYYY-NNNN/FNN] or [FEAT-YYYY-NNNN] at the start of a title.
_TITLE_RE = re.compile(
    r"^\[(?P<id>(?:INIT-\d{4}-\d{4}/F\d{2}|FEAT-\d{4}-\d{4}))\]\s*(?P<summary>.*)$"
)


def _default_runner(repo: str) -> list:
    """Shell out to gh and return parsed JSON issue list. Not called in tests."""
    result = subprocess.run(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--label", "specfuse:feature",
            "--state", "open",
            "--json", "number,title,labels,url,body",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _extract_label_value(labels: list, prefix: str) -> Optional[str]:
    for label in labels:
        name = label.get("name", "")
        if name.startswith(prefix):
            return name[len(prefix):]
    return None


def list_features(repo: str, runner: Any = None) -> list:
    """Return loop-feature candidates for open specfuse:feature issues in repo.

    runner: callable(repo: str) -> list[dict]. Defaults to shelling out to gh.
    Issues whose titles lack a parseable [<id>] tag are skipped with a warning.
    """
    if runner is None:
        runner = _default_runner

    issues = runner(repo)
    candidates = []

    for issue in issues:
        title = issue.get("title", "")
        m = _TITLE_RE.match(title)
        if not m:
            print(
                f"WARNING: skipping issue #{issue.get('number')}: "
                f"no [<id>] tag in title: {title!r}",
                file=sys.stderr,
            )
            continue

        labels = issue.get("labels", [])
        candidates.append({
            "feature_id": m.group("id"),
            "title": m.group("summary").strip(),
            "initiative": _extract_label_value(labels, "initiative:"),
            "task_type": _extract_label_value(labels, "type:"),
            "autonomy": _extract_label_value(labels, "autonomy:") or "review",
            "url": issue.get("url", ""),
            "number": issue.get("number"),
            "body": issue.get("body", ""),
        })

    return candidates


def main(_runner: Any = None) -> None:
    """CLI entrypoint. _runner is injectable for tests."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <owner/repo>", file=sys.stderr)
        sys.exit(1)

    repo = sys.argv[1]
    candidates = list_features(repo, runner=_runner)
    for c in candidates:
        print(f"{c['feature_id']}\t{c['task_type']}\t{c['autonomy']}\t{c['url']}")


if __name__ == "__main__":
    main()
