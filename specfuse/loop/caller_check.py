#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Find public functions whose only callers are tests (#3324).

Four defects in September 2026 shared one shape — a symbol that existed, was
tested, and was wired to nothing: the `replan` event had a consumer and no
emitter for two years; `check_binding_block_budget` and the distillation
accept step were each called only from their own tests. Each passed a gate
whose oracle asserted the thing *existed*
(`[FEAT-2026-0104/operator/asserting-existence-is-not-asserting-truth]`), and
each was found by a later feature rather than its own gate.

Three of the four were detectable from the tree alone. This is that detection.

**Reachability, and why it is broader than "is called".** A function counts as
reached when any of these holds:

* a production module calls it — `name(`;
* a production module names it as a **string**, which is how
  `closing_requirements.py` dispatches every closing guard by
  `enforced_by="assert_..."` and how providers are resolved by configuration;
* it is a declared console-script target, or the `main` of a module carrying a
  `__main__` block — an operator-facing entry point legitimately has no
  in-tree caller.

Missing any of those and being called from `tests/` is the finding.

**Baseline, not zero tolerance.** The tree carries pre-existing instances, and
a guard that fails on today's state is the unsatisfiable-predicate defect
`planning-discipline.md` §2 names — the same reason #3320's binding-block check
ships as an advisory. `unreached_symbols` reports; `new_since_baseline`
compares against a recorded set so only *additions* are a finding.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path


def _repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parent


def _console_script_targets(root: Path) -> set[str]:
    try:
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
    except OSError:
        return set()
    block = re.search(r"\[project\.scripts\](.*?)(\n\[|\Z)", text, re.S)
    if not block:
        return set()
    targets = set()
    for line in block.group(1).splitlines():
        if "=" in line and ":" in line:
            targets.add(line.split(":")[-1].strip().strip('"').strip("'"))
    return targets


def unreached_symbols(root: Path | None = None) -> list[dict]:
    """Public functions defined under `specfuse/` that only `tests/` calls.

    Returns one dict per finding, sorted by name: `{"name", "module",
    "test_references"}`. Deterministic, read-only, and cheap enough to run at
    close time — it parses the tree once.
    """
    root = root or _repo_root()
    src, test_dir = root / "specfuse", root / "tests"
    prod_files = [p for p in src.rglob("*.py") if "data/" not in str(p)]

    defs: dict[str, Path] = {}
    entry_points = _console_script_targets(root)
    for path in prod_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text)
        except (OSError, SyntaxError):
            continue
        if '__name__ == "__main__"' in text:
            entry_points.add("main")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                defs.setdefault(node.name, path)

    prod_text = "".join(
        p.read_text(encoding="utf-8", errors="replace") for p in prod_files)
    try:
        test_text = "".join(
            p.read_text(encoding="utf-8", errors="replace")
            for p in test_dir.rglob("*.py"))
    except OSError:
        test_text = ""

    findings = []
    for name, module in sorted(defs.items()):
        if name in entry_points:
            continue
        called = prod_text.count(name + "(") > 1        # its own def is one
        named = f'"{name}"' in prod_text or f"'{name}'" in prod_text
        if called or named:
            continue
        refs = test_text.count(name + "(")
        if refs:
            findings.append({
                "name": name,
                "module": str(module.relative_to(root)),
                "test_references": refs,
            })
    return findings


def new_since_baseline(baseline: "set[str]", root: Path | None = None) -> list[dict]:
    """Findings whose symbol is absent from *baseline* — the ratchet.

    The recorded baseline is what the tree carried when the guard landed.
    Anything new is a symbol someone added and did not wire, which is the case
    worth failing on.
    """
    return [f for f in unreached_symbols(root) if f["name"] not in baseline]


def render(findings: "list[dict]") -> str:
    if not findings:
        return "caller-check: every public symbol has a non-test caller"
    lines = [f"caller-check: {len(findings)} public symbol(s) called only from tests:"]
    for f in findings:
        lines.append(f"  {f['name']}  ({f['module']}, {f['test_references']} test refs)")
    return "\n".join(lines)


def main(argv: "list[str] | None" = None) -> int:
    """Operator surface: `python3 -m specfuse.loop.caller_check`."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 -m specfuse.loop.caller_check",
        description="Report public symbols whose only callers are tests.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument(
        "--baseline", default=None, metavar="NAME,NAME",
        help="comma-separated symbols to treat as already accepted; only "
             "additions are reported, which is the ratchet the suite applies")
    args = parser.parse_args(argv)
    if args.baseline is not None:
        accepted = {n.strip() for n in args.baseline.split(",") if n.strip()}
        findings = new_since_baseline(accepted, args.root)
    else:
        findings = unreached_symbols(args.root)
    print(render(findings))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
