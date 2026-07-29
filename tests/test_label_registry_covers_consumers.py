#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every label the package *uses* must be a label the registry *declares* (#300).

FEAT-2026-0071 built `LABEL_REGISTRY` on the premise that "specfuse ships code that
queries GitHub labels it never creates", and sourced each entry's name from the module
that owns it so the two could not drift. One feature later, FEAT-2026-0040's `T09`
added ``FINDING_LABEL = "monitoring-finding"`` and no registry entry — so
``provision_labels()`` created seven labels and not the eighth the harvester needs.

`gh issue create` rejects an unknown label outright, so the harvester could not file a
single finding on any repository that had not had the label made by hand:

    could not add label: 'monitoring-finding' not found

Nothing caught it. `T09`'s tests all inject a stub runner, and a stub accepts any
``--label`` argument; only a real ``gh`` against a real repository rejects it, and that
path was deferred precisely because ``gh`` is unusable inside a work-unit session. A
stub that cannot fail this way plus a deferred real run that would is how a
shipping-blocker survived three gates and a terminal close.

This is the guard that closes it, in the shape FEAT-2026-0072 established for
declared-but-unasserted surfaces: **discover** the constants by walking the package
rather than listing them, because a hand-written list reproduces the author's blind
spots — which is the blind spot that caused this.
"""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

from specfuse.loop.labels import LABEL_REGISTRY

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "specfuse"

# A label a consumer uses that is deliberately NOT provisioned. Empty by design:
# an entry here is a decision, and it needs a written reason.
_INTENTIONALLY_UNREGISTERED: dict[str, str] = {}


def _module_name(path: Path) -> str:
    rel = path.relative_to(_PACKAGE_ROOT.parent).with_suffix("")
    return ".".join(rel.parts)


def _discover_label_constants() -> list[tuple[str, str, str]]:
    """Every module-level ``*_LABEL`` / ``*_LABELS`` constant in the package.

    Returns (module, constant_name, label_value) triples, one per label value —
    a frozenset constant such as ``CATEGORY_LABELS`` contributes one row per member.

    Discovered by walking and parsing, never enumerated by hand.
    """
    found: list[tuple[str, str, str]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [
            target.id
            for node in tree.body
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name)
            and (target.id.endswith("_LABEL") or target.id.endswith("_LABELS"))
        ]
        if not names:
            continue
        module = importlib.import_module(_module_name(path))
        for name in names:
            value = getattr(module, name, None)
            if isinstance(value, str):
                found.append((_module_name(path), name, value))
            elif isinstance(value, (set, frozenset, list, tuple)):
                for item in sorted(value):
                    if isinstance(item, str):
                        found.append((_module_name(path), name, item))
    return found


def _registry_names() -> set[str]:
    return {spec.name for spec in LABEL_REGISTRY}


class TestRegistryCoversEveryConsumerLabel(unittest.TestCase):

    def test_every_label_constant_has_a_registry_entry(self):
        """The #300 regression: a consumer label with no registry entry cannot be
        provisioned, and `gh issue create` then rejects it outright."""
        declared = _registry_names()
        missing = [
            f"{module}.{const} = {value!r}"
            for module, const, value in _discover_label_constants()
            if value not in declared and value not in _INTENTIONALLY_UNREGISTERED
        ]
        self.assertEqual(
            missing, [],
            "label(s) used by the package but absent from LABEL_REGISTRY — "
            "provision_labels() will not create them and `gh` will reject every "
            "issue that carries one:\n  " + "\n  ".join(missing))

    def test_the_sweep_cannot_pass_vacuously(self):
        """A discovery walk that finds nothing satisfies 'all are declared' — the
        defect FEAT-2026-0069's probe found in two of its own boundary tests."""
        found = _discover_label_constants()
        self.assertGreaterEqual(
            len(found), 7,
            f"expected at least 7 label values across the package, found {len(found)}: "
            f"{[f'{m}.{c}' for m, c, _ in found]}")
        modules = {module for module, _, _ in found}
        self.assertIn("specfuse.monitor.issues", modules)
        self.assertIn("specfuse.loop.escalation", modules)
        self.assertIn("specfuse.loop.gh_features", modules)

    def test_intentionally_unregistered_entries_carry_a_reason(self):
        for name, reason in _INTENTIONALLY_UNREGISTERED.items():
            self.assertTrue(
                reason and reason.strip(),
                f"_INTENTIONALLY_UNREGISTERED[{name!r}] needs a written reason")


if __name__ == "__main__":
    unittest.main()
