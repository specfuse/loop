#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Parse .specfuse/LEARNINGS.md entries and rank them by BM25 relevance.

`parse_entries` splits the file's `- [<tag>] <text>` bullets (which may wrap
across several lines) into individual entries, skipping the file's header,
`## Format` example, and section headings. `rank` scores those entries against
a query string with a stdlib-only BM25 implementation so a planning consumer
can load only the relevant slice instead of the whole file.

`should_load_whole` and the CLI entrypoint (FEAT-2026-0025/T02) add a
size-threshold fallback: below the threshold the whole file is cheap and safe
to load verbatim, so the CLI signals that instead of slicing.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

_ANCHOR = "<!-- lessons work units append below this line -->"
_BULLET_RE = re.compile(r"^-\s*\[([^\]]+)\]\s*(.*)$")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

_BM25_K1 = 1.5
_BM25_B = 0.75

# Below this many entries, loading the whole file verbatim is cheaper and
# carries no relevance risk, so the CLI signals load-whole instead of slicing.
DEFAULT_LOAD_WHOLE_THRESHOLD = 40

LOAD_WHOLE_SENTINEL = "LEARNINGS-LOAD-WHOLE"

_DEFAULT_LEARNINGS_PATH = (
    Path(__file__).resolve().parent.parent / "LEARNINGS.md"
)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def parse_entries(text: str) -> list[dict]:
    """Parse LEARNINGS.md-style bullets into entry dicts.

    Only lines after the `_ANCHOR` marker (the line the append-only section
    starts below) are considered, which excludes the header prose and the
    `## Format` example bullet. A blank line or a `##`/`#` heading ends the
    current entry; a following non-bullet line is joined onto the current
    entry as a wrapped continuation.
    """
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if _ANCHOR in line:
            start = i + 1
            break

    entries: list[dict] = []
    current: dict | None = None

    def flush() -> None:
        if current is None:
            return
        entry_text = " ".join(part for part in current["parts"] if part).strip()
        if entry_text:
            entries.append(
                {
                    "tag": current["tag"],
                    "text": entry_text,
                    "raw": "\n".join(current["raw_lines"]),
                }
            )

    for line in lines[start:]:
        stripped = line.strip()
        match = _BULLET_RE.match(stripped)
        if match:
            flush()
            current = {
                "tag": match.group(1).strip(),
                "parts": [match.group(2).strip()],
                "raw_lines": [line],
            }
        elif stripped == "" or stripped.startswith("#"):
            flush()
            current = None
        elif current is not None:
            current["parts"].append(stripped)
            current["raw_lines"].append(line)

    flush()
    return entries


def rank(query: str, entries: list[dict], top_n: int | None = None) -> list[dict]:
    """Rank entries by BM25 relevance to query, descending; ties keep original order."""
    n = len(entries)
    if n == 0:
        return []

    docs = [_tokenize(entry["text"]) for entry in entries]
    doc_lens = [len(doc) for doc in docs]
    avgdl = sum(doc_lens) / n if n else 0.0

    doc_freq: dict[str, int] = {}
    for doc in docs:
        for term in set(doc):
            doc_freq[term] = doc_freq.get(term, 0) + 1

    idf = {
        term: math.log(1 + (n - freq + 0.5) / (freq + 0.5))
        for term, freq in doc_freq.items()
    }

    query_terms = _tokenize(query)

    scores = []
    for i, doc in enumerate(docs):
        term_freq: dict[str, int] = {}
        for term in doc:
            term_freq[term] = term_freq.get(term, 0) + 1

        dl = doc_lens[i]
        length_norm = _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl) if avgdl else _BM25_K1
        score = 0.0
        for term in query_terms:
            freq = term_freq.get(term)
            if not freq:
                continue
            score += idf.get(term, 0.0) * (freq * (_BM25_K1 + 1)) / (freq + length_norm)
        scores.append(score)

    order = sorted(range(n), key=lambda i: (-scores[i], i))
    ranked = [entries[i] for i in order]
    return ranked[:top_n] if top_n is not None else ranked


def should_load_whole(entries: list[dict], threshold: int) -> bool:
    """True when there are fewer entries than `threshold` (whole-file load is cheaper)."""
    return len(entries) < threshold


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank .specfuse/LEARNINGS.md entries by relevance to a query, "
        "or signal that the whole file should be loaded when it is small."
    )
    parser.add_argument("query", help="Query text to rank entries against.")
    parser.add_argument(
        "--top", type=int, default=10, help="Max number of ranked entries to print."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_LOAD_WHOLE_THRESHOLD,
        help="Entry count below which the CLI signals load-whole instead of slicing.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=_DEFAULT_LEARNINGS_PATH,
        help="Path to a LEARNINGS.md-formatted file (default: repo's .specfuse/LEARNINGS.md).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    try:
        text = args.file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"learnings_query: cannot read {args.file}: {exc}", file=sys.stderr)
        return 1

    entries = parse_entries(text)
    if not entries:
        print(f"learnings_query: no entries found in {args.file}", file=sys.stderr)
        return 1

    if should_load_whole(entries, args.threshold):
        print(LOAD_WHOLE_SENTINEL)
        return 0

    ranked = rank(args.query, entries, top_n=args.top)
    for entry in ranked:
        print(entry["raw"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
