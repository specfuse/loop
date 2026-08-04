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
    """Yield `(name, command)` for every gate in *set_name*, in declared order.

    Order is preserved because gate order is a real signal: the cheap,
    fast-failing gates are declared first so a broken build reports in seconds
    rather than after the full suite.
    """
    text = Path(verification_yml).read_text(encoding="utf-8")
    block = _set_block(text, set_name)
    if not block:
        return []

    gates: list[tuple[str, str]] = []
    entries = re.split(r"^  - name:\s*", block, flags=re.M)[1:]
    for entry in entries:
        name = entry.split("\n", 1)[0].strip()
        m = _COMMAND_RE.search(entry)
        command = m.group(1).strip() if m else ""
        gates.append((name, command))
    return gates


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
