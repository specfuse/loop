#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Read the gate sets out of `.specfuse/verification.yml` (#592).

`verification.yml` is the source of truth for what gets verified. Anything
that runs gates should derive its list from here rather than keeping a copy.

`scripts/smoke-test.sh` used to carry a hand-maintained mirror under the
comment "Keep in sync". It drifted by six gates, and two of them
(`roadmap-link-gate`, `arm-sweep-gate`) shipped with features that week and
were never once executed by CI. A declared-but-unrun gate is worse than an
absent one, because the declaration reads as coverage.

Deliberately not a YAML dependency: `_miniyaml` already parses this project's
files, and adding a third-party parser to a path CI depends on would trade one
drift risk for an install risk.
"""

from __future__ import annotations

import re
from pathlib import Path

_SET_RE = re.compile(r"^([a-z_][a-z0-9_]*):\s*$", re.M)
_NAME_RE = re.compile(r"^  - name:\s*(\S+)\s*$", re.M)
_COMMAND_RE = re.compile(r'^\s+command:\s*"(.*?)"\s*$', re.M | re.S)
_NEEDS_RE = re.compile(r"^\s+needs:\s*\[(.*?)\]\s*$", re.M)


def _order_gates(gates: list[dict]) -> list[dict]:
    """Stable topological sort by `needs:`, mirroring `loop.order_gate_set`
    (FEAT-2026-0102/T01) so the two never disagree about the same file.

    Reimplemented rather than imported: importing `loop.py` here would pull
    in `_miniyaml`, the third-party-parser-shaped dependency this module's
    docstring records as deliberately avoided on a path CI depends on.
    """
    by_name = {gate["name"]: gate for gate in gates}
    for gate in gates:
        for dep in gate["needs"]:
            if dep not in by_name:
                raise ValueError(
                    f"gate {gate['name']!r} declares `needs: [{dep}]` but no "
                    f"{dep!r} gate is configured in this set"
                )

    ordered: list[dict] = []
    placed: set[str] = set()
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in placed:
            return
        if name in visiting:
            raise ValueError(f"`needs` cycle detected involving gate {name!r}")
        visiting.add(name)
        for dep in by_name[name]["needs"]:
            visit(dep)
        visiting.discard(name)
        placed.add(name)
        ordered.append(by_name[name])

    for gate in gates:
        visit(gate["name"])
    return ordered


def _set_block(text: str, set_name: str) -> str:
    """Return the raw text of one top-level gate set, without its siblings."""
    starts = [(m.group(1), m.start()) for m in _SET_RE.finditer(text)]
    for i, (name, pos) in enumerate(starts):
        if name != set_name:
            continue
        end = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        return text[pos:end]
    return ""


def iter_code_gates(
    verification_yml: "Path | str", set_name: str = "code"
) -> list[tuple[str, str]]:
    """Yield `(name, command)` for every gate in *set_name*, dependency-ordered.

    Declared order is preserved among gates with no `needs:` edge between
    them, because gate order is a real signal: the cheap, fast-failing gates
    are declared first so a broken build reports in seconds rather than after
    the full suite. A gate declaring `needs: [<gate>]` (FEAT-2026-0102/T02)
    is moved after its dependency, matching the order `loop._run_gate_set`
    executes — the two must never disagree about the same file.
    """
    text = Path(verification_yml).read_text(encoding="utf-8")
    block = _set_block(text, set_name)
    if not block:
        return []

    gates: list[dict] = []
    entries = re.split(r"^  - name:\s*", block, flags=re.M)[1:]
    for entry in entries:
        name = entry.split("\n", 1)[0].strip()
        m = _COMMAND_RE.search(entry)
        command = m.group(1).strip() if m else ""
        n = _NEEDS_RE.search(entry)
        needs = (
            [dep.strip() for dep in n.group(1).split(",") if dep.strip()]
            if n
            else []
        )
        gates.append({"name": name, "command": command, "needs": needs})

    return [(g["name"], g["command"]) for g in _order_gates(gates)]


def code_gate_names(
    verification_yml: "Path | str", set_name: str = "code"
) -> list[str]:
    """Names only, for parity checks."""
    text = Path(verification_yml).read_text(encoding="utf-8")
    return _NAME_RE.findall(_set_block(text, set_name))


def main() -> int:
    """Print `name<TAB>command` per gate, for shell consumption.

    Used by `scripts/smoke-test.sh`, which substitutes its own interpreter for
    a leading `python3`: the declared commands name `python3` because that is
    what a target project's driver invokes, while the smoke test must use the
    virtualenv interpreter that actually has the dependencies installed.
    """
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("verification_yml")
    ap.add_argument("--set", default="code", dest="set_name")
    args = ap.parse_args()
    for name, command in iter_code_gates(args.verification_yml, args.set_name):
        print(f"{name}\t{command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
