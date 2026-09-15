#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Operator surface for the LEARNINGS distillation accept step (#3315).

FEAT-2026-0111/T03 built `propose_distilled_learnings` and
`apply_distilled_decisions` -- a ranked proposal against a word budget, and a
writer that only writes what a human explicitly accepted -- and shipped them
with no caller. Their only callers were their own tests, so the step existed
and nobody could run it. This module is that caller, in the shape
`learnings_query` already established for an operator-facing loop surface.

Two steps, deliberately separate, because the separation is the point:

    python3 -m specfuse.loop.learnings_distil
        Ranks the corpus and prints the proposal with each entry's evidence --
        cost, reach, matched failure signatures, word count -- plus the guard
        review prompt. Writes nothing.

    python3 -m specfuse.loop.learnings_distil --apply decisions.json
        Applies a decisions file: one object per reviewed entry with `tag`,
        `action` (accept / edit / reject) and `text`. Writes only what is
        accepted or edited.

The propose step is read-only by construction rather than by convention: it
never touches the output path, so an operator can look at the ranking without
risking the file. Nothing here prompts or reads stdin, so both halves are safe
in a headless context -- the human's judgement arrives as a decisions file,
not as an interactive answer this module could fabricate.

Note on scope while FEAT-2026-0112 is open: at the binding block's current
budget there is very little room for a distillate, so a real run today will
propose few entries or none. That is a fact about the cap, not about this
surface, and it is why the ranking is worth reading on its own -- the scores
are useful for curating `LEARNINGS.md` itself regardless of how many entries
ever reach the dispatch path.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .loop import (
    LEARNINGS_DISTILLED_WORD_CAP,
    apply_distilled_decisions,
    propose_distilled_learnings,
)


def _render(proposal: dict) -> str:
    lines: list[str] = []
    proposed = proposal.get("proposed") or []
    cut = proposal.get("cut") or []
    cap = proposal.get("word_cap", LEARNINGS_DISTILLED_WORD_CAP)

    lines.append(f"Proposed distillate — {len(proposed)} entries, cap {cap} words")
    lines.append("")
    if not proposed:
        lines.append("  (nothing fits the budget: see FEAT-2026-0112)")
    for entry in proposed:
        lines.append(f"  [{entry.get('tag')}]  "
                     f"words={entry.get('word_count')}  "
                     f"reach={entry.get('reach')}  "
                     f"cost=${entry.get('cost_usd', 0):.2f}")
        sigs = entry.get("failure_signatures") or []
        if sigs:
            lines.append(f"      failure signatures: {', '.join(map(str, sigs))}")
        prompt = entry.get("guard_review_prompt")
        if prompt:
            lines.append(f"      {prompt}")
        lines.append("")
    if cut:
        lines.append(f"Cut for budget: {len(cut)} entries "
                     f"(lowest-ranked first past the cap)")
    caveat = proposal.get("reach_caveat")
    if caveat:
        lines.append("")
        lines.append(caveat)
    return "\n".join(lines)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m specfuse.loop.learnings_distil",
        description="Rank LEARNINGS entries against the distillate word "
                    "budget, and apply a human's per-entry decisions.")
    parser.add_argument("--learnings", type=Path, default=None,
                        help="path to LEARNINGS.md (default: the repo's own)")
    parser.add_argument("--features", type=Path, default=None,
                        help="features dir used to compute reach")
    parser.add_argument("--word-cap", type=int, default=LEARNINGS_DISTILLED_WORD_CAP,
                        help=f"budget to cut the ranking at "
                             f"(default {LEARNINGS_DISTILLED_WORD_CAP})")
    parser.add_argument("--apply", type=Path, default=None, metavar="DECISIONS.json",
                        help="apply a decisions file instead of proposing")
    parser.add_argument("--out", type=Path, default=None,
                        help="distillate path to write (default: the repo's own)")
    args = parser.parse_args(argv)

    if args.apply is not None:
        try:
            decisions = json.loads(args.apply.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"learnings_distil: cannot read {args.apply}: {exc}",
                  file=sys.stderr)
            return 1
        if not isinstance(decisions, list):
            print("learnings_distil: decisions file must be a JSON list",
                  file=sys.stderr)
            return 1
        result = apply_distilled_decisions(decisions, rules_local_path=args.out)
        written = result.get("written") or []
        if written:
            print(f"wrote {len(written)} entr{'y' if len(written) == 1 else 'ies'} "
                  f"to {result.get('path')}")
            for tag in written:
                print(f"  {tag}")
        else:
            print("nothing accepted — the distillate is unchanged")
        return 0

    try:
        proposal = propose_distilled_learnings(
            learnings_path=args.learnings,
            features_dir=args.features,
            word_cap=args.word_cap,
        )
    except OSError as exc:
        print(f"learnings_distil: {exc}", file=sys.stderr)
        return 1
    print(_render(proposal))
    return 0


if __name__ == "__main__":
    sys.exit(main())
