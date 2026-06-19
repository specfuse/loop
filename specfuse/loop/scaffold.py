# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path

try:
    from importlib.resources.abc import Traversable  # Python 3.11+
except ImportError:
    from importlib.abc import Traversable  # Python 3.10

_DATA: Traversable = importlib.resources.files("specfuse.loop").joinpath("data")


def _walk(node: Traversable, prefix: str) -> list[tuple[str, bytes]]:
    results: list[tuple[str, bytes]] = []
    for child in node.iterdir():
        rel = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            results.extend(_walk(child, rel))
        else:
            results.append((rel, child.read_bytes()))
    return results


def iter_scaffold_files() -> list[tuple[str, bytes]]:
    """Return every seed file as (relpath, content) pairs."""
    return _walk(_DATA, "")


def scaffold_version() -> str:
    """Return the packaged VERSION string."""
    return _DATA.joinpath("VERSION").read_text(encoding="utf-8").strip()


def read_scaffold(relpath: str) -> bytes:
    """Return content of one seed file by relpath (e.g. 'templates/PLAN.template.md')."""
    node: Traversable = _DATA
    for part in relpath.split("/"):
        node = node.joinpath(part)
    return node.read_bytes()


class ScaffoldExistsError(Exception):
    """Raised by init_specfuse when .specfuse/ already exists in the target."""


# Seed relpaths that map to a different target name inside .specfuse/
_SEED_RENAME: dict[str, str] = {
    "roadmap.template.md": "roadmap.md",
    "LEARNINGS.template.md": "LEARNINGS.md",
    "verification.yml.example": "verification.yml",
}

# Seed files handled by other work units (T05); skip during init
_SKIP_SEEDS: frozenset[str] = frozenset({"gitignore.snippet"})


def init_specfuse(
    target: str | Path, *, ci_check: str | None = None
) -> list[str]:
    """Write a fresh .specfuse/ tree in *target* from the packaged seed.

    Returns the sorted list of relpaths written (relative to .specfuse/).
    Raises ScaffoldExistsError if .specfuse/ already exists; nothing is written.
    ci_check is accepted for API compatibility but wiring is deferred to T06.
    """
    target_path = Path(target)
    specfuse_dir = target_path / ".specfuse"

    if specfuse_dir.exists():
        raise ScaffoldExistsError(
            f"{specfuse_dir} already exists; run `specfuse upgrade` to update."
        )

    written: list[str] = []

    for relpath, content in iter_scaffold_files():
        if relpath in _SKIP_SEEDS:
            continue
        dest_rel = _SEED_RENAME.get(relpath, relpath)
        dest = specfuse_dir / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        written.append(dest_rel)

    features_keep = specfuse_dir / "features" / ".gitkeep"
    features_keep.parent.mkdir(parents=True, exist_ok=True)
    features_keep.write_bytes(b"")
    written.append("features/.gitkeep")

    return sorted(written)


# ---------------------------------------------------------------------------
# .claude / .gitignore wiring (FEAT-2026-0026/T05)
# ---------------------------------------------------------------------------

_RULES_BLOCK = (
    "## Specfuse binding rules (read before any work-unit dispatch)\n"
    "@.specfuse/rules/result-contract.md\n"
    "@.specfuse/rules/correlation-ids.md\n"
    "@.specfuse/rules/never-touch.md\n"
    "@.specfuse/rules/security-boundaries.md\n"
)

_RULES_SENTINEL = "@.specfuse/rules/result-contract.md"

_GITIGNORE_SENTINEL = ".specfuse/.loop.lock"

_ALLOW_ENTRIES: list[str] = [
    "Bash(specfuse-loop:*)",
    "Bash(specfuse-lint:*)",
]

_MARKETPLACE_KEY = "specfuse"
_MARKETPLACE_VALUE: dict = {
    "source": {
        "source": "github",
        "repo": "specfuse/specfuse",
    }
}
_PLUGIN_KEY = "specfuse@specfuse"


def _write_gitignore(target_path: Path) -> None:
    snippet = read_scaffold("gitignore.snippet").decode("utf-8")
    gitignore = target_path / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if _GITIGNORE_SENTINEL in existing:
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    gitignore.write_text(existing + snippet, encoding="utf-8")


def _write_claude_md(target_path: Path) -> None:
    claude_dir = target_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    claude_md = claude_dir / "CLAUDE.md"
    if claude_md.exists():
        existing = claude_md.read_text(encoding="utf-8")
        if _RULES_SENTINEL in existing:
            return
        if not existing.endswith("\n"):
            existing += "\n"
        claude_md.write_text(existing + "\n" + _RULES_BLOCK, encoding="utf-8")
    else:
        claude_md.write_text(_RULES_BLOCK, encoding="utf-8")


def _write_settings_json(target_path: Path) -> None:
    claude_dir = target_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path = claude_dir / "settings.json"

    if settings_path.exists():
        original_text = settings_path.read_text(encoding="utf-8")
        data: dict = json.loads(original_text)
    else:
        original_text = None
        data = {}

    perms: dict = data.setdefault("permissions", {})
    allow: list = perms.setdefault("allow", [])
    for entry in _ALLOW_ENTRIES:
        if entry not in allow:
            allow.append(entry)

    marketplaces: dict = data.setdefault("extraKnownMarketplaces", {})
    if _MARKETPLACE_KEY not in marketplaces:
        marketplaces[_MARKETPLACE_KEY] = _MARKETPLACE_VALUE

    plugins: dict = data.setdefault("enabledPlugins", {})
    if _PLUGIN_KEY not in plugins:
        plugins[_PLUGIN_KEY] = True

    new_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if new_text != original_text:
        settings_path.write_text(new_text, encoding="utf-8")


def wire_claude(target: str | Path) -> None:
    """Write .gitignore snippet, .claude/CLAUDE.md, and .claude/settings.json.

    All writes are merge-safe: existing content is preserved and entries are
    added only when absent.
    """
    target_path = Path(target)
    _write_gitignore(target_path)
    _write_claude_md(target_path)
    _write_settings_json(target_path)


def init(target: str | Path, *, ci_check: str | None = None) -> list[str]:
    """Bootstrap a Specfuse-enabled repo: write .specfuse/ then wire .claude/.

    Returns the sorted list of .specfuse/ relpaths written (from init_specfuse).
    """
    written = init_specfuse(target, ci_check=ci_check)
    wire_claude(target)
    return written
