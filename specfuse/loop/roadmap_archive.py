# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""CLI entry for the single-feature roadmap archiver.

`auto_archive_feature` (loop.py) is the complete archiving algorithm but was
only reachable from `fire_terminal_flips`. This module exposes it on a
command line without editing its behaviour.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .loop import auto_archive_feature


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="roadmap_archive.py",
        description="Archive a done or abandoned feature's roadmap detail section",
    )
    parser.add_argument("feature_id", help="Feature ID (full FEAT-YYYY-NNNN)")
    parser.add_argument(
        "--repo",
        type=str,
        metavar="PATH",
        default=None,
        help="Target repo root containing .specfuse/ (default: current working directory)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo).resolve() if args.repo else Path.cwd()
    outcome = auto_archive_feature(args.feature_id, repo_root)

    print(outcome)
    if outcome.startswith("refused:"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
