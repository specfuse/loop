# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Read-only monitoring-config access for the findings providers
(FEAT-2026-0049/T09).

Neither `KIND_FINDING_DIAGNOSE` nor `KIND_FINDING_AUTOFIX` providers can get
"which component is this finding about, and what has the operator said
about it?" from `specfuse.agent.state`'s snapshot -- `_read_issues` requests
only `number,title,labels,body`, and the component is prose inside the body.
This module answers both questions, and nothing else: it performs no write
of any kind (no issue comment, no label, no file), and it parses
`.specfuse/monitoring.yml` with `specfuse.loop._miniyaml.parse`, the same
reader `specfuse.monitor.autofix_run.main` uses, rather than inventing a
second one.

Does **not** read the `autofix` dial. `specfuse.monitor.autofix._read_dial`
already owns that (reached via `run_autofix`, which T11 calls with the raw
parsed config) -- a second copy here is exactly the drift the binding rules'
single-source-of-truth discipline exists to prevent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from specfuse.loop import _miniyaml

__all__ = ("load_monitoring_config", "component_for_finding", "component_diagnose_dial")

_COMPONENT_MARKER = "**Component:** "


def load_monitoring_config(path: Path) -> Optional[Any]:
    """Parse a monitoring.yml-shaped file at `path`.

    Returns `None` -- never raises -- when the file is absent. An absent
    `.specfuse/monitoring.yml` is a correct, valid final state (the file's
    own words); the agent must read it as "nothing to do here", not as an
    error.
    """
    p = Path(path)
    if not p.exists():
        return None
    return _miniyaml.parse(p.read_text(encoding="utf-8"))


def component_for_finding(issue_body: str) -> Optional[str]:
    """Resolve the component name from a finding issue's body.

    Reads the `**Component:** <name>` line
    `specfuse.monitor.issues._render_body` writes. Returns `None` when the
    line is absent rather than raising.
    """
    for line in issue_body.splitlines():
        if line.startswith(_COMPONENT_MARKER):
            return line[len(_COMPONENT_MARKER):].strip()
    return None


def component_diagnose_dial(monitoring_config: Any, component: str) -> Optional[str]:
    """Read `component`'s `diagnose` dial out of a parsed monitoring config's
    `components:` list. Returns `None` when the config, the component entry,
    or the dial is absent or malformed rather than raising."""
    if not isinstance(monitoring_config, dict):
        return None
    components = monitoring_config.get("components")
    if not isinstance(components, list):
        return None
    for entry in components:
        if isinstance(entry, dict) and entry.get("name") == component:
            dial = entry.get("diagnose")
            return dial if isinstance(dial, str) else None
    return None
